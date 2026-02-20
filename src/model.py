from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class Role(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"

class User(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field(min_length=8)
    role : Role = Field(default=Role.EDITOR)

class Home(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hero_image: Optional[str] = Field(index=True)
    hero_image_public_id: Optional[str] = Field(index=True)
    hero_text: Optional[str] = Field(index=True)
    p_desk_m: Optional[str] = Field(index=True)
    p_desk_m_image: Optional[str] = Field(index=True)
    p_desk_m_image_public_id: Optional[str] = Field(index=True)
    updated_at: datetime
    updated_by: str

class HeroSlide(SQLModel, table=True):
    """Hero slideshow images with captions"""
    id: Optional[int] = Field(default=None, primary_key=True)
    image_url: str = Field(index=True)  # Cloudinary secure_url
    image_public_id: str = Field(index=True)  # Cloudinary public_id
    caption: Optional[str] = Field(default=None)  # Slide caption/text
    order_index: int = Field(default=0, index=True)  # Display order
    is_active: bool = Field(default=True, index=True)  # Enable/disable slide
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

class Leadership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = Field(index=True)
    role: Optional[str] = Field(index=True)
    image: Optional[str] = Field(index=True)
    image_public_id: Optional[str] = Field(index=True)
    year: Optional[str] = Field(index=True)
    note: Optional[str] = Field(index=True)
    update_at: datetime
    update_by: str

class News(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    news_image: Optional[str] = Field(index=True)
    news_image_public_id: Optional[str] = Field(index=True)
    news_head: Optional[str]  = Field(index=True)
    news_note: Optional[str] = Field(index=True)
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class Gallary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    g_image: Optional[str] = Field(index=True)
    g_image_text: Optional[str] = Field(index=True)
    g_image_public_id: Optional[str] = Field(index=True)
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None

class Contact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    address: Optional[str]
    c_email: Optional[str]
    phone: Optional[str]
    update_by: str
    update_at: datetime


class AuditLog(SQLModel, table=True):
    """Audit log to track user actions and system events"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(foreign_key="user.id", index=True)
    user_email: str = Field(index=True)
    user_role: str = Field(index=True)
    action: str = Field(index=True)  # e.g., "login", "create_news", "update_leadership", "delete_user"
    resource: Optional[str] = None  # e.g., "news", "leadership", "user"
    resource_id: Optional[str] = None  # ID of the affected resource
    details: Optional[str] = None  # Additional details about the action
    ip_address: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)


