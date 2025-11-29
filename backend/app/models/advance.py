"""
GigMoney Guru - Micro Advance Model
"""
from datetime import datetime
from typing import Optional, List
from beanie import Document, PydanticObjectId
from pydantic import Field


class MicroAdvance(Document):
    """Micro-advance / short-term loan from future earnings."""
    
    user_id: PydanticObjectId = Field(...)
    
    # Advance details
    principal: float = Field(..., gt=0)  # Amount borrowed
    purpose: str = Field(...)  # "emi_shortfall", "rent_shortfall", "emergency"
    
    # For which obligation
    obligation_id: Optional[PydanticObjectId] = None
    obligation_name: Optional[str] = None
    
    # Terms (no interest for MVP, but structure supports it)
    fee: float = Field(default=0)  # Any processing fee
    total_repayable: float = Field(...)  # principal + fee
    
    # Repayment schedule
    repayment_date: datetime = Field(...)  # When it should be repaid
    repayment_source: str = Field(default="weekend_earnings")  # Expected source
    max_repayment_percentage: float = Field(default=40)  # Max % of earnings to use
    
    # Status
    status: str = Field(default="offered")  # "offered", "accepted", "active", "repaid", "defaulted"
    
    # Risk assessment
    risk_score: str = Field(default="low")  # "low", "medium", "high"
    risk_explanation: Optional[str] = None
    
    # Actual repayment tracking
    amount_repaid: float = Field(default=0)
    repayment_events: List[dict] = Field(default_factory=list)
    
    # Timestamps
    offered_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    disbursed_at: Optional[datetime] = None
    repaid_at: Optional[datetime] = None
    
    # Guardrails
    weekly_income_estimate: float = Field(default=0)
    advance_to_income_ratio: float = Field(default=0)
    
    @property
    def is_fully_repaid(self) -> bool:
        return self.amount_repaid >= self.total_repayable
    
    @property
    def remaining_balance(self) -> float:
        return max(0, self.total_repayable - self.amount_repaid)
    
    class Settings:
        name = "micro_advances"
        indexes = [
            "user_id",
            "status",
            "repayment_date",
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "principal": 1000,
                "purpose": "emi_shortfall",
                "obligation_name": "Bike EMI",
                "total_repayable": 1000,
                "repayment_date": "2024-01-14T00:00:00",
                "status": "offered",
                "risk_score": "low"
            }
        }
