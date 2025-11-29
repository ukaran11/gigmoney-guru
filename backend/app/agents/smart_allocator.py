"""
GigMoney Guru - Smart Allocator Agent (LLM-Powered)

Uses GPT to make intelligent allocation decisions based on:
- Current financial situation
- Upcoming obligations and risks
- Spending patterns
- Goals progress
"""
from typing import Dict, Any, List
from datetime import datetime, date
import json
from app.llm.client import get_llm_client


ALLOCATION_SYSTEM_PROMPT = """You are a smart financial allocation AI for Indian gig workers.

You analyze the user's complete financial picture and decide how to allocate their daily income.

Your job is to:
1. Prioritize upcoming bills (rent, EMI) that are due soon
2. Ensure emergency fund has minimum buffer
3. Keep progress on savings goals
4. Leave enough for daily spending (safe-to-spend)

IMPORTANT RULES:
- Rent and EMI are top priority - never miss these
- If a bill is due in <7 days and bucket is underfunded, increase allocation
- Safe-to-spend should be AT LEAST 15% of income for food/fuel
- Be practical - this is a gig worker with variable income

Respond ONLY with a valid JSON object with this structure:
{
  "allocations": [
    {"bucket": "essentials", "amount": 500, "reason": "Room rent due in 6 days"},
    {"bucket": "flex", "amount": 200, "reason": "Daily spending needs"}
  ],
  "safe_to_spend": 200,
  "risk_assessment": "medium",
  "key_insight": "Rent is due soon, prioritizing essentials bucket",
  "recommended_action": "Try to earn extra ₹500 this week to be safe"
}
"""


class SmartAllocatorAgent:
    """
    LLM-powered allocation agent that makes intelligent decisions.
    """
    
    def __init__(self):
        self.name = "smart_allocator"
        self.llm = get_llm_client()
    
    async def run_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to make smart allocation decisions.
        """
        today_income = state.get("today_income", 0)
        bucket_balances = state.get("bucket_balances", {})
        obligations = state.get("obligations", [])
        obligation_risks = state.get("obligation_risks", [])
        income_patterns = state.get("income_patterns", {})
        expense_history = state.get("expense_history", [])
        goals = state.get("goals", [])
        run_date = state.get("run_date")
        
        if today_income <= 0:
            # No income to allocate
            state["today_allocation"] = {
                "date": run_date,
                "total_income": 0,
                "allocations": [],
                "safe_to_spend": 0,
                "ai_insight": "No income today to allocate",
            }
            return state
        
        # Build context for LLM
        context = self._build_context(
            today_income, bucket_balances, obligations,
            obligation_risks, income_patterns, expense_history, goals, run_date
        )
        
        try:
            # Call LLM for allocation decision
            response = await self.llm.generate_json(
                prompt=context,
                system_prompt=ALLOCATION_SYSTEM_PROMPT,
                temperature=0.3
            )
            
            # Process LLM response
            allocations = response.get("allocations", [])
            safe_to_spend = response.get("safe_to_spend", today_income * 0.15)
            risk_assessment = response.get("risk_assessment", "unknown")
            key_insight = response.get("key_insight", "")
            recommended_action = response.get("recommended_action", "")
            
            # Validate allocations don't exceed income
            total_allocated = sum(a.get("amount", 0) for a in allocations)
            if total_allocated > today_income:
                # Scale down proportionally
                scale = today_income / total_allocated
                for a in allocations:
                    a["amount"] = round(a["amount"] * scale, 0)
                total_allocated = today_income
                safe_to_spend = 0
            
            # Update bucket balances
            new_bucket_balances = bucket_balances.copy()
            formatted_allocations = []
            
            bucket_icons = {
                "essentials": "🏠", "flex": "🛒", "goals": "🎯",
                "emergency": "🆘", "rent": "🏠", "emi": "🏍️",
                "fuel": "⛽", "savings": "💰", "discretionary": "🎯"
            }
            
            for alloc in allocations:
                bucket = alloc.get("bucket", "flex")
                amount = alloc.get("amount", 0)
                reason = alloc.get("reason", "AI allocation")
                
                new_bucket_balances[bucket] = new_bucket_balances.get(bucket, 0) + amount
                
                formatted_allocations.append({
                    "bucket_name": bucket,
                    "amount": round(amount, 0),
                    "reason": reason,
                    "icon": bucket_icons.get(bucket, "💰"),
                })
            
            # Build allocation plan
            allocation_plan = {
                "date": run_date if isinstance(run_date, str) else run_date.isoformat(),
                "total_income": today_income,
                "allocations": formatted_allocations,
                "safe_to_spend": round(safe_to_spend, 0),
                "risk_assessment": risk_assessment,
                "ai_insight": key_insight,
                "recommended_action": recommended_action,
                "ai_powered": True,
            }
            
            state["today_allocation"] = allocation_plan
            state["bucket_balances"] = new_bucket_balances
            state["risk_score"] = self._risk_to_score(risk_assessment)
            state["safe_to_spend"] = round(safe_to_spend, 0)
            
        except Exception as e:
            print(f"Smart Allocator LLM Error: {e}")
            # Fallback to simple allocation
            state = self._fallback_allocation(state, today_income, bucket_balances, run_date)
        
        return state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Sync version with simple fallback."""
        today_income = state.get("today_income", 0)
        bucket_balances = state.get("bucket_balances", {})
        run_date = state.get("run_date")
        return self._fallback_allocation(state, today_income, bucket_balances, run_date)
    
    def _build_context(
        self, today_income, bucket_balances, obligations,
        obligation_risks, income_patterns, expense_history, goals, run_date
    ) -> str:
        """Build context string for LLM."""
        # Handle None values safely
        bucket_balances = bucket_balances or {}
        obligations = obligations or []
        obligation_risks = obligation_risks or []
        income_patterns = income_patterns or {}
        expense_history = expense_history or []
        goals = goals or []
        
        # Summarize expense patterns
        recent_expenses = expense_history[-30:] if expense_history else []
        expense_by_category = {}
        for exp in recent_expenses:
            cat = exp.get("category", "other") if isinstance(exp, dict) else "other"
            expense_by_category[cat] = expense_by_category.get(cat, 0) + (exp.get("amount", 0) if isinstance(exp, dict) else 0)
        
        # Summarize high-risk obligations
        high_risks = [r for r in obligation_risks if isinstance(r, dict) and r.get("risk_level") in ["high", "medium"]]
        
        # Safe access to income patterns
        weekday_avg = income_patterns.get("weekday_average", 0) if isinstance(income_patterns, dict) else 0
        weekend_avg = income_patterns.get("weekend_average", 0) if isinstance(income_patterns, dict) else 0
        trend = income_patterns.get("trend_direction", "flat") if isinstance(income_patterns, dict) else "flat"
        
        context = f"""
TODAY'S INCOME: ₹{today_income}

CURRENT BUCKET BALANCES:
{json.dumps(bucket_balances, indent=2)}

UPCOMING OBLIGATIONS (next 30 days):
{json.dumps([{
    "name": o.get("name"),
    "amount": o.get("amount"),
    "due_day": o.get("due_day"),
    "bucket": o.get("bucket_name")
} for o in obligations if isinstance(o, dict)], indent=2)}

HIGH-RISK ITEMS:
{json.dumps([{
    "name": r.get("obligation_name"),
    "amount": r.get("amount"),
    "days_until_due": r.get("days_until_due"),
    "shortfall": r.get("shortfall_amount"),
    "risk_level": r.get("risk_level")
} for r in high_risks], indent=2)}

MONTHLY SPENDING PATTERNS:
{json.dumps(expense_by_category, indent=2)}

INCOME PATTERNS:
- Weekday average: ₹{weekday_avg:.0f}
- Weekend average: ₹{weekend_avg:.0f}
- Trend: {trend}

ACTIVE GOALS:
{json.dumps([{
    "name": g.get("name"),
    "target": g.get("target_amount"),
    "current": g.get("current_amount"),
    "progress": round(g.get("current_amount", 0) / max(g.get("target_amount", 1), 1) * 100, 1)
} for g in goals if isinstance(g, dict)], indent=2)}

Based on this complete picture, decide how to allocate today's ₹{today_income} income.
Remember: The user needs money for food and fuel today (safe-to-spend), so don't allocate 100% to buckets.
"""
        return context
    
    def _fallback_allocation(self, state, today_income, bucket_balances, run_date):
        """Simple fallback when LLM unavailable."""
        if today_income <= 0:
            state["today_allocation"] = {
                "date": run_date if isinstance(run_date, str) else run_date.isoformat() if run_date else "",
                "total_income": 0,
                "allocations": [],
                "safe_to_spend": 0,
            }
            return state
        
        # Simple 50-30-20 rule
        essentials = today_income * 0.50
        flex = today_income * 0.30
        safe_to_spend = today_income * 0.20
        
        allocations = [
            {"bucket_name": "essentials", "amount": round(essentials, 0), "reason": "50% to bills", "icon": "🏠"},
            {"bucket_name": "flex", "amount": round(flex, 0), "reason": "30% to flex spending", "icon": "🛒"},
        ]
        
        new_balances = bucket_balances.copy()
        new_balances["essentials"] = new_balances.get("essentials", 0) + essentials
        new_balances["flex"] = new_balances.get("flex", 0) + flex
        
        state["today_allocation"] = {
            "date": run_date if isinstance(run_date, str) else run_date.isoformat() if run_date else "",
            "total_income": today_income,
            "allocations": allocations,
            "safe_to_spend": round(safe_to_spend, 0),
            "ai_powered": False,
        }
        state["bucket_balances"] = new_balances
        state["safe_to_spend"] = round(safe_to_spend, 0)
        
        return state
    
    def _risk_to_score(self, risk: str) -> int:
        """Convert risk level to 0-100 score."""
        return {"low": 20, "medium": 50, "high": 80, "critical": 95}.get(risk, 30)


# Async node for graph
async def smart_allocator_node_async(state: Dict[str, Any]) -> Dict[str, Any]:
    """Async LangGraph node for Smart Allocator."""
    agent = SmartAllocatorAgent()
    return await agent.run_async(state)


# Sync fallback node
def smart_allocator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Sync LangGraph node for Smart Allocator (fallback)."""
    agent = SmartAllocatorAgent()
    return agent.run(state)
