"""
GigMoney Guru - Obligation Model
"""
from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field


class Obligation(Document):
    """Recurring financial obligation (rent, EMI, fees, etc.)."""
    
    user_id: PydanticObjectId = Field(...)
    
    # Obligation details
    name: str = Field(...)  # "Rent", "Bike EMI", "School Fees", "Netflix"
    category: str = Field(...)  # "rent", "emi", "education", "subscription", "tax", "other"
    
    # Amount
    amount: float = Field(..., gt=0)
    currency: str = Field(default="INR")
    
    # Schedule
    frequency: str = Field(default="monthly")  # "monthly", "quarterly", "yearly", "one_time"
    due_day: int = Field(default=1, ge=1, le=31)  # Day of month
    
    # For flexible obligations
    is_flexible: bool = Field(default=False)
    flexible_window_days: int = Field(default=0)  # Can pay +/- these days
    
    # Status
    is_active: bool = Field(default=True)
    
    # Linked bucket
    bucket_name: Optional[str] = None  # Which bucket pays for this
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    next_due_date: Optional[datetime] = None
    last_paid_date: Optional[datetime] = None
    
    class Settings:
        name = "obligations"
        indexes = [
            "user_id",
            "category",
            "next_due_date",
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Room Rent",
                "category": "rent",
                "amount": 8000,
                "frequency": "monthly",
                "due_day": 5,
                "bucket_name": "rent"
            }
        }
