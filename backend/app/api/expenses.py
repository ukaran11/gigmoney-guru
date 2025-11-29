"""
GigMoney Guru - Expenses API

Track and manage expenses.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from typing import Optional
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


router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("/")
async def add_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_user)
):
    """Add a new expense and optionally deduct from a bucket."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    # Determine which bucket to use
    bucket_name = expense_data.bucket_name
    
    # Map categories to buckets
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
    
    if not bucket_name:
        bucket_name = category_bucket_map.get(expense_data.category.lower(), "discretionary")
    
    # Create expense record
    expense = Expense(
        user_id=user_oid,
        category=expense_data.category,
        amount=expense_data.amount,
        description=expense_data.description,
        bucket_name=bucket_name,
        spent_at=datetime.now(),
        recorded_at=datetime.now(),
    )
    await expense.save()
    
    # Try to find the bucket, fallback to discretionary, then any bucket with balance
    bucket = await Bucket.find_one(
        Bucket.user_id == user_oid,
        Bucket.name == bucket_name
    )
    
    # Fallback: if bucket not found, try discretionary
    if not bucket and bucket_name != "discretionary":
        bucket = await Bucket.find_one(
            Bucket.user_id == user_oid,
            Bucket.name == "discretionary"
        )
        if bucket:
            bucket_name = "discretionary"
    
    # Final fallback: find any bucket with enough balance
    if not bucket:
        all_buckets = await Bucket.find(
            Bucket.user_id == user_oid,
            Bucket.is_active == True
        ).sort("-current_balance").to_list()
        
        for b in all_buckets:
            if b.current_balance >= expense_data.amount:
                bucket = b
                bucket_name = b.name
                break
        
        # If no bucket has enough, use the one with highest balance
        if not bucket and all_buckets:
            bucket = all_buckets[0]
            bucket_name = bucket.name
    
    bucket_deducted = False
    new_balance = None
    
    if bucket and bucket.is_active:
        old_balance = bucket.current_balance
        bucket.current_balance = max(0, bucket.current_balance - expense_data.amount)
        bucket.updated_at = datetime.now()
        await bucket.save()
        bucket_deducted = True
        new_balance = bucket.current_balance
        
        # Update expense with actual bucket used
        expense.bucket_name = bucket_name
        await expense.save()
    
    return {
        "success": True,
        "expense_id": str(expense.id),
        "message": f"₹{expense_data.amount} expense recorded" + (f" from {bucket.display_name}" if bucket_deducted else ""),
        "bucket_deducted": bucket_deducted,
        "bucket_name": bucket_name if bucket_deducted else None,
        "new_balance": new_balance,
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
