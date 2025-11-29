"""
GigMoney Guru - LangGraph Agent Orchestrator

Defines the agent graph and runs the full pipeline.
"""
from typing import Dict, Any, Optional
from datetime import datetime, date
import uuid

from langgraph.graph import StateGraph, END

from app.agents.income_pattern import income_pattern_node
from app.agents.obligation_risk import obligation_risk_node
from app.agents.cashflow_planner import cashflow_planner_node
from app.agents.bucket_allocation import bucket_allocation_node
from app.agents.micro_advance import micro_advance_node
from app.agents.goal_scenario import goal_scenario_node
from app.agents.conversation import conversation_node
from app.agents.explainability import explainability_node


def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph agent graph.
    
    Graph structure:
    START -> income_pattern -> obligation_risk -> cashflow_planner
          -> bucket_allocation -> micro_advance -> goal_scenario
          -> conversation -> explainability -> END
    
    Returns:
        Compiled StateGraph
    """
    # Define the graph with dict state
    graph = StateGraph(dict)
    
    # Add nodes (each agent)
    graph.add_node("income_pattern", income_pattern_node)
    graph.add_node("obligation_risk", obligation_risk_node)
    graph.add_node("cashflow_planner", cashflow_planner_node)
    graph.add_node("bucket_allocation", bucket_allocation_node)
    graph.add_node("micro_advance", micro_advance_node)
    graph.add_node("goal_scenario", goal_scenario_node)
    graph.add_node("conversation", conversation_node)
    graph.add_node("explainability", explainability_node)
    
    # Define edges (execution order)
    graph.set_entry_point("income_pattern")
    
    graph.add_edge("income_pattern", "obligation_risk")
    graph.add_edge("obligation_risk", "cashflow_planner")
    graph.add_edge("cashflow_planner", "bucket_allocation")
    graph.add_edge("bucket_allocation", "micro_advance")
    graph.add_edge("micro_advance", "goal_scenario")
    graph.add_edge("goal_scenario", "conversation")
    graph.add_edge("conversation", "explainability")
    graph.add_edge("explainability", END)
    
    return graph.compile()


def run_agent_graph(
    initial_state: Dict[str, Any],
    run_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Run the full agent graph with initial state.
    
    Args:
        initial_state: Initial financial context
        run_date: Date to run for (defaults to today)
        
    Returns:
        Final state with all agent outputs
    """
    # Generate run ID
    run_id = str(uuid.uuid4())[:8]
    
    # Set run date
    if run_date is None:
        run_date = datetime.now().date()
    
    # Prepare initial state
    state = {
        **initial_state,
        "run_id": run_id,
        "run_date": run_date.isoformat() if isinstance(run_date, date) else run_date,
    }
    
    # Create and run graph
    graph = create_agent_graph()
    
    try:
        result = graph.invoke(state)
        return result
    except Exception as e:
        print(f"Agent graph error: {e}")
        # Return partial state with error
        state["error"] = str(e)
        return state


def run_single_agent(
    agent_name: str,
    state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run a single agent for testing/debugging.
    
    Args:
        agent_name: Name of agent to run
        state: Input state
        
    Returns:
        Updated state
    """
    agents = {
        "income_pattern": income_pattern_node,
        "obligation_risk": obligation_risk_node,
        "cashflow_planner": cashflow_planner_node,
        "bucket_allocation": bucket_allocation_node,
        "micro_advance": micro_advance_node,
        "goal_scenario": goal_scenario_node,
        "conversation": conversation_node,
        "explainability": explainability_node,
    }
    
    if agent_name not in agents:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    return agents[agent_name](state)


# Partial graph runners for specific use cases

def run_allocation_only(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run only income pattern and allocation agents."""
    state = income_pattern_node(state)
    state = obligation_risk_node(state)
    state = bucket_allocation_node(state)
    return state


def run_forecast_only(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run income pattern and forecast agents."""
    state = income_pattern_node(state)
    state = obligation_risk_node(state)
    state = cashflow_planner_node(state)
    return state


def run_advance_check(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run agents to check if advance is needed."""
    state = income_pattern_node(state)
    state = obligation_risk_node(state)
    state = cashflow_planner_node(state)
    state = micro_advance_node(state)
    return state
