"""Pydantic schemas for API requests and responses"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


# User schemas
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    role: str = Field(default="editor")


class AdminCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    role: str = Field(default="admin")


class EditorCreate(UserBase):
    password: Optional[str] = None  # Not required, will use name as default
    role: str = Field(default="editor")


class UserResponse(UserBase):
    id: uuid.UUID
    role: str
    
    class Config:
        from_attributes = True


# Login schema
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Token schema
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    must_change_password: bool = False
    refresh_token: Optional[str] = None


# News schemas
class NewsBase(BaseModel):
    news_head: Optional[str] = None
    news_note: Optional[str] = None
    news_image: Optional[str] = None


class NewsCreate(NewsBase):
    pass


class NewsUpdate(NewsBase):
    pass


class NewsResponse(NewsBase):
    id: int
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


# Leadership schemas
class LeadershipBase(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    year: Optional[str] = None
    note: Optional[str] = None


class LeadershipCreate(LeadershipBase):
    pass


class LeadershipCreate(LeadershipBase):
    pass


class LeadershipUpdate(LeadershipBase):
    pass


class LeadershipResponse(LeadershipBase):
    id: int
    update_at: datetime
    update_by: str
    
    class Config:
        from_attributes = True


# Gallery schemas
class GalleryBase(BaseModel):
    g_image: Optional[str] = None
    g_image_text: Optional[str] = None


class GalleryCreate(GalleryBase):
    pass


class GalleryUpdate(GalleryBase):
    pass


class GalleryResponse(GalleryBase):
    id: int
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


# Home schemas
class HomeBase(BaseModel):
    hero_image: Optional[str] = None
    hero_text: Optional[str] = None
    p_desk_m: Optional[str] = None
    p_desk_m_image: Optional[str] = None


class HomeUpdate(HomeBase):
    pass


class HomeResponse(HomeBase):
    id: int
    updated_at: datetime
    updated_by: str
    
    class Config:
        from_attributes = True


# Contact schemas
class ContactBase(BaseModel):
    address: Optional[str] = None
    c_email: Optional[str] = None
    phone: Optional[str] = None


class ContactUpdate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: int
    update_at: datetime
    update_by: str
    
    class Config:
        from_attributes = True


# ─────────────────── Bills schemas ────────────────────────────────────────────

class DocumentItem(BaseModel):
    """A single attached document (e.g. a PDF report)."""
    name: str = Field(..., min_length=1, max_length=200)
    url: str  = Field(..., min_length=1)


class TimelineItem(BaseModel):
    """A single historical status-change event."""
    label: str = Field(..., min_length=1, max_length=200)
    date: str  = Field(..., description="ISO date string, e.g. '2026-02-22'")


class BillCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=300)
    description: str = Field(..., min_length=10)
    category: str = Field(..., description="One of: Welfare, Academic, Finance, Infrastructure, Events, Constitutional")
    status: str = Field(default="Draft", description="One of: Draft, Under Review, Voting, Approved, Rejected")
    sponsor: str = Field(..., min_length=2, max_length=200)
    date_proposed: str = Field(..., description="ISO date string, e.g. '2026-02-22'")

    # Voting (optional at creation)
    votes_for: Optional[int] = None
    votes_against: Optional[int] = None
    abstain: Optional[int] = None
    total_senators: Optional[int] = None

    # JSON arrays
    documents: Optional[list[DocumentItem]] = None
    timeline: Optional[list[TimelineItem]] = None


class BillUpdate(BaseModel):
    """All fields optional — only provided fields are updated."""
    title: Optional[str] = Field(None, min_length=2, max_length=300)
    description: Optional[str] = Field(None, min_length=10)
    category: Optional[str] = None
    status: Optional[str] = None
    sponsor: Optional[str] = Field(None, min_length=2, max_length=200)
    date_proposed: Optional[str] = None

    votes_for: Optional[int] = None
    votes_against: Optional[int] = None
    abstain: Optional[int] = None
    total_senators: Optional[int] = None

    documents: Optional[list[DocumentItem]] = None
    timeline: Optional[list[TimelineItem]] = None


class BillResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    status: str
    sponsor: str
    date_proposed: str

    votes_for: Optional[int]
    votes_against: Optional[int]
    abstain: Optional[int]
    total_senators: Optional[int]

    documents: Optional[list]
    timeline: Optional[list]

    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True
