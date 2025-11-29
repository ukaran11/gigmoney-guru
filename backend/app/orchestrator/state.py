"""
GigMoney Guru - State Management

Functions to load and save financial context from/to MongoDB.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from beanie import PydanticObjectId

from app.models.user import User
from app.models.income import IncomeEvent
from app.models.expense import ExpenseEvent
from app.models.obligation import Obligation
from app.models.bucket import Bucket
from app.models.goal import Goal
from app.models.advance import MicroAdvance
from app.models.decision import AgentDecision


async def load_financial_context(
    user_id: str,
    run_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Load complete financial context from database.
    
    Args:
        user_id: User's MongoDB ID
        run_date: Date to load context for (defaults to today)
        
    Returns:
        Dict with all context for agent graph
    """
    if run_date is None:
        run_date = datetime.now().date()
    
    # Convert string ID to PydanticObjectId
    user_oid = PydanticObjectId(user_id)
    
    # Load user
    user = await User.get(user_oid)
    if not user:
        raise ValueError(f"User not found: {user_id}")
    
    # Load income history (last 30 days)
    thirty_days_ago = datetime.combine(run_date - timedelta(days=30), datetime.min.time())
    income_events = await IncomeEvent.find(
        IncomeEvent.user_id == user_oid,
        IncomeEvent.earned_at >= thirty_days_ago
    ).to_list()
    
    # Load today's income
    today_start = datetime.combine(run_date, datetime.min.time())
    today_end = datetime.combine(run_date, datetime.max.time())
    today_income_events = await IncomeEvent.find(
        IncomeEvent.user_id == user_oid,
        IncomeEvent.earned_at >= today_start,
        IncomeEvent.earned_at <= today_end
    ).to_list()
    
    # Load expense history
    expense_events = await ExpenseEvent.find(
        ExpenseEvent.user_id == user_oid,
        ExpenseEvent.spent_at >= thirty_days_ago
    ).to_list()
    
    # Load obligations
    obligations = await Obligation.find(
        Obligation.user_id == user_oid,
        {"is_active": True}
    ).to_list()
    
    # Load buckets
    buckets = await Bucket.find(
        Bucket.user_id == user_oid,
        {"is_active": True}
    ).to_list()
    
    # Load goals
    goals = await Goal.find(
        Goal.user_id == user_oid,
        {"status": "active"}
    ).to_list()
    
    # Load active advances
    active_advances = await MicroAdvance.find(
        MicroAdvance.user_id == user_oid,
        {"status": {"$in": ["accepted", "active"]}}
    ).to_list()
    
    # Build bucket balances dict
    bucket_balances = {
        bucket.name: bucket.current_balance
        for bucket in buckets
    }
    
    # Calculate today's total income
    today_income = sum(event.amount for event in today_income_events)
    
    # Build context dict
    context = {
        "user_id": user_id,
        "user_name": user.name,
        "preferred_language": user.preferred_language,
        "run_date": run_date.isoformat(),
        
        # Balances
        "total_balance": sum(bucket_balances.values()),
        "bucket_balances": bucket_balances,
        
        # Today
        "today_income": today_income,
        "today_income_events": [
            {
                "id": str(e.id),
                "source_type": e.source_type,
                "source_name": e.source_name,
                "platform_type": e.platform_type,
                "amount": e.amount,
                "earned_at": e.earned_at.isoformat(),
            }
            for e in today_income_events
        ],
        
        # History
        "income_history": [
            {
                "id": str(e.id),
                "source_name": e.source_name,
                "platform_type": e.platform_type,
                "amount": e.amount,
                "earned_at": e.earned_at.isoformat(),
            }
            for e in income_events
        ],
        "expense_history": [
            {
                "id": str(e.id),
                "category": e.category,
                "amount": e.amount,
                "spent_at": e.spent_at.isoformat(),
            }
            for e in expense_events
        ],
        
        # Obligations
        "obligations": [
            {
                "id": str(o.id),
                "name": o.name,
                "category": o.category,
                "amount": o.amount,
                "frequency": o.frequency,
                "due_day": o.due_day,
                "is_flexible": o.is_flexible,
                "bucket_name": o.bucket_name,
                "is_active": o.is_active,
            }
            for o in obligations
        ],
        
        # Goals
        "goals": [
            {
                "id": str(g.id),
                "name": g.name,
                "target_amount": g.target_amount,
                "current_amount": g.current_amount,
                "target_date": g.target_date.isoformat() if g.target_date else None,
                "monthly_contribution": g.monthly_contribution,
                "status": g.status,
            }
            for g in goals
        ],
        
        # Active advances
        "active_advances": [
            {
                "id": str(a.id),
                "principal": a.principal,
                "total_repayable": a.total_repayable,
                "amount_repaid": a.amount_repaid,
                "status": a.status,
                "repayment_date": a.repayment_date.isoformat(),
            }
            for a in active_advances
        ],
        
        # Will be populated by agents
        "income_patterns": None,
        "obligation_risks": [],
        "red_flag_days": [],
        "forecast": [],
        "forecast_summary": "",
        "today_allocation": None,
        "advance_proposal": None,
        "goal_scenarios": [],
        "messages": [],
        "explanations": [],
        "warnings": [],
        "has_shortfall": False,
        "needs_advance": False,
    }
    
    return context


async def save_agent_decisions(
    user_id: str,
    run_id: str,
    run_date: date,
    final_state: Dict[str, Any]
) -> List[str]:
    """
    Save agent decisions to database for observability.
    
    Args:
        user_id: User's MongoDB ID
        run_id: Unique run identifier
        run_date: Date of the run
        final_state: Final state after all agents
        
    Returns:
        List of saved decision IDs
    """
    user_oid = PydanticObjectId(user_id)
    decision_ids = []
    
    # Save income pattern decision
    if final_state.get("income_patterns"):
        decision = AgentDecision(
            user_id=user_oid,
            agent_name="income_pattern",
            run_id=run_id,
            run_date=datetime.combine(run_date, datetime.min.time()),
            input_summary={
                "income_events_count": len(final_state.get("income_history", [])),
            },
            output_summary=final_state["income_patterns"],
            decision_type="pattern_analysis",
            decision_value=f"Trend: {final_state['income_patterns'].get('trend_direction', 'flat')}",
        )
        await decision.insert()
        decision_ids.append(str(decision.id))
    
    # Save allocation decision
    if final_state.get("today_allocation"):
        alloc = final_state["today_allocation"]
        decision = AgentDecision(
            user_id=user_oid,
            agent_name="bucket_allocation",
            run_id=run_id,
            run_date=datetime.combine(run_date, datetime.min.time()),
            input_summary={
                "today_income": final_state.get("today_income", 0),
            },
            output_summary=alloc,
            decision_type="allocation",
            decision_value=f"Safe to spend: ₹{alloc.get('safe_to_spend', 0)}",
        )
        await decision.insert()
        decision_ids.append(str(decision.id))
    
    # Save advance decision
    if final_state.get("advance_proposal"):
        proposal = final_state["advance_proposal"]
        decision = AgentDecision(
            user_id=user_oid,
            agent_name="micro_advance",
            run_id=run_id,
            run_date=datetime.combine(run_date, datetime.min.time()),
            input_summary={
                "has_shortfall": final_state.get("has_shortfall", False),
            },
            output_summary=proposal,
            decision_type="advance_recommendation",
            decision_value=f"Advance needed: {proposal.get('needed', False)}",
        )
        await decision.insert()
        decision_ids.append(str(decision.id))
    
    return decision_ids


async def update_bucket_balances(
    user_id: str,
    allocations: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Update bucket balances after allocation.
    
    Args:
        user_id: User's MongoDB ID
        allocations: List of allocations from Bucket Allocation Agent
        
    Returns:
        Updated bucket balances
    """
    user_oid = PydanticObjectId(user_id)
    updated_balances = {}
    
    for alloc in allocations:
        bucket_name = alloc.get("bucket_name")
        amount = alloc.get("amount", 0)
        
        bucket = await Bucket.find_one(
            Bucket.user_id == user_oid,
            Bucket.name == bucket_name
        )
        
        if bucket:
            bucket.current_balance += amount
            bucket.last_allocation_at = datetime.utcnow()
            bucket.updated_at = datetime.utcnow()
            await bucket.save()
            updated_balances[bucket_name] = bucket.current_balance
    
    return updated_balances
