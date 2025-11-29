"""
GigMoney Guru - Risk Calculator Agent (LLM-Powered)

Uses GPT to assess overall financial health and risk:
- Analyzes all obligations and shortfalls
- Evaluates spending vs income patterns
- Considers emergency fund status
- Provides actionable risk score 0-100
"""
from typing import Dict, Any, List
from datetime import datetime
import json
from app.llm.client import get_llm_client


RISK_SYSTEM_PROMPT = """You are a financial risk assessment AI for Indian gig workers.

Analyze the user's complete financial situation and provide a risk score from 0-100:
- 0-30: Low risk - finances are healthy
- 31-50: Moderate risk - some attention needed
- 51-70: High risk - action required soon
- 71-100: Critical risk - immediate action needed

Consider:
1. Upcoming bills vs available funds
2. Days until obligations are due
3. Emergency fund status (should have at least ₹5000)
4. Income trend (declining = higher risk)
5. Expense patterns vs income

Respond ONLY with valid JSON:
{
  "risk_score": 45,
  "risk_level": "moderate",
  "primary_concerns": ["Rent due in 6 days with ₹2000 shortfall", "Emergency fund below ₹5000"],
  "positive_factors": ["Income trending up", "EMI bucket fully funded"],
  "recommended_actions": ["Work extra hours this weekend", "Reduce discretionary spending"],
  "forecast_summary": "Agle 30 din mein 24 din tight ho sakte hain. Pehla shortfall 2025-12-05 ko expected hai."
}
"""


class RiskCalculatorAgent:
    """
    LLM-powered agent that calculates real financial risk score.
    """
    
    def __init__(self):
        self.name = "risk_calculator"
        self.llm = get_llm_client()
    
    async def run_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk score using LLM analysis."""
        bucket_balances = state.get("bucket_balances", {})
        obligations = state.get("obligations", [])
        obligation_risks = state.get("obligation_risks", [])
        income_patterns = state.get("income_patterns", {})
        expense_history = state.get("expense_history", [])
        total_balance = state.get("total_balance", sum(bucket_balances.values()))
        
        # Build context
        context = self._build_context(
            bucket_balances, obligations, obligation_risks,
            income_patterns, expense_history, total_balance
        )
        
        try:
            response = await self.llm.generate_json(
                prompt=context,
                system_prompt=RISK_SYSTEM_PROMPT,
                temperature=0.2
            )
            
            risk_score = response.get("risk_score", 30)
            risk_level = response.get("risk_level", "moderate")
            primary_concerns = response.get("primary_concerns", [])
            positive_factors = response.get("positive_factors", [])
            recommended_actions = response.get("recommended_actions", [])
            forecast_summary = response.get("forecast_summary", "")
            
            # Update state
            state["risk_score"] = risk_score
            state["risk_level"] = risk_level
            state["risk_concerns"] = primary_concerns
            state["risk_positives"] = positive_factors
            state["recommended_actions"] = recommended_actions
            state["forecast_summary"] = forecast_summary
            
            # Add warnings for high-risk items
            if risk_score >= 50:
                warnings = state.get("warnings", [])
                for concern in primary_concerns[:2]:
                    warnings.append(f"⚠️ {concern}")
                state["warnings"] = warnings
            
        except Exception as e:
            print(f"Risk Calculator LLM Error: {e}")
            state = self._fallback_risk(state, obligation_risks, bucket_balances)
        
        return state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Sync fallback."""
        obligation_risks = state.get("obligation_risks", [])
        bucket_balances = state.get("bucket_balances", {})
        return self._fallback_risk(state, obligation_risks, bucket_balances)
    
    def _build_context(
        self, bucket_balances, obligations, obligation_risks,
        income_patterns, expense_history, total_balance
    ) -> str:
        """Build context for LLM risk analysis."""
        # Handle None values safely
        bucket_balances = bucket_balances or {}
        obligations = obligations or []
        obligation_risks = obligation_risks or []
        income_patterns = income_patterns or {}
        expense_history = expense_history or []
        
        # Summarize expenses
        recent_expenses = expense_history[-30:] if expense_history else []
        total_expenses = sum(e.get("amount", 0) for e in recent_expenses if isinstance(e, dict))
        
        # High risk obligations
        high_risks = [r for r in obligation_risks if isinstance(r, dict) and r.get("risk_level") in ["high", "medium"]]
        total_shortfall = sum(r.get("shortfall_amount", 0) for r in high_risks)
        
        # Safe access to income patterns
        weekly_avg = income_patterns.get("weekly_average", 0) if isinstance(income_patterns, dict) else 0
        trend = income_patterns.get("trend_direction", "flat") if isinstance(income_patterns, dict) else "flat"
        multiplier = income_patterns.get("season_multiplier", 1.0) if isinstance(income_patterns, dict) else 1.0
        
        return f"""
FINANCIAL SNAPSHOT:
- Total Balance: ₹{total_balance}
- Bucket Balances: {json.dumps(bucket_balances)}
- Emergency Fund: ₹{bucket_balances.get("emergency", 0)}

UPCOMING OBLIGATIONS:
{json.dumps([{
    "name": r.get("obligation_name"),
    "amount": r.get("amount"),
    "days_until": r.get("days_until_due"),
    "shortfall": r.get("shortfall_amount"),
    "risk": r.get("risk_level")
} for r in obligation_risks if isinstance(r, dict)], indent=2)}

TOTAL SHORTFALL: ₹{total_shortfall}

INCOME PATTERNS:
- Daily average: ₹{weekly_avg / 7:.0f}
- Trend: {trend}
- Weekend multiplier: {multiplier}

MONTHLY EXPENSES: ₹{total_expenses}

Assess the overall financial risk and provide your analysis.
"""
    
    def _fallback_risk(self, state, obligation_risks, bucket_balances):
        """Calculate risk without LLM."""
        # Handle None values
        obligation_risks = obligation_risks or []
        bucket_balances = bucket_balances or {}
        
        # Simple risk calculation
        high_risk_count = len([r for r in obligation_risks if isinstance(r, dict) and r.get("risk_level") == "high"])
        medium_risk_count = len([r for r in obligation_risks if isinstance(r, dict) and r.get("risk_level") == "medium"])
        
        total_shortfall = sum(r.get("shortfall_amount", 0) for r in obligation_risks if isinstance(r, dict))
        emergency_fund = bucket_balances.get("emergency", 0) if isinstance(bucket_balances, dict) else 0
        
        # Base score
        risk_score = 20  # Start low
        
        # Add for high-risk obligations
        risk_score += high_risk_count * 25
        risk_score += medium_risk_count * 10
        
        # Add for shortfall
        if total_shortfall > 0:
            risk_score += min(30, total_shortfall / 100)
        
        # Add if emergency fund is low
        if emergency_fund < 5000:
            risk_score += 15
        if emergency_fund < 2000:
            risk_score += 10
        
        risk_score = min(100, max(0, risk_score))
        
        # Determine level
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        state["risk_score"] = round(risk_score)
        state["risk_level"] = risk_level
        state["risk_concerns"] = [
            f"{r.get('obligation_name')} due in {r.get('days_until_due')} days"
            for r in obligation_risks if r.get("risk_level") == "high"
        ]
        
        return state


async def risk_calculator_node_async(state: Dict[str, Any]) -> Dict[str, Any]:
    """Async node for Risk Calculator."""
    agent = RiskCalculatorAgent()
    return await agent.run_async(state)


def risk_calculator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Sync fallback node."""
    agent = RiskCalculatorAgent()
    return agent.run(state)
