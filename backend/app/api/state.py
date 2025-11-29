"""
GigMoney Guru - State API

Returns dashboard state and forecast.
"""
from fastapi import APIRouter, Depends
from datetime import datetime, date
from typing import Optional
from beanie import PydanticObjectId

from app.api.auth import get_current_user
from app.models.user import User
from app.models.income import IncomeEvent
from app.models.bucket import Bucket
from app.models.obligation import Obligation
from app.services.forecast import ForecastService
from app.services.charts import ChartService
from app.services.allocation import AllocationService
# Schemas are used for reference only, responses are dicts


router = APIRouter(prefix="/state", tags=["State"])


@router.get("/today")
async def get_today_state(current_user: User = Depends(get_current_user)):
    """Get today's dashboard state."""
    user_id = str(current_user.id)
    user_oid = PydanticObjectId(user_id)
    today = datetime.now().date()
    
    # Get today's income
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    income_events = await IncomeEvent.find(
        IncomeEvent.user_id == user_oid,
        IncomeEvent.earned_at >= today_start,
        IncomeEvent.earned_at <= today_end
    ).to_list()
    
    today_earnings = sum(e.amount for e in income_events)
    
    # Group by source
    income_breakdown = {}
    for event in income_events:
        source = event.source_name
        if source not in income_breakdown:
            income_breakdown[source] = {"amount": 0, "count": 0}
        income_breakdown[source]["amount"] += event.amount
        income_breakdown[source]["count"] += 1
    
    # Get buckets (create defaults if none exist)
    buckets = await Bucket.find(
        Bucket.user_id == user_oid,
        Bucket.is_active == True
    ).sort("+priority").to_list()
    
    if not buckets:
        # Create default buckets for the user
        buckets = await AllocationService.create_default_buckets(user_id)
    
    bucket_states = []
    total_balance = 0
    safe_to_spend = 0
    
    for bucket in buckets:
        progress = (bucket.current_balance / bucket.target_amount * 100) if bucket.target_amount > 0 else 0
        bucket_states.append({
            "name": bucket.name,
            "display_name": bucket.display_name,
            "icon": bucket.icon,
            "color": bucket.color,
            "target_amount": bucket.target_amount,
            "current_balance": bucket.current_balance,
            "progress_percentage": round(progress, 1),
            "priority": bucket.priority,
        })
        total_balance += bucket.current_balance
        
        # Safe to spend = discretionary + flex buckets
        if bucket.name in ["discretionary", "flex"]:
            safe_to_spend += bucket.current_balance
    
    # Get upcoming obligations
    obligations = await Obligation.find(
        Obligation.user_id == user_oid,
        {"is_active": True}
    ).to_list()
    
    upcoming = []
    for obl in obligations:
        # Calculate next due date
        due_day = obl.due_day
        if today.day > due_day:
            # Next month
            if today.month == 12:
                next_due = date(today.year + 1, 1, due_day)
            else:
                next_due = date(today.year, today.month + 1, due_day)
        else:
            next_due = date(today.year, today.month, due_day)
        
        days_until = (next_due - today).days
        
        # Get bucket balance
        bucket = next((b for b in buckets if b.name == obl.bucket_name), None)
        bucket_balance = bucket.current_balance if bucket else 0
        
        # Calculate shortfall
        shortfall = max(0, obl.amount - bucket_balance)
        
        # Determine risk
        if days_until <= 3 and shortfall > 0:
            risk = "high"
        elif days_until <= 7 and shortfall > obl.amount * 0.3:
            risk = "medium"
        else:
            risk = "low"
        
        upcoming.append({
            "id": str(obl.id),
            "name": obl.name,
            "category": obl.category,
            "amount": obl.amount,
            "due_date": next_due.isoformat(),
            "days_until_due": days_until,
            "risk_level": risk,
            "bucket_balance": bucket_balance,
            "shortfall": shortfall,
        })
    
    # Sort by due date
    upcoming.sort(key=lambda x: x["days_until_due"])
    
    # Calculate REAL risk score (0-100)
    risk_score = 10  # Base score (everyone has some risk)
    
    # Add risk for each high/medium obligation
    high_risk_count = sum(1 for o in upcoming if o["risk_level"] == "high")
    medium_risk_count = sum(1 for o in upcoming if o["risk_level"] == "medium")
    risk_score += high_risk_count * 25
    risk_score += medium_risk_count * 10
    
    # Add risk for total shortfall
    total_shortfall = sum(o["shortfall"] for o in upcoming)
    if total_shortfall > 0:
        risk_score += min(20, total_shortfall / 500)  # Cap at 20
    
    # Add risk for low emergency fund
    emergency_bucket = next((b for b in buckets if b.name == "emergency"), None)
    emergency_balance = emergency_bucket.current_balance if emergency_bucket else 0
    if emergency_balance < 2000:
        risk_score += 15
    elif emergency_balance < 5000:
        risk_score += 8
    
    # Add risk if safe_to_spend is very low
    if safe_to_spend < 500:
        risk_score += 10
    
    # Cap at 100
    risk_score = min(100, max(0, int(risk_score)))
    
    # Check for warnings
    warnings = []
    has_warnings = False
    
    for obl in upcoming[:5]:
        if obl["risk_level"] == "high":
            has_warnings = True
            warnings.append(f"{obl['name']} due in {obl['days_until_due']} days, ₹{obl['shortfall']:.0f} short")
    
    # Greeting based on time
    hour = datetime.now().hour
    if hour < 12:
        greeting = f"Good morning, {current_user.name}!"
    elif hour < 17:
        greeting = f"Good afternoon, {current_user.name}!"
    else:
        greeting = f"Good evening, {current_user.name}!"
    
    return {
        "date": today.isoformat(),
        "greeting": greeting,
        "today_earnings": today_earnings,
        "income_breakdown": [
            {
                "source_name": source,
                "amount": data["amount"],
                "count": data["count"],
            }
            for source, data in income_breakdown.items()
        ],
        "buckets": bucket_states,
        "total_balance": total_balance,
        "safe_to_spend": safe_to_spend,
        "risk_score": risk_score,
        "upcoming_obligations": upcoming[:5],
        "has_warnings": has_warnings,
        "warnings": warnings,
        "safe_spending_streak": 0,  # TODO: Calculate from history
    }


@router.get("/forecast")
async def get_forecast(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get cashflow forecast."""
    user_id = str(current_user.id)
    
    # Generate forecast
    forecast = await ForecastService.generate_30_day_forecast(user_id)
    forecast = forecast[:days]
    
    # Generate summary
    summary = ForecastService.summarize_forecast(forecast)
    
    # Calculate risk stats
    risk_days = sum(1 for d in forecast if d["status"] == "tight")
    shortfall_days = sum(1 for d in forecast if d["status"] == "shortfall")
    
    # Generate chart
    chart_image = ChartService.generate_forecast_chart(forecast)
    
    return {
        "forecast": forecast,
        "summary": summary,
        "risk_days": risk_days,
        "shortfall_days": shortfall_days,
        "chart_image_base64": chart_image,
    }


@router.get("/buckets/chart")
async def get_buckets_chart(current_user: User = Depends(get_current_user)):
    """Get bucket progress chart."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    buckets = await Bucket.find(
        Bucket.user_id == user_oid,
        {"is_active": True}
    ).sort("+priority").to_list()
    
    bucket_data = [
        {
            "name": b.name,
            "display_name": b.display_name,
            "target_amount": b.target_amount,
            "current_balance": b.current_balance,
            "color": b.color,
        }
        for b in buckets
        if b.target_amount > 0  # Only show buckets with targets
    ]
    
    chart_image = ChartService.generate_bucket_chart(bucket_data)
    
    return {"chart_image_base64": chart_image}
