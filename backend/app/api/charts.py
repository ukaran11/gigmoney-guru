"""
GigMoney Guru - Charts API

Provides chart data for frontend visualizations.
"""
from fastapi import APIRouter, Depends, HTTPException
from beanie import PydanticObjectId
from typing import Optional

from app.api.auth import get_current_user
from app.services.charts import ChartService
from app.models.user import User

router = APIRouter(prefix="/charts", tags=["charts"])


@router.get("/all")
async def get_all_charts(
    current_user: User = Depends(get_current_user)
):
    """
    Get all chart data for the current user.
    Returns data formatted for Recharts components.
    """
    try:
        chart_data = await ChartService.get_comprehensive_chart_data(current_user.id)
        return {
            "success": True,
            "charts": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate charts: {str(e)}")


@router.get("/forecast")
async def get_forecast_chart(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get 30-day cashflow forecast chart data."""
    from app.services.forecast import ForecastService
    
    try:
        forecast_list = await ForecastService.generate_30_day_forecast(str(current_user.id))
        chart_data = ChartService.get_forecast_chart_data(forecast_list)
        
        # Calculate risk score
        shortfall_days = sum(1 for d in forecast_list if d["status"] == "shortfall")
        tight_days = sum(1 for d in forecast_list if d["status"] == "tight")
        risk_score = min(100, shortfall_days * 15 + tight_days * 5)
        risk_factors = []
        if shortfall_days > 0:
            risk_factors.append(f"{shortfall_days} days with projected shortfall")
        if tight_days > 0:
            risk_factors.append(f"{tight_days} days with tight cash flow")
        
        return {
            "success": True,
            "chart": chart_data,
            "riskScore": risk_score,
            "riskFactors": risk_factors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast chart: {str(e)}")


@router.get("/buckets")
async def get_bucket_chart(
    current_user: User = Depends(get_current_user)
):
    """Get bucket progress chart data."""
    from app.models.bucket import Bucket
    
    try:
        buckets = await Bucket.find(Bucket.user_id == current_user.id).to_list()
        bucket_dicts = [
            {
                "display_name": b.display_name,
                "target_amount": b.target_amount,
                "current_balance": b.current_balance,
                "color": getattr(b, "color", "#4CAF50")
            }
            for b in buckets
        ]
        chart_data = ChartService.get_bucket_chart_data(bucket_dicts)
        
        return {
            "success": True,
            "chart": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate bucket chart: {str(e)}")


@router.get("/income-trend")
async def get_income_trend_chart(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get income trend chart data."""
    from app.models.income import IncomeEvent
    
    try:
        incomes = await IncomeEvent.find(IncomeEvent.user_id == current_user.id).to_list()
        income_dicts = [
            {"amount": i.amount, "platform": i.source_name, "earned_at": i.earned_at.isoformat()}
            for i in incomes
        ]
        chart_data = ChartService.get_income_trend_data(income_dicts, days)
        
        return {
            "success": True,
            "chart": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate income trend chart: {str(e)}")


@router.get("/expenses")
async def get_expense_chart(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get expense breakdown chart data."""
    from app.models.expense import ExpenseEvent
    
    try:
        expenses = await ExpenseEvent.find(ExpenseEvent.user_id == current_user.id).to_list()
        expense_dicts = [
            {"amount": e.amount, "category": e.category, "date": e.spent_at.isoformat()}
            for e in expenses
        ]
        chart_data = ChartService.get_expense_breakdown_data(expense_dicts, days)
        
        return {
            "success": True,
            "chart": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate expense chart: {str(e)}")


@router.get("/goals")
async def get_goal_chart(
    current_user: User = Depends(get_current_user)
):
    """Get goal progress chart data."""
    from app.models.goal import Goal
    
    try:
        goals = await Goal.find(Goal.user_id == current_user.id).to_list()
        goal_dicts = [
            {
                "name": g.name,
                "target_amount": g.target_amount,
                "current_amount": g.current_amount,
                "deadline": g.target_date.isoformat() if g.target_date else None,
                "daily_contribution": getattr(g, "monthly_contribution", 0) / 30
            }
            for g in goals
        ]
        chart_data = ChartService.get_goal_progress_data(goal_dicts)
        
        return {
            "success": True,
            "chart": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate goal chart: {str(e)}")


@router.get("/risk")
async def get_risk_gauge(
    current_user: User = Depends(get_current_user)
):
    """Get risk gauge chart data."""
    from app.services.forecast import ForecastService
    
    try:
        forecast_list = await ForecastService.generate_30_day_forecast(str(current_user.id))
        
        # Calculate risk score
        shortfall_days = sum(1 for d in forecast_list if d["status"] == "shortfall")
        tight_days = sum(1 for d in forecast_list if d["status"] == "tight")
        risk_score = min(100, shortfall_days * 15 + tight_days * 5)
        risk_factors = []
        if shortfall_days > 0:
            risk_factors.append(f"{shortfall_days} days with projected shortfall")
        if tight_days > 0:
            risk_factors.append(f"{tight_days} days with tight cash flow")
        
        chart_data = ChartService.get_risk_gauge_data(risk_score, risk_factors)
        
        return {
            "success": True,
            "chart": chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate risk gauge: {str(e)}")
