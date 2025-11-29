"""
GigMoney Guru - Fully Agentic Pipeline

This is the main orchestrator that implements TRUE agentic behavior:
1. Agent Router - LLM decides which agents to run (autonomy)
2. ReAct Pattern - Agents can reason, act, observe, repeat
3. Tool Calling - Agents can query data and take actions
4. Memory - Decisions are logged for learning
5. ENHANCED MODE - Planning, Self-Reflection, Debate, Learning
"""
from typing import Dict, Any, List
from datetime import datetime
import asyncio

from app.orchestrator.agent_router import route_agents
from app.agents.react_agent import run_react_agent
from app.agents.enhanced_react_agent import run_enhanced_react_agent
from app.agents.income_pattern import IncomePatternAgent
from app.agents.cashflow_planner import CashflowPlannerAgent
from app.agents.obligation_risk import ObligationRiskAgent
from app.agents.bucket_allocation import BucketAllocationAgent
from app.agents.goal_scenario import GoalScenarioAgent
from app.agents.micro_advance import MicroAdvanceAgent
from app.agents.smart_allocator import SmartAllocatorAgent
from app.agents.risk_calculator import RiskCalculatorAgent
from app.agents.expense_analyzer import ExpenseAnalyzerAgent


# Agent mapping
AGENT_MAP = {
    "INCOME_ANALYZER": IncomePatternAgent,
    "EXPENSE_ANALYZER": ExpenseAnalyzerAgent,
    "OBLIGATION_RISK_ANALYZER": ObligationRiskAgent,
    "BUCKET_ALLOCATOR": SmartAllocatorAgent,  # Use LLM-powered allocator
    "RISK_CALCULATOR": RiskCalculatorAgent,
    "GOAL_TRACKER": GoalScenarioAgent,
    "CASHFLOW_FORECASTER": CashflowPlannerAgent,
    "ADVANCE_EVALUATOR": MicroAdvanceAgent,
}


async def run_fully_agentic_pipeline(state: Dict[str, Any], use_react: bool = True, user_id: str = None, mode: str = None) -> Dict[str, Any]:
    """
    Run the fully agentic pipeline.
    
    This pipeline has FOUR modes:
    
    1. FULL REACT MODE (mode="react" or use_react=True):
       - Single ReAct agent handles everything
       - Has tools to query data and take actions
       - Maximum autonomy, minimum structure
    
    2. ENHANCED MODE (mode="enhanced"):
       - Planning: Creates multi-step plan before execution
       - Self-Reflection: Validates each action succeeded
       - Debate: Multiple perspectives before final decision
       - Learning: Adjusts behavior based on past outcomes
       
    3. ROUTED MODE (mode="routed" or use_react=False):
       - Router LLM decides which specialist agents to run
       - Each specialist agent runs independently
       - More structured but still autonomous routing
    
    4. FAST MODE (mode="fast"):
       - No LLM calls, just rule-based analysis
       - Fastest execution
    
    Args:
        state: The current financial state
        use_react: If True, use single ReAct agent. If False, use router + specialists.
        user_id: User ID for database persistence
        mode: Explicit mode selection ("react", "enhanced", "routed", "fast")
    
    Returns:
        Updated state with agent analysis results
    """
    start_time = datetime.now()
    
    # Determine mode
    if mode is None:
        mode = "react" if use_react else "routed"
    
    # Initialize agent activity log
    state["agent_activity"] = []
    state["agentic_mode"] = mode
    
    if mode == "enhanced":
        # ENHANCED MODE - Full agentic capabilities
        state["agent_activity"].append({
            "agent": "EnhancedReActAgent",
            "status": "running",
            "message": "🧠 AI is planning, analyzing, reflecting, and debating...",
            "features": ["planning", "self-reflection", "debate", "learning"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Run the Enhanced ReAct agent
        state = await run_enhanced_react_agent(state, user_id=user_id)
        
        # Build detailed completion message
        tool_count = len(state.get("tool_calls_log", []))
        iterations = state.get("react_iterations", 0)
        reflections = len(state.get("reflections", []))
        debate = state.get("debate_result", {})
        plan_revisions = state.get("plan_revisions", 0)
        
        state["agent_activity"].append({
            "agent": "EnhancedReActAgent",
            "status": "completed",
            "message": f"Deep analysis with {tool_count} tools, {reflections} reflections, {plan_revisions} plan revisions",
            "tools_called": tool_count,
            "iterations": iterations,
            "reflections_count": reflections,
            "plan_revisions": plan_revisions,
            "debate_held": bool(debate),
            "debate_confidence": debate.get("confidence"),
            "advisors_consulted": [p.get("advisor") for p in debate.get("individual_perspectives", [])],
            "learnings_applied": bool(state.get("learnings")),
            "timestamp": datetime.now().isoformat()
        })
        
    elif mode == "react":
        # FULL REACT MODE - Single agent with tools
        state["agent_activity"].append({
            "agent": "ReActAgent",
            "status": "running",
            "message": "AI is analyzing your finances with full autonomy...",
            "timestamp": datetime.now().isoformat()
        })
        
        # Run the ReAct agent with user_id for DB persistence
        state = await run_react_agent(state, user_id=user_id)
        
        # Build detailed completion message
        tool_count = len(state.get("tool_calls_log", []))
        iterations = state.get("react_iterations", 0)
        
        state["agent_activity"].append({
            "agent": "ReActAgent",
            "status": "completed",
            "message": f"Deep analysis complete: {tool_count} tools called in {iterations} cycles",
            "tools_called": tool_count,
            "iterations": iterations,
            "tools_used": [t.get("tool") for t in state.get("tool_calls_log", [])],
            "reasoning_chain": state.get("reasoning_chain", []),
            "timestamp": datetime.now().isoformat()
        })
        
    else:
        # ROUTED MODE - Router decides which agents to run
        
        # Step 1: Router decides
        state["agent_activity"].append({
            "agent": "AgentRouter",
            "status": "running",
            "message": "AI is deciding what analysis to perform...",
            "timestamp": datetime.now().isoformat()
        })
        
        routing_decision = await route_agents(state)
        
        state["routing_decision"] = routing_decision
        state["agent_activity"].append({
            "agent": "AgentRouter",
            "status": "completed",
            "message": f"Will run: {', '.join(routing_decision['agents_to_run'])}",
            "reasoning": routing_decision.get("reasoning"),
            "urgency": routing_decision.get("urgency"),
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 2: Run selected agents
        agents_to_run = routing_decision.get("agents_to_run", [])
        
        for agent_name in agents_to_run:
            agent_class = AGENT_MAP.get(agent_name)
            if not agent_class:
                continue
            
            state["agent_activity"].append({
                "agent": agent_name,
                "status": "running",
                "message": f"Running {agent_name}...",
                "timestamp": datetime.now().isoformat()
            })
            
            try:
                agent = agent_class()
                
                # Check if agent has async run method
                if hasattr(agent, "run_async"):
                    result = await agent.run_async(state)
                else:
                    result = agent.run(state)
                
                # Merge result into state
                if isinstance(result, dict):
                    state.update(result)
                
                state["agent_activity"].append({
                    "agent": agent_name,
                    "status": "completed",
                    "message": f"{agent_name} completed successfully",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                state["agent_activity"].append({
                    "agent": agent_name,
                    "status": "error",
                    "message": f"{agent_name} failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
    
    # Calculate total execution time
    end_time = datetime.now()
    state["execution_time_ms"] = (end_time - start_time).total_seconds() * 1000
    
    # Ensure we have required fields
    _ensure_required_fields(state)
    
    return state


def _ensure_required_fields(state: Dict[str, Any]) -> None:
    """Ensure all required fields exist in state with USEFUL defaults."""
    
    # Try to get values from today_allocation first
    today_allocation = state.get("today_allocation") or {}
    bucket_balances = state.get("bucket_balances") or {}
    obligations = state.get("obligations") or []
    obligation_risks = state.get("obligation_risks") or []
    
    # Calculate total balance
    total_balance = sum(bucket_balances.values()) if bucket_balances else 0
    
    # Safe to spend - check allocation first, then buckets
    if not state.get("safe_to_spend"):
        if today_allocation.get("safe_to_spend"):
            state["safe_to_spend"] = today_allocation["safe_to_spend"]
        else:
            state["safe_to_spend"] = (
                bucket_balances.get("flex", 0) +
                bucket_balances.get("discretionary", 0)
            )
    
    # Risk score - calculate from data if not set
    if not state.get("risk_score"):
        # Calculate risk based on obligation coverage
        total_obligations = sum(o.get("amount", 0) for o in obligations)
        if total_obligations > 0 and total_balance > 0:
            coverage_ratio = total_balance / total_obligations
            if coverage_ratio < 0.5:
                state["risk_score"] = 80
            elif coverage_ratio < 1.0:
                state["risk_score"] = 50
            elif coverage_ratio < 1.5:
                state["risk_score"] = 25
            else:
                state["risk_score"] = 10
        else:
            state["risk_score"] = 30  # Default moderate
    
    if not state.get("risk_level"):
        score = state["risk_score"]
        if score >= 75:
            state["risk_level"] = "critical"
        elif score >= 50:
            state["risk_level"] = "high"
        elif score >= 25:
            state["risk_level"] = "moderate"
        else:
            state["risk_level"] = "low"
    
    # Key insight - GENERATE useful insight from data if not set
    if not state.get("key_insight") or len(state.get("key_insight", "")) < 10:
        insight = _generate_smart_insight(state, bucket_balances, obligations, obligation_risks)
        state["key_insight"] = insight
    
    # Recommended action - GENERATE if not set
    if not state.get("recommended_action") or len(state.get("recommended_action", "")) < 5:
        action = _generate_recommended_action(state, bucket_balances, obligations)
        state["recommended_action"] = action
    
    # AI insight (for frontend) - same as key_insight
    state["ai_insight"] = state.get("key_insight", "")


def _generate_smart_insight(state: Dict, buckets: Dict, obligations: List, risks: List) -> str:
    """Generate a meaningful insight from the data."""
    total_balance = sum(buckets.values()) if buckets else 0
    safe_to_spend = state.get("safe_to_spend", 0)
    today_income = state.get("today_income", 0)
    
    # Find urgent obligations
    urgent_obligations = []
    for risk in risks:
        if risk.get("days_until_due", 30) <= 5:
            urgent_obligations.append(risk)
    
    # Find shortfalls
    total_shortfall = sum(r.get("shortfall_amount", 0) for r in risks if r.get("shortfall_amount", 0) > 0)
    
    # Generate insight based on situation
    if total_shortfall > 0:
        urgent_name = urgent_obligations[0].get("obligation_name", "bill") if urgent_obligations else "bills"
        return f"⚠️ Bhai, ₹{int(total_shortfall):,} ka gap hai {urgent_name} ke liye! Aaj thoda extra kaam karke cover kar lo, warna late fee lagega."
    
    if urgent_obligations:
        ob = urgent_obligations[0]
        days = ob.get("days_until_due", 0)
        name = ob.get("obligation_name", "bill")
        amount = ob.get("amount", 0)
        return f"📅 {name} ka ₹{int(amount):,} {days} din mein due hai. Essentials bucket check karo - cover ho jayega!"
    
    if today_income > 0:
        return f"💰 Aaj ₹{int(today_income):,} kamaye! Accha chal raha hai. Safe to spend: ₹{int(safe_to_spend):,} - baaki bills ke liye set aside hai."
    
    if total_balance > 0:
        # Find lowest bucket
        if buckets:
            lowest_bucket = min(buckets.items(), key=lambda x: x[1])
            if lowest_bucket[1] < 1000:
                return f"💡 {lowest_bucket[0].title()} bucket mein sirf ₹{int(lowest_bucket[1]):,} hai. Agle income se pehle top-up karo!"
        return f"✅ Total balance ₹{int(total_balance):,} hai. Safe to spend aaj: ₹{int(safe_to_spend):,}"
    
    return "👋 Namaste! Add some income and bills to get personalized insights."


def _generate_recommended_action(state: Dict, buckets: Dict, obligations: List) -> str:
    """Generate a recommended action from the data."""
    total_balance = sum(buckets.values()) if buckets else 0
    risks = state.get("obligation_risks", []) or []
    
    # Check for shortfalls first
    for risk in risks:
        if risk.get("shortfall_amount", 0) > 500:
            shortfall = risk.get("shortfall_amount", 0)
            return f"Consider a micro-advance of ₹{int(shortfall):,} to cover the gap - repay in 7 days with just 2% fee."
    
    # Check for low emergency bucket
    emergency = buckets.get("emergency", 0)
    if emergency < 2000 and total_balance > 5000:
        return "Emergency fund thoda low hai. Agle income ka 10% emergency mein daalo."
    
    # Check for upcoming obligations
    upcoming = [o for o in obligations if o.get("days_until_due", 30) <= 7]
    if upcoming:
        names = ", ".join([o.get("name", "bill")[:10] for o in upcoming[:2]])
        return f"Focus on: {names} - ye hafte due hai. Extra trip le lo agar possible ho."
    
    # Default positive action
    if total_balance > 0:
        return "Sab set hai! Apna kaam karo aur consistent income maintain karo. 💪"
    
    return "Start by adding your income and monthly bills to get smart recommendations."


async def run_agent_with_mode(state: Dict[str, Any], mode: str = "react", user_id: str = None) -> Dict[str, Any]:
    """
    Run agents with a specific mode.
    
    Modes:
    - "enhanced": Full agentic with planning, reflection, debate, learning
    - "react": Full ReAct agent (maximum autonomy)
    - "routed": Router + specialist agents
    - "fast": Just run essential analysis (no LLM)
    """
    if mode == "enhanced":
        return await run_fully_agentic_pipeline(state, mode="enhanced", user_id=user_id)
    elif mode == "react":
        return await run_fully_agentic_pipeline(state, mode="react", user_id=user_id)
    elif mode == "routed":
        return await run_fully_agentic_pipeline(state, mode="routed", user_id=user_id)
    elif mode == "fast":
        # Fast mode - no LLM, just calculations
        from app.orchestrator.graph import run_agent_graph
        result = run_agent_graph(state)
        result["agentic_mode"] = "fast"
        return result
    else:
        return await run_fully_agentic_pipeline(state, mode="react", user_id=user_id)
