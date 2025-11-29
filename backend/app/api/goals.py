"""
GigMoney Guru - Goals API

Manage savings goals for users.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional, List
from beanie import PydanticObjectId

from app.api.auth import get_current_user
from app.models.user import User
from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalUpdate
from pydantic import BaseModel, Field


class GoalScenario(BaseModel):
    """Scenario for goal simulation."""
    name: str
    daily_savings: float = Field(..., gt=0)


router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("/")
async def list_goals(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all goals for the user."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    query = Goal.find(Goal.user_id == user_oid)
    
    if status:
        query = query.find({"status": status})
    
    goals = await query.sort("-priority").to_list()
    
    return {
        "goals": [
            {
                "id": str(g.id),
                "name": g.name,
                "emoji": g.icon,
                "target_amount": g.target_amount,
                "current_amount": g.current_amount,
                "progress_percent": round((g.current_amount / g.target_amount) * 100, 1) if g.target_amount > 0 else 0,
                "target_date": g.target_date.isoformat() if g.target_date else None,
                "priority": g.priority,
                "status": g.status,
                "created_at": g.created_at.isoformat(),
            }
            for g in goals
        ]
    }


@router.post("/")
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new savings goal."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    # Check for duplicate goal name
    existing = await Goal.find_one(
        Goal.user_id == user_oid,
        Goal.name == goal_data.name,
        {"status": "active"}
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"You already have an active goal named '{goal_data.name}'"
        )
    
    goal = Goal(
        user_id=user_oid,
        name=goal_data.name,
        icon=getattr(goal_data, 'icon', None) or "🎯",
        target_amount=goal_data.target_amount,
        current_amount=0,
        target_date=goal_data.target_date,
        priority=goal_data.priority or 1,
        status="active",
    )
    
    await goal.save()
    
    return {
        "success": True,
        "message": f"Goal '{goal.name}' created!",
        "goal": {
            "id": str(goal.id),
            "name": goal.name,
            "emoji": goal.icon,
            "target_amount": goal.target_amount,
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
        }
    }


@router.get("/{goal_id}")
async def get_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific goal."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    try:
        goal_oid = PydanticObjectId(goal_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid goal ID")
    
    goal = await Goal.find_one(
        Goal.id == goal_oid,
        Goal.user_id == user_oid
    )
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Calculate days remaining
    days_remaining = None
    if goal.target_date:
        delta = goal.target_date - datetime.now()
        days_remaining = max(0, delta.days)
    
    # Calculate daily savings needed
    daily_needed = None
    remaining_amount = goal.target_amount - goal.current_amount
    if days_remaining and days_remaining > 0:
        daily_needed = round(remaining_amount / days_remaining, 2)
    
    return {
        "goal": {
            "id": str(goal.id),
            "name": goal.name,
            "emoji": goal.icon,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "remaining_amount": remaining_amount,
            "progress_percent": round((goal.current_amount / goal.target_amount) * 100, 1) if goal.target_amount > 0 else 0,
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
            "days_remaining": days_remaining,
            "daily_savings_needed": daily_needed,
            "priority": goal.priority,
            "status": goal.status,
            "created_at": goal.created_at.isoformat(),
        }
    }


@router.put("/{goal_id}")
async def update_goal(
    goal_id: str,
    updates: GoalUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a goal."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    try:
        goal_oid = PydanticObjectId(goal_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid goal ID")
    
    goal = await Goal.find_one(
        Goal.id == goal_oid,
        Goal.user_id == user_oid
    )
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Apply updates
    if updates.name is not None:
        goal.name = updates.name
    if getattr(updates, 'icon', None) is not None:
        goal.icon = updates.icon
    if updates.target_amount is not None:
        goal.target_amount = updates.target_amount
    if updates.target_date is not None:
        goal.target_date = updates.target_date
    if updates.priority is not None:
        goal.priority = updates.priority
    if updates.status is not None:
        goal.status = updates.status
    
    goal.updated_at = datetime.now()
    await goal.save()
    
    return {
        "success": True,
        "message": f"Goal '{goal.name}' updated",
    }


@router.post("/{goal_id}/contribute")
async def contribute_to_goal(
    goal_id: str,
    amount: float,
    current_user: User = Depends(get_current_user)
):
    """Add money to a goal."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    try:
        goal_oid = PydanticObjectId(goal_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid goal ID")
    
    goal = await Goal.find_one(
        Goal.id == goal_oid,
        Goal.user_id == user_oid
    )
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    if goal.status != "active":
        raise HTTPException(status_code=400, detail="Goal is not active")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    goal.current_amount += amount
    goal.updated_at = datetime.now()
    
    # Check if goal completed
    if goal.current_amount >= goal.target_amount:
        goal.status = "completed"
        goal.current_amount = goal.target_amount  # Cap at target
    
    await goal.save()
    
    progress = round((goal.current_amount / goal.target_amount) * 100, 1)
    
    message = f"₹{amount} added to '{goal.name}'! Progress: {progress}%"
    if goal.status == "completed":
        message = f"🎉 Congratulations! You've completed your goal '{goal.name}'!"
    
    return {
        "success": True,
        "message": message,
        "current_amount": goal.current_amount,
        "progress_percent": progress,
        "status": goal.status,
    }


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a goal."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    try:
        goal_oid = PydanticObjectId(goal_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid goal ID")
    
    goal = await Goal.find_one(
        Goal.id == goal_oid,
        Goal.user_id == user_oid
    )
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    await goal.delete()
    
    return {
        "success": True,
        "message": f"Goal '{goal.name}' deleted",
    }


@router.post("/scenarios")
async def simulate_goal_scenarios(
    goal_id: str,
    scenarios: List[GoalScenario],
    current_user: User = Depends(get_current_user)
):
    """Simulate different savings scenarios for a goal."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    try:
        goal_oid = PydanticObjectId(goal_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid goal ID")
    
    goal = await Goal.find_one(
        Goal.id == goal_oid,
        Goal.user_id == user_oid
    )
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    remaining = goal.target_amount - goal.current_amount
    results = []
    
    for scenario in scenarios:
        if scenario.daily_savings > 0:
            days_to_complete = remaining / scenario.daily_savings
            from datetime import timedelta
            completion_date = datetime.now() + timedelta(days=int(days_to_complete))
            
            results.append({
                "name": scenario.name,
                "daily_savings": scenario.daily_savings,
                "days_to_complete": int(days_to_complete),
                "completion_date": completion_date.strftime("%Y-%m-%d"),
                "weekly_savings": scenario.daily_savings * 7,
                "monthly_savings": scenario.daily_savings * 30,
            })
    
    return {
        "goal": goal.name,
        "remaining_amount": remaining,
        "scenarios": results,
    }
