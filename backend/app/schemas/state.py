"""
GigMoney Guru - State Schemas
"""
from typing import Optional, List, Dict
from datetime import datetime, date
from pydantic import BaseModel, Field


class BucketState(BaseModel):
    """Current state of a bucket."""
    name: str
    display_name: str
    icon: str
    color: str
    target_amount: float
    current_balance: float
    progress_percentage: float
    today_allocation: float = 0
    priority: int
    
    class Config:
        from_attributes = True


class IncomeBreakdown(BaseModel):
    """Income breakdown by source."""
    source_name: str
    platform_type: Optional[str] = None
    amount: float
    count: int = 1


class ObligationStatus(BaseModel):
    """Upcoming obligation status."""
    id: str
    name: str
    category: str
    amount: float
    due_date: datetime
    days_until_due: int
    risk_level: str  # "low", "medium", "high"
    bucket_balance: float
    shortfall: float = 0
    
    class Config:
        from_attributes = True


class AllocationPlan(BaseModel):
    """Today's allocation plan."""
    total_income: float
    allocations: Dict[str, float]  # bucket_name -> amount
    safe_to_spend: float
    explanation: Optional[str] = None


class DailyState(BaseModel):
    """Complete daily dashboard state."""
    # Date
    date: date
    greeting: str
    
    # Income
    today_earnings: float
    income_breakdown: List[IncomeBreakdown]
    
    # Buckets
    buckets: List[BucketState]
    
    # Allocations
    today_allocations: AllocationPlan
    safe_to_spend: float
    
    # Upcoming obligations
    upcoming_obligations: List[ObligationStatus]
    
    # Alerts
    has_warnings: bool = False
    warnings: List[str] = []
    
    # Streak / gamification
    safe_spending_streak: int = 0
    
    # Micro-advance
    has_active_advance: bool = False
    has_advance_offer: bool = False


class ForecastDay(BaseModel):
    """Single day in forecast."""
    date: date
    day_name: str
    is_weekend: bool
    
    # Projected
    projected_income: float
    projected_expenses: float
    
    # Obligations due
    obligations_due: List[str] = []
    obligation_amount: float = 0
    
    # Balance
    start_balance: float
    end_balance: float
    
    # Status
    status: str  # "safe", "tight", "shortfall"
    

class ForecastResponse(BaseModel):
    """30-day forecast response."""
    forecast: List[ForecastDay]
    chart_image_base64: Optional[str] = None
    summary: str
    risk_days: int = 0
    shortfall_days: int = 0
