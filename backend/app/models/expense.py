"""
GigMoney Guru - Expense Event Model
"""
from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field


class ExpenseEvent(Document):
    """Individual expense/spending transaction."""
    
    user_id: PydanticObjectId = Field(...)
    
    # Category
    category: str = Field(...)  # "fuel", "food", "data", "withdrawal", "other"
    
    # Amount
    amount: float = Field(..., gt=0)
    currency: str = Field(default="INR")
    
    # Timing
    spent_at: datetime = Field(default_factory=datetime.utcnow)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    description: Optional[str] = None
    payment_method: str = Field(default="upi")  # "upi", "cash", "card"
    
    # Which bucket it was drawn from
    bucket_name: Optional[str] = None
    
    class Settings:
        name = "expense_events"
        indexes = [
            "user_id",
            "spent_at",
            "category",
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "category": "fuel",
                "amount": 500.0,
                "description": "Petrol refill",
                "payment_method": "upi"
            }
        }
