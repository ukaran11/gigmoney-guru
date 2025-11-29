"""
GigMoney Guru - Agents API

Run the FULLY AGENTIC pipeline with:
- Agent Router (LLM decides which agents to run)
- ReAct Pattern (Reason, Act, Observe, Repeat)
- Tool Calling (Agents can query data and take actions)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, date
from typing import Optional
import traceback
import logging

from app.api.auth import get_current_user
from app.models.user import User
from app.orchestrator.agentic_pipeline import run_fully_agentic_pipeline, run_agent_with_mode
from app.orchestrator.state import load_financial_context, save_agent_decisions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Agents"])


@router.post("/run-daily")
async def run_daily_agents(
    target_date: Optional[str] = None,
    mode: str = Query("react", description="Agent mode: react, routed, or fast"),
    current_user: User = Depends(get_current_user)
):
    """
    Run the FULLY AGENTIC pipeline for daily analysis.
    
    Modes:
    - react: Full ReAct agent (maximum autonomy, tool calling)
    - routed: Router LLM decides which specialist agents to run
    - fast: Just calculations, no LLM (for quick responses)
    
    The ReAct agent can:
    1. THINK - Reason about the situation
    2. ACT - Call tools to get data or take actions
    3. OBSERVE - See the results
    4. REPEAT - Continue until analysis is complete
    """
    user_id = str(current_user.id)
    
    # Parse target date
    if target_date:
        run_date = datetime.fromisoformat(target_date).date()
    else:
        run_date = datetime.now().date()
    
    try:
        logger.info(f"[Run Daily] Starting for user {user_id} on {run_date} (mode={mode})")
        
        # Load context from database
        logger.info("[Run Daily] Loading financial context...")
        context = await load_financial_context(user_id, run_date)
        context["run_date"] = run_date
        logger.info(f"[Run Daily] Context loaded. Keys: {list(context.keys())}")
        
        # Run FULLY AGENTIC pipeline
        logger.info(f"[Run Daily] Running FULLY AGENTIC pipeline (mode={mode})...")
        result = await run_agent_with_mode(context, mode, user_id=user_id)
        logger.info(f"[Run Daily] Pipeline completed. Mode: {result.get('agentic_mode')}, Iterations: {result.get('react_iterations', 'N/A')}, Tools: {result.get('total_tool_calls', 'N/A')}")
        
        # Save decisions for observability
        run_id = f"{user_id}_{run_date.isoformat()}_{datetime.now().timestamp()}"
        result["run_id"] = run_id
        
        logger.info("[Run Daily] Saving agent decisions...")
        await save_agent_decisions(
            user_id=user_id,
            run_id=run_id,
            run_date=run_date,
            final_state=result
        )
        
        logger.info("[Run Daily] Completed successfully")
        
        # Get today's income breakdown for clarity
        today_income_events = context.get("today_income_events", [])
        today_sources = {}
        for event in today_income_events:
            source = event.get("source_name", "unknown")
            today_sources[source] = today_sources.get(source, 0) + event.get("amount", 0)
        
        # Return summary
        return {
            "success": True,
            "run_id": run_id,
            "run_date": run_date.isoformat(),
            
            # Agentic info
            "agentic_mode": result.get("agentic_mode"),
            "react_iterations": result.get("react_iterations"),
            "total_tool_calls": result.get("total_tool_calls", len(result.get("tool_calls_log", []))),
            "tool_calls_log": result.get("tool_calls_log", []),
            "reasoning_chain": result.get("reasoning_chain", []),
            "routing_decision": result.get("routing_decision"),
            
            # Today's data specifically
            "today_income_total": context.get("today_income", 0),
            "today_income_by_source": today_sources,
            
            # Key outputs from agent
            "safe_to_spend": result.get("safe_to_spend", 0),
            "key_insight": result.get("key_insight", ""),
            "recommended_action": result.get("recommended_action", ""),
            "confidence_score": result.get("confidence_score", 0),
            
            # Risk assessment
            "risk_score": result.get("risk_score", 0),
            "risk_level": result.get("risk_level", "unknown"),
            "risk_reasons": result.get("risk_reasons", []),
            
            # Advance proposal (if any)
            "advance_proposal": result.get("advance_proposal"),
            
            # Messages and alerts from agent to user
            "messages": result.get("messages", []),
            "alerts": result.get("alerts", []),
            
            # Decisions made (for memory/learning)
            "decisions_made": result.get("decisions_made", []),
            "bucket_changes": result.get("bucket_changes", []),
            
            # Agent activity log (for UI)
            "agent_activity": result.get("agent_activity", []),
            
            # Legacy fields for compatibility
            "income_patterns": result.get("income_patterns"),
            "today_allocation": result.get("today_allocation"),
            "forecast_summary": result.get("forecast_summary"),
            "expense_analysis": result.get("expense_analysis"),
            "warnings": result.get("warnings", []),
            
            # Flags
            "has_shortfall": result.get("has_shortfall", False),
            "needs_advance": result.get("needs_advance", False),
            "analysis_complete": result.get("analysis_complete", True),
        }
    except Exception as e:
        logger.error(f"[Run Daily] ERROR: {str(e)}")
        logger.error(f"[Run Daily] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/{agent_name}")
async def run_specific_agent(
    agent_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Run a specific agent for testing/debugging.
    
    In the new agentic system, you can run:
    - react: Full ReAct agent (calls tools autonomously)
    - router: Just the agent router (decides which agents to run)
    
    Or legacy agents:
    - income_pattern, obligation_risk, cashflow_planner, bucket_allocation, etc.
    """
    from app.agents.income_pattern import IncomePatternAgent
    from app.agents.obligation_risk import ObligationRiskAgent
    from app.agents.cashflow_planner import CashflowPlannerAgent
    from app.agents.bucket_allocation import BucketAllocationAgent
    from app.agents.micro_advance import MicroAdvanceAgent
    from app.agents.goal_scenario import GoalScenarioAgent
    from app.orchestrator.agent_router import route_agents
    from app.agents.react_agent import run_react_agent
    
    user_id = str(current_user.id)
    run_date = datetime.now().date()
    
    agent_map = {
        "income_pattern": IncomePatternAgent,
        "obligation_risk": ObligationRiskAgent,
        "cashflow_planner": CashflowPlannerAgent,
        "bucket_allocation": BucketAllocationAgent,
        "micro_advance": MicroAdvanceAgent,
        "goal_scenario": GoalScenarioAgent,
    }
    
    try:
        # Load context
        context = await load_financial_context(user_id, run_date)
        context["run_date"] = run_date
        
        if agent_name == "react":
            # Run full ReAct agent
            result = await run_react_agent(context)
            return {
                "success": True,
                "agent": "ReActAgent",
                "iterations": result.get("react_iterations"),
                "tool_calls": result.get("tool_calls_log", []),
                "result": {
                    "safe_to_spend": result.get("safe_to_spend"),
                    "key_insight": result.get("key_insight"),
                    "risk_score": result.get("risk_score"),
                    "messages": result.get("messages", []),
                }
            }
        elif agent_name == "router":
            # Just run the router to see decisions
            result = await route_agents(context)
            return {
                "success": True,
                "agent": "AgentRouter",
                "result": result
            }
        elif agent_name in agent_map:
            # Run legacy agent
            agent_class = agent_map[agent_name]
            agent = agent_class()
            result = agent.run(context)
            return {
                "success": True,
                "agent": agent_name,
                "result": result,
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent name. Options: react, router, {', '.join(agent_map.keys())}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions")
async def get_recent_decisions(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get recent agent decisions for a user."""
    from app.models.decision import AgentDecision
    from beanie import PydanticObjectId
    
    user_oid = PydanticObjectId(str(current_user.id))
    
    decisions = await AgentDecision.find(
        AgentDecision.user_id == user_oid
    ).sort("-created_at").limit(limit).to_list()
    
    return {
        "decisions": [
            {
                "id": str(d.id),
                "agent_name": d.agent_name,
                "run_id": d.run_id,
                "run_date": d.run_date.isoformat() if d.run_date else None,
                "decision_type": d.decision_type,
                "decision_value": d.decision_value,
                "created_at": d.created_at.isoformat(),
            }
            for d in decisions
        ]
    }


@router.get("/proactive-check")
async def run_proactive_checks(
    current_user: User = Depends(get_current_user)
):
    """
    Run all proactive checks and return alerts.
    This is called on dashboard load to show proactive AI insights.
    
    The PROACTIVE nature of this endpoint makes the system truly agentic:
    - Checks upcoming obligations automatically
    - Detects low bucket balances
    - Finds expense anomalies
    - Generates alerts without user asking
    """
    from app.services.proactive_agent import ProactiveAgentService
    
    user_id = str(current_user.id)
    
    result = await ProactiveAgentService.run_all_proactive_checks(user_id)
    
    return {
        "success": True,
        "proactive": True,
        "alerts": result.get("alerts", []),
        "alert_count": result.get("alert_count", 0),
        "urgent_count": result.get("urgent_count", 0),
        "checked_at": result.get("checked_at")
    }


@router.post("/daily-analysis")
async def run_daily_analysis(
    current_user: User = Depends(get_current_user)
):
    """
    Run comprehensive daily analysis.
    This would typically be scheduled to run each morning.
    """
    from app.services.proactive_agent import ProactiveAgentService
    
    user_id = str(current_user.id)
    
    result = await ProactiveAgentService.run_daily_analysis(user_id)
    
    return {
        "success": True,
        "trigger_type": "daily_analysis",
        "key_insight": result.get("key_insight", ""),
        "recommended_action": result.get("recommended_action", ""),
        "safe_to_spend": result.get("safe_to_spend", 0),
        "risk_score": result.get("risk_score", 0),
        "risk_level": result.get("risk_level", "unknown"),
        "alerts": result.get("all_alerts", []),
        "tools_used": result.get("tools_used", 0)
    }
