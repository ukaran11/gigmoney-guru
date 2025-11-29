"""
GigMoney Guru - Income Event Model
"""
from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field


class IncomeEvent(Document):
    """Individual income transaction."""
    
    user_id: PydanticObjectId = Field(...)
    
    # Source
    source_type: str = Field(...)  # "platform", "upi", "cash", "other"
    source_name: str = Field(...)  # "uber", "swiggy", "gpay", etc.
    platform_type: Optional[str] = None  # "rides", "food_delivery", "quick_commerce"
    
    # Amount
    amount: float = Field(..., gt=0)
    currency: str = Field(default="INR")
    
    # Timing
    earned_at: datetime = Field(default_factory=datetime.utcnow)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    description: Optional[str] = None
    trip_id: Optional[str] = None  # For platform earnings
    
    # Processing status
    allocated: bool = Field(default=False)
    allocation_id: Optional[str] = None
    
    class Settings:
        name = "income_events"
        indexes = [
            "user_id",
            "earned_at",
            "source_name",
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "source_type": "platform",
                "source_name": "uber",
                "platform_type": "rides",
                "amount": 450.0,
                "description": "Morning rides - 5 trips"
            }
        }
