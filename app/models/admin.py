from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class AdminUser(BaseModel):
    id: UUID
    user_id: str  # Supabase user ID
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_super_admin: bool = False
    last_login: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime
    updated_at: datetime

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    is_super_admin: bool = False

class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_super_admin: Optional[bool] = None

class AdminUserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_super_admin: bool
    last_login: Optional[datetime] = None
    login_count: int
    created_at: datetime
    updated_at: datetime 