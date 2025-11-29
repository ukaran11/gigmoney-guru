"""
GigMoney Guru - Micro Advance Agent

Proposes micro-advances when shortfall is detected:
- Calculate advance amount needed
- Set repayment terms
- Apply guardrails
- Generate risk explanation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date


class MicroAdvanceAgent:
    """
    Agent that proposes micro-advances for shortfalls.
    
    Input:
        - forecast: From Cashflow Planner
        - obligation_risks: From Obligation Risk Agent
        - income_patterns: From Income Pattern Agent
        - active_advances: Currently active advances
        
    Output:
        - advance_proposal: Proposed advance (or none needed)
        - needs_advance: Boolean flag
    """
    
    def __init__(self):
        self.name = "micro_advance"
        
        # Guardrails
        self.max_advance_pct_of_weekly = 0.40  # Max 40% of weekly income
        self.max_active_advances = 1  # Don't stack advances
        self.min_advance_amount = 500  # Minimum advance
        self.max_advance_amount = 5000  # Maximum advance
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze if advance is needed and propose one.
        
        Algorithm:
        1. Check for upcoming shortfalls
        2. If no shortfall, return "no advance needed"
        3. If shortfall:
           a. Calculate amount needed
           b. Check against guardrails
           c. Find repayment date (next weekend)
           d. Calculate risk
           e. Generate proposal
        """
        forecast = state.get("forecast", [])
        obligation_risks = state.get("obligation_risks", [])
        income_patterns = state.get("income_patterns", {})
        active_advances = state.get("active_advances", [])
        run_date = state.get("run_date")
        
        if isinstance(run_date, str):
            run_date = datetime.fromisoformat(run_date).date()
        elif run_date is None:
            run_date = datetime.now().date()
        
        # Check if we already have an active advance
        if len(active_advances) >= self.max_active_advances:
            state["advance_proposal"] = {
                "needed": False,
                "reason": "Already have an active advance",
            }
            state["needs_advance"] = False
            return state
        
        # Find the first high-risk obligation
        high_risk = None
        for risk in obligation_risks:
            if risk.get("risk_level") == "high" and risk.get("shortfall_amount", 0) > 0:
                high_risk = risk
                break
        
        # If no high risk, check forecast for shortfall days
        if not high_risk:
            for day in forecast[:14]:  # Look at next 2 weeks
                if day.get("status") == "shortfall":
                    # Find associated obligation
                    due_obligations = day.get("obligations_due", [])
                    if due_obligations:
                        shortfall = abs(day.get("end_balance", 0))
                        high_risk = {
                            "obligation_name": due_obligations[0],
                            "shortfall_amount": shortfall,
                            "due_date": day.get("date"),
                            "days_until_due": (
                                datetime.fromisoformat(day["date"]).date() - run_date
                            ).days if isinstance(day.get("date"), str) else 7,
                        }
                        break
        
        # If still no issue, no advance needed
        if not high_risk:
            state["advance_proposal"] = {
                "needed": False,
                "reason": "No shortfall detected in next 2 weeks",
            }
            state["needs_advance"] = False
            return state
        
        # Calculate advance details
        shortfall = high_risk.get("shortfall_amount", 0)
        obligation_name = high_risk.get("obligation_name", "upcoming payment")
        
        # Get weekly income for guardrails
        weekly_income = income_patterns.get("weekly_average", 15000)
        
        # Calculate advance amount (cover shortfall + 10% buffer)
        proposed_amount = shortfall * 1.1
        
        # Apply guardrails
        max_allowed = weekly_income * self.max_advance_pct_of_weekly
        proposed_amount = min(proposed_amount, max_allowed)
        proposed_amount = min(proposed_amount, self.max_advance_amount)
        proposed_amount = max(proposed_amount, self.min_advance_amount)
        proposed_amount = round(proposed_amount, -2)  # Round to nearest 100
        
        # If amount is too small to be useful
        if proposed_amount < self.min_advance_amount:
            state["advance_proposal"] = {
                "needed": False,
                "reason": f"Shortfall (₹{shortfall:.0f}) too small for advance",
            }
            state["needs_advance"] = False
            return state
        
        # Find repayment date (next weekend)
        repayment_date = self._find_next_weekend(run_date)
        
        # Calculate risk
        risk_score, risk_explanation = self._calculate_risk(
            proposed_amount, weekly_income, repayment_date, run_date
        )
        
        # Generate proposal
        advance_proposal = {
            "needed": True,
            "principal": proposed_amount,
            "fee": 0,  # No fees in MVP
            "total_repayable": proposed_amount,
            "purpose": f"{obligation_name.lower()}_shortfall",
            "obligation_name": obligation_name,
            "shortfall_amount": round(shortfall, 0),
            "repayment_date": repayment_date.isoformat(),
            "repayment_source": "weekend_earnings",
            "max_percentage": self.max_advance_pct_of_weekly * 100,
            "risk_score": risk_score,
            "risk_explanation": risk_explanation,
            "weekly_income_estimate": round(weekly_income, 0),
            "advance_to_income_ratio": round((proposed_amount / weekly_income) * 100, 1),
            "impact_explanation": self._generate_impact_explanation(
                proposed_amount, repayment_date, weekly_income
            ),
            "without_advance_scenario": self._generate_without_scenario(
                shortfall, obligation_name, high_risk.get("due_date", "soon")
            ),
        }
        
        state["advance_proposal"] = advance_proposal
        state["needs_advance"] = True
        
        return state
    
    def _find_next_weekend(self, from_date: date) -> date:
        """Find the next Saturday or Sunday after from_date."""
        days_ahead = 5 - from_date.weekday()  # Saturday is 5
        if days_ahead <= 0:
            days_ahead += 7
        return from_date + timedelta(days=days_ahead)
    
    def _calculate_risk(
        self,
        amount: float,
        weekly_income: float,
        repayment_date: date,
        run_date: date
    ) -> tuple:
        """Calculate risk score and explanation."""
        ratio = amount / weekly_income
        days_to_repay = (repayment_date - run_date).days
        
        if ratio < 0.2 and days_to_repay >= 5:
            return "low", "Chhota advance hai aur weekend tak repay ho jayega."
        elif ratio < 0.3 and days_to_repay >= 3:
            return "medium", "Manageable hai, par weekend mein achha earning chahiye."
        else:
            return "high", "Thoda risky hai, weekend earnings pe depend karega."
    
    def _generate_impact_explanation(
        self,
        amount: float,
        repayment_date: date,
        weekly_income: float
    ) -> str:
        """Generate explanation of impact on future earnings."""
        repay_day = repayment_date.strftime("%A")
        weekend_estimate = weekly_income * 0.4  # Weekend is ~40% of weekly
        remaining = weekend_estimate - amount
        
        return (
            f"{repay_day} ko jab earnings aayegi, ₹{amount:.0f} auto-repay ho jayega. "
            f"Expected weekend earning ₹{weekend_estimate:.0f} mein se "
            f"₹{remaining:.0f} aapke paas bachega."
        )
    
    def _generate_without_scenario(
        self,
        shortfall: float,
        obligation_name: str,
        due_date: str
    ) -> str:
        """Generate scenario if user doesn't take advance."""
        return (
            f"Agar advance nahi lete, toh {obligation_name} ke liye "
            f"₹{shortfall:.0f} ki kami ho sakti hai. "
            f"Late payment se penalty ya credit score pe asar ho sakta hai."
        )


# Function for LangGraph node
def micro_advance_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node wrapper for Micro Advance Agent."""
    agent = MicroAdvanceAgent()
    return agent.run(state)
