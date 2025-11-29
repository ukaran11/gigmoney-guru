"""
GigMoney Guru - Advance Service

Business logic for micro-advances.
"""
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from beanie import PydanticObjectId

from app.models.advance import MicroAdvance
from app.models.bucket import Bucket
from app.models.obligation import Obligation


class AdvanceService:
    """Service for micro-advance operations."""
    
    # Guardrails
    MAX_ADVANCE_PCT_OF_WEEKLY = 0.40
    MAX_ACTIVE_ADVANCES = 3  # Allow up to 3 advances, but total capped at 40% of weekly income
    MIN_ADVANCE_AMOUNT = 100
    MAX_ADVANCE_AMOUNT = 5000
    
    @staticmethod
    async def calculate_available_advance(user_id: str) -> dict:
        """Calculate how much advance a user can request."""
        from app.models.income import IncomeEvent
        from datetime import timedelta
        
        user_oid = PydanticObjectId(user_id)
        
        # Check for active advances
        active_advances = await AdvanceService.get_active_advances(user_id)
        outstanding = sum(a.total_repayable - a.amount_repaid for a in active_advances)
        
        # Calculate weekly income estimate
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_income = await IncomeEvent.find(
            IncomeEvent.user_id == user_oid,
            IncomeEvent.earned_at >= week_ago
        ).to_list()
        
        weekly_income = sum(e.amount for e in recent_income)
        if weekly_income < 1000:
            weekly_income = 15000  # Default estimate
        
        # Calculate max total allowed (40% of weekly income, capped at MAX_ADVANCE_AMOUNT)
        max_total_allowed = min(
            weekly_income * AdvanceService.MAX_ADVANCE_PCT_OF_WEEKLY,
            AdvanceService.MAX_ADVANCE_AMOUNT
        )
        
        # Available = max allowed - what's already outstanding
        available_amount = max(max_total_allowed - outstanding, 0)
        available_amount = round(available_amount, -2)  # Round to nearest 100
        
        # Check guardrails
        if len(active_advances) >= AdvanceService.MAX_ACTIVE_ADVANCES:
            return {
                "max_amount": 0,
                "max_total_allowed": max_total_allowed,
                "outstanding": outstanding,
                "can_request": False,
                "reason": f"Maximum {AdvanceService.MAX_ACTIVE_ADVANCES} active advances allowed. Please repay one first."
            }
        
        if available_amount < AdvanceService.MIN_ADVANCE_AMOUNT:
            return {
                "max_amount": 0,
                "max_total_allowed": max_total_allowed,
                "outstanding": outstanding,
                "can_request": False,
                "reason": f"You've used most of your advance limit (₹{outstanding:.0f} of ₹{max_total_allowed:.0f}). Repay to unlock more."
            }
        
        return {
            "max_amount": available_amount,
            "max_total_allowed": max_total_allowed,
            "outstanding": outstanding,
            "can_request": True,
            "weekly_income": weekly_income,
        }
    
    @staticmethod
    async def get_active_advances(user_id: str) -> List[MicroAdvance]:
        """Get all active advances for a user."""
        user_oid = PydanticObjectId(user_id)
        
        return await MicroAdvance.find(
            MicroAdvance.user_id == user_oid,
            {"status": {"$in": ["accepted", "active"]}}
        ).to_list()
    
    @staticmethod
    async def get_pending_offers(user_id: str) -> List[MicroAdvance]:
        """Get pending advance offers for a user."""
        user_oid = PydanticObjectId(user_id)
        
        return await MicroAdvance.find(
            MicroAdvance.user_id == user_oid,
            {"status": "offered"}
        ).to_list()
    
    @staticmethod
    async def create_advance_offer(
        user_id: str,
        principal: float,
        purpose: str,
        obligation_name: Optional[str] = None,
        weekly_income_estimate: float = 15000,
        repayment_date: Optional[date] = None
    ) -> MicroAdvance:
        """Create a new advance offer."""
        user_oid = PydanticObjectId(user_id)
        
        # Apply guardrails
        max_allowed = weekly_income_estimate * AdvanceService.MAX_ADVANCE_PCT_OF_WEEKLY
        principal = min(principal, max_allowed)
        principal = min(principal, AdvanceService.MAX_ADVANCE_AMOUNT)
        principal = max(principal, AdvanceService.MIN_ADVANCE_AMOUNT)
        principal = round(principal, -2)  # Round to nearest 100
        
        # Find repayment date (next weekend if not specified)
        if repayment_date is None:
            today = datetime.now().date()
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0:
                days_until_saturday = 7
            repayment_date = today + timedelta(days=days_until_saturday)
        
        # Calculate risk
        ratio = principal / weekly_income_estimate
        if ratio < 0.2:
            risk_score = "low"
            risk_explanation = "Chhota advance hai, weekend earnings se aasani se repay ho jayega."
        elif ratio < 0.3:
            risk_score = "medium"
            risk_explanation = "Manageable hai, par weekend mein achha earning chahiye."
        else:
            risk_score = "high"
            risk_explanation = "Thoda zyada hai, weekend earnings pe heavily depend karega."
        
        advance = MicroAdvance(
            user_id=user_oid,
            principal=principal,
            purpose=purpose,
            obligation_name=obligation_name,
            fee=0,  # No fees in MVP
            total_repayable=principal,
            repayment_date=datetime.combine(repayment_date, datetime.min.time()),
            repayment_source="weekend_earnings",
            max_repayment_percentage=AdvanceService.MAX_ADVANCE_PCT_OF_WEEKLY * 100,
            status="offered",
            risk_score=risk_score,
            risk_explanation=risk_explanation,
            weekly_income_estimate=weekly_income_estimate,
            advance_to_income_ratio=round(ratio * 100, 1),
        )
        
        await advance.insert()
        
        return advance
    
    @staticmethod
    async def accept_advance(advance_id: str, user_id: str) -> Optional[MicroAdvance]:
        """Accept an advance offer."""
        user_oid = PydanticObjectId(user_id)
        advance_oid = PydanticObjectId(advance_id)
        
        # Get the advance
        advance = await MicroAdvance.get(advance_oid)
        
        if not advance or advance.user_id != user_oid:
            return None
        
        if advance.status != "offered":
            return None
        
        # Check guardrails
        active_advances = await AdvanceService.get_active_advances(user_id)
        if len(active_advances) >= AdvanceService.MAX_ACTIVE_ADVANCES:
            return None
        
        # Accept the advance
        advance.status = "active"
        advance.accepted_at = datetime.utcnow()
        advance.disbursed_at = datetime.utcnow()
        
        await advance.save()
        
        # Add principal to discretionary bucket
        discretionary = await Bucket.find_one(
            Bucket.user_id == user_oid,
            Bucket.name == "discretionary"
        )
        
        if discretionary:
            discretionary.current_balance += advance.principal
            discretionary.updated_at = datetime.utcnow()
            await discretionary.save()
        
        return advance
    
    @staticmethod
    async def decline_advance(advance_id: str, user_id: str) -> bool:
        """Decline an advance offer."""
        user_oid = PydanticObjectId(user_id)
        advance_oid = PydanticObjectId(advance_id)
        
        advance = await MicroAdvance.get(advance_oid)
        
        if not advance or advance.user_id != user_oid:
            return False
        
        if advance.status != "offered":
            return False
        
        # Delete the offer
        await advance.delete()
        
        return True
    
    @staticmethod
    async def process_repayment(
        user_id: str,
        income_amount: float
    ) -> Optional[Dict]:
        """Process repayment from income."""
        user_oid = PydanticObjectId(user_id)
        
        # Get active advances
        advances = await MicroAdvance.find(
            MicroAdvance.user_id == user_oid,
            {"status": "active"}
        ).to_list()
        
        if not advances:
            return None
        
        # Take from oldest advance first
        advance = advances[0]
        
        # Calculate repayment (max 40% of income)
        max_repayment = income_amount * AdvanceService.MAX_ADVANCE_PCT_OF_WEEKLY
        remaining = advance.total_repayable - advance.amount_repaid
        repayment = min(max_repayment, remaining)
        
        if repayment <= 0:
            return None
        
        # Apply repayment
        advance.amount_repaid += repayment
        advance.repayment_events.append({
            "amount": repayment,
            "date": datetime.utcnow().isoformat(),
        })
        
        # Check if fully repaid
        if advance.amount_repaid >= advance.total_repayable:
            advance.status = "repaid"
            advance.repaid_at = datetime.utcnow()
        
        await advance.save()
        
        return {
            "advance_id": str(advance.id),
            "repayment_amount": repayment,
            "remaining_balance": max(0, advance.total_repayable - advance.amount_repaid),
            "is_fully_repaid": advance.status == "repaid",
        }
    
    @staticmethod
    async def get_advance_history(user_id: str) -> List[MicroAdvance]:
        """Get advance history for a user."""
        user_oid = PydanticObjectId(user_id)
        
        return await MicroAdvance.find(
            MicroAdvance.user_id == user_oid
        ).sort("-offered_at").to_list()
