"""
GigMoney Guru - Goal Model
"""
from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field


class Goal(Document):
    """Savings goal defined by user."""
    
    user_id: PydanticObjectId = Field(...)
    
    # Goal details
    name: str = Field(...)  # "New Phone", "Emergency Fund", "Festival Shopping"
    description: Optional[str] = None
    icon: str = Field(default="🎯")
    
    # Target
    target_amount: float = Field(..., gt=0)
    current_amount: float = Field(default=0)
    target_date: Optional[datetime] = None
    
    # Allocation
    monthly_contribution: float = Field(default=0)
    auto_allocate: bool = Field(default=True)
    
    # Status
    status: str = Field(default="active")  # "active", "completed", "paused", "cancelled"
    priority: int = Field(default=5)  # 1-10
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    @property
    def progress_percentage(self) -> float:
        if self.target_amount <= 0:
            return 0
        return min(100, (self.current_amount / self.target_amount) * 100)
    
    @property
    def remaining_amount(self) -> float:
        return max(0, self.target_amount - self.current_amount)
    
    class Settings:
        name = "goals"
        indexes = [
            "user_id",
            "status",
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "name": "New Smartphone",
                "description": "Save for a new phone",
                "target_amount": 15000,
                "current_amount": 5000,
                "monthly_contribution": 2000
            }
        }
