"""
GigMoney Guru - Expense Analyzer Agent (LLM-Powered)

Uses GPT to analyze spending patterns and provide insights:
- Categorize spending
- Identify unusual expenses
- Compare to income
- Suggest savings opportunities
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
from app.llm.client import get_llm_client


EXPENSE_SYSTEM_PROMPT = """You are a spending analysis AI for Indian gig workers.

Analyze the user's expense patterns and provide actionable insights in Hinglish (mix of Hindi and English).

Consider:
1. Are they spending too much on any category?
2. How does spending compare to income?
3. Are there unusual or one-time expenses?
4. Where can they save money?

For a gig worker earning ₹15,000-25,000/month:
- Food: ₹3,000-5,000 is normal
- Fuel: ₹2,000-4,000 is normal
- Phone: ₹300-500 is normal

Respond ONLY with valid JSON:
{
  "total_spent": 5000,
  "by_category": {"food": 2000, "fuel": 1500, "phone": 300},
  "spending_health": "good",
  "insights": [
    "Food pe thoda zyada kharcha ho raha hai - ₹2000 is month",
    "Fuel expense normal range mein hai"
  ],
  "savings_tips": [
    "Ghar ka khana lao, ₹500/month bach sakta hai",
    "Petrol pump ka loyalty card use karo"
  ],
  "unusual_expenses": ["₹1500 medical expense on 25th"],
  "expense_vs_income_ratio": 0.35
}
"""


class ExpenseAnalyzerAgent:
    """
    LLM-powered agent that analyzes spending patterns.
    """
    
    def __init__(self):
        self.name = "expense_analyzer"
        self.llm = get_llm_client()
    
    async def run_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze expenses using LLM."""
        expense_history = state.get("expense_history", [])
        income_patterns = state.get("income_patterns", {})
        today_income = state.get("today_income", 0)
        run_date = state.get("run_date")
        
        if not expense_history:
            state["expense_analysis"] = {
                "total_spent": 0,
                "insights": ["No expenses recorded yet. Start tracking to get insights!"],
            }
            return state
        
        # Build context
        context = self._build_context(expense_history, income_patterns, run_date)
        
        try:
            response = await self.llm.generate_json(
                prompt=context,
                system_prompt=EXPENSE_SYSTEM_PROMPT,
                temperature=0.4
            )
            
            state["expense_analysis"] = {
                "total_spent": response.get("total_spent", 0),
                "by_category": response.get("by_category", {}),
                "spending_health": response.get("spending_health", "unknown"),
                "insights": response.get("insights", []),
                "savings_tips": response.get("savings_tips", []),
                "unusual_expenses": response.get("unusual_expenses", []),
                "expense_vs_income_ratio": response.get("expense_vs_income_ratio", 0),
                "ai_powered": True,
            }
            
            # Add insights to messages
            messages = state.get("messages", [])
            if response.get("insights"):
                for insight in response.get("insights", [])[:2]:
                    messages.append({
                        "content": f"💸 {insight}",
                        "message_type": "insight",
                        "priority": 4,
                    })
            state["messages"] = messages
            
        except Exception as e:
            print(f"Expense Analyzer LLM Error: {e}")
            state = self._fallback_analysis(state, expense_history, income_patterns)
        
        return state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Sync fallback."""
        expense_history = state.get("expense_history", [])
        income_patterns = state.get("income_patterns", {})
        return self._fallback_analysis(state, expense_history, income_patterns)
    
    def _build_context(self, expense_history, income_patterns, run_date):
        """Build context for LLM."""
        # Handle None values
        expense_history = expense_history or []
        income_patterns = income_patterns or {}
        
        # Group by category
        by_category = {}
        for exp in expense_history:
            if isinstance(exp, dict):
                cat = exp.get("category", "other")
                by_category[cat] = by_category.get(cat, 0) + exp.get("amount", 0)
        
        total_spent = sum(by_category.values())
        monthly_income = income_patterns.get("monthly_average", 0) if isinstance(income_patterns, dict) else 0
        
        return f"""
EXPENSE DATA (Last 30 days):

BY CATEGORY:
{json.dumps(by_category, indent=2)}

TOTAL SPENT: ₹{total_spent}

INDIVIDUAL EXPENSES:
{json.dumps([{
    "date": exp.get("spent_at", "")[:10] if exp.get("spent_at") else "",
    "category": exp.get("category"),
    "amount": exp.get("amount"),
    "description": exp.get("description", "")
} for exp in expense_history[-20:] if isinstance(exp, dict)], indent=2)}

MONTHLY INCOME: ₹{monthly_income}
EXPENSE/INCOME RATIO: {total_spent / max(monthly_income, 1):.2f}

Analyze this spending pattern and provide insights.
"""
    
    def _fallback_analysis(self, state, expense_history, income_patterns):
        """Simple analysis without LLM."""
        # Handle None values
        expense_history = expense_history or []
        income_patterns = income_patterns or {}
        
        # Group by category
        by_category = {}
        for exp in expense_history:
            if isinstance(exp, dict):
                cat = exp.get("category", "other")
                by_category[cat] = by_category.get(cat, 0) + exp.get("amount", 0)
        
        total_spent = sum(by_category.values())
        monthly_income = (income_patterns.get("monthly_average", 0) if isinstance(income_patterns, dict) else 0) or 15000
        ratio = total_spent / max(monthly_income, 1)
        
        # Generate insights
        insights = []
        if ratio > 0.7:
            insights.append("Kharcha income se zyada ho raha hai - budget banana zaroori hai")
        elif ratio > 0.5:
            insights.append("Spending moderate hai, thoda aur save kar sakte ho")
        else:
            insights.append("Achhi saving ho rahi hai! Keep it up 👍")
        
        # Category insights
        if by_category.get("food", 0) > 5000:
            insights.append(f"Food pe ₹{by_category['food']:.0f} kharcha - ghar ka khana try karo")
        if by_category.get("fuel", 0) > 4000:
            insights.append(f"Fuel pe ₹{by_category['fuel']:.0f} - kya route optimize kar sakte ho?")
        
        state["expense_analysis"] = {
            "total_spent": total_spent,
            "by_category": by_category,
            "spending_health": "good" if ratio < 0.5 else "moderate" if ratio < 0.7 else "high",
            "insights": insights,
            "savings_tips": ["Ghar ka khana lao", "Unnecessary subscriptions cancel karo"],
            "expense_vs_income_ratio": round(ratio, 2),
            "ai_powered": False,
        }
        
        return state


async def expense_analyzer_node_async(state: Dict[str, Any]) -> Dict[str, Any]:
    """Async node."""
    agent = ExpenseAnalyzerAgent()
    return await agent.run_async(state)


def expense_analyzer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Sync fallback."""
    agent = ExpenseAnalyzerAgent()
    return agent.run(state)
