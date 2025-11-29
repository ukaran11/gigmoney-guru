"""
GigMoney Guru - Async Agent Orchestrator

Runs the full agent pipeline with LLM-powered agents.
This is the REAL agentic system that uses GPT for decisions.
"""
from typing import Dict, Any, Optional
from datetime import datetime, date
import uuid
import asyncio

# Import all agents
from app.agents.income_pattern import IncomePatternAgent
from app.agents.obligation_risk import ObligationRiskAgent
from app.agents.expense_analyzer import ExpenseAnalyzerAgent
from app.agents.smart_allocator import SmartAllocatorAgent
from app.agents.risk_calculator import RiskCalculatorAgent
from app.agents.micro_advance import MicroAdvanceAgent
from app.agents.goal_scenario import GoalScenarioAgent
from app.agents.conversation import ConversationAgent
from app.agents.explainability import ExplainabilityAgent


async def run_agentic_pipeline(
    context: Dict[str, Any],
    run_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Run the full agentic pipeline with LLM-powered decisions.
    
    Pipeline:
    1. Income Pattern Analysis (math-based, fast)
    2. Obligation Risk Assessment (math-based, fast)
    3. Expense Analysis (LLM-powered) 
    4. Smart Allocation (LLM-powered)
    5. Risk Calculation (LLM-powered)
    6. Micro-Advance Check (rule-based)
    7. Goal Scenarios (rule-based)
    8. Conversation Generation (LLM-powered)
    9. Explainability (LLM-powered)
    
    Args:
        context: Financial context from load_financial_context()
        run_date: Date to run for
        
    Returns:
        Final state with all agent outputs
    """
    run_id = str(uuid.uuid4())[:8]
    
    if run_date is None:
        run_date = datetime.now().date()
    
    # Initialize state
    state = {
        **context,
        "run_id": run_id,
        "run_date": run_date.isoformat() if isinstance(run_date, date) else run_date,
        "agent_log": [],  # Track what each agent did
    }
    
    def log_agent(name: str, decision: str, details: Any = None):
        """Log agent activity."""
        state["agent_log"].append({
            "agent": name,
            "decision": decision,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        })
    
    try:
        # === Phase 1: Data Analysis (Fast, No LLM) ===
        
        # 1. Income Pattern Analysis
        income_agent = IncomePatternAgent()
        state = income_agent.run(state)
        log_agent("income_pattern", "Analyzed income patterns", {
            "weekday_avg": state.get("income_patterns", {}).get("weekday_average"),
            "trend": state.get("income_patterns", {}).get("trend_direction"),
        })
        
        # 2. Obligation Risk Assessment  
        risk_agent = ObligationRiskAgent()
        state = risk_agent.run(state)
        high_risks = [r for r in state.get("obligation_risks", []) if r.get("risk_level") == "high"]
        log_agent("obligation_risk", f"Found {len(high_risks)} high-risk obligations", {
            "high_risk_count": len(high_risks),
            "total_shortfall": sum(r.get("shortfall_amount", 0) for r in high_risks),
        })
        
        # === Phase 2: LLM-Powered Analysis ===
        
        # 3. Expense Analysis (LLM)
        expense_agent = ExpenseAnalyzerAgent()
        state = await expense_agent.run_async(state)
        expense_analysis = state.get("expense_analysis", {})
        log_agent("expense_analyzer", "Analyzed spending patterns", {
            "total_spent": expense_analysis.get("total_spent"),
            "health": expense_analysis.get("spending_health"),
            "insights_count": len(expense_analysis.get("insights", [])),
        })
        
        # 4. Smart Allocation (LLM)
        allocator = SmartAllocatorAgent()
        state = await allocator.run_async(state)
        allocation = state.get("today_allocation", {})
        log_agent("smart_allocator", "Made allocation decisions", {
            "total_income": allocation.get("total_income"),
            "safe_to_spend": allocation.get("safe_to_spend"),
            "ai_insight": allocation.get("ai_insight"),
        })
        
        # 5. Risk Calculation (LLM)
        risk_calc = RiskCalculatorAgent()
        state = await risk_calc.run_async(state)
        log_agent("risk_calculator", f"Calculated risk score: {state.get('risk_score')}/100", {
            "risk_score": state.get("risk_score"),
            "risk_level": state.get("risk_level"),
        })
        
        # === Phase 3: Decisions ===
        
        # 6. Micro-Advance Check
        advance_agent = MicroAdvanceAgent()
        state = advance_agent.run(state)
        advance = state.get("advance_proposal", {})
        log_agent("micro_advance", "Checked advance need", {
            "needed": advance.get("needed", False),
            "amount": advance.get("principal") if advance.get("needed") else None,
        })
        
        # 7. Goal Scenarios
        goal_agent = GoalScenarioAgent()
        state = goal_agent.run(state)
        log_agent("goal_scenario", f"Analyzed {len(state.get('goal_scenarios', []))} goals")
        
        # === Phase 4: Communication (LLM) ===
        
        # 8. Conversation Generation (LLM)
        conv_agent = ConversationAgent()
        state = await conv_agent.run_async(state)
        log_agent("conversation", f"Generated {len(state.get('messages', []))} messages")
        
        # 9. Explainability (LLM) 
        explain_agent = ExplainabilityAgent()
        state = await explain_agent.run_async(state)
        log_agent("explainability", f"Generated {len(state.get('explanations', []))} explanations")
        
        # Mark as successfully completed
        state["pipeline_completed"] = True
        state["pipeline_llm_powered"] = True
        
    except Exception as e:
        print(f"Agentic Pipeline Error: {e}")
        import traceback
        traceback.print_exc()
        state["error"] = str(e)
        state["pipeline_completed"] = False
    
    return state


# Sync wrapper for compatibility
def run_agent_graph(
    initial_state: Dict[str, Any],
    run_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Sync wrapper that runs the async pipeline.
    """
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context - this shouldn't happen in FastAPI
            # but just in case, run sync version
            return run_sync_pipeline(initial_state, run_date)
        else:
            return loop.run_until_complete(run_agentic_pipeline(initial_state, run_date))
    except RuntimeError:
        # No event loop exists, create one
        return asyncio.run(run_agentic_pipeline(initial_state, run_date))


def run_sync_pipeline(
    context: Dict[str, Any],
    run_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Synchronous fallback pipeline (no LLM calls).
    Used when async is not available.
    """
    run_id = str(uuid.uuid4())[:8]
    
    if run_date is None:
        run_date = datetime.now().date()
    
    state = {
        **context,
        "run_id": run_id,
        "run_date": run_date.isoformat() if isinstance(run_date, date) else run_date,
    }
    
    # Run sync versions of all agents
    state = IncomePatternAgent().run(state)
    state = ObligationRiskAgent().run(state)
    state = ExpenseAnalyzerAgent().run(state)
    state = SmartAllocatorAgent().run(state)
    state = RiskCalculatorAgent().run(state)
    state = MicroAdvanceAgent().run(state)
    state = GoalScenarioAgent().run(state)
    state = ConversationAgent().run(state)
    state = ExplainabilityAgent().run(state)
    
    state["pipeline_completed"] = True
    state["pipeline_llm_powered"] = False
    
    return state


def run_single_agent(
    agent_name: str,
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """Run a single agent for testing."""
    from app.agents.income_pattern import income_pattern_node
    from app.agents.obligation_risk import obligation_risk_node
    from app.agents.bucket_allocation import bucket_allocation_node
    from app.agents.micro_advance import micro_advance_node
    from app.agents.goal_scenario import goal_scenario_node
    from app.agents.conversation import conversation_node
    from app.agents.explainability import explainability_node
    from app.agents.expense_analyzer import expense_analyzer_node
    from app.agents.smart_allocator import smart_allocator_node
    from app.agents.risk_calculator import risk_calculator_node
    
    agents = {
        "income_pattern": income_pattern_node,
        "obligation_risk": obligation_risk_node,
        "bucket_allocation": bucket_allocation_node,
        "micro_advance": micro_advance_node,
        "goal_scenario": goal_scenario_node,
        "conversation": conversation_node,
        "explainability": explainability_node,
        "expense_analyzer": expense_analyzer_node,
        "smart_allocator": smart_allocator_node,
        "risk_calculator": risk_calculator_node,
    }
    
    if agent_name not in agents:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    return agents[agent_name](state)
