"""
GigMoney Guru - Chart Service

Generate charts using Matplotlib for forecast visualization.
Also provides JSON data for frontend charts (Recharts).
"""
import io
import base64
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from beanie import PydanticObjectId


class ChartService:
    """Service for generating charts."""
    
    # Chart styling
    COLORS = {
        "safe": "#4CAF50",
        "tight": "#FF9800",
        "shortfall": "#F44336",
        "income": "#2196F3",
        "balance": "#9C27B0",
        "obligation": "#FF5722",
    }
    
    @staticmethod
    def generate_forecast_chart(
        forecast: List[Dict],
        width: int = 10,
        height: int = 6
    ) -> str:
        """
        Generate a 30-day forecast chart.
        
        Args:
            forecast: List of day projections
            width: Chart width in inches
            height: Chart height in inches
            
        Returns:
            Base64-encoded PNG image
        """
        # Parse data
        dates = [datetime.fromisoformat(d["date"]) for d in forecast]
        balances = [d["end_balance"] for d in forecast]
        incomes = [d["projected_income"] for d in forecast]
        obligations = [d["obligation_amount"] for d in forecast]
        statuses = [d["status"] for d in forecast]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(width, height))
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        
        # Plot balance line
        ax.plot(dates, balances, color=ChartService.COLORS["balance"], 
                linewidth=2, label="Balance", marker='o', markersize=4)
        
        # Fill areas based on status
        for i in range(len(dates) - 1):
            color = ChartService.COLORS[statuses[i]]
            ax.fill_between(
                [dates[i], dates[i+1]],
                [balances[i], balances[i+1]],
                alpha=0.3,
                color=color
            )
        
        # Plot income as bars
        ax.bar(dates, incomes, alpha=0.5, color=ChartService.COLORS["income"],
               label="Income", width=0.8)
        
        # Mark obligation days
        for i, (d, o) in enumerate(zip(dates, obligations)):
            if o > 0:
                ax.axvline(x=d, color=ChartService.COLORS["obligation"], 
                          linestyle='--', alpha=0.7, linewidth=1)
                ax.annotate(f'₹{o:.0f}', xy=(d, max(balances)*0.9),
                           fontsize=8, color='white', ha='center')
        
        # Zero line
        ax.axhline(y=0, color='white', linestyle='-', alpha=0.3, linewidth=1)
        
        # Styling
        ax.set_xlabel('Date', color='white', fontsize=10)
        ax.set_ylabel('Amount (₹)', color='white', fontsize=10)
        ax.set_title('30-Day Cashflow Forecast', color='white', fontsize=14, fontweight='bold')
        
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Format x-axis
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        plt.xticks(rotation=45)
        
        # Legend
        ax.legend(loc='upper left', facecolor='#1a1a2e', edgecolor='white',
                 labelcolor='white')
        
        # Grid
        ax.grid(True, alpha=0.2, color='white')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, facecolor='#1a1a2e',
                   edgecolor='none', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    @staticmethod
    def generate_bucket_chart(
        buckets: List[Dict],
        width: int = 8,
        height: int = 6
    ) -> str:
        """
        Generate a bucket status chart.
        
        Args:
            buckets: List of bucket data
            width: Chart width in inches
            height: Chart height in inches
            
        Returns:
            Base64-encoded PNG image
        """
        # Parse data
        names = [b["display_name"] for b in buckets]
        targets = [b["target_amount"] for b in buckets]
        currents = [b["current_balance"] for b in buckets]
        colors_list = [b.get("color", "#4CAF50") for b in buckets]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(width, height))
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        
        y_pos = np.arange(len(names))
        
        # Plot target bars (background)
        ax.barh(y_pos, targets, color='#333', alpha=0.5, label='Target')
        
        # Plot current bars
        ax.barh(y_pos, currents, color=colors_list, alpha=0.8, label='Current')
        
        # Add labels
        for i, (target, current) in enumerate(zip(targets, currents)):
            pct = (current / target * 100) if target > 0 else 0
            ax.text(max(target, current) + 100, i, f'{pct:.0f}%', 
                   va='center', color='white', fontsize=10)
        
        # Styling
        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, color='white', fontsize=10)
        ax.set_xlabel('Amount (₹)', color='white', fontsize=10)
        ax.set_title('Bucket Progress', color='white', fontsize=14, fontweight='bold')
        
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        ax.legend(loc='lower right', facecolor='#1a1a2e', edgecolor='white',
                 labelcolor='white')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, facecolor='#1a1a2e',
                   edgecolor='none', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    @staticmethod
    def generate_income_trend_chart(
        income_history: List[Dict],
        days: int = 14,
        width: int = 8,
        height: int = 4
    ) -> str:
        """
        Generate income trend chart.
        
        Args:
            income_history: List of income events
            days: Number of days to show
            width: Chart width in inches
            height: Chart height in inches
            
        Returns:
            Base64-encoded PNG image
        """
        # Aggregate by date
        daily_totals = {}
        for event in income_history:
            date_str = event.get("earned_at", "")[:10]
            if date_str:
                if date_str not in daily_totals:
                    daily_totals[date_str] = 0
                daily_totals[date_str] += event.get("amount", 0)
        
        # Sort and take last N days
        sorted_dates = sorted(daily_totals.keys())[-days:]
        dates = [datetime.fromisoformat(d) for d in sorted_dates]
        amounts = [daily_totals[d] for d in sorted_dates]
        
        if not dates:
            return ""
        
        # Create figure
        fig, ax = plt.subplots(figsize=(width, height))
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        
        # Plot
        ax.fill_between(dates, amounts, alpha=0.3, color=ChartService.COLORS["income"])
        ax.plot(dates, amounts, color=ChartService.COLORS["income"], 
               linewidth=2, marker='o', markersize=5)
        
        # Add average line
        avg = sum(amounts) / len(amounts) if amounts else 0
        ax.axhline(y=avg, color='white', linestyle='--', alpha=0.5, 
                  label=f'Avg: ₹{avg:.0f}')
        
        # Styling
        ax.set_xlabel('Date', color='white', fontsize=10)
        ax.set_ylabel('Income (₹)', color='white', fontsize=10)
        ax.set_title('Income Trend', color='white', fontsize=12, fontweight='bold')
        
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        plt.xticks(rotation=45)
        
        ax.legend(loc='upper left', facecolor='#1a1a2e', edgecolor='white',
                 labelcolor='white')
        
        ax.grid(True, alpha=0.2, color='white')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, facecolor='#1a1a2e',
                   edgecolor='none', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    # =========================================================================
    # JSON DATA METHODS FOR FRONTEND RECHARTS
    # =========================================================================
    
    @staticmethod
    def get_forecast_chart_data(forecast: List[Dict]) -> Dict:
        """Get forecast data formatted for Recharts."""
        chart_data = []
        for day in forecast:
            chart_data.append({
                "date": day["date"][:10],
                "displayDate": datetime.fromisoformat(day["date"]).strftime("%d %b"),
                "balance": round(day["end_balance"], 2),
                "income": round(day["projected_income"], 2),
                "expenses": round(day.get("expense_amount", 0), 2),
                "obligations": round(day["obligation_amount"], 2),
                "status": day["status"],
                "statusColor": ChartService.COLORS.get(day["status"], "#9C27B0")
            })
        
        total_income = sum(d["income"] for d in chart_data)
        total_expenses = sum(d["expenses"] for d in chart_data)
        total_obligations = sum(d["obligations"] for d in chart_data)
        shortfall_days = sum(1 for d in chart_data if d["status"] == "shortfall")
        
        return {
            "data": chart_data,
            "summary": {
                "totalIncome": round(total_income, 2),
                "totalExpenses": round(total_expenses, 2),
                "totalObligations": round(total_obligations, 2),
                "shortfallDays": shortfall_days,
                "projectedBalance": chart_data[-1]["balance"] if chart_data else 0
            }
        }
    
    @staticmethod
    def get_bucket_chart_data(buckets: List[Dict]) -> Dict:
        """Get bucket data formatted for Recharts."""
        chart_data = []
        total_target = 0
        total_current = 0
        
        for bucket in buckets:
            target = bucket["target_amount"]
            current = bucket["current_balance"]
            total_target += target
            total_current += current
            
            chart_data.append({
                "name": bucket["display_name"],
                "target": round(target, 2),
                "current": round(current, 2),
                "percentage": round((current / target * 100) if target > 0 else 0, 1),
                "color": bucket.get("color", "#4CAF50"),
                "gap": round(max(0, target - current), 2)
            })
        
        return {
            "data": chart_data,
            "summary": {
                "totalTarget": round(total_target, 2),
                "totalCurrent": round(total_current, 2),
                "overallPercentage": round((total_current / total_target * 100) if total_target > 0 else 0, 1),
                "bucketsOnTrack": sum(1 for d in chart_data if d["percentage"] >= 80)
            }
        }
    
    @staticmethod
    def get_income_trend_data(income_history: List[Dict], days: int = 30) -> Dict:
        """Get income trend data formatted for Recharts."""
        daily_totals = {}
        platform_breakdown = {}
        
        for event in income_history:
            date_str = event.get("earned_at", "")[:10]
            platform = event.get("platform", "other")
            amount = event.get("amount", 0)
            
            if date_str:
                if date_str not in daily_totals:
                    daily_totals[date_str] = {"total": 0, "platforms": {}}
                daily_totals[date_str]["total"] += amount
                daily_totals[date_str]["platforms"][platform] = \
                    daily_totals[date_str]["platforms"].get(platform, 0) + amount
                platform_breakdown[platform] = platform_breakdown.get(platform, 0) + amount
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        chart_data = []
        current = start_date
        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            day_data = daily_totals.get(date_str, {"total": 0, "platforms": {}})
            chart_data.append({
                "date": date_str,
                "displayDate": current.strftime("%d %b"),
                "dayOfWeek": current.strftime("%a"),
                "total": round(day_data["total"], 2),
                "platforms": day_data["platforms"]
            })
            current += timedelta(days=1)
        
        amounts = [d["total"] for d in chart_data]
        avg = sum(amounts) / len(amounts) if amounts else 0
        max_day = max(chart_data, key=lambda x: x["total"]) if chart_data else {}
        
        return {
            "data": chart_data,
            "summary": {
                "totalIncome": round(sum(amounts), 2),
                "dailyAverage": round(avg, 2),
                "bestDay": max_day.get("displayDate", "N/A"),
                "bestAmount": max_day.get("total", 0),
                "activeDays": sum(1 for a in amounts if a > 0)
            },
            "platformBreakdown": [
                {"platform": p, "amount": round(a, 2), "percentage": round(a / sum(platform_breakdown.values()) * 100, 1)}
                for p, a in platform_breakdown.items()
            ] if platform_breakdown else []
        }
    
    @staticmethod
    def get_expense_breakdown_data(expenses: List[Dict], days: int = 30) -> Dict:
        """Get expense breakdown data for Recharts pie/bar charts."""
        cutoff = datetime.now() - timedelta(days=days)
        category_totals = {}
        daily_totals = {}
        
        for exp in expenses:
            exp_date_str = exp.get("date", "")[:10]
            if exp_date_str:
                try:
                    exp_date = datetime.fromisoformat(exp_date_str)
                    if exp_date >= cutoff:
                        category = exp.get("category", "other")
                        amount = exp.get("amount", 0)
                        category_totals[category] = category_totals.get(category, 0) + amount
                        if exp_date_str not in daily_totals:
                            daily_totals[exp_date_str] = 0
                        daily_totals[exp_date_str] += amount
                except:
                    pass
        
        total = sum(category_totals.values())
        
        pie_data = [
            {"name": cat.title(), "value": round(amt, 2), "percentage": round(amt / total * 100, 1) if total > 0 else 0}
            for cat, amt in sorted(category_totals.items(), key=lambda x: -x[1])
        ]
        
        return {
            "categoryBreakdown": pie_data,
            "summary": {
                "totalExpenses": round(total, 2),
                "dailyAverage": round(total / days, 2),
                "topCategory": pie_data[0]["name"] if pie_data else "N/A",
                "categoryCount": len(pie_data)
            }
        }
    
    @staticmethod
    def get_risk_gauge_data(risk_score: float, risk_factors: List[str] = None) -> Dict:
        """Get risk score data for gauge chart."""
        if risk_score <= 30:
            level, color, message = "low", "#4CAF50", "Your finances are stable"
        elif risk_score <= 60:
            level, color, message = "moderate", "#FF9800", "Some areas need attention"
        else:
            level, color, message = "high", "#F44336", "Immediate action recommended"
        
        return {
            "score": round(risk_score, 1),
            "level": level,
            "color": color,
            "message": message,
            "factors": risk_factors or [],
            "gaugeData": [
                {"name": "Risk", "value": round(risk_score, 1)},
                {"name": "Safe", "value": round(100 - risk_score, 1)}
            ]
        }
    
    @staticmethod
    def get_goal_progress_data(goals: List[Dict]) -> Dict:
        """Get goal progress data for Recharts."""
        chart_data = []
        
        for goal in goals:
            target = goal.get("target_amount", 0)
            current = goal.get("current_amount", 0)
            deadline = goal.get("deadline", "")
            
            days_left = 0
            if deadline:
                try:
                    deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                    days_left = max(0, (deadline_dt - datetime.now(deadline_dt.tzinfo)).days)
                except:
                    pass
            
            daily_needed = (target - current) / days_left if days_left > 0 else 0
            
            chart_data.append({
                "name": goal.get("name", "Goal"),
                "target": round(target, 2),
                "current": round(current, 2),
                "percentage": round((current / target * 100) if target > 0 else 0, 1),
                "daysLeft": days_left,
                "dailyNeeded": round(daily_needed, 2),
                "onTrack": daily_needed <= goal.get("daily_contribution", 0) if days_left > 0 else current >= target
            })
        
        return {
            "data": chart_data,
            "summary": {
                "totalGoals": len(chart_data),
                "goalsOnTrack": sum(1 for g in chart_data if g["onTrack"]),
                "totalTarget": round(sum(g["target"] for g in chart_data), 2),
                "totalSaved": round(sum(g["current"] for g in chart_data), 2)
            }
        }
    
    @staticmethod
    async def get_comprehensive_chart_data(user_id: PydanticObjectId) -> Dict:
        """Get all chart data for a user in one call."""
        from app.models.income import IncomeEvent
        from app.models.expense import ExpenseEvent
        from app.models.bucket import Bucket
        from app.models.goal import Goal
        from app.services.forecast import ForecastService
        
        incomes = await IncomeEvent.find(IncomeEvent.user_id == user_id).to_list()
        expenses = await ExpenseEvent.find(ExpenseEvent.user_id == user_id).to_list()
        buckets = await Bucket.find(Bucket.user_id == user_id).to_list()
        goals = await Goal.find(Goal.user_id == user_id).to_list()
        
        # Generate forecast using correct method
        forecast_list = await ForecastService.generate_30_day_forecast(str(user_id))
        
        # Calculate risk score from forecast
        shortfall_days = sum(1 for d in forecast_list if d["status"] == "shortfall")
        tight_days = sum(1 for d in forecast_list if d["status"] == "tight")
        risk_score = min(100, shortfall_days * 15 + tight_days * 5)
        risk_factors = []
        if shortfall_days > 0:
            risk_factors.append(f"{shortfall_days} days with projected shortfall")
        if tight_days > 0:
            risk_factors.append(f"{tight_days} days with tight cash flow")
        
        income_dicts = [{"amount": i.amount, "platform": i.source_name, "earned_at": i.earned_at.isoformat()} for i in incomes]
        expense_dicts = [{"amount": e.amount, "category": e.category, "date": e.spent_at.isoformat()} for e in expenses]
        bucket_dicts = [{"display_name": b.display_name, "target_amount": b.target_amount, "current_balance": b.current_balance, "color": getattr(b, "color", "#4CAF50")} for b in buckets]
        goal_dicts = [{"name": g.name, "target_amount": g.target_amount, "current_amount": g.current_amount, "deadline": g.target_date.isoformat() if g.target_date else None, "daily_contribution": getattr(g, "monthly_contribution", 0) / 30} for g in goals]
        
        return {
            "forecast": ChartService.get_forecast_chart_data(forecast_list),
            "buckets": ChartService.get_bucket_chart_data(bucket_dicts),
            "incomeTrend": ChartService.get_income_trend_data(income_dicts),
            "expenses": ChartService.get_expense_breakdown_data(expense_dicts),
            "goals": ChartService.get_goal_progress_data(goal_dicts),
            "riskGauge": ChartService.get_risk_gauge_data(risk_score, risk_factors),
            "generatedAt": datetime.now().isoformat()
        }
