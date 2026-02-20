"""Content management routes for news, leadership, gallery, and home sections"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select
from typing import Annotated
import uuid
from datetime import datetime
import os
from pathlib import Path

from .database import get_session
from .model import News, Leadership, Gallary as Gallery, Home, Contact, User, HeroSlide
from .schemas import NewsCreate, NewsUpdate, LeadershipCreate, LeadershipUpdate, GalleryCreate, GalleryUpdate, HomeUpdate, ContactUpdate
from .dependencies import get_current_admin, get_current_active_user
from .audit import create_audit_log

router = APIRouter(prefix="/api", tags=["Content Management"])

# News Management Routes
@router.get("/news/", response_model=list[dict])
def get_news(session: Annotated[Session, Depends(get_session)]):
    """
    Get all news articles
    Returns empty list if no news exists
    """
    try:
        statement = select(News).order_by(News.created_at.desc())
        news_items = session.exec(statement).all()
        
        # Handle empty case gracefully
        if not news_items:
            return []
        
        # Convert to dict format to include all fields properly
        news_list = []
        for item in news_items:
            news_dict = {
                "id": item.id,
                "news_image": item.news_image,
                "news_image_public_id": item.news_image_public_id,
                "news_head": item.news_head,
                "news_note": item.news_note,
                "created_by": item.created_by,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
            news_list.append(news_dict)
        
        return news_list
    except Exception as e:
        # Log the error and return empty list
        print(f"Error fetching news: {e}")
        return []


@router.post("/news/", response_model=dict)
async def create_news(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Create a new news article.
    Expects FormData with:
      - news_head (required)
      - news_note (optional)
      - news_image (optional) - Cloudinary secure_url returned after direct upload
      - news_image_public_id (optional) - Cloudinary public_id
    """
    from .audit import create_audit_log

    # Parse form data
    form = await request.form()

    news_head = (form.get("news_head") or "").strip()
    news_note = (form.get("news_note") or "").strip()
    news_image = (form.get("news_image") or "").strip()          # Cloudinary secure_url
    news_image_public_id = (form.get("news_image_public_id") or "").strip()

    if not news_head:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="News headline is required"
        )

    new_news = News(
        news_image=news_image if news_image else None,
        news_image_public_id=news_image_public_id if news_image_public_id else None,
        news_head=news_head,
        news_note=news_note if news_note else None,
        created_by=current_user.email,
        created_at=datetime.utcnow()
    )

    session.add(new_news)
    session.commit()
    session.refresh(new_news)

    create_audit_log(
        session=session,
        user=current_user,
        action="create_news",
        resource="news",
        resource_id=str(new_news.id),
        details=f"Created news article: {new_news.news_head}",
        request=request
    )

    return {
        "id": new_news.id,
        "news_image": new_news.news_image,
        "news_image_public_id": new_news.news_image_public_id,
        "news_head": new_news.news_head,
        "news_note": new_news.news_note,
        "created_by": new_news.created_by,
        "created_at": new_news.created_at.isoformat(),
        "updated_at": None,
    }


@router.put("/news/{news_id}", response_model=dict)
async def update_news(
    news_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Update a news article.
    Expects FormData with any of:
      - news_head, news_note
      - news_image (Cloudinary secure_url)
      - news_image_public_id (Cloudinary public_id)
    """
    statement = select(News).where(News.id == news_id)
    news_item = session.exec(statement).first()

    if not news_item:
        raise HTTPException(status_code=404, detail="News article not found")

    old_title = news_item.news_head

    form = await request.form()
    news_head = form.get("news_head")
    news_note = form.get("news_note")
    news_image = form.get("news_image")
    news_image_public_id = form.get("news_image_public_id")

    if news_head is not None:
        news_item.news_head = news_head.strip()
    if news_note is not None:
        news_item.news_note = news_note.strip()
    if news_image is not None:
        news_item.news_image = news_image.strip() or None
    if news_image_public_id is not None:
        news_item.news_image_public_id = news_image_public_id.strip() or None

    news_item.updated_at = datetime.utcnow()

    session.add(news_item)
    session.commit()
    session.refresh(news_item)

    create_audit_log(
        session=session,
        user=current_user,
        action="update_news",
        resource="news",
        resource_id=str(news_item.id),
        details=f"Updated news article from '{old_title}' to '{news_item.news_head}'",
        request=request
    )

    return {
        "id": news_item.id,
        "news_image": news_item.news_image,
        "news_image_public_id": news_item.news_image_public_id,
        "news_head": news_item.news_head,
        "news_note": news_item.news_note,
        "created_by": news_item.created_by,
        "created_at": news_item.created_at.isoformat(),
        "updated_at": news_item.updated_at.isoformat() if news_item.updated_at else None,
    }


@router.delete("/news/{news_id}")
def delete_news(
    news_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Delete a news article (authenticated users only)
    """
    # Find news article
    statement = select(News).where(News.id == news_id)
    news_item = session.exec(statement).first()
    
    if not news_item:
        raise HTTPException(status_code=404, detail="News article not found")
    
    # Store values for audit
    title = news_item.news_head
    
    # Create audit log before deletion
    create_audit_log(
        session=session,
        user=current_user,
        action="delete_news",
        resource="news",
        resource_id=str(news_item.id),
        details=f"Deleted news article: {title}",
        request=request
    )
    
    # Delete news article
    session.delete(news_item)
    session.commit()
    
    return {"message": f"News article '{title}' deleted successfully"}


# Leadership Management Routes
@router.get("/leadership/", response_model=list[dict])
def get_leadership(session: Annotated[Session, Depends(get_session)]):
    """
    Get all leadership members
    """
    statement = select(Leadership).order_by(Leadership.update_at.desc())
    leadership_items = session.exec(statement).all()
    
    leadership_list = []
    for item in leadership_items:
        leadership_dict = {
            "id": item.id,
            "name": item.name,
            "role": item.role,
            "image": item.image,
            "image_public_id": item.image_public_id,
            "year": item.year,
            "note": item.note,
            "update_at": item.update_at.isoformat(),
            "update_by": item.update_by,
        }
        leadership_list.append(leadership_dict)

    return leadership_list


@router.post("/leadership/", response_model=dict)
async def create_leadership(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Create a new leadership member.
    Accepts JSON with: name, role, year, note
    OR FormData with additionally: image (Cloudinary secure_url), image_public_id
    """
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        body = await request.json()
        name = body.get("name", "").strip()
        role = body.get("role", "").strip()
        year = body.get("year", "2024/2025").strip()
        note = body.get("note", "").strip()
        image = body.get("image", None)
        image_public_id = body.get("image_public_id", None)
    else:
        form = await request.form()
        name = (form.get("name") or "").strip()
        role = (form.get("role") or "").strip()
        year = (form.get("year") or "2024/2025").strip()
        note = (form.get("note") or "").strip()
        image = (form.get("image") or "").strip() or None
        image_public_id = (form.get("image_public_id") or "").strip() or None

    if not name or not role:
        raise HTTPException(status_code=400, detail="Name and role are required")

    new_leadership = Leadership(
        name=name,
        role=role,
        image=image,
        image_public_id=image_public_id,
        year=year,
        note=note if note else None,
        update_at=datetime.utcnow(),
        update_by=current_user.email
    )

    session.add(new_leadership)
    session.commit()
    session.refresh(new_leadership)

    create_audit_log(
        session=session,
        user=current_user,
        action="create_leadership",
        resource="leadership",
        resource_id=str(new_leadership.id),
        details=f"Added leadership member: {new_leadership.name} as {new_leadership.role}",
        request=request
    )

    return {
        "id": new_leadership.id,
        "name": new_leadership.name,
        "role": new_leadership.role,
        "image": new_leadership.image,
        "image_public_id": new_leadership.image_public_id,
        "year": new_leadership.year,
        "note": new_leadership.note,
        "update_at": new_leadership.update_at.isoformat(),
        "update_by": new_leadership.update_by,
    }


@router.put("/leadership/{leadership_id}", response_model=dict)
async def update_leadership(
    leadership_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Update a leadership member.
    Accepts JSON or FormData with any of: name, role, year, note, image, image_public_id
    """
    statement = select(Leadership).where(Leadership.id == leadership_id)
    leadership_item = session.exec(statement).first()

    if not leadership_item:
        raise HTTPException(status_code=404, detail="Leadership member not found")

    old_name = leadership_item.name
    old_role = leadership_item.role

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        name = body.get("name")
        role = body.get("role")
        year = body.get("year")
        note = body.get("note")
        image = body.get("image")
        image_public_id = body.get("image_public_id")
    else:
        form = await request.form()
        name = form.get("name")
        role = form.get("role")
        year = form.get("year")
        note = form.get("note")
        image = form.get("image")
        image_public_id = form.get("image_public_id")

    if name is not None:
        leadership_item.name = name.strip()
    if role is not None:
        leadership_item.role = role.strip()
    if year is not None:
        leadership_item.year = year.strip()
    if note is not None:
        leadership_item.note = note.strip() or None
    if image is not None:
        leadership_item.image = image.strip() or None
    if image_public_id is not None:
        leadership_item.image_public_id = image_public_id.strip() or None

    leadership_item.update_at = datetime.utcnow()
    leadership_item.update_by = current_user.email

    session.add(leadership_item)
    session.commit()
    session.refresh(leadership_item)

    create_audit_log(
        session=session,
        user=current_user,
        action="update_leadership",
        resource="leadership",
        resource_id=str(leadership_item.id),
        details=f"Updated leadership member '{old_name}' ({old_role}) to '{leadership_item.name}' ({leadership_item.role})",
        request=request
    )

    return {
        "id": leadership_item.id,
        "name": leadership_item.name,
        "role": leadership_item.role,
        "image": leadership_item.image,
        "image_public_id": leadership_item.image_public_id,
        "year": leadership_item.year,
        "note": leadership_item.note,
        "update_at": leadership_item.update_at.isoformat(),
        "update_by": leadership_item.update_by,
    }


@router.delete("/leadership/{leadership_id}")
def delete_leadership(
    leadership_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Delete a leadership member (authenticated users only)
    """
    # Find leadership member
    statement = select(Leadership).where(Leadership.id == leadership_id)
    leadership_item = session.exec(statement).first()
    
    if not leadership_item:
        raise HTTPException(status_code=404, detail="Leadership member not found")
    
    # Store values for audit
    name = leadership_item.name
    role = leadership_item.role
    
    # Create audit log before deletion
    create_audit_log(
        session=session,
        user=current_user,
        action="delete_leadership",
        resource="leadership",
        resource_id=str(leadership_item.id),
        details=f"Deleted leadership member: {name} ({role})",
        request=request
    )
    
    # Delete leadership member
    session.delete(leadership_item)
    session.commit()
    
    return {"message": f"Leadership member '{name}' deleted successfully"}


# Gallery Management Routes
@router.get("/gallery/", response_model=list[dict])
def get_gallery(session: Annotated[Session, Depends(get_session)]):
    """
    Get all gallery items
    """
    statement = select(Gallery).order_by(Gallery.created_at.desc())
    gallery_items = session.exec(statement).all()
    
    gallery_list = []
    for item in gallery_items:
        gallery_dict = {
            "id": item.id,
            "g_image": item.g_image,
            "g_image_text": item.g_image_text,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "created_by": item.created_by,
        }
        gallery_list.append(gallery_dict)
    
    return gallery_list


@router.post("/gallery/", response_model=dict)
async def create_gallery(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Create a new gallery item.
    Expects FormData with:
      - g_image_text (optional caption)
      - g_image (Cloudinary secure_url)
      - g_image_public_id (Cloudinary public_id)
    """
    form = await request.form()
    g_image = (form.get("g_image") or "").strip() or None
    g_image_public_id = (form.get("g_image_public_id") or "").strip() or None
    g_image_text = (form.get("g_image_text") or "").strip() or None

    new_gallery = Gallery(
        g_image=g_image,
        g_image_public_id=g_image_public_id,
        g_image_text=g_image_text,
        created_at=datetime.utcnow(),
        created_by=current_user.email
    )

    session.add(new_gallery)
    session.commit()
    session.refresh(new_gallery)

    create_audit_log(
        session=session,
        user=current_user,
        action="create_gallery",
        resource="gallery",
        resource_id=str(new_gallery.id),
        details=f"Added gallery item: {new_gallery.g_image_text}",
        request=request
    )

    return {
        "id": new_gallery.id,
        "g_image": new_gallery.g_image,
        "g_image_public_id": new_gallery.g_image_public_id,
        "g_image_text": new_gallery.g_image_text,
        "created_at": new_gallery.created_at.isoformat(),
        "updated_at": None,
        "created_by": new_gallery.created_by,
    }


@router.put("/gallery/{gallery_id}", response_model=dict)
async def update_gallery(
    gallery_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Update a gallery item.
    Expects FormData with any of: g_image_text, g_image, g_image_public_id
    """
    statement = select(Gallery).where(Gallery.id == gallery_id)
    gallery_item = session.exec(statement).first()

    if not gallery_item:
        raise HTTPException(status_code=404, detail="Gallery item not found")

    old_text = gallery_item.g_image_text

    form = await request.form()
    g_image = form.get("g_image")
    g_image_public_id = form.get("g_image_public_id")
    g_image_text = form.get("g_image_text")

    if g_image is not None:
        gallery_item.g_image = g_image.strip() or None
    if g_image_public_id is not None:
        gallery_item.g_image_public_id = g_image_public_id.strip() or None
    if g_image_text is not None:
        gallery_item.g_image_text = g_image_text.strip() or None

    gallery_item.updated_at = datetime.utcnow()
    gallery_item.created_by = current_user.email

    session.add(gallery_item)
    session.commit()
    session.refresh(gallery_item)

    create_audit_log(
        session=session,
        user=current_user,
        action="update_gallery",
        resource="gallery",
        resource_id=str(gallery_item.id),
        details=f"Updated gallery item from '{old_text}' to '{gallery_item.g_image_text}'",
        request=request
    )

    return {
        "id": gallery_item.id,
        "g_image": gallery_item.g_image,
        "g_image_public_id": gallery_item.g_image_public_id,
        "g_image_text": gallery_item.g_image_text,
        "created_at": gallery_item.created_at.isoformat(),
        "updated_at": gallery_item.updated_at.isoformat() if gallery_item.updated_at else None,
        "created_by": gallery_item.created_by,
    }


@router.delete("/gallery/{gallery_id}")
def delete_gallery(
    gallery_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Delete a gallery item (authenticated users only)
    """
    # Find gallery item
    statement = select(Gallery).where(Gallery.id == gallery_id)
    gallery_item = session.exec(statement).first()
    
    if not gallery_item:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    # Store values for audit
    text = gallery_item.g_image_text
    
    # Create audit log before deletion
    create_audit_log(
        session=session,
        user=current_user,
        action="delete_gallery",
        resource="gallery",
        resource_id=str(gallery_item.id),
        details=f"Deleted gallery item: {text}",
        request=request
    )
    
    # Delete gallery item
    session.delete(gallery_item)
    session.commit()
    
    return {"message": f"Gallery item '{text}' deleted successfully"}


# Home Section Management Routes
@router.get("/home/", response_model=dict)
def get_home(session: Annotated[Session, Depends(get_session)]):
    """
    Get home section data (hero image, text, etc.)
    """
    # Get the most recently updated home record
    statement = select(Home).order_by(Home.updated_at.desc()).limit(1)
    home_data = session.exec(statement).first()
    
    if not home_data:
        raise HTTPException(status_code=404, detail="Home section data not found")
    
    return {
        "id": home_data.id,
        "hero_image": home_data.hero_image,
        "hero_image_public_id": home_data.hero_image_public_id,
        "hero_text": home_data.hero_text,
        "p_desk_m": home_data.p_desk_m,
        "p_desk_m_image": home_data.p_desk_m_image,
        "p_desk_m_image_public_id": home_data.p_desk_m_image_public_id,
        "updated_at": home_data.updated_at.isoformat(),
        "updated_by": home_data.updated_by,
    }


@router.put("/home/", response_model=dict)
async def update_home(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Update home section data (authenticated users only).
    Accepts FormData with any of:
      - hero_image, hero_image_public_id (Cloudinary secure_url + public_id)
      - hero_text
      - p_desk_m (president message text)
      - p_desk_m_image, p_desk_m_image_public_id (Cloudinary secure_url + public_id)
    """
    form = await request.form()

    hero_image = (form.get("hero_image") or "").strip() or None
    hero_image_public_id = (form.get("hero_image_public_id") or "").strip() or None
    hero_text = (form.get("hero_text") or "").strip() or None
    p_desk_m = (form.get("p_desk_m") or "").strip() or None
    p_desk_m_image = (form.get("p_desk_m_image") or "").strip() or None
    p_desk_m_image_public_id = (form.get("p_desk_m_image_public_id") or "").strip() or None

    # Get the most recent home record to update
    statement = select(Home).order_by(Home.updated_at.desc()).limit(1)
    existing_home = session.exec(statement).first()

    if not existing_home:
        # Create first home record if none exists
        new_home = Home(
            hero_image=hero_image,
            hero_image_public_id=hero_image_public_id,
            hero_text=hero_text,
            p_desk_m=p_desk_m,
            p_desk_m_image=p_desk_m_image,
            p_desk_m_image_public_id=p_desk_m_image_public_id,
            updated_at=datetime.utcnow(),
            updated_by=current_user.email
        )

        session.add(new_home)
        session.commit()
        session.refresh(new_home)

        create_audit_log(
            session=session,
            user=current_user,
            action="create_home",
            resource="home",
            resource_id=str(new_home.id),
            details="Created home section data",
            request=request
        )

        return {
            "id": new_home.id,
            "hero_image": new_home.hero_image,
            "hero_image_public_id": new_home.hero_image_public_id,
            "hero_text": new_home.hero_text,
            "p_desk_m": new_home.p_desk_m,
            "p_desk_m_image": new_home.p_desk_m_image,
            "p_desk_m_image_public_id": new_home.p_desk_m_image_public_id,
            "updated_at": new_home.updated_at.isoformat(),
            "updated_by": new_home.updated_by,
        }
    else:
        # Update existing home record (only update fields that are provided)
        if hero_image is not None:
            existing_home.hero_image = hero_image
        if hero_image_public_id is not None:
            existing_home.hero_image_public_id = hero_image_public_id
        if hero_text is not None:
            existing_home.hero_text = hero_text
        if p_desk_m is not None:
            existing_home.p_desk_m = p_desk_m
        if p_desk_m_image is not None:
            existing_home.p_desk_m_image = p_desk_m_image
        if p_desk_m_image_public_id is not None:
            existing_home.p_desk_m_image_public_id = p_desk_m_image_public_id

        existing_home.updated_at = datetime.utcnow()
        existing_home.updated_by = current_user.email

        session.add(existing_home)
        session.commit()
        session.refresh(existing_home)

        create_audit_log(
            session=session,
            user=current_user,
            action="update_home",
            resource="home",
            resource_id=str(existing_home.id),
            details="Updated home section",
            request=request
        )

        return {
            "id": existing_home.id,
            "hero_image": existing_home.hero_image,
            "hero_image_public_id": existing_home.hero_image_public_id,
            "hero_text": existing_home.hero_text,
            "p_desk_m": existing_home.p_desk_m,
            "p_desk_m_image": existing_home.p_desk_m_image,
            "p_desk_m_image_public_id": existing_home.p_desk_m_image_public_id,
            "updated_at": existing_home.updated_at.isoformat(),
            "updated_by": existing_home.updated_by,
        }


# Contact Management Routes
@router.get("/contact/", response_model=dict)
def get_contact(session: Annotated[Session, Depends(get_session)]):
    """
    Get contact information
    """
    # Get the most recently updated contact record
    statement = select(Contact).order_by(Contact.update_at.desc()).limit(1)
    contact_data = session.exec(statement).first()
    
    if not contact_data:
        raise HTTPException(status_code=404, detail="Contact information not found")
    
    return {
        "id": contact_data.id,
        "address": contact_data.address,
        "c_email": contact_data.c_email,
        "phone": contact_data.phone,
        "update_at": contact_data.update_at.isoformat(),
        "update_by": contact_data.update_by,
    }


@router.put("/contact/", response_model=dict)
def update_contact(
    contact_data: ContactUpdate,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Update contact information (authenticated users only)
    """
    # Get the most recent contact record to update
    statement = select(Contact).order_by(Contact.update_at.desc()).limit(1)
    existing_contact = session.exec(statement).first()
    
    if not existing_contact:
        # Create first contact record if none exists
        new_contact = Contact(
            address=contact_data.address,
            c_email=contact_data.c_email,
            phone=contact_data.phone,
            update_at=datetime.utcnow(),
            update_by=current_user.email
        )
        
        session.add(new_contact)
        session.commit()
        session.refresh(new_contact)
        
        # Create audit log
        create_audit_log(
            session=session,
            user=current_user,
            action="create_contact",
            resource="contact",
            resource_id=str(new_contact.id),
            details=f"Created contact information",
            request=request
        )
        
        return {
            "id": new_contact.id,
            "address": new_contact.address,
            "c_email": new_contact.c_email,
            "phone": new_contact.phone,
            "update_at": new_contact.update_at.isoformat(),
            "update_by": new_contact.update_by,
        }
    else:
        # Store old values for audit
        old_email = existing_contact.c_email
        
        # Update existing contact record
        if contact_data.address is not None:
            existing_contact.address = contact_data.address
        if contact_data.c_email is not None:
            existing_contact.c_email = contact_data.c_email
        if contact_data.phone is not None:
            existing_contact.phone = contact_data.phone
            
        existing_contact.update_at = datetime.utcnow()
        existing_contact.update_by = current_user.email
        
        session.add(existing_contact)
        session.commit()
        session.refresh(existing_contact)
        
        # Create audit log
        create_audit_log(
            session=session,
            user=current_user,
            action="update_contact",
            resource="contact",
            resource_id=str(existing_contact.id),
            details=f"Updated contact email from '{old_email}' to '{existing_contact.c_email}'",
            request=request
        )
        
        return {
            "id": existing_contact.id,
            "address": existing_contact.address,
            "c_email": existing_contact.c_email,
            "phone": existing_contact.phone,
            "update_at": existing_contact.update_at.isoformat(),
            "update_by": existing_contact.update_by,
        }


# Hero Slides Management Routes
@router.get("/hero-slides/", response_model=list[dict])
def get_hero_slides(session: Annotated[Session, Depends(get_session)]):
    """
    Get all active hero slides ordered by order_index
    """
    statement = select(HeroSlide).where(HeroSlide.is_active == True).order_by(HeroSlide.order_index.asc())
    slides = session.exec(statement).all()
    
    slides_list = []
    for slide in slides:
        slide_dict = {
            "id": slide.id,
            "image_url": slide.image_url,
            "image_public_id": slide.image_public_id,
            "caption": slide.caption,
            "order_index": slide.order_index,
            "is_active": slide.is_active,
            "created_at": slide.created_at.isoformat(),
            "created_by": slide.created_by,
            "updated_at": slide.updated_at.isoformat() if slide.updated_at else None,
            "updated_by": slide.updated_by,
        }
        slides_list.append(slide_dict)
    
    return slides_list


@router.post("/hero-slides/", response_model=dict)
async def create_hero_slide(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Create a new hero slide.
    Expects FormData with:
      - image_url (required) - Cloudinary secure_url
      - image_public_id (required) - Cloudinary public_id
      - caption (optional) - Slide caption/text
      - order_index (optional) - Display order (default: next available)
    """
    form = await request.form()
    
    image_url = (form.get("image_url") or "").strip()
    image_public_id = (form.get("image_public_id") or "").strip()
    caption = (form.get("caption") or "").strip() or None
    order_index = form.get("order_index")
    
    if not image_url or not image_public_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image URL and public ID are required"
        )
    
    # If no order_index provided, set it to the next available
    if order_index is None:
        statement = select(HeroSlide).order_by(HeroSlide.order_index.desc()).limit(1)
        last_slide = session.exec(statement).first()
        order_index = (last_slide.order_index + 1) if last_slide else 0
    else:
        try:
            order_index = int(order_index)
        except ValueError:
            order_index = 0
    
    new_slide = HeroSlide(
        image_url=image_url,
        image_public_id=image_public_id,
        caption=caption,
        order_index=order_index,
        is_active=True,
        created_at=datetime.utcnow(),
        created_by=current_user.email
    )
    
    session.add(new_slide)
    session.commit()
    session.refresh(new_slide)
    
    create_audit_log(
        session=session,
        user=current_user,
        action="create_hero_slide",
        resource="hero_slide",
        resource_id=str(new_slide.id),
        details=f"Created hero slide: {new_slide.caption or 'No caption'}",
        request=request
    )
    
    return {
        "id": new_slide.id,
        "image_url": new_slide.image_url,
        "image_public_id": new_slide.image_public_id,
        "caption": new_slide.caption,
        "order_index": new_slide.order_index,
        "is_active": new_slide.is_active,
        "created_at": new_slide.created_at.isoformat(),
        "created_by": new_slide.created_by,
        "updated_at": None,
        "updated_by": None,
    }


@router.put("/hero-slides/{slide_id}", response_model=dict)
async def update_hero_slide(
    slide_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Update a hero slide.
    Expects FormData with any of: image_url, image_public_id, caption, order_index, is_active
    """
    statement = select(HeroSlide).where(HeroSlide.id == slide_id)
    slide = session.exec(statement).first()
    
    if not slide:
        raise HTTPException(status_code=404, detail="Hero slide not found")
    
    old_caption = slide.caption
    
    form = await request.form()
    image_url = form.get("image_url")
    image_public_id = form.get("image_public_id")
    caption = form.get("caption")
    order_index = form.get("order_index")
    is_active = form.get("is_active")
    
    if image_url is not None:
        slide.image_url = image_url.strip()
    if image_public_id is not None:
        slide.image_public_id = image_public_id.strip()
    if caption is not None:
        slide.caption = caption.strip() or None
    if order_index is not None:
        try:
            slide.order_index = int(order_index)
        except ValueError:
            pass  # Keep existing order_index if invalid
    if is_active is not None:
        slide.is_active = is_active.lower() in ('true', '1', 'yes', 'on')
    
    slide.updated_at = datetime.utcnow()
    slide.updated_by = current_user.email
    
    session.add(slide)
    session.commit()
    session.refresh(slide)
    
    create_audit_log(
        session=session,
        user=current_user,
        action="update_hero_slide",
        resource="hero_slide",
        resource_id=str(slide.id),
        details=f"Updated hero slide from '{old_caption}' to '{slide.caption}'",
        request=request
    )
    
    return {
        "id": slide.id,
        "image_url": slide.image_url,
        "image_public_id": slide.image_public_id,
        "caption": slide.caption,
        "order_index": slide.order_index,
        "is_active": slide.is_active,
        "created_at": slide.created_at.isoformat(),
        "created_by": slide.created_by,
        "updated_at": slide.updated_at.isoformat() if slide.updated_at else None,
        "updated_by": slide.updated_by,
    }


@router.delete("/hero-slides/{slide_id}")
def delete_hero_slide(
    slide_id: int,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Delete a hero slide (authenticated users only)
    """
    # Find hero slide
    statement = select(HeroSlide).where(HeroSlide.id == slide_id)
    slide = session.exec(statement).first()
    
    if not slide:
        raise HTTPException(status_code=404, detail="Hero slide not found")
    
    # Store values for audit
    caption = slide.caption or "No caption"
    
    # Create audit log before deletion
    create_audit_log(
        session=session,
        user=current_user,
        action="delete_hero_slide",
        resource="hero_slide",
        resource_id=str(slide.id),
        details=f"Deleted hero slide: {caption}",
        request=request
    )
    
    # Delete hero slide
    session.delete(slide)
    session.commit()
    
    return {"message": f"Hero slide '{caption}' deleted successfully"}


@router.put("/hero-slides/reorder", response_model=dict)
async def reorder_hero_slides(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Reorder hero slides.
    Expects JSON with: [{"id": 1, "order_index": 0}, {"id": 2, "order_index": 1}, ...]
    """
    try:
        body = await request.json()
        slide_orders = body.get("slides", [])
        
        if not slide_orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No slide order data provided"
            )
        
        # Update each slide's order_index
        updated_count = 0
        for slide_data in slide_orders:
            slide_id = slide_data.get("id")
            order_index = slide_data.get("order_index")
            
            if slide_id is not None and order_index is not None:
                statement = select(HeroSlide).where(HeroSlide.id == slide_id)
                slide = session.exec(statement).first()
                
                if slide:
                    slide.order_index = int(order_index)
                    slide.updated_at = datetime.utcnow()
                    slide.updated_by = current_user.email
                    session.add(slide)
                    updated_count += 1
        
        session.commit()
        
        create_audit_log(
            session=session,
            user=current_user,
            action="reorder_hero_slides",
            resource="hero_slide",
            resource_id=None,
            details=f"Reordered {updated_count} hero slides",
            request=request
        )
        
        return {"message": f"Successfully reordered {updated_count} hero slides"}
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reorder slides: {str(e)}"
        )