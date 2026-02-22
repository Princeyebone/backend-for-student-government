"""Senate Bills router — CRUD with role-based access, auto-timeline, and audit logging."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlmodel import Session, select
from typing import Annotated, Optional
from datetime import datetime, date

from .database import get_session
from .model import Bill, BillCategory, BillStatus, User
from .schemas import BillCreate, BillUpdate
from .dependencies import get_current_admin, get_current_active_user
from .audit import create_audit_log

router = APIRouter(prefix="/api/bills", tags=["Bills"])

# ─────────────────── helpers ─────────────────────────────────────────────────

def _validate_category(value: str) -> BillCategory:
    """Case-insensitive lookup for BillCategory enum."""
    for member in BillCategory:
        if member.value.lower() == value.strip().lower():
            return member
    valid = [m.value for m in BillCategory]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid category '{value}'. Must be one of: {valid}"
    )


def _validate_status(value: str) -> BillStatus:
    """Case-insensitive lookup for BillStatus enum."""
    for member in BillStatus:
        if member.value.lower() == value.strip().lower():
            return member
    valid = [m.value for m in BillStatus]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid status '{value}'. Must be one of: {valid}"
    )


def _parse_date(value: str, field_name: str = "date_proposed") -> date:
    """Parse an ISO date string (YYYY-MM-DD)."""
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format for '{field_name}'. Expected YYYY-MM-DD, got '{value}'."
        )


def _bill_to_dict(bill: Bill) -> dict:
    """Serialise a Bill ORM object to a plain dict suitable for JSON responses."""
    return {
        "id": bill.id,
        "title": bill.title,
        "description": bill.description,
        "category": bill.category.value if isinstance(bill.category, BillCategory) else bill.category,
        "status": bill.status.value if isinstance(bill.status, BillStatus) else bill.status,
        "sponsor": bill.sponsor,
        "date_proposed": bill.date_proposed.isoformat() if isinstance(bill.date_proposed, date) else bill.date_proposed,
        "votes_for": bill.votes_for,
        "votes_against": bill.votes_against,
        "abstain": bill.abstain,
        "total_senators": bill.total_senators,
        "documents": bill.documents or [],
        "timeline": bill.timeline or [],
        "created_at": bill.created_at.isoformat(),
        "updated_at": bill.updated_at.isoformat(),
        "created_by": bill.created_by,
        "updated_by": bill.updated_by,
    }


def _auto_timeline_entry(new_status: BillStatus) -> dict:
    """Generate an automatic timeline entry when the status changes."""
    labels = {
        BillStatus.DRAFT:        "Bill drafted",
        BillStatus.UNDER_REVIEW: "Moved to Under Review",
        BillStatus.VOTING:       "Moved to Voting stage",
        BillStatus.APPROVED:     "Bill Approved",
        BillStatus.REJECTED:     "Bill Rejected",
    }
    return {
        "label": labels.get(new_status, f"Status changed to {new_status.value}"),
        "date": datetime.utcnow().date().isoformat(),
    }


# ─────────────────── public endpoints ────────────────────────────────────────

@router.get("/", response_model=list[dict])
def list_bills(
    session: Annotated[Session, Depends(get_session)],
    status_filter: Optional[str] = Query(
        None, alias="status",
        description="Filter by status: Draft, Under Review, Voting, Approved, Rejected"
    ),
    category_filter: Optional[str] = Query(
        None, alias="category",
        description="Filter by category: Welfare, Academic, Finance, Infrastructure, Events, Constitutional"
    ),
    search: Optional[str] = Query(None, description="Search bills by title (case-insensitive)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List all bills.
    Supports optional filtering by ?status=, ?category=, and ?search= (title).
    Public — no authentication required.
    """
    statement = select(Bill)

    if status_filter:
        status_enum = _validate_status(status_filter)
        statement = statement.where(Bill.status == status_enum)

    if category_filter:
        category_enum = _validate_category(category_filter)
        statement = statement.where(Bill.category == category_enum)

    # Order: most recently proposed first
    statement = statement.order_by(Bill.date_proposed.desc()).offset(offset).limit(limit)
    bills = session.exec(statement).all()

    # Apply title search in Python (portable, avoids dialect-specific ILIKE)
    if search:
        q = search.strip().lower()
        bills = [b for b in bills if q in b.title.lower()]

    return [_bill_to_dict(b) for b in bills]


@router.get("/{bill_id}", response_model=dict)
def get_bill(
    bill_id: int,
    session: Annotated[Session, Depends(get_session)],
):
    """
    Get full details of a single bill.
    Public — no authentication required.
    """
    bill = session.get(Bill, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return _bill_to_dict(bill)


# ─────────────────── admin / editor endpoints ─────────────────────────────────

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_bill(
    bill_data: BillCreate,
    http_request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Create a new Senate bill.
    Accessible to both Admins and Editors.

    - If no `timeline` is provided, an automatic first entry is created.
    - `date_proposed` must be in ISO format: YYYY-MM-DD.
    """
    category = _validate_category(bill_data.category)
    bill_status = _validate_status(bill_data.status)
    proposed_date = _parse_date(bill_data.date_proposed)

    # Serialise nested Pydantic models to plain dicts for JSON storage
    documents = [doc.model_dump() for doc in bill_data.documents] if bill_data.documents else []
    if bill_data.timeline:
        timeline = [t.model_dump() for t in bill_data.timeline]
    else:
        # Auto-generate the first timeline entry
        timeline = [_auto_timeline_entry(bill_status)]

    now = datetime.utcnow()
    new_bill = Bill(
        title=bill_data.title.strip(),
        description=bill_data.description.strip(),
        category=category,
        status=bill_status,
        sponsor=bill_data.sponsor.strip(),
        date_proposed=proposed_date,
        votes_for=bill_data.votes_for,
        votes_against=bill_data.votes_against,
        abstain=bill_data.abstain,
        total_senators=bill_data.total_senators,
        documents=documents,
        timeline=timeline,
        created_at=now,
        updated_at=now,
        created_by=current_user.email,
        updated_by=current_user.email,
    )

    session.add(new_bill)
    session.commit()
    session.refresh(new_bill)

    create_audit_log(
        session=session,
        user=current_user,
        action="create_bill",
        resource="bill",
        resource_id=str(new_bill.id),
        details=f"Created bill: '{new_bill.title}' (status: {new_bill.status.value}, category: {new_bill.category.value})",
        request=http_request,
    )

    return _bill_to_dict(new_bill)


@router.put("/{bill_id}", response_model=dict)
def update_bill(
    bill_id: int,
    bill_data: BillUpdate,
    http_request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Update an existing bill.
    Accessible to both Admins and Editors.

    - Only fields explicitly provided in the request body are updated.
    - If `status` changes, an automatic timeline entry is appended unless a
      manual `timeline` array is also provided in the same request.
    """
    bill = session.get(Bill, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    old_status = bill.status
    old_title = bill.title
    status_changed = False

    # Apply updates for each supplied field
    if bill_data.title is not None:
        bill.title = bill_data.title.strip()

    if bill_data.description is not None:
        bill.description = bill_data.description.strip()

    if bill_data.category is not None:
        bill.category = _validate_category(bill_data.category)

    if bill_data.status is not None:
        new_status = _validate_status(bill_data.status)
        if new_status != old_status:
            status_changed = True
        bill.status = new_status

    if bill_data.sponsor is not None:
        bill.sponsor = bill_data.sponsor.strip()

    if bill_data.date_proposed is not None:
        bill.date_proposed = _parse_date(bill_data.date_proposed)

    if bill_data.votes_for is not None:
        bill.votes_for = bill_data.votes_for

    if bill_data.votes_against is not None:
        bill.votes_against = bill_data.votes_against

    if bill_data.abstain is not None:
        bill.abstain = bill_data.abstain

    if bill_data.total_senators is not None:
        bill.total_senators = bill_data.total_senators

    if bill_data.documents is not None:
        bill.documents = [doc.model_dump() for doc in bill_data.documents]

    # Timeline: if explicitly provided, use it; otherwise auto-append on status change
    current_timeline = list(bill.timeline or [])
    if bill_data.timeline is not None:
        bill.timeline = [t.model_dump() for t in bill_data.timeline]
    elif status_changed:
        current_timeline.append(_auto_timeline_entry(bill.status))
        bill.timeline = current_timeline

    bill.updated_at = datetime.utcnow()
    bill.updated_by = current_user.email

    session.add(bill)
    session.commit()
    session.refresh(bill)

    # Build readable audit detail
    changes = []
    if old_title != bill.title:
        changes.append(f"title: '{old_title}' → '{bill.title}'")
    if status_changed:
        changes.append(f"status: '{old_status.value}' → '{bill.status.value}'")
    detail_str = f"Updated bill #{bill_id}" + (f" ({', '.join(changes)})" if changes else "")

    create_audit_log(
        session=session,
        user=current_user,
        action="update_bill",
        resource="bill",
        resource_id=str(bill.id),
        details=detail_str,
        request=http_request,
    )

    return _bill_to_dict(bill)


@router.delete("/{bill_id}", status_code=status.HTTP_200_OK)
def delete_bill(
    bill_id: int,
    http_request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_admin: Annotated[User, Depends(get_current_admin)],  # Admin-only
):
    """
    Permanently delete a bill.
    Admin only — Editors cannot delete bills.
    """
    bill = session.get(Bill, bill_id)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    title = bill.title

    create_audit_log(
        session=session,
        user=current_admin,
        action="delete_bill",
        resource="bill",
        resource_id=str(bill_id),
        details=f"Deleted bill: '{title}' (was {bill.status.value})",
        request=http_request,
    )

    session.delete(bill)
    session.commit()

    return {"message": f"Bill '{title}' deleted successfully"}
