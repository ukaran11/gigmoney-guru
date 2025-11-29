"""
GigMoney Guru - User Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserProfile(BaseModel):
    """User profile response."""
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    city: str
    platforms_used: List[str] = []
    monthly_rent: float = 0
    has_emi: bool = False
    preferred_language: str = "hinglish"
    onboarding_completed: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """User profile update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    city: Optional[str] = None
    platforms_used: Optional[List[str]] = None
    monthly_rent: Optional[float] = None
    has_emi: Optional[bool] = None
    preferred_language: Optional[str] = None
    onboarding_completed: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "platforms_used": ["uber", "swiggy", "zepto"],
                "monthly_rent": 8000,
                "has_emi": True,
                "onboarding_completed": True
            }
        }


class PlatformConnect(BaseModel):
    """Platform connection request."""
    platform_name: str  # "uber", "swiggy", etc.
    platform_type: str  # "rides", "food_delivery", "quick_commerce"
    
    class Config:
        json_schema_extra = {
            "example": {
                "platform_name": "uber",
                "platform_type": "rides"
            }
        }
