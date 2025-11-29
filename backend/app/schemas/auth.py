"""
GigMoney Guru - Auth Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserRegister(BaseModel):
    """User registration request."""
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6)
    city: str = Field(default="Mumbai")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Ravi Kumar",
                "phone": "9876543210",
                "email": "ravi@example.com",
                "password": "password123",
                "city": "Mumbai"
            }
        }


class UserLogin(BaseModel):
    """User login request."""
    phone: str = Field(...)
    password: str = Field(...)
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone": "9876543210",
                "password": "password123"
            }
        }


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    user_id: Optional[str] = None
    phone: Optional[str] = None
