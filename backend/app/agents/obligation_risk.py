"""
GigMoney Guru - Obligation Risk Agent

Assesses risk for upcoming obligations:
- Timeline of mandatory outflows
- Risk score per obligation
- Red flag days identification
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta, date


class ObligationRiskAgent:
    """
    Agent that assesses risk for upcoming obligations.
    
    Input:
        - obligations: List of obligations with due dates
        - bucket_balances: Current bucket balances
        - income_patterns: From Income Pattern Agent
        - run_date: Current date
        
    Output:
        - obligation_risks: List of risk assessments
        - red_flag_days: Days where cash might go negative
    """
    
    def __init__(self):
        self.name = "obligation_risk"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk for upcoming obligations.
        
        Algorithm:
        1. For each obligation:
           - Calculate days until due
           - Check bucket balance vs required amount
           - Calculate projected balance at due date
           - Assign risk level (low/medium/high)
        2. Identify red flag days
        3. Sort by due date
        """
        obligations = state.get("obligations", [])
        bucket_balances = state.get("bucket_balances", {})
        income_patterns = state.get("income_patterns", {})
        run_date = state.get("run_date")
        
        if isinstance(run_date, str):
            run_date = datetime.fromisoformat(run_date).date()
        elif run_date is None:
            run_date = datetime.now().date()
        
        obligation_risks = []
        red_flag_days = []
        
        # Get daily income projection
        daily_income = income_patterns.get("weekly_average", 0) / 7 if income_patterns else 0
        
        for obligation in obligations:
            risk = self._assess_obligation(
                obligation, 
                bucket_balances, 
                daily_income,
                run_date
            )
            obligation_risks.append(risk)
            
            # Track red flag days
            if risk["is_red_flag"]:
                red_flag_days.append(risk["due_date"])
        
        # Sort by due date
        obligation_risks.sort(key=lambda x: x["due_date"])
        red_flag_days.sort()
        
        # Update state
        state["obligation_risks"] = obligation_risks
        state["red_flag_days"] = [d.isoformat() if isinstance(d, date) else d for d in red_flag_days]
        state["has_shortfall"] = len(red_flag_days) > 0
        
        return state
    
    def _assess_obligation(
        self,
        obligation: Dict[str, Any],
        bucket_balances: Dict[str, float],
        daily_income: float,
        run_date: date
    ) -> Dict[str, Any]:
        """Assess risk for a single obligation."""
        # Extract obligation details
        obligation_id = str(obligation.get("_id", obligation.get("id", "")))
        name = obligation.get("name", "Unknown")
        category = obligation.get("category", "other")
        amount = float(obligation.get("amount", 0))
        bucket_name = obligation.get("bucket_name", category)
        
        # Calculate due date
        due_day = obligation.get("due_day", 1)
        next_due = self._get_next_due_date(run_date, due_day)
        days_until = (next_due - run_date).days
        
        # Get current bucket balance
        current_balance = bucket_balances.get(bucket_name, 0)
        
        # Project balance at due date
        # Assume daily allocation rate = amount / 30
        daily_allocation = amount / 30
        projected_income_for_bucket = daily_allocation * days_until
        projected_balance = current_balance + projected_income_for_bucket
        
        # Calculate shortfall
        shortfall = max(0, amount - projected_balance)
        
        # Determine risk level
        risk_level, risk_score = self._calculate_risk(
            amount, projected_balance, days_until
        )
        
        # Is this a red flag day?
        is_red_flag = risk_level == "high" or shortfall > 0
        
        return {
            "obligation_id": obligation_id,
            "obligation_name": name,
            "category": category,
            "amount": amount,
            "due_date": next_due.isoformat(),
            "days_until_due": days_until,
            "bucket_name": bucket_name,
            "current_bucket_balance": current_balance,
            "projected_bucket_balance": round(projected_balance, 2),
            "shortfall_amount": round(shortfall, 2),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "is_red_flag": is_red_flag,
        }
    
    def _get_next_due_date(self, run_date: date, due_day: int) -> date:
        """Get the next due date for an obligation."""
        # Try this month first
        try:
            this_month_due = run_date.replace(day=due_day)
            if this_month_due >= run_date:
                return this_month_due
        except ValueError:
            # Invalid day for this month
            pass
        
        # Next month
        if run_date.month == 12:
            next_month = run_date.replace(year=run_date.year + 1, month=1, day=1)
        else:
            next_month = run_date.replace(month=run_date.month + 1, day=1)
        
        try:
            return next_month.replace(day=due_day)
        except ValueError:
            # Last day of month if day doesn't exist
            import calendar
            last_day = calendar.monthrange(next_month.year, next_month.month)[1]
            return next_month.replace(day=min(due_day, last_day))
    
    def _calculate_risk(
        self,
        amount: float,
        projected_balance: float,
        days_until: int
    ) -> tuple:
        """Calculate risk level and score."""
        if amount <= 0:
            return "low", 0
        
        # Coverage ratio
        coverage = projected_balance / amount
        
        # Base risk score (0-100)
        if coverage >= 1.0:
            base_score = 0
        elif coverage >= 0.8:
            base_score = 30
        elif coverage >= 0.5:
            base_score = 60
        else:
            base_score = 90
        
        # Adjust by time urgency
        if days_until <= 3:
            time_factor = 1.3
        elif days_until <= 7:
            time_factor = 1.1
        else:
            time_factor = 1.0
        
        final_score = min(100, base_score * time_factor)
        
        # Determine level
        if final_score >= 70:
            level = "high"
        elif final_score >= 40:
            level = "medium"
        else:
            level = "low"
        
        return level, round(final_score, 0)


# Function for LangGraph node
def obligation_risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node wrapper for Obligation Risk Agent."""
    agent = ObligationRiskAgent()
    return agent.run(state)
