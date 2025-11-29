"""
GigMoney Guru - Platform Account Model
"""
from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field


class PlatformAccount(Document):
    """Linked gig platform account."""
    
    user_id: PydanticObjectId = Field(...)
    
    # Platform info
    platform_name: str = Field(...)  # "uber", "ola", "swiggy", "zomato", "zepto", "blinkit"
    platform_type: str = Field(...)  # "rides", "food_delivery", "quick_commerce"
    
    # Mock connection status
    is_connected: bool = Field(default=True)
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    
    # For demo - mock account ID
    mock_account_id: Optional[str] = None
    
    class Settings:
        name = "platform_accounts"
        
    class Config:
        json_schema_extra = {
            "example": {
                "platform_name": "uber",
                "platform_type": "rides",
                "is_connected": True
            }
        }
