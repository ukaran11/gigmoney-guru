"""
GigMoney Guru - Admin API

Admin endpoints for monitoring and management.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from datetime import datetime, timedelta
from typing import Optional
from beanie import PydanticObjectId

from app.config import settings
from app.models.user import User
from app.models.income import IncomeEvent
from app.models.expense import ExpenseEvent
from app.models.advance import MicroAdvance
from app.models.decision import AgentDecision


router = APIRouter(prefix="/admin", tags=["Admin"])


async def verify_admin(x_admin_key: str = Header(None)):
    """Simple admin key verification."""
    admin_key = getattr(settings, "ADMIN_API_KEY", "admin-secret-key")
    if x_admin_key != admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return True


@router.get("/stats")
async def get_platform_stats(
    _: bool = Depends(verify_admin)
):
    """Get overall platform statistics."""
    total_users = await User.count()
    active_users_7d = await User.find(
        User.updated_at >= datetime.now() - timedelta(days=7)
    ).count()
    
    total_income = await IncomeEvent.find().sum("amount") or 0
    total_advances = await MicroAdvance.count()
    advances_outstanding = await MicroAdvance.find(
        {"status": {"$in": ["approved", "pending"]}}
    ).count()
    
    return {
        "users": {
            "total": total_users,
            "active_7d": active_users_7d,
        },
        "income": {
            "total_tracked": total_income,
        },
        "advances": {
            "total_issued": total_advances,
            "currently_outstanding": advances_outstanding,
        },
        "generated_at": datetime.now().isoformat(),
    }


@router.get("/users")
async def list_users(
    limit: int = 50,
    offset: int = 0,
    _: bool = Depends(verify_admin)
):
    """List all users (paginated)."""
    users = await User.find().skip(offset).limit(limit).to_list()
    total = await User.count()
    
    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "preferred_language": u.preferred_language,
                "onboarding_complete": u.onboarding_complete,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    _: bool = Depends(verify_admin)
):
    """Get detailed information about a specific user."""
    try:
        user_oid = PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    user = await User.get(user_oid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user statistics
    income_count = await IncomeEvent.find(IncomeEvent.user_id == user_oid).count()
    expense_count = await ExpenseEvent.find(ExpenseEvent.user_id == user_oid).count()
    advance_count = await MicroAdvance.find(MicroAdvance.user_id == user_oid).count()
    
    recent_income = await IncomeEvent.find(
        IncomeEvent.user_id == user_oid
    ).sort("-event_date").limit(5).to_list()
    
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "preferred_language": user.preferred_language,
            "onboarding_complete": user.onboarding_complete,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "stats": {
            "income_events": income_count,
            "expense_events": expense_count,
            "advances": advance_count,
        },
        "recent_income": [
            {
                "source": i.source,
                "amount": i.amount,
                "date": i.event_date.isoformat() if i.event_date else None,
            }
            for i in recent_income
        ],
    }


@router.get("/agent-runs")
async def get_agent_runs(
    limit: int = 50,
    user_id: Optional[str] = None,
    _: bool = Depends(verify_admin)
):
    """Get recent agent run decisions."""
    query = AgentDecision.find()
    
    if user_id:
        try:
            user_oid = PydanticObjectId(user_id)
            query = query.find(AgentDecision.user_id == user_oid)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user ID")
    
    decisions = await query.sort("-created_at").limit(limit).to_list()
    
    return {
        "decisions": [
            {
                "id": str(d.id),
                "user_id": str(d.user_id),
                "agent_name": d.agent_name,
                "run_id": d.run_id,
                "decision_type": d.decision_type,
                "decision_value": d.decision_value,
                "confidence": d.confidence,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in decisions
        ]
    }


@router.get("/advances/report")
async def get_advances_report(
    days: int = 30,
    _: bool = Depends(verify_admin)
):
    """Get advances report for the specified period."""
    since = datetime.now() - timedelta(days=days)
    
    advances = await MicroAdvance.find(
        MicroAdvance.created_at >= since
    ).to_list()
    
    total_issued = sum(a.amount for a in advances)
    total_fees = sum(a.fee for a in advances)
    repaid = [a for a in advances if a.status == "repaid"]
    outstanding = [a for a in advances if a.status in ["approved", "pending"]]
    
    # Repayment rate
    total_repaid = len(repaid)
    on_time = len([a for a in repaid if a.repaid_at and a.due_date and a.repaid_at <= a.due_date])
    
    return {
        "period_days": days,
        "summary": {
            "total_advances": len(advances),
            "total_amount_issued": total_issued,
            "total_fees_collected": total_fees,
            "currently_outstanding_count": len(outstanding),
            "currently_outstanding_amount": sum(a.total_repayment for a in outstanding),
        },
        "repayment": {
            "total_repaid": total_repaid,
            "on_time_repayments": on_time,
            "on_time_rate": (on_time / total_repaid * 100) if total_repaid > 0 else 100,
        },
        "generated_at": datetime.now().isoformat(),
    }


@router.post("/broadcast")
async def broadcast_message(
    message: str,
    message_type: str = "info",
    _: bool = Depends(verify_admin)
):
    """Broadcast a message to all users (placeholder for push notifications)."""
    # In a real app, this would send push notifications or emails
    total_users = await User.count()
    
    return {
        "success": True,
        "message": f"Message would be sent to {total_users} users",
        "content": message,
        "type": message_type,
    }
