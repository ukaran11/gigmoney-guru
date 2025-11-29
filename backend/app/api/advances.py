"""
GigMoney Guru - Advances API

Manage micro-advances for users.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from beanie import PydanticObjectId

from app.api.auth import get_current_user
from app.models.user import User
from app.models.advance import MicroAdvance


class AdvanceRequest(BaseModel):
    """Request for a micro-advance."""
    amount: float = Field(..., gt=0, description="Amount to request")
    reason: Optional[str] = Field(None, description="Reason for the advance")
    due_days: Optional[int] = Field(3, ge=0, le=7, description="Days until due")


router = APIRouter(prefix="/advances", tags=["Advances"])


@router.get("/")
async def list_advances(
    status: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get user's micro-advance history."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    query = MicroAdvance.find(MicroAdvance.user_id == user_oid)
    
    if status:
        query = query.find({"status": status})
    
    advances = await query.sort("-offered_at").limit(limit).to_list()
    
    return {
        "advances": [
            {
                "id": str(a.id),
                "amount": a.principal,
                "fee": a.fee,
                "total_repayment": a.total_repayable,
                "status": a.status,
                "reason": a.purpose,
                "due_date": a.repayment_date.isoformat() if a.repayment_date else None,
                "approved_at": a.accepted_at.isoformat() if a.accepted_at else None,
                "repaid_at": a.repaid_at.isoformat() if a.repaid_at else None,
                "created_at": a.offered_at.isoformat(),
            }
            for a in advances
        ]
    }


@router.get("/available")
async def get_available_advance(
    current_user: User = Depends(get_current_user)
):
    """Check what advance amount is available for the user."""
    from app.services.advance import AdvanceService
    
    user_id = str(current_user.id)
    
    available = await AdvanceService.calculate_available_advance(user_id)
    
    return {
        "max_advance_amount": available["max_amount"],
        "current_outstanding": available["outstanding"],
        "can_request": available["can_request"],
        "reason": available.get("reason"),
        "fee_rate": 0.01,  # 1% fee
    }


@router.post("/request")
async def request_advance(
    request: AdvanceRequest,
    current_user: User = Depends(get_current_user)
):
    """Request a micro-advance."""
    from app.services.advance import AdvanceService
    from datetime import timedelta
    
    user_id = str(current_user.id)
    user_oid = PydanticObjectId(user_id)
    
    # Check if advance is possible
    available = await AdvanceService.calculate_available_advance(user_id)
    
    if not available["can_request"]:
        raise HTTPException(
            status_code=400,
            detail=available.get("reason", "Cannot request advance at this time")
        )
    
    if request.amount > available["max_amount"]:
        raise HTTPException(
            status_code=400,
            detail=f"Requested amount exceeds maximum available: ₹{available['max_amount']}"
        )
    
    if request.amount < 100:
        raise HTTPException(
            status_code=400,
            detail="Minimum advance amount is ₹100"
        )
    
    # Calculate fee (1% of amount)
    fee = round(request.amount * 0.01, 2)
    total_repayable = request.amount + fee
    
    # Calculate repayment date
    repayment_date = datetime.now() + timedelta(days=request.due_days or 3)
    
    # Create advance record
    advance = MicroAdvance(
        user_id=user_oid,
        principal=request.amount,
        purpose=request.reason or "User requested advance",
        fee=fee,
        total_repayable=total_repayable,
        status="active",
        repayment_date=repayment_date,
        accepted_at=datetime.now(),
        disbursed_at=datetime.now(),
    )
    
    await advance.save()
    
    return {
        "success": True,
        "message": f"Advance of ₹{request.amount} approved!",
        "advance": {
            "id": str(advance.id),
            "amount": advance.principal,
            "fee": advance.fee,
            "total_repayment": advance.total_repayable,
            "due_date": advance.repayment_date.isoformat(),
        }
    }


@router.post("/{advance_id}/repay")
async def repay_advance(
    advance_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark an advance as repaid."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    try:
        advance_oid = PydanticObjectId(advance_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid advance ID")
    
    advance = await MicroAdvance.find_one(
        MicroAdvance.id == advance_oid,
        MicroAdvance.user_id == user_oid
    )
    
    if not advance:
        raise HTTPException(status_code=404, detail="Advance not found")
    
    if advance.status == "repaid":
        raise HTTPException(status_code=400, detail="Advance already repaid")
    
    advance.status = "repaid"
    advance.amount_repaid = advance.total_repayable
    advance.repaid_at = datetime.now()
    await advance.save()
    
    return {
        "success": True,
        "message": f"Advance of ₹{advance.principal} marked as repaid",
    }


@router.get("/stats")
async def get_advance_stats(
    current_user: User = Depends(get_current_user)
):
    """Get advance statistics for the user."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    all_advances = await MicroAdvance.find(
        MicroAdvance.user_id == user_oid
    ).to_list()
    
    total_taken = sum(a.principal for a in all_advances)
    total_fees = sum(a.fee for a in all_advances)
    outstanding = sum(
        a.total_repayable - a.amount_repaid for a in all_advances 
        if a.status in ["active", "accepted"]
    )
    repaid = sum(
        a.total_repayable for a in all_advances 
        if a.status == "repaid"
    )
    
    on_time = len([a for a in all_advances if a.status == "repaid" and a.repaid_at and a.repayment_date and a.repaid_at <= a.repayment_date])
    total_repaid = len([a for a in all_advances if a.status == "repaid"])
    
    return {
        "total_advances_taken": len(all_advances),
        "total_amount_taken": total_taken,
        "total_fees_paid": total_fees,
        "currently_outstanding": outstanding,
        "total_repaid": repaid,
        "on_time_repayment_rate": (on_time / total_repaid * 100) if total_repaid > 0 else 100,
    }
