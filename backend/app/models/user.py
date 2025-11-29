"""
GigMoney Guru - User Model
"""
from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import Field, EmailStr


class User(Document):
    """User document model for MongoDB."""
    
    # Basic info
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    email: Optional[EmailStr] = None
    city: str = Field(default="Mumbai")
    
    # Auth
    password_hash: str = Field(...)
    
    # Profile
    platforms_used: List[str] = Field(default_factory=list)  # ["uber", "swiggy", "zepto"]
    monthly_rent: float = Field(default=0)
    has_emi: bool = Field(default=False)
    
    # Settings
    preferred_language: str = Field(default="hinglish")  # "english", "hindi", "hinglish"
    notification_enabled: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Onboarding
    onboarding_completed: bool = Field(default=False)
    
    class Settings:
        name = "users"
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Ravi Kumar",
                "phone": "9876543210",
                "email": "ravi@example.com",
                "city": "Mumbai",
                "platforms_used": ["uber", "swiggy", "zepto"],
                "monthly_rent": 8000,
                "has_emi": True
            }
        }
