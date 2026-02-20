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
