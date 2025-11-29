"""
GigMoney Guru - Income Pattern Agent

Analyzes income history to detect patterns:
- Weekday vs weekend averages
- Platform-wise breakdown
- Short-term trends
- Seasonality hints
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict


class IncomePatternAgent:
    """
    Agent that analyzes income patterns from historical data.
    
    Input:
        - income_history: List of income events (last 30 days)
        - run_date: Current date
        
    Output:
        - income_patterns: Dict with averages, trends, breakdown
    """
    
    def __init__(self):
        self.name = "income_pattern"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze income patterns and update state.
        
        Algorithm:
        1. Group income by day of week
        2. Calculate weekday vs weekend averages
        3. Calculate platform-wise breakdown
        4. Detect trend (last 2 weeks vs previous 2 weeks)
        5. Apply seasonality multiplier (mocked)
        """
        income_history = state.get("income_history", [])
        run_date = state.get("run_date", datetime.now().date().isoformat())
        
        if isinstance(run_date, str):
            run_date = datetime.fromisoformat(run_date).date()
        
        # Initialize pattern data
        patterns = {
            "weekday_average": 0,
            "weekend_average": 0,
            "weekly_average": 0,
            "monthly_average": 0,
            "trend_direction": "flat",
            "trend_percentage": 0,
            "platform_breakdown": {},
            "season_tag": "normal",
            "season_multiplier": 1.0,
            "daily_averages": {},
        }
        
        if not income_history:
            state["income_patterns"] = patterns
            return state
        
        # Group by day of week and platform
        daily_totals = defaultdict(float)
        platform_totals = defaultdict(float)
        weekday_totals = []
        weekend_totals = []
        
        # Parse dates and amounts
        for event in income_history:
            earned_at = event.get("earned_at")
            if isinstance(earned_at, str):
                earned_date = datetime.fromisoformat(earned_at.replace("Z", "+00:00")).date()
            elif isinstance(earned_at, datetime):
                earned_date = earned_at.date()
            else:
                continue
                
            amount = float(event.get("amount", 0))
            source = event.get("source_name", "unknown")
            
            # Add to daily total
            date_str = earned_date.isoformat()
            daily_totals[date_str] += amount
            
            # Add to platform total
            platform_totals[source] += amount
            
            # Categorize by weekday/weekend
            day_of_week = earned_date.weekday()
            if day_of_week >= 5:  # Saturday=5, Sunday=6
                weekend_totals.append(amount)
            else:
                weekday_totals.append(amount)
        
        # Calculate averages
        if weekday_totals:
            patterns["weekday_average"] = sum(weekday_totals) / len(weekday_totals)
        if weekend_totals:
            patterns["weekend_average"] = sum(weekend_totals) / len(weekend_totals)
        
        # Weekly and monthly
        all_earnings = list(daily_totals.values())
        if all_earnings:
            total = sum(all_earnings)
            days = len(all_earnings)
            patterns["monthly_average"] = total  # Total for the month
            patterns["weekly_average"] = total / max(1, days / 7)
        
        # Platform breakdown (percentages)
        total_platform = sum(platform_totals.values())
        if total_platform > 0:
            patterns["platform_breakdown"] = {
                platform: round((amount / total_platform) * 100, 1)
                for platform, amount in platform_totals.items()
            }
        
        # Calculate trend (last 2 weeks vs previous 2 weeks)
        patterns["trend_direction"], patterns["trend_percentage"] = self._calculate_trend(
            daily_totals, run_date
        )
        
        # Apply seasonality (mocked based on month)
        patterns["season_tag"], patterns["season_multiplier"] = self._get_seasonality(run_date)
        
        # Calculate daily averages by day of week
        patterns["daily_averages"] = self._calculate_daily_averages(income_history)
        
        # Update state
        state["income_patterns"] = patterns
        
        return state
    
    def _calculate_trend(
        self, 
        daily_totals: Dict[str, float], 
        run_date
    ) -> tuple:
        """Calculate trend direction and percentage."""
        if not daily_totals:
            return "flat", 0
        
        # Split into last 14 days and previous 14 days
        recent_total = 0
        previous_total = 0
        recent_days = 0
        previous_days = 0
        
        for date_str, amount in daily_totals.items():
            date = datetime.fromisoformat(date_str).date()
            days_ago = (run_date - date).days
            
            if days_ago <= 14:
                recent_total += amount
                recent_days += 1
            elif days_ago <= 28:
                previous_total += amount
                previous_days += 1
        
        # Calculate averages
        recent_avg = recent_total / max(1, recent_days)
        previous_avg = previous_total / max(1, previous_days)
        
        if previous_avg == 0:
            return "flat", 0
        
        change_pct = ((recent_avg - previous_avg) / previous_avg) * 100
        
        if change_pct > 10:
            return "up", round(change_pct, 1)
        elif change_pct < -10:
            return "down", round(abs(change_pct), 1)
        else:
            return "flat", round(abs(change_pct), 1)
    
    def _get_seasonality(self, run_date) -> tuple:
        """Get seasonality tag and multiplier (mocked)."""
        month = run_date.month
        
        # Monsoon season (June-September) - typically lower earnings
        if month in [6, 7, 8, 9]:
            return "monsoon", 0.85
        
        # Festival season (October-November) - higher earnings
        elif month in [10, 11]:
            return "festive", 1.20
        
        # Year-end (December) - moderate boost
        elif month == 12:
            return "year_end", 1.10
        
        # Normal
        else:
            return "normal", 1.0
    
    def _calculate_daily_averages(self, income_history: List[Dict]) -> Dict[str, float]:
        """Calculate average earnings by day of week."""
        day_totals = defaultdict(list)
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for event in income_history:
            earned_at = event.get("earned_at")
            if isinstance(earned_at, str):
                earned_date = datetime.fromisoformat(earned_at.replace("Z", "+00:00")).date()
            elif isinstance(earned_at, datetime):
                earned_date = earned_at.date()
            else:
                continue
            
            day_name = day_names[earned_date.weekday()]
            day_totals[day_name].append(float(event.get("amount", 0)))
        
        return {
            day: round(sum(amounts) / len(amounts), 0) if amounts else 0
            for day, amounts in day_totals.items()
        }


# Function for LangGraph node
def income_pattern_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node wrapper for Income Pattern Agent."""
    agent = IncomePatternAgent()
    return agent.run(state)
