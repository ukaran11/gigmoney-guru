"""
GigMoney Guru - Agent Router

LLM-powered agent that decides which agents to run based on the user's situation.
This is the brain of the agentic system - it has autonomy to choose actions.
"""
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from app.config import settings
import json


ROUTER_SYSTEM_PROMPT = """You are the AI coordinator for GigMoney Guru, a financial coach for Indian gig workers.

Your job is to analyze the user's financial situation and DECIDE which specialist agents need to run.
You have AUTONOMY - you choose what to do based on the situation.

AVAILABLE AGENTS (you decide which to activate):

1. INCOME_ANALYZER
   - Analyzes income patterns (weekday vs weekend, platform breakdown)
   - When to run: Always run first to understand earning patterns

2. EXPENSE_ANALYZER  
   - Analyzes spending patterns and finds savings opportunities
   - When to run: If user has expense history

3. OBLIGATION_RISK_ANALYZER
   - Calculates risk of missing bill payments
   - When to run: If user has obligations/bills

4. BUCKET_ALLOCATOR
   - Decides how to allocate money across buckets
   - When to run: If there's new income to allocate

5. RISK_CALCULATOR
   - Calculates overall financial risk score
   - When to run: After income and obligation analysis

6. GOAL_TRACKER
   - Tracks progress toward savings goals
   - When to run: If user has savings goals

7. CASHFLOW_FORECASTER
   - Predicts future income and expenses
   - When to run: For advance planning or when bills are due soon

8. ADVANCE_EVALUATOR
   - Evaluates if user should take a micro-advance
   - When to run: ONLY if there's a shortfall for upcoming bills

RULES:
- Analyze the situation carefully before deciding
- Don't run every agent - only the ones needed
- Prioritize based on urgency (upcoming bills > long-term goals)
- If income just arrived, prioritize allocation
- If there's a shortfall, prioritize advance evaluation
- Return your decision as JSON

Your response MUST be valid JSON with this structure:
{
  "reasoning": "Your analysis of the situation in 2-3 sentences",
  "urgency": "low|medium|high|critical",
  "agents_to_run": ["AGENT_NAME_1", "AGENT_NAME_2", ...],
  "focus_message": "One sentence about what matters most right now"
}
"""


class AgentRouter:
    """
    LLM-powered router that decides which agents to activate.
    This gives the system TRUE autonomy - it's not a fixed pipeline.
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def decide_agents(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the user's situation and decide which agents to run.
        
        Returns:
            {
                "reasoning": str,
                "urgency": str,
                "agents_to_run": List[str],
                "focus_message": str
            }
        """
        # Build context for the LLM
        context = self._build_context(state)
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate the response
            if "agents_to_run" not in result:
                result["agents_to_run"] = ["INCOME_ANALYZER", "RISK_CALCULATOR"]
            if "reasoning" not in result:
                result["reasoning"] = "Default analysis"
            if "urgency" not in result:
                result["urgency"] = "medium"
            if "focus_message" not in result:
                result["focus_message"] = "Analyzing your finances"
            
            return result
            
        except Exception as e:
            # Fallback to default agents
            return {
                "reasoning": f"Using default analysis (router error: {str(e)})",
                "urgency": "medium",
                "agents_to_run": [
                    "INCOME_ANALYZER",
                    "EXPENSE_ANALYZER", 
                    "OBLIGATION_RISK_ANALYZER",
                    "BUCKET_ALLOCATOR",
                    "RISK_CALCULATOR"
                ],
                "focus_message": "Running standard financial analysis"
            }
    
    def _build_context(self, state: Dict[str, Any]) -> str:
        """Build context string for the router LLM."""
        # Income summary
        today_income = state.get("today_income", 0)
        total_income = state.get("total_income", 0)
        income_count = len(state.get("income_history", []))
        
        # Expense summary
        expense_history = state.get("expense_history", [])
        total_expenses = sum(e.get("amount", 0) for e in expense_history)
        
        # Obligations summary
        obligations = state.get("obligations", [])
        obligation_risks = state.get("obligation_risks", [])
        
        # Calculate urgency indicators
        high_risk_obligations = [
            o for o in obligation_risks 
            if o.get("risk_level") in ["high", "critical"]
        ]
        
        # Bucket balances
        bucket_balances = state.get("bucket_balances", {})
        
        # Goals
        goals = state.get("goals", [])
        
        context = f"""
USER'S CURRENT FINANCIAL SITUATION:

💰 INCOME:
- Today's income: ₹{today_income}
- This month's total: ₹{total_income}
- Number of income entries: {income_count}

💸 EXPENSES:
- Total expenses this period: ₹{total_expenses}
- Number of expense entries: {len(expense_history)}

📋 OBLIGATIONS (BILLS):
- Total obligations: {len(obligations)}
- High/critical risk obligations: {len(high_risk_obligations)}
"""
        
        if high_risk_obligations:
            context += "\n⚠️ URGENT OBLIGATIONS:\n"
            for o in high_risk_obligations:
                context += f"  - {o.get('obligation_name')}: ₹{o.get('shortfall_amount', 0)} shortfall, {o.get('days_until_due')} days until due\n"
        
        context += f"""
🪣 BUCKET BALANCES:
- Essentials: ₹{bucket_balances.get('essentials', 0)}
- Flex (discretionary): ₹{bucket_balances.get('flex', 0)}
- Goals: ₹{bucket_balances.get('goals', 0)}
- Emergency: ₹{bucket_balances.get('emergency', 0)}

🎯 GOALS:
- Number of active goals: {len(goals)}

DECISION REQUIRED:
Based on this situation, which agents should I run?
Consider:
1. Is there new income that needs allocation?
2. Are there urgent bills at risk?
3. Is the user's spending concerning?
4. Should I evaluate a micro-advance?

Return your decision as JSON.
"""
        return context


# Singleton instance
agent_router = AgentRouter()


async def route_agents(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for agent routing.
    Returns routing decision from the LLM.
    """
    return await agent_router.decide_agents(state)
