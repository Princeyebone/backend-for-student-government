"""Authentication and user management routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import Annotated
from pydantic import BaseModel
import uuid

from .database import get_session
from .model import User, Role
from .schemas import UserCreate, AdminCreate, EditorCreate, UserResponse, LoginRequest, Token
from .auth import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_refresh_token
from .dependencies import get_current_admin, get_current_active_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register/admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_admin(
    user_data: AdminCreate,
    session: Annotated[Session, Depends(get_session)]
):
    """
    Register a new admin user (UNPROTECTED - disable after first admin is created)
    
    This endpoint should be disabled in production after the first admin is registered.
    """
    # Check if user already exists
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new admin user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        id=uuid.uuid4(),
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        role=Role.ADMIN  # Force admin role
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return new_user


@router.post("/register/editor", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_editor(
    user_data: EditorCreate,
    session: Annotated[Session, Depends(get_session)],
    current_admin: Annotated[User, Depends(get_current_admin)]
):
    """
    Register a new editor user (PROTECTED - only admins can register editors)
    Default password is set to '12345678'
    Editor must change password on first login
    """
    # Check if user already exists
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new editor user with default password '12345678'
    # This will force them to change password on first login
    DEFAULT_EDITOR_PASSWORD = "12345678"
    hashed_password = get_password_hash(DEFAULT_EDITOR_PASSWORD)
    new_user = User(
        id=uuid.uuid4(),
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        role=Role.EDITOR  # Force editor role
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    request: Request,
    session: Annotated[Session, Depends(get_session)]
):
    """
    Login endpoint - returns JWT access token and refresh token
    Checks if user needs to change password (password == '12345678')
    """
    from .audit import create_audit_log
    
    # Find user by email
    statement = select(User).where(User.email == login_data.email)
    user = session.exec(statement).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if password is the default password (must change password)
    DEFAULT_EDITOR_PASSWORD = "12345678"
    must_change_password = verify_password(DEFAULT_EDITOR_PASSWORD, user.hashed_password)
    
    # Create audit log for successful login
    create_audit_log(
        session=session,
        user=user,
        action="login",
        details=f"Successful login for {user.role.value}",
        request=request
    )
    
    # Create access and refresh tokens
    token_data = {"sub": user.email, "role": user.role.value}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value
        ),
        must_change_password=must_change_password,
        refresh_token=refresh_token
    )


@router.post("/login/form", response_model=Token)
def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)]
):
    """
    Login endpoint using OAuth2 password flow (for Swagger UI)
    """
    # Find user by email (username field contains email)
    statement = select(User).where(User.email == form_data.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value
        )
    )


@router.get("/users", response_model=list[UserResponse])
def list_users(
    session: Annotated[Session, Depends(get_session)],
    current_admin: Annotated[User, Depends(get_current_admin)]
):
    """
    List all users (PROTECTED - admin only)
    """
    statement = select(User)
    users = session.exec(statement).all()
    return users


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Change user password (requires authentication)
    """
    # Verify old password
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(request.new_password)
    session.add(current_user)
    session.commit()
    
    return {"message": "Password changed successfully"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: uuid.UUID,
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    current_admin: Annotated[User, Depends(get_current_admin)]
):
    """
    Delete a user (PROTECTED - admin only)
    Only editors can be deleted, not admins
    Admins cannot delete themselves
    """
    from .audit import create_audit_log
    
    # Find user
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deletion of admins
    if user.role == Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete admin users. Only editors can be deleted."
        )
    
    # Prevent admin from deleting themselves (redundant but safe)
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete yourself"
        )
    
    # Create audit log before deletion
    create_audit_log(
        session=session,
        user=current_admin,
        action="delete_user",
        resource="user",
        resource_id=str(user.id),
        details=f"Deleted user {user.name} ({user.email})",
        request=request
    )
    
    # Delete user
    session.delete(user)
    session.commit()
    
    return {"message": f"User {user.name} deleted successfully"}


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token)
def refresh_access_token(
    request: RefreshTokenRequest,
    session: Annotated[Session, Depends(get_session)]
):
    """
    Refresh access token using refresh token
    """
    # Decode refresh token
    token_data = decode_refresh_token(request.refresh_token)
    
    if token_data is None or token_data.email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    statement = select(User).where(User.email == token_data.email)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    new_token_data = {"sub": user.email, "role": user.role.value}
    access_token = create_access_token(data=new_token_data)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role.value
        ),
        refresh_token=request.refresh_token  # Return same refresh token
    )


@router.get("/audit-logs")
def get_audit_logs(
    session: Annotated[Session, Depends(get_session)],
    current_admin: Annotated[User, Depends(get_current_admin)],
    limit: int = 100,
    offset: int = 0
):
    """
    Get audit logs (PROTECTED - admin only)
    Returns recent audit log entries
    """
    from .model import AuditLog
    
    # Get logs ordered by most recent first
    statement = select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
    logs = session.exec(statement).all()
    
    # Convert to dict for JSON response
    logs_data = []
    for log in logs:
        logs_data.append({
            "id": log.id,
            "user_email": log.user_email,
            "user_role": log.user_role,
            "action": log.action,
            "resource": log.resource,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp.isoformat()
        })
    
    return {"logs": logs_data, "total": len(logs_data)}
