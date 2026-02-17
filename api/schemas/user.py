"""
TechCare Bot - User Schemas
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base User Schema"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """User Creation Schema"""
    password: str = Field(..., min_length=8, max_length=100)

    @validator("password")
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain digit")
        return v


class UserLogin(BaseModel):
    """User Login Schema"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User Update Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    company: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """User Response Schema"""
    id: str
    is_active: bool
    is_admin: bool
    repairs_this_month: int
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT Token Response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
