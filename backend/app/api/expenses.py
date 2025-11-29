"""
GigMoney Guru - Expenses API

Track and manage expenses with CASCADE DEDUCTION across buckets.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from typing import Optional, List
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.api.auth import get_current_user
from app.models.user import User
from app.models.expense import ExpenseEvent as Expense
from app.models.bucket import Bucket


class ExpenseCreate(BaseModel):
    """Create expense request."""
    category: str = Field(..., min_length=1, max_length=50)
    amount: float = Field(..., gt=0)
    description: Optional[str] = None
    bucket_name: Optional[str] = None  # Which bucket to deduct from
    force: bool = False  # Force recording even if insufficient funds


router = APIRouter(prefix="/expenses", tags=["Expenses"])


# Priority order for cascade deduction (lower priority buckets drained first)
DEDUCTION_PRIORITY = [
    "discretionary",  # Safe to spend - use first
    "flex",           # Flexible spending
    "savings",        # Savings - reluctantly use
    "fuel",           # Category-specific
    "emergency",      # Emergency - last resort
    # Never touch: rent, emi, tax (reserved for obligations)
]

# Buckets that should NEVER be used for regular expenses
PROTECTED_BUCKETS = ["rent", "emi", "tax"]


@router.post("/")
async def add_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Add a new expense with CASCADE DEDUCTION across buckets.
    
    If the primary bucket doesn't have enough funds, we cascade through
    other buckets in priority order until the expense is fully covered.
    """
    user_oid = PydanticObjectId(str(current_user.id))
    
    # Map categories to primary buckets
    category_bucket_map = {
        "food": "discretionary",
        "fuel": "fuel",
        "petrol": "fuel",
        "transport": "discretionary",
        "phone": "discretionary",
        "medical": "emergency",
        "entertainment": "discretionary",
        "shopping": "discretionary",
        "family": "discretionary",
        "repair": "emergency",
        "other": "discretionary",
    }
    
    primary_bucket_name = expense_data.bucket_name or category_bucket_map.get(
        expense_data.category.lower(), "discretionary"
    )
    
    # Get ALL active buckets for this user
    all_buckets = await Bucket.find(
        Bucket.user_id == user_oid,
        Bucket.is_active == True
    ).to_list()
    
    if not all_buckets:
        raise HTTPException(
            status_code=400,
            detail="No buckets configured. Please add income first."
        )
    
    # Calculate total available balance (excluding protected buckets)
    total_available = sum(
        b.current_balance for b in all_buckets 
        if b.name not in PROTECTED_BUCKETS
    )
    total_all = sum(b.current_balance for b in all_buckets)
    
    # Check if expense exceeds available funds
    expense_amount = expense_data.amount
    is_overspending = expense_amount > total_available
    uncovered_amount = max(0, expense_amount - total_available)
    
    # If overspending and not forced, return warning
    if is_overspending and not expense_data.force:
        return {
            "success": False,
            "warning": True,
            "message": f"⚠️ Expense ₹{expense_amount:,.0f} exceeds available balance ₹{total_available:,.0f}",
            "total_available": total_available,
            "total_all_buckets": total_all,
            "shortfall": uncovered_amount,
            "hint": "Set force=true to record anyway, or reduce the amount",
        }
    
    # Build deduction order: primary bucket first, then by priority
    bucket_map = {b.name: b for b in all_buckets}
    ordered_buckets = []
    
    # Add primary bucket first if it exists and is not protected
    if primary_bucket_name in bucket_map and primary_bucket_name not in PROTECTED_BUCKETS:
        ordered_buckets.append(bucket_map[primary_bucket_name])
    
    # Add remaining buckets in priority order
    for bucket_name in DEDUCTION_PRIORITY:
        if bucket_name in bucket_map and bucket_name != primary_bucket_name:
            ordered_buckets.append(bucket_map[bucket_name])
    
    # Add any other non-protected buckets not in priority list
    for bucket in all_buckets:
        if bucket not in ordered_buckets and bucket.name not in PROTECTED_BUCKETS:
            ordered_buckets.append(bucket)
    
    # CASCADE DEDUCTION
    remaining_to_deduct = expense_amount
    deductions = []
    
    for bucket in ordered_buckets:
        if remaining_to_deduct <= 0:
            break
        
        if bucket.current_balance <= 0:
            continue
        
        # Calculate how much to deduct from this bucket
        deduct_amount = min(bucket.current_balance, remaining_to_deduct)
        old_balance = bucket.current_balance
        
        # Update bucket
        bucket.current_balance -= deduct_amount
        bucket.updated_at = datetime.now()
        await bucket.save()
        
        deductions.append({
            "bucket_name": bucket.name,
            "display_name": bucket.display_name,
            "amount_deducted": deduct_amount,
            "old_balance": old_balance,
            "new_balance": bucket.current_balance,
        })
        
        remaining_to_deduct -= deduct_amount
    
    # Calculate what was actually deducted
    total_deducted = expense_amount - remaining_to_deduct
    
    # Create expense record
    expense = Expense(
        user_id=user_oid,
        category=expense_data.category,
        amount=expense_amount,  # Record full amount
        description=expense_data.description,
        bucket_name=primary_bucket_name,
        spent_at=datetime.now(),
        recorded_at=datetime.now(),
    )
    await expense.save()
    
    # Calculate new totals
    updated_buckets = await Bucket.find(
        Bucket.user_id == user_oid,
        Bucket.is_active == True
    ).to_list()
    new_total_balance = sum(b.current_balance for b in updated_buckets)
    new_safe_to_spend = sum(
        b.current_balance for b in updated_buckets 
        if b.name in ["discretionary", "flex"]
    )
    
    # Build response message
    if len(deductions) == 1:
        message = f"₹{expense_amount:,.0f} deducted from {deductions[0]['display_name']}"
    elif len(deductions) > 1:
        bucket_names = ", ".join(d['display_name'] for d in deductions[:3])
        message = f"₹{total_deducted:,.0f} deducted from {bucket_names}"
        if len(deductions) > 3:
            message += f" (+{len(deductions) - 3} more)"
    else:
        message = f"₹{expense_amount:,.0f} expense recorded (no buckets to deduct from)"
    
    # Add warning if overspending
    if is_overspending:
        message += f" ⚠️ Overspent by ₹{uncovered_amount:,.0f}!"
    
    return {
        "success": True,
        "expense_id": str(expense.id),
        "message": message,
        "expense_amount": expense_amount,
        "total_deducted": total_deducted,
        "uncovered_amount": remaining_to_deduct,
        "is_overspending": is_overspending,
        "deductions": deductions,
        "new_total_balance": new_total_balance,
        "new_safe_to_spend": new_safe_to_spend,
    }


@router.get("/")
async def list_expenses(
    days: int = 7,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get recent expenses."""
    user_oid = PydanticObjectId(str(current_user.id))
    start_date = datetime.now() - timedelta(days=days)
    
    query = Expense.find(
        Expense.user_id == user_oid,
        Expense.spent_at >= start_date
    )
    
    if category:
        query = query.find({"category": category})
    
    expenses = await query.sort("-spent_at").to_list()
    
    # Group by date
    by_date = {}
    for exp in expenses:
        date_key = exp.spent_at.strftime("%Y-%m-%d")
        if date_key not in by_date:
            by_date[date_key] = {"date": date_key, "total": 0, "items": []}
        by_date[date_key]["total"] += exp.amount
        by_date[date_key]["items"].append({
            "id": str(exp.id),
            "category": exp.category,
            "amount": exp.amount,
            "description": exp.description,
            "time": exp.spent_at.strftime("%H:%M"),
        })
    
    return {
        "total": sum(exp.amount for exp in expenses),
        "count": len(expenses),
        "days": list(by_date.values()),
    }


@router.get("/summary")
async def expense_summary(
    current_user: User = Depends(get_current_user)
):
    """Get expense summary by category."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    # This month
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    expenses = await Expense.find(
        Expense.user_id == user_oid,
        Expense.spent_at >= month_start
    ).to_list()
    
    # By category
    by_category = {}
    for exp in expenses:
        cat = exp.category
        if cat not in by_category:
            by_category[cat] = {"category": cat, "total": 0, "count": 0}
        by_category[cat]["total"] += exp.amount
        by_category[cat]["count"] += 1
    
    # Sort by total descending
    categories = sorted(by_category.values(), key=lambda x: -x["total"])
    
    return {
        "total": sum(exp.amount for exp in expenses),
        "count": len(expenses),
        "by_category": categories,
        "daily_average": sum(exp.amount for exp in expenses) / max(now.day, 1),
    }


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an expense."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    try:
        expense_oid = PydanticObjectId(expense_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid expense ID")
    
    expense = await Expense.find_one(
        Expense.id == expense_oid,
        Expense.user_id == user_oid
    )
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    await expense.delete()
    
    return {"success": True, "message": "Expense deleted"}
