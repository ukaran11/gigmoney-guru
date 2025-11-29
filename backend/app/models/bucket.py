"""
GigMoney Guru - Bucket Model
"""
from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field


class Bucket(Document):
    """Money bucket/envelope for categorized savings."""
    
    user_id: PydanticObjectId = Field(...)
    
    # Bucket identity
    name: str = Field(...)  # "rent", "emi", "tax", "fuel", "emergency", "discretionary", "savings"
    display_name: str = Field(...)  # "Kiraya", "Bike EMI", "Tax", etc.
    icon: str = Field(default="💰")
    color: str = Field(default="#4CAF50")  # Hex color for UI
    
    # Target and balance
    target_amount: float = Field(default=0)  # Monthly target
    current_balance: float = Field(default=0)
    
    # Allocation rules
    allocation_type: str = Field(default="percentage")  # "percentage", "fixed", "remainder"
    allocation_value: float = Field(default=0)  # % or fixed amount
    priority: int = Field(default=5)  # 1-10, lower = higher priority
    
    # For obligations
    linked_obligation_id: Optional[PydanticObjectId] = None
    
    # Status
    is_active: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_allocation_at: Optional[datetime] = None
    
    class Settings:
        name = "buckets"
        indexes = [
            "user_id",
            "name",
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "rent",
                "display_name": "Kiraya (Rent)",
                "icon": "🏠",
                "color": "#FF9800",
                "target_amount": 8000,
                "current_balance": 2500,
                "allocation_type": "percentage",
                "allocation_value": 25,
                "priority": 1
            }
        }
