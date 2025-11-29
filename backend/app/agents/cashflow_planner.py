"""
GigMoney Guru - Cashflow Planner Agent

Creates day-by-day 30-day forecast:
- Starting balance, projected income, outflows
- Marks days as safe, tight, or shortfall
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta, date


class CashflowPlannerAgent:
    """
    Agent that creates 30-day cashflow forecast.
    
    Input:
        - bucket_balances: Current bucket balances
        - income_patterns: From Income Pattern Agent
        - obligations: List of obligations
        - obligation_risks: From Obligation Risk Agent
        - run_date: Current date
        
    Output:
        - forecast: 30-day forecast with daily projections
        - forecast_summary: Text summary
    """
    
    def __init__(self):
        self.name = "cashflow_planner"
        self.day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate 30-day cashflow forecast.
        
        Algorithm:
        1. Get baseline daily income (with weekend boost)
        2. For each day:
           - Calculate projected income
           - Check for obligations due
           - Calculate ending balance
           - Mark status
        3. Generate summary
        """
        bucket_balances = state.get("bucket_balances", {})
        income_patterns = state.get("income_patterns", {})
        obligations = state.get("obligations", [])
        run_date = state.get("run_date")
        
        if isinstance(run_date, str):
            run_date = datetime.fromisoformat(run_date).date()
        elif run_date is None:
            run_date = datetime.now().date()
        
        # Calculate starting balance (total of all buckets)
        total_balance = sum(bucket_balances.values())
        
        # Get income projections
        weekday_avg = income_patterns.get("weekday_average", 2000)
        weekend_avg = income_patterns.get("weekend_average", 3500)
        season_mult = income_patterns.get("season_multiplier", 1.0)
        
        # Build obligation lookup by due day
        obligation_by_day = self._build_obligation_lookup(obligations)
        
        # Generate 30-day forecast
        forecast = []
        running_balance = total_balance
        
        for day_offset in range(30):
            current_date = run_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()
            is_weekend = day_of_week >= 5
            
            # Project income
            base_income = weekend_avg if is_weekend else weekday_avg
            projected_income = base_income * season_mult
            
            # Check obligations due
            due_day = current_date.day
            obligations_due = obligation_by_day.get(due_day, [])
            obligation_amount = sum(o.get("amount", 0) for o in obligations_due)
            obligation_names = [o.get("name", "") for o in obligations_due]
            
            # Estimate daily expenses (non-obligation)
            daily_expenses = self._estimate_daily_expenses(is_weekend)
            
            # Calculate balances
            start_balance = running_balance
            end_balance = start_balance + projected_income - obligation_amount - daily_expenses
            running_balance = end_balance
            
            # Determine status
            status = self._determine_status(end_balance, obligation_amount)
            
            forecast.append({
                "date": current_date.isoformat(),
                "day_name": self.day_names[day_of_week],
                "is_weekend": is_weekend,
                "projected_income": round(projected_income, 0),
                "projected_expenses": round(daily_expenses, 0),
                "obligations_due": obligation_names,
                "obligation_amount": round(obligation_amount, 0),
                "start_balance": round(start_balance, 0),
                "end_balance": round(end_balance, 0),
                "status": status,
            })
        
        # Generate summary
        summary = self._generate_summary(forecast)
        
        # Update state
        state["forecast"] = forecast
        state["forecast_summary"] = summary
        
        return state
    
    def _build_obligation_lookup(self, obligations: List[Dict]) -> Dict[int, List[Dict]]:
        """Build lookup of obligations by due day."""
        lookup = {}
        for obligation in obligations:
            if not obligation.get("is_active", True):
                continue
            due_day = obligation.get("due_day", 1)
            if due_day not in lookup:
                lookup[due_day] = []
            lookup[due_day].append(obligation)
        return lookup
    
    def _estimate_daily_expenses(self, is_weekend: bool) -> float:
        """Estimate daily variable expenses."""
        # Base daily expenses
        base = 300  # Food, misc
        
        # Fuel (higher on weekdays due to work)
        fuel = 150 if not is_weekend else 100
        
        # Weekend leisure
        leisure = 200 if is_weekend else 50
        
        return base + fuel + leisure
    
    def _determine_status(self, end_balance: float, obligation_amount: float) -> str:
        """Determine day status."""
        if end_balance < 0:
            return "shortfall"
        elif end_balance < 500 or (obligation_amount > 0 and end_balance < obligation_amount * 0.2):
            return "tight"
        else:
            return "safe"
    
    def _generate_summary(self, forecast: List[Dict]) -> str:
        """Generate text summary of forecast."""
        safe_days = sum(1 for d in forecast if d["status"] == "safe")
        tight_days = sum(1 for d in forecast if d["status"] == "tight")
        shortfall_days = sum(1 for d in forecast if d["status"] == "shortfall")
        
        total_income = sum(d["projected_income"] for d in forecast)
        total_obligations = sum(d["obligation_amount"] for d in forecast)
        
        # Find first shortfall if any
        first_shortfall = next(
            (d for d in forecast if d["status"] == "shortfall"),
            None
        )
        
        if shortfall_days > 0 and first_shortfall:
            return (
                f"⚠️ Agle 30 din mein {shortfall_days} din tight ho sakte hain. "
                f"Pehla shortfall {first_shortfall['date']} ko expected hai. "
                f"Total income projection: ₹{total_income:,.0f}, "
                f"Obligations: ₹{total_obligations:,.0f}."
            )
        elif tight_days > 0:
            return (
                f"Agle 30 din mostly achhe hain! {safe_days} din safe, "
                f"{tight_days} din thode tight. "
                f"Total income projection: ₹{total_income:,.0f}."
            )
        else:
            return (
                f"🎉 Agle 30 din ekdum smooth lag rahe hain! "
                f"Sab {safe_days} din safe hain. "
                f"Total income projection: ₹{total_income:,.0f}."
            )


# Function for LangGraph node
def cashflow_planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node wrapper for Cashflow Planner Agent."""
    agent = CashflowPlannerAgent()
    return agent.run(state)
