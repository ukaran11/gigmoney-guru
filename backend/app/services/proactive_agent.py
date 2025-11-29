"""
GigMoney Guru - Proactive Agent Service

Event-driven agent triggers that run automatically when:
1. Income is added (analyze and allocate)
2. Obligation is due soon (alert user)
3. Bucket balance is low (warn user)
4. Expense pattern changes (detect anomalies)
5. Daily scheduled analysis

This makes the system TRULY agentic - it acts without being asked.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from beanie import PydanticObjectId
import asyncio
import logging

from app.orchestrator.agentic_pipeline import run_agent_with_mode
from app.orchestrator.state import load_financial_context
from app.models.bucket import Bucket
from app.models.obligation import Obligation
from app.models.income import IncomeEvent
from app.models.expense import ExpenseEvent

logger = logging.getLogger(__name__)


class ProactiveAgentService:
    """
    Proactive agent that runs automatically based on events and conditions.
    This is what makes the system truly agentic - it doesn't wait for user commands.
    """
    
    # Thresholds for triggering proactive runs
    LOW_BUCKET_THRESHOLD = 500  # ₹500 minimum
    URGENT_DAYS_THRESHOLD = 3   # Days until due
    EXPENSE_SPIKE_THRESHOLD = 1.5  # 50% above average
    
    @classmethod
    async def on_income_added(
        cls,
        user_id: str,
        amount: float,
        source: str
    ) -> Dict[str, Any]:
        """
        Triggered when user adds income.
        Runs quick analysis to provide immediate feedback.
        """
        logger.info(f"[Proactive] Income added: ₹{amount} from {source} for user {user_id}")
        
        try:
            # Load context
            context = await load_financial_context(user_id, datetime.now().date())
            context["trigger"] = "income_added"
            context["trigger_amount"] = amount
            context["trigger_source"] = source
            
            # Run quick analysis with timeout (don't block the income add)
            try:
                result = await asyncio.wait_for(
                    run_agent_with_mode(context, mode="fast", user_id=user_id),
                    timeout=5.0  # 5 second timeout for quick response
                )
            except asyncio.TimeoutError:
                logger.warning(f"[Proactive] Agent timed out, returning quick response")
                return {
                    "triggered": True,
                    "trigger_type": "income_added",
                    "quick_insight": f"₹{amount} from {source} allocated to your buckets!",
                    "safe_to_spend": 0,
                    "alerts": [],
                    "allocation_suggestion": None
                }
            
            # Extract key info for immediate response
            return {
                "triggered": True,
                "trigger_type": "income_added",
                "quick_insight": result.get("key_insight", f"₹{amount} received and allocated!"),
                "safe_to_spend": result.get("safe_to_spend", 0),
                "alerts": result.get("alerts", []),
                "allocation_suggestion": cls._get_allocation_suggestion(result, amount)
            }
        except Exception as e:
            logger.error(f"[Proactive] Error on income_added: {e}")
            return {
                "triggered": False, 
                "error": str(e),
                "quick_insight": f"₹{amount} added successfully!"
            }
    
    @classmethod
    async def check_upcoming_obligations(cls, user_id: str) -> Dict[str, Any]:
        """
        Check for obligations due soon and trigger alerts.
        Should be called periodically (e.g., daily) or on dashboard load.
        """
        user_oid = PydanticObjectId(user_id)
        
        # Find obligations due within threshold
        obligations = await Obligation.find(
            Obligation.user_id == user_oid,
            Obligation.is_active == True
        ).to_list()
        
        urgent_alerts = []
        today = datetime.now().day
        
        for ob in obligations:
            days_until = ob.due_day - today
            if days_until < 0:
                days_until += 30  # Next month
            
            if days_until <= cls.URGENT_DAYS_THRESHOLD:
                # Check if we can cover it
                bucket = await Bucket.find_one({
                    "user_id": user_oid,
                    "name": ob.bucket_name or "essentials"
                })
                
                bucket_balance = bucket.current_balance if bucket else 0
                shortfall = max(0, ob.amount - bucket_balance)
                
                alert = {
                    "type": "urgent" if days_until <= 1 else "warning",
                    "title": f"{ob.name} due in {days_until} days!",
                    "message": f"₹{ob.amount:,.0f} due on {ob.due_day}th. " + (
                        f"⚠️ ₹{shortfall:,.0f} shortfall!" if shortfall > 0 
                        else "✅ Covered by bucket."
                    ),
                    "obligation_id": str(ob.id),
                    "amount": ob.amount,
                    "days_until": days_until,
                    "shortfall": shortfall,
                    "can_cover": shortfall == 0
                }
                urgent_alerts.append(alert)
        
        return {
            "triggered": len(urgent_alerts) > 0,
            "trigger_type": "obligation_check",
            "alerts": urgent_alerts,
            "urgent_count": len([a for a in urgent_alerts if a["type"] == "urgent"]),
            "total_shortfall": sum(a["shortfall"] for a in urgent_alerts)
        }
    
    @classmethod
    async def check_low_buckets(cls, user_id: str) -> Dict[str, Any]:
        """
        Check for buckets with critically low balance.
        """
        user_oid = PydanticObjectId(user_id)
        
        buckets = await Bucket.find(
            Bucket.user_id == user_oid,
            Bucket.is_active == True
        ).to_list()
        
        low_bucket_alerts = []
        
        for bucket in buckets:
            # Check if below threshold or below 20% of target
            is_low = (
                bucket.current_balance < cls.LOW_BUCKET_THRESHOLD or
                (bucket.target_amount > 0 and 
                 bucket.current_balance < bucket.target_amount * 0.2)
            )
            
            if is_low:
                deficit = max(
                    cls.LOW_BUCKET_THRESHOLD - bucket.current_balance,
                    (bucket.target_amount * 0.2) - bucket.current_balance if bucket.target_amount > 0 else 0
                )
                
                alert = {
                    "type": "warning",
                    "title": f"{bucket.display_name} bucket is low!",
                    "message": f"Only ₹{bucket.current_balance:,.0f} remaining. Top up ₹{deficit:,.0f} soon.",
                    "bucket_name": bucket.name,
                    "current_balance": bucket.current_balance,
                    "target_amount": bucket.target_amount,
                    "deficit": deficit
                }
                low_bucket_alerts.append(alert)
        
        return {
            "triggered": len(low_bucket_alerts) > 0,
            "trigger_type": "low_bucket_check",
            "alerts": low_bucket_alerts,
            "critical_buckets": [a["bucket_name"] for a in low_bucket_alerts]
        }
    
    @classmethod
    async def detect_expense_anomaly(cls, user_id: str) -> Dict[str, Any]:
        """
        Detect unusual spending patterns.
        """
        user_oid = PydanticObjectId(user_id)
        
        # Get expenses from last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        recent_expenses = await ExpenseEvent.find(
            ExpenseEvent.user_id == user_oid,
            ExpenseEvent.spent_at >= week_ago
        ).to_list()
        
        # Get expenses from previous 7 days for comparison
        two_weeks_ago = datetime.now() - timedelta(days=14)
        previous_expenses = await ExpenseEvent.find(
            ExpenseEvent.user_id == user_oid,
            ExpenseEvent.spent_at >= two_weeks_ago,
            ExpenseEvent.spent_at < week_ago
        ).to_list()
        
        # Calculate totals by category
        recent_by_cat = {}
        for exp in recent_expenses:
            cat = exp.category or "other"
            recent_by_cat[cat] = recent_by_cat.get(cat, 0) + exp.amount
        
        previous_by_cat = {}
        for exp in previous_expenses:
            cat = exp.category or "other"
            previous_by_cat[cat] = previous_by_cat.get(cat, 0) + exp.amount
        
        # Detect spikes
        anomalies = []
        for cat, amount in recent_by_cat.items():
            prev_amount = previous_by_cat.get(cat, amount / 2)  # Default to half if no history
            if prev_amount > 0 and amount > prev_amount * cls.EXPENSE_SPIKE_THRESHOLD:
                spike_pct = ((amount - prev_amount) / prev_amount) * 100
                anomalies.append({
                    "type": "tip",
                    "title": f"Spending spike in {cat}!",
                    "message": f"₹{amount:,.0f} this week vs ₹{prev_amount:,.0f} last week ({spike_pct:.0f}% increase)",
                    "category": cat,
                    "current": amount,
                    "previous": prev_amount,
                    "spike_percent": spike_pct
                })
        
        return {
            "triggered": len(anomalies) > 0,
            "trigger_type": "expense_anomaly",
            "alerts": anomalies,
            "total_recent": sum(recent_by_cat.values()),
            "total_previous": sum(previous_by_cat.values())
        }
    
    @classmethod
    async def run_daily_analysis(cls, user_id: str) -> Dict[str, Any]:
        """
        Comprehensive daily analysis - should be scheduled to run each morning.
        """
        logger.info(f"[Proactive] Running daily analysis for user {user_id}")
        
        try:
            # Load full context
            context = await load_financial_context(user_id, datetime.now().date())
            context["trigger"] = "daily_scheduled"
            
            # Run full ReAct analysis
            result = await run_agent_with_mode(context, mode="react", user_id=user_id)
            
            # Also run all proactive checks
            obligation_check = await cls.check_upcoming_obligations(user_id)
            bucket_check = await cls.check_low_buckets(user_id)
            anomaly_check = await cls.detect_expense_anomaly(user_id)
            
            # Combine all alerts
            all_alerts = (
                result.get("alerts", []) +
                obligation_check.get("alerts", []) +
                bucket_check.get("alerts", []) +
                anomaly_check.get("alerts", [])
            )
            
            return {
                "triggered": True,
                "trigger_type": "daily_analysis",
                "key_insight": result.get("key_insight", ""),
                "recommended_action": result.get("recommended_action", ""),
                "safe_to_spend": result.get("safe_to_spend", 0),
                "risk_score": result.get("risk_score", 0),
                "risk_level": result.get("risk_level", "unknown"),
                "all_alerts": all_alerts,
                "tools_used": result.get("total_tool_calls", 0),
                "analysis_complete": True
            }
        except Exception as e:
            logger.error(f"[Proactive] Error in daily analysis: {e}")
            return {"triggered": False, "error": str(e)}
    
    @classmethod
    async def run_all_proactive_checks(cls, user_id: str) -> Dict[str, Any]:
        """
        Run all proactive checks at once.
        Called on dashboard load to show all relevant alerts.
        """
        results = await asyncio.gather(
            cls.check_upcoming_obligations(user_id),
            cls.check_low_buckets(user_id),
            cls.detect_expense_anomaly(user_id),
            return_exceptions=True
        )
        
        all_alerts = []
        for result in results:
            if isinstance(result, dict) and result.get("alerts"):
                all_alerts.extend(result["alerts"])
        
        # Sort by urgency
        priority = {"urgent": 0, "warning": 1, "tip": 2, "info": 3}
        all_alerts.sort(key=lambda a: priority.get(a.get("type", "info"), 3))
        
        return {
            "triggered": len(all_alerts) > 0,
            "alerts": all_alerts,
            "alert_count": len(all_alerts),
            "urgent_count": len([a for a in all_alerts if a.get("type") == "urgent"]),
            "checked_at": datetime.now().isoformat()
        }
    
    @classmethod
    def _get_allocation_suggestion(cls, result: Dict, amount: float) -> str:
        """Generate allocation suggestion from analysis result."""
        allocations = result.get("allocations_made", [])
        if allocations:
            parts = [f"{a['bucket']}: ₹{a['amount']:.0f}" for a in allocations[:3]]
            return "Suggested: " + ", ".join(parts)
        
        # Default suggestion based on amount
        if amount >= 1000:
            return f"Suggested: Essentials ₹{amount*0.5:.0f}, Goals ₹{amount*0.3:.0f}, Flex ₹{amount*0.2:.0f}"
        else:
            return f"Suggested: Add to Essentials bucket"
