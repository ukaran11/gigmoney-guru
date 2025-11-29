"""
GigMoney Guru - Allocation Service

Business logic for bucket allocation.
"""
from typing import Dict, List, Optional
from datetime import datetime, date
from beanie import PydanticObjectId

from app.models.bucket import Bucket
from app.models.income import IncomeEvent
from app.models.obligation import Obligation


class AllocationService:
    """Service for allocation operations."""
    
    # Default bucket configuration
    DEFAULT_BUCKETS = [
        {
            "name": "rent",
            "display_name": "Kiraya (Rent)",
            "icon": "🏠",
            "color": "#FF9800",
            "allocation_type": "percentage",
            "allocation_value": 25,
            "priority": 1,
        },
        {
            "name": "emi",
            "display_name": "Bike EMI",
            "icon": "🏍️",
            "color": "#F44336",
            "allocation_type": "percentage",
            "allocation_value": 15,
            "priority": 2,
        },
        {
            "name": "tax",
            "display_name": "Tax Savings",
            "icon": "📋",
            "color": "#9C27B0",
            "allocation_type": "percentage",
            "allocation_value": 5,
            "priority": 3,
        },
        {
            "name": "fuel",
            "display_name": "Fuel/Petrol",
            "icon": "⛽",
            "color": "#4CAF50",
            "allocation_type": "percentage",
            "allocation_value": 10,
            "priority": 4,
        },
        {
            "name": "emergency",
            "display_name": "Emergency Fund",
            "icon": "🛡️",
            "color": "#2196F3",
            "allocation_type": "percentage",
            "allocation_value": 10,
            "priority": 5,
        },
        {
            "name": "savings",
            "display_name": "Bachat (Savings)",
            "icon": "💰",
            "color": "#00BCD4",
            "allocation_type": "percentage",
            "allocation_value": 10,
            "priority": 6,
        },
        {
            "name": "discretionary",
            "display_name": "Safe to Spend",
            "icon": "🎯",
            "color": "#607D8B",
            "allocation_type": "remainder",
            "allocation_value": 0,
            "priority": 7,
        },
    ]
    
    @staticmethod
    async def create_default_buckets(user_id: str, monthly_rent: float = 8000, has_emi: bool = True) -> List[Bucket]:
        """Create default buckets for a new user."""
        user_oid = PydanticObjectId(user_id)
        buckets = []
        
        for config in AllocationService.DEFAULT_BUCKETS:
            # Set target amounts
            target = 0
            if config["name"] == "rent":
                target = monthly_rent
            elif config["name"] == "emi" and has_emi:
                target = 4500  # Default EMI
            elif config["name"] == "tax":
                target = 5000  # Quarterly tax
            elif config["name"] == "emergency":
                target = 15000  # Emergency fund target
            
            bucket = Bucket(
                user_id=user_oid,
                name=config["name"],
                display_name=config["display_name"],
                icon=config["icon"],
                color=config["color"],
                target_amount=target,
                current_balance=0,
                allocation_type=config["allocation_type"],
                allocation_value=config["allocation_value"],
                priority=config["priority"],
            )
            
            await bucket.insert()
            buckets.append(bucket)
        
        return buckets
    
    @staticmethod
    async def get_user_buckets(user_id: str) -> List[Bucket]:
        """Get all buckets for a user."""
        user_oid = PydanticObjectId(user_id)
        return await Bucket.find(
            Bucket.user_id == user_oid,
            {"is_active": True}
        ).sort("+priority").to_list()
    
    @staticmethod
    async def allocate_income(
        user_id: str,
        amount: float = None,
        source: str = None,
        income_event: IncomeEvent = None,
        high_risk_buckets: Optional[List[str]] = None
    ) -> Dict:
        """
        Allocate an income event to buckets.
        
        Args:
            user_id: User's ID
            amount: Amount to allocate (if no income_event)
            source: Source of income (if no income_event)
            income_event: The income event to allocate
            high_risk_buckets: Buckets with high-risk obligations (get priority)
            
        Returns:
            Dict with allocations and summary
        """
        user_oid = PydanticObjectId(user_id)
        
        # Get amount from income_event if provided
        if income_event:
            amount = income_event.amount
        elif amount is None:
            return {"allocations": [], "total_allocated": 0}
        
        allocations = []
        
        # Get buckets sorted by priority
        buckets = await Bucket.find(
            Bucket.user_id == user_oid,
            {"is_active": True}
        ).sort("+priority").to_list()
        
        if not buckets:
            return {"allocations": [], "total_allocated": 0, "message": "No buckets configured"}
        
        remaining = amount
        
        for bucket in buckets:
            if remaining <= 0:
                break
            
            # Calculate allocation
            if bucket.allocation_type == "percentage":
                alloc = amount * (bucket.allocation_value / 100)
            elif bucket.allocation_type == "fixed":
                alloc = bucket.allocation_value
            else:  # remainder
                alloc = remaining
            
            # Boost high-risk buckets
            if high_risk_buckets and bucket.name in high_risk_buckets:
                alloc = alloc * 1.3  # 30% boost
            
            # Don't exceed remaining
            alloc = min(alloc, remaining)
            
            # Don't exceed target if set
            if bucket.target_amount > 0:
                room = bucket.target_amount - bucket.current_balance
                if room <= 0:
                    alloc = alloc * 0.3  # Maintenance mode
                else:
                    alloc = min(alloc, room + alloc * 0.1)  # Allow slight overflow
            
            if alloc > 0:
                # Update bucket
                bucket.current_balance += alloc
                bucket.last_allocation_at = datetime.utcnow()
                bucket.updated_at = datetime.utcnow()
                await bucket.save()
                
                allocations.append({
                    "bucket_name": bucket.name,
                    "display_name": bucket.display_name,
                    "icon": bucket.icon,
                    "amount": round(alloc, 2),
                    "new_balance": round(bucket.current_balance, 2),
                })
                remaining -= alloc
        
        # Mark income as allocated if provided
        if income_event:
            income_event.allocated = True
            income_event.allocation_id = datetime.utcnow().isoformat()
            await income_event.save()
        
        return {
            "allocations": allocations,
            "total_allocated": round(amount - remaining, 2),
            "remaining": round(remaining, 2),
        }
    
    @staticmethod
    async def get_safe_to_spend(user_id: str) -> float:
        """Get current safe-to-spend amount."""
        user_oid = PydanticObjectId(user_id)
        
        # Get discretionary bucket
        discretionary = await Bucket.find_one(
            Bucket.user_id == user_oid,
            Bucket.name == "discretionary"
        )
        
        return discretionary.current_balance if discretionary else 0
    
    @staticmethod
    async def deduct_from_bucket(
        user_id: str,
        bucket_name: str,
        amount: float
    ) -> bool:
        """Deduct amount from a bucket (for expenses)."""
        user_oid = PydanticObjectId(user_id)
        
        bucket = await Bucket.find_one(
            Bucket.user_id == user_oid,
            Bucket.name == bucket_name
        )
        
        if not bucket:
            return False
        
        if bucket.current_balance < amount:
            return False
        
        bucket.current_balance -= amount
        bucket.updated_at = datetime.utcnow()
        await bucket.save()
        
        return True
    
    @staticmethod
    async def reset_monthly_buckets(user_id: str) -> None:
        """Reset buckets for a new month (after obligations are paid)."""
        user_oid = PydanticObjectId(user_id)
        
        # Get obligations to know which buckets to reset
        obligations = await Obligation.find(
            Obligation.user_id == user_oid,
            {"is_active": True}
        ).to_list()
        
        paid_categories = set(o.bucket_name or o.category for o in obligations)
        
        # Reset buckets for paid obligations
        buckets = await Bucket.find(
            Bucket.user_id == user_oid,
            {"is_active": True}
        ).to_list()
        
        for bucket in buckets:
            if bucket.name in paid_categories:
                bucket.current_balance = 0
                bucket.updated_at = datetime.utcnow()
                await bucket.save()
