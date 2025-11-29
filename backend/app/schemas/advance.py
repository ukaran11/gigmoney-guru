"""
GigMoney Guru - Advance Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class AdvanceOffer(BaseModel):
    """Micro-advance offer."""
    id: str
    principal: float
    fee: float = 0
    total_repayable: float
    
    # Why
    purpose: str
    obligation_name: Optional[str] = None
    shortfall_amount: float = 0
    shortfall_date: Optional[datetime] = None
    
    # Terms
    repayment_date: datetime
    repayment_source: str
    max_repayment_percentage: float
    
    # Risk
    risk_score: str
    risk_explanation: Optional[str] = None
    
    # Impact
    impact_explanation: str
    without_advance_scenario: str
    
    # Guardrails
    weekly_income_estimate: float
    advance_to_income_ratio: float
    
    class Config:
        from_attributes = True


class AdvanceAccept(BaseModel):
    """Accept advance request."""
    advance_id: str


class AdvanceStatus(BaseModel):
    """Current advance status."""
    id: str
    principal: float
    total_repayable: float
    amount_repaid: float
    remaining_balance: float
    
    status: str
    repayment_date: datetime
    days_until_repayment: int
    
    accepted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AdvanceListResponse(BaseModel):
    """List of advances."""
    active_advances: List[AdvanceStatus]
    pending_offers: List[AdvanceOffer]
    past_advances: List[AdvanceStatus]
