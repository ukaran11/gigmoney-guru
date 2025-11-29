"""
GigMoney Guru - Income API

Add and manage income events with auto-allocation.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional, List
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.models.user import User
from app.models.income import IncomeEvent
from app.models.bucket import Bucket
from app.services.allocation import AllocationService

# Import proactive agent lazily to avoid startup delays
def get_proactive_agent():
    from app.services.proactive_agent import ProactiveAgentService
    return ProactiveAgentService


class IncomeCreate(BaseModel):
    """Create income request."""
    source_name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    notes: Optional[str] = None
    run_ai: bool = Field(default=False, description="Run AI analysis after adding income (slower)")


router = APIRouter(prefix="/income", tags=["Income"])


@router.post("/")
async def add_income(
    income_data: IncomeCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Add new income and auto-allocate to buckets.
    
    This is the main entry point for gig workers to log their earnings.
    The AI will automatically distribute the income across buckets.
    """
    user_id = str(current_user.id)
    user_oid = PydanticObjectId(user_id)
    
    # Ensure user has buckets (create defaults if none exist)
    existing_buckets = await Bucket.find(
        Bucket.user_id == user_oid,
        Bucket.is_active == True
    ).to_list()
    
    if not existing_buckets:
        await AllocationService.create_default_buckets(user_id)
    
    # Create income event
    income = IncomeEvent(
        user_id=user_oid,
        source_name=income_data.source_name,
        source_type="manual",
        amount=income_data.amount,
        description=income_data.notes,
        earned_at=datetime.now(),
    )
    await income.save()
    
    # Auto-allocate to buckets
    allocation_result = await AllocationService.allocate_income(
        user_id=user_id,
        amount=income_data.amount,
        source=income_data.source_name
    )
    
    # Build allocation summary
    allocations = allocation_result.get("allocations", [])
    if allocations:
        summary_parts = []
        for alloc in allocations[:3]:
            summary_parts.append(f"{alloc['icon']} ₹{alloc['amount']:.0f}")
        allocation_summary = "Allocated: " + ", ".join(summary_parts)
    else:
        allocation_summary = "No buckets configured yet"
    
    # PROACTIVE: Run AI analysis if requested (non-blocking)
    ai_insight = None
    proactive_alerts = []
    if income_data.run_ai:
        try:
            ProactiveAgentService = get_proactive_agent()
            proactive_result = await ProactiveAgentService.on_income_added(
                user_id=user_id,
                amount=income_data.amount,
                source=income_data.source_name
            )
            ai_insight = proactive_result.get("quick_insight")
            proactive_alerts = proactive_result.get("alerts", [])
        except Exception as e:
            # Don't fail the income addition if AI fails
            ai_insight = f"₹{income_data.amount} allocated to your buckets!"
    
    return {
        "success": True,
        "message": f"₹{income_data.amount} from {income_data.source_name} added!",
        "income_id": str(income.id),
        "allocation_summary": allocation_summary,
        "allocations": allocations,
        "ai_insight": ai_insight,
        "proactive_alerts": proactive_alerts,
    }


@router.get("/")
async def list_income(
    days: int = 7,
    current_user: User = Depends(get_current_user)
):
    """Get recent income events."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    from datetime import timedelta
    start_date = datetime.now() - timedelta(days=days)
    
    incomes = await IncomeEvent.find(
        IncomeEvent.user_id == user_oid,
        IncomeEvent.earned_at >= start_date
    ).sort("-earned_at").to_list()
    
    # Group by date
    by_date = {}
    for inc in incomes:
        date_key = inc.earned_at.strftime("%Y-%m-%d")
        if date_key not in by_date:
            by_date[date_key] = {"date": date_key, "total": 0, "items": []}
        by_date[date_key]["total"] += inc.amount
        by_date[date_key]["items"].append({
            "id": str(inc.id),
            "source": inc.source_name,
            "amount": inc.amount,
            "time": inc.earned_at.strftime("%H:%M"),
            "notes": inc.description,
        })
    
    return {
        "total": sum(inc.amount for inc in incomes),
        "count": len(incomes),
        "days": list(by_date.values()),
    }


@router.get("/summary")
async def income_summary(
    current_user: User = Depends(get_current_user)
):
    """Get income summary statistics."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    from datetime import timedelta
    now = datetime.now()
    
    # Today
    today_start = datetime.combine(now.date(), datetime.min.time())
    today_income = await IncomeEvent.find(
        IncomeEvent.user_id == user_oid,
        IncomeEvent.earned_at >= today_start
    ).to_list()
    today_total = sum(inc.amount for inc in today_income)
    
    # This week
    week_start = now - timedelta(days=now.weekday())
    week_income = await IncomeEvent.find(
        IncomeEvent.user_id == user_oid,
        IncomeEvent.earned_at >= week_start
    ).to_list()
    week_total = sum(inc.amount for inc in week_income)
    
    # This month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_income = await IncomeEvent.find(
        IncomeEvent.user_id == user_oid,
        IncomeEvent.earned_at >= month_start
    ).to_list()
    month_total = sum(inc.amount for inc in month_income)
    
    # By source
    by_source = {}
    for inc in month_income:
        source = inc.source_name
        if source not in by_source:
            by_source[source] = 0
        by_source[source] += inc.amount
    
    return {
        "today": today_total,
        "this_week": week_total,
        "this_month": month_total,
        "by_source": [
            {"source": source, "amount": amount}
            for source, amount in sorted(by_source.items(), key=lambda x: -x[1])
        ],
        "daily_average": month_total / max(now.day, 1),
    }
