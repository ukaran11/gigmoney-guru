"""
GigMoney Guru - Goal Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    """Create goal request."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: str = "🎯"
    target_amount: float = Field(..., gt=0)
    target_date: Optional[datetime] = None
    monthly_contribution: float = Field(default=0, ge=0)
    auto_allocate: bool = True
    priority: int = Field(default=5, ge=1, le=10)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "New Smartphone",
                "description": "Save for a new phone",
                "target_amount": 15000,
                "monthly_contribution": 2000
            }
        }


class GoalUpdate(BaseModel):
    """Update goal request."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[datetime] = None
    monthly_contribution: Optional[float] = Field(None, ge=0)
    auto_allocate: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[str] = None


class GoalResponse(BaseModel):
    """Goal response."""
    id: str
    name: str
    description: Optional[str] = None
    icon: str
    target_amount: float
    current_amount: float
    target_date: Optional[datetime] = None
    monthly_contribution: float
    auto_allocate: bool
    status: str
    priority: int
    progress_percentage: float
    remaining_amount: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScenarioRequest(BaseModel):
    """What-if scenario request."""
    scenario_type: str  # "extra_hours", "reduce_expense", "custom"
    
    # For extra_hours
    extra_hours_per_week: Optional[float] = None
    hourly_rate: Optional[float] = None
    
    # For reduce_expense
    expense_category: Optional[str] = None
    reduction_amount: Optional[float] = None
    
    # For custom
    monthly_income_change: Optional[float] = None
    monthly_expense_change: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "scenario_type": "extra_hours",
                "extra_hours_per_week": 4,
                "hourly_rate": 150
            }
        }


class ScenarioComparison(BaseModel):
    """Comparison between baseline and scenario."""
    metric: str
    baseline_value: float
    scenario_value: float
    difference: float
    improvement_percentage: float


class ScenarioResponse(BaseModel):
    """What-if scenario response."""
    scenario_type: str
    scenario_description: str
    
    # Goal impact
    goal_id: str
    goal_name: str
    
    # Comparison
    comparisons: List[ScenarioComparison]
    
    # Timeline
    baseline_completion_date: Optional[datetime] = None
    scenario_completion_date: Optional[datetime] = None
    days_saved: int = 0
    
    # Recommendation
    recommendation: str
