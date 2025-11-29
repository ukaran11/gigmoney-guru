"""
GigMoney Guru - Explainability Agent

Generates human-readable explanations for all decisions:
- Allocation explanations
- Risk explanations
- Advance recommendations
"""
from typing import Dict, Any, List
from datetime import datetime
from app.llm.client import get_llm_client
from app.llm.prompts import PromptTemplates


class ExplainabilityAgent:
    """
    Agent that generates explanations for all decisions.
    
    Input:
        - Full context from previous agents
        
    Output:
        - explanations: List of explanations for each decision
    """
    
    def __init__(self):
        self.name = "explainability"
        self.prompts = PromptTemplates()
    
    async def run_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate explanations (async version for LLM calls).
        """
        llm = get_llm_client()
        explanations = []
        
        # Explain allocation
        today_allocation = state.get("today_allocation", {})
        if today_allocation:
            alloc_exp = await self._explain_allocation(llm, state)
            explanations.append(alloc_exp)
        
        # Explain risk assessments
        obligation_risks = state.get("obligation_risks", [])
        high_risks = [r for r in obligation_risks if r.get("risk_level") in ["high", "medium"]]
        for risk in high_risks[:2]:  # Limit to 2 explanations
            risk_exp = await self._explain_risk(llm, risk)
            explanations.append(risk_exp)
        
        # Explain advance recommendation
        advance_proposal = state.get("advance_proposal", {})
        if advance_proposal.get("needed"):
            advance_exp = await self._explain_advance(llm, advance_proposal, state)
            explanations.append(advance_exp)
        
        state["explanations"] = explanations
        
        return state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync version with fallback explanations.
        """
        explanations = []
        
        # Explain allocation
        today_allocation = state.get("today_allocation", {})
        income_patterns = state.get("income_patterns", {})
        
        if today_allocation:
            adjustments = today_allocation.get("adjustments_made", [])
            if adjustments:
                exp_text = " ".join(adjustments)
            else:
                exp_text = (
                    f"Income ko priority ke hisaab se divide kiya: "
                    f"pehle rent aur EMI, phir tax, fuel, aur savings."
                )
            
            explanations.append({
                "topic": "Today's Allocation",
                "explanation": exp_text,
                "data_points": {
                    "total_income": today_allocation.get("total_income", 0),
                    "safe_to_spend": today_allocation.get("safe_to_spend", 0),
                }
            })
        
        # Explain trend
        if income_patterns:
            trend = income_patterns.get("trend_direction", "flat")
            trend_pct = income_patterns.get("trend_percentage", 0)
            
            if trend == "up":
                exp_text = f"Achhi khabar! Pichle 2 hafton mein income {trend_pct:.0f}% badha hai."
            elif trend == "down":
                exp_text = f"Income thodi kam hui hai ({trend_pct:.0f}%). Thoda zyada kaam karna helpful ho sakta hai."
            else:
                exp_text = "Income stable chal rahi hai. Good job maintaining consistency!"
            
            explanations.append({
                "topic": "Income Trend",
                "explanation": exp_text,
                "data_points": {
                    "weekday_avg": income_patterns.get("weekday_average", 0),
                    "weekend_avg": income_patterns.get("weekend_average", 0),
                }
            })
        
        # Explain high risk obligations
        obligation_risks = state.get("obligation_risks", [])
        for risk in obligation_risks:
            if risk.get("risk_level") == "high":
                shortfall = risk.get("shortfall_amount", 0)
                days = risk.get("days_until_due", 0)
                
                explanations.append({
                    "topic": f"{risk.get('obligation_name')} Risk",
                    "explanation": (
                        f"₹{shortfall:.0f} ki shortage hai aur {days} din bache hain. "
                        f"Extra income ya advance se cover ho sakta hai."
                    ),
                    "data_points": {
                        "amount_due": risk.get("amount", 0),
                        "current_balance": risk.get("current_bucket_balance", 0),
                        "shortfall": shortfall,
                    }
                })
                break
        
        # Explain advance
        advance_proposal = state.get("advance_proposal", {})
        if advance_proposal.get("needed"):
            explanations.append({
                "topic": "Micro-Advance Recommendation",
                "explanation": (
                    f"₹{advance_proposal.get('principal', 0):.0f} ka advance isliye recommend kiya "
                    f"kyunki {advance_proposal.get('obligation_name')} ke liye paise kam pad rahe hain. "
                    f"Weekend earnings se repay ho jayega."
                ),
                "data_points": {
                    "advance_amount": advance_proposal.get("principal", 0),
                    "shortfall_covered": advance_proposal.get("shortfall_amount", 0),
                    "risk_level": advance_proposal.get("risk_score", "low"),
                }
            })
        
        state["explanations"] = explanations
        
        return state
    
    async def _explain_allocation(self, llm, state: Dict) -> Dict[str, Any]:
        """Generate allocation explanation."""
        today_allocation = state.get("today_allocation", {})
        allocs = today_allocation.get("allocations", [])
        
        factors = []
        obligation_risks = state.get("obligation_risks", [])
        high_risks = [r for r in obligation_risks if r.get("risk_level") == "high"]
        if high_risks:
            factors.append(f"High risk: {high_risks[0].get('obligation_name')}")
        
        income_patterns = state.get("income_patterns", {})
        if income_patterns.get("trend_direction") == "down":
            factors.append("Income trend is down")
        
        prompt = PromptTemplates.EXPLAIN_ALLOCATION.format(
            total_income=today_allocation.get("total_income", 0),
            allocations=", ".join([f"{a['bucket_name']}: ₹{a['amount']}" for a in allocs]),
            safe_to_spend=today_allocation.get("safe_to_spend", 0),
            factors=", ".join(factors) if factors else "Standard priority-based allocation"
        )
        
        try:
            explanation = await llm.generate_text(
                prompt,
                system_prompt=PromptTemplates.SYSTEM_EXPLAINABILITY,
                temperature=0.5
            )
        except:
            explanation = "Income ko priority ke hisaab se divide kiya: pehle rent/EMI, phir baaki."
        
        return {
            "topic": "Today's Allocation",
            "explanation": explanation,
            "data_points": {
                "total_income": today_allocation.get("total_income", 0),
                "safe_to_spend": today_allocation.get("safe_to_spend", 0),
            }
        }
    
    async def _explain_risk(self, llm, risk: Dict) -> Dict[str, Any]:
        """Generate risk explanation."""
        prompt = PromptTemplates.EXPLAIN_RISK.format(
            obligation_name=risk.get("obligation_name", "Payment"),
            risk_level=risk.get("risk_level", "medium"),
            factors=f"Shortfall: ₹{risk.get('shortfall_amount', 0)}, Days left: {risk.get('days_until_due', 0)}",
            recommendation="Increase allocation or consider advance"
        )
        
        try:
            explanation = await llm.generate_text(
                prompt,
                system_prompt=PromptTemplates.SYSTEM_EXPLAINABILITY,
                temperature=0.5
            )
        except:
            explanation = f"{risk.get('obligation_name')} mein thodi kami hai, par manageable hai."
        
        return {
            "topic": f"{risk.get('obligation_name')} Risk",
            "explanation": explanation,
            "data_points": {
                "amount_due": risk.get("amount", 0),
                "shortfall": risk.get("shortfall_amount", 0),
            }
        }
    
    async def _explain_advance(self, llm, proposal: Dict, state: Dict) -> Dict[str, Any]:
        """Generate advance recommendation explanation."""
        # Find the shortfall day from forecast
        forecast = state.get("forecast", [])
        shortfall_day = next(
            (d for d in forecast if d.get("status") == "shortfall"),
            None
        )
        
        prompt = PromptTemplates.EXPLAIN_ADVANCE_RECOMMENDATION.format(
            shortfall=proposal.get("shortfall_amount", 0),
            shortfall_date=shortfall_day.get("date", "soon") if shortfall_day else "soon",
            obligation_name=proposal.get("obligation_name", "payment"),
            advance_amount=proposal.get("principal", 0),
            without_advance_scenario=proposal.get("without_advance_scenario", "Payment might be late"),
            risk_assessment=proposal.get("risk_explanation", "Low risk")
        )
        
        try:
            explanation = await llm.generate_text(
                prompt,
                system_prompt=PromptTemplates.SYSTEM_EXPLAINABILITY,
                temperature=0.5
            )
        except:
            explanation = proposal.get("impact_explanation", "Weekend earnings se repay ho jayega.")
        
        return {
            "topic": "Micro-Advance Recommendation",
            "explanation": explanation,
            "data_points": {
                "advance_amount": proposal.get("principal", 0),
                "repayment_date": proposal.get("repayment_date", ""),
            }
        }


# Function for LangGraph node
def explainability_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node wrapper for Explainability Agent."""
    agent = ExplainabilityAgent()
    return agent.run(state)


async def explainability_node_async(state: Dict[str, Any]) -> Dict[str, Any]:
    """Async LangGraph node wrapper for Explainability Agent."""
    agent = ExplainabilityAgent()
    return await agent.run_async(state)
