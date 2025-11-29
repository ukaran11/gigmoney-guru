"""
GigMoney Guru - Obligations API

Manage recurring bills and payments.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, date
from typing import Optional
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.models.user import User
from app.models.obligation import Obligation
from app.models.bucket import Bucket


class ObligationCreate(BaseModel):
    """Create obligation request."""
    name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    due_day: int = Field(..., ge=1, le=28)
    category: str = Field(default="other")
    frequency: str = Field(default="monthly")
    bucket_name: Optional[str] = None


class ObligationUpdate(BaseModel):
    """Update obligation request."""
    name: Optional[str] = None
    amount: Optional[float] = None
    due_day: Optional[int] = None
    is_active: Optional[bool] = None


router = APIRouter(prefix="/obligations", tags=["Obligations"])


def get_bucket_for_category(category: str) -> str:
    """Map obligation category to bucket."""
    mapping = {
        "rent": "essentials",
        "emi": "essentials",
        "loan": "essentials",
        "mobile": "essentials",
        "electricity": "essentials",
        "internet": "essentials",
        "insurance": "essentials",
        "other": "essentials",
    }
    return mapping.get(category.lower(), "essentials")


@router.post("/")
async def create_obligation(
    data: ObligationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new recurring obligation."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    # Check for duplicate
    existing = await Obligation.find_one(
        Obligation.user_id == user_oid,
        Obligation.name == data.name,
        {"is_active": True}
    )
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"You already have an obligation named '{data.name}'"
        )
    
    # Determine bucket
    bucket_name = data.bucket_name or get_bucket_for_category(data.category)
    
    obligation = Obligation(
        user_id=user_oid,
        name=data.name,
        category=data.category,
        amount=data.amount,
        due_day=data.due_day,
        frequency=data.frequency,
        bucket_name=bucket_name,
        is_active=True,
    )
    await obligation.save()
    
    # Update bucket target if it exists
    bucket = await Bucket.find_one(
        Bucket.user_id == user_oid,
        Bucket.name == bucket_name,
        {"is_active": True}
    )
    
    if bucket:
        # Add this obligation amount to the bucket's target
        bucket.target_amount += data.amount
        bucket.updated_at = datetime.now()
        await bucket.save()
    
    return {
        "success": True,
        "message": f"'{data.name}' added - Due on {data.due_day}th of every month",
        "obligation": {
            "id": str(obligation.id),
            "name": obligation.name,
            "amount": obligation.amount,
            "due_day": obligation.due_day,
            "bucket_name": bucket_name,
        },
    }


@router.get("/")
async def list_obligations(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Get all obligations."""
    user_oid = PydanticObjectId(str(current_user.id))
    today = datetime.now().date()
    
    query = Obligation.find(Obligation.user_id == user_oid)
    
    if not include_inactive:
        query = query.find({"is_active": True})
    
    obligations = await query.sort("+due_day").to_list()
    
    result = []
    total_monthly = 0
    
    for obl in obligations:
        # Calculate next due date
        due_day = obl.due_day
        if today.day > due_day:
            # Next month
            if today.month == 12:
                next_due = date(today.year + 1, 1, due_day)
            else:
                next_due = date(today.year, today.month + 1, due_day)
        else:
            next_due = date(today.year, today.month, due_day)
        
        days_until = (next_due - today).days
        
        result.append({
            "id": str(obl.id),
            "name": obl.name,
            "category": obl.category,
            "amount": obl.amount,
            "due_day": obl.due_day,
            "next_due_date": next_due.isoformat(),
            "days_until_due": days_until,
            "is_urgent": days_until <= 3,
            "bucket_name": obl.bucket_name,
            "is_active": obl.is_active,
        })
        
        if obl.is_active:
            total_monthly += obl.amount
    
    return {
        "obligations": result,
        "total_monthly": total_monthly,
        "count": len(result),
    }


@router.put("/{obligation_id}")
async def update_obligation(
    obligation_id: str,
    data: ObligationUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an obligation."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    try:
        obl_oid = PydanticObjectId(obligation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid obligation ID")
    
    obligation = await Obligation.find_one(
        Obligation.id == obl_oid,
        Obligation.user_id == user_oid
    )
    
    if not obligation:
        raise HTTPException(status_code=404, detail="Obligation not found")
    
    if data.name is not None:
        obligation.name = data.name
    if data.amount is not None:
        obligation.amount = data.amount
    if data.due_day is not None:
        obligation.due_day = data.due_day
    if data.is_active is not None:
        obligation.is_active = data.is_active
    
    obligation.updated_at = datetime.now()
    await obligation.save()
    
    return {
        "success": True,
        "message": f"'{obligation.name}' updated",
    }


@router.delete("/{obligation_id}")
async def delete_obligation(
    obligation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an obligation."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    try:
        obl_oid = PydanticObjectId(obligation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid obligation ID")
    
    obligation = await Obligation.find_one(
        Obligation.id == obl_oid,
        Obligation.user_id == user_oid
    )
    
    if not obligation:
        raise HTTPException(status_code=404, detail="Obligation not found")
    
    await obligation.delete()
    
    return {"success": True, "message": f"'{obligation.name}' deleted"}


@router.post("/{obligation_id}/mark-paid")
async def mark_obligation_paid(
    obligation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark an obligation as paid for this month."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    try:
        obl_oid = PydanticObjectId(obligation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid obligation ID")
    
    obligation = await Obligation.find_one(
        Obligation.id == obl_oid,
        Obligation.user_id == user_oid
    )
    
    if not obligation:
        raise HTTPException(status_code=404, detail="Obligation not found")
    
    # Record the payment (could add a payments collection later)
    obligation.last_paid_date = datetime.now()
    obligation.updated_at = datetime.now()
    await obligation.save()
    
    # Deduct from bucket
    bucket = await Bucket.find_one(
        Bucket.user_id == user_oid,
        Bucket.name == obligation.bucket_name,
        {"is_active": True}
    )
    
    if bucket:
        bucket.current_balance = max(0, bucket.current_balance - obligation.amount)
        bucket.updated_at = datetime.now()
        await bucket.save()
    
    return {
        "success": True,
        "message": f"'{obligation.name}' marked as paid - ₹{obligation.amount}",
    }
