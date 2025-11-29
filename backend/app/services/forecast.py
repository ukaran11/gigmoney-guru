"""
GigMoney Guru - Forecast Service

Business logic for cashflow forecasting.
"""
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from beanie import PydanticObjectId

from app.models.income import IncomeEvent
from app.models.obligation import Obligation
from app.models.bucket import Bucket


class ForecastService:
    """Service for forecasting operations."""
    
    @staticmethod
    async def get_income_averages(
        user_id: str,
        days: int = 30
    ) -> Dict[str, float]:
        """Calculate income averages from history."""
        user_oid = PydanticObjectId(user_id)
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        events = await IncomeEvent.find(
            IncomeEvent.user_id == user_oid,
            IncomeEvent.earned_at >= cutoff
        ).to_list()
        
        if not events:
            return {
                "daily_average": 2000,
                "weekday_average": 2000,
                "weekend_average": 3500,
                "weekly_average": 14000,
                "monthly_total": 0,
            }
        
        # Group by day type
        weekday_amounts = []
        weekend_amounts = []
        daily_totals = {}
        
        for event in events:
            earned_date = event.earned_at.date()
            day_key = earned_date.isoformat()
            
            if day_key not in daily_totals:
                daily_totals[day_key] = 0
            daily_totals[day_key] += event.amount
            
            if earned_date.weekday() >= 5:
                weekend_amounts.append(event.amount)
            else:
                weekday_amounts.append(event.amount)
        
        monthly_total = sum(daily_totals.values())
        daily_avg = monthly_total / len(daily_totals) if daily_totals else 2000
        weekday_avg = sum(weekday_amounts) / len(weekday_amounts) if weekday_amounts else 2000
        weekend_avg = sum(weekend_amounts) / len(weekend_amounts) if weekend_amounts else 3500
        
        return {
            "daily_average": round(daily_avg, 0),
            "weekday_average": round(weekday_avg, 0),
            "weekend_average": round(weekend_avg, 0),
            "weekly_average": round(daily_avg * 7, 0),
            "monthly_total": round(monthly_total, 0),
        }
    
    @staticmethod
    async def project_day(
        user_id: str,
        target_date: date,
        income_averages: Dict[str, float]
    ) -> Dict[str, any]:
        """Project income and obligations for a specific day."""
        user_oid = PydanticObjectId(user_id)
        
        is_weekend = target_date.weekday() >= 5
        projected_income = (
            income_averages.get("weekend_average", 3500)
            if is_weekend
            else income_averages.get("weekday_average", 2000)
        )
        
        # Get obligations due on this day
        obligations = await Obligation.find(
            Obligation.user_id == user_oid,
            {"is_active": True},
            Obligation.due_day == target_date.day
        ).to_list()
        
        obligation_amount = sum(o.amount for o in obligations)
        obligation_names = [o.name for o in obligations]
        
        # Estimate daily expenses
        daily_expenses = 400 if not is_weekend else 500
        
        return {
            "date": target_date.isoformat(),
            "is_weekend": is_weekend,
            "projected_income": projected_income,
            "projected_expenses": daily_expenses,
            "obligations_due": obligation_names,
            "obligation_amount": obligation_amount,
        }
    
    @staticmethod
    async def generate_30_day_forecast(
        user_id: str,
        start_date: Optional[date] = None
    ) -> List[Dict[str, any]]:
        """Generate a 30-day forecast."""
        if start_date is None:
            start_date = datetime.now().date()
        
        # Get income averages
        income_averages = await ForecastService.get_income_averages(user_id)
        
        # Get current bucket balances
        user_oid = PydanticObjectId(user_id)
        buckets = await Bucket.find(
            Bucket.user_id == user_oid,
            {"is_active": True}
        ).to_list()
        
        running_balance = sum(b.current_balance for b in buckets)
        
        forecast = []
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for offset in range(30):
            current_date = start_date + timedelta(days=offset)
            
            day_projection = await ForecastService.project_day(
                user_id, current_date, income_averages
            )
            
            start_balance = running_balance
            income = day_projection["projected_income"]
            expenses = day_projection["projected_expenses"]
            obligations = day_projection["obligation_amount"]
            
            end_balance = start_balance + income - expenses - obligations
            running_balance = end_balance
            
            # Determine status
            if end_balance < 0:
                status = "shortfall"
            elif end_balance < 500 or (obligations > 0 and end_balance < obligations * 0.2):
                status = "tight"
            else:
                status = "safe"
            
            forecast.append({
                "date": current_date.isoformat(),
                "day_name": day_names[current_date.weekday()],
                "is_weekend": day_projection["is_weekend"],
                "projected_income": income,
                "projected_expenses": expenses,
                "obligations_due": day_projection["obligations_due"],
                "obligation_amount": obligations,
                "start_balance": round(start_balance, 0),
                "end_balance": round(end_balance, 0),
                "status": status,
            })
        
        return forecast
    
    @staticmethod
    def summarize_forecast(forecast: List[Dict]) -> str:
        """Generate text summary of forecast."""
        safe_days = sum(1 for d in forecast if d["status"] == "safe")
        tight_days = sum(1 for d in forecast if d["status"] == "tight")
        shortfall_days = sum(1 for d in forecast if d["status"] == "shortfall")
        
        total_income = sum(d["projected_income"] for d in forecast)
        total_obligations = sum(d["obligation_amount"] for d in forecast)
        
        if shortfall_days > 0:
            first_shortfall = next(d for d in forecast if d["status"] == "shortfall")
            return (
                f"⚠️ Next 30 days: {shortfall_days} shortfall days detected. "
                f"First on {first_shortfall['date']}. "
                f"Projected income: ₹{total_income:,.0f}, Obligations: ₹{total_obligations:,.0f}"
            )
        elif tight_days > 0:
            return (
                f"📊 Next 30 days: {safe_days} safe, {tight_days} tight. "
                f"Projected income: ₹{total_income:,.0f}"
            )
        else:
            return (
                f"✅ All {safe_days} days looking good! "
                f"Projected income: ₹{total_income:,.0f}"
            )
