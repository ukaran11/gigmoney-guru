"""
GigMoney Guru - Bucket Allocation Agent

Allocates today's income to buckets:
- Priority-based allocation
- Reserve for obligations
- Maintain emergency buffer
- Calculate safe-to-spend
"""
from typing import Dict, Any, List
from datetime import datetime, date


class BucketAllocationAgent:
    """
    Agent that allocates today's income to buckets.
    
    Input:
        - today_income: Today's total earnings
        - bucket_balances: Current bucket balances
        - obligations: List of obligations
        - obligation_risks: From Obligation Risk Agent
        - income_patterns: From Income Pattern Agent
        
    Output:
        - today_allocation: Allocation plan with safe-to-spend
    """
    
    def __init__(self):
        self.name = "bucket_allocation"
        
        # Default bucket configuration
        self.default_buckets = {
            "rent": {"priority": 1, "allocation_pct": 0.25, "icon": "🏠"},
            "emi": {"priority": 2, "allocation_pct": 0.15, "icon": "🏍️"},
            "tax": {"priority": 3, "allocation_pct": 0.05, "icon": "📋"},
            "fuel": {"priority": 4, "allocation_pct": 0.10, "icon": "⛽"},
            "emergency": {"priority": 5, "allocation_pct": 0.10, "icon": "🛡️"},
            "savings": {"priority": 6, "allocation_pct": 0.10, "icon": "💰"},
            "discretionary": {"priority": 7, "allocation_pct": 0.25, "icon": "🎯"},
        }
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Allocate today's income to buckets.
        
        Algorithm:
        1. Get today's income
        2. Calculate minimum daily allocation for each bucket
        3. Adjust for high-risk obligations
        4. Allocate remaining to discretionary/safe-to-spend
        5. Return allocation plan
        """
        today_income = state.get("today_income", 0)
        bucket_balances = state.get("bucket_balances", {})
        obligations = state.get("obligations", [])
        obligation_risks = state.get("obligation_risks", [])
        run_date = state.get("run_date")
        
        if isinstance(run_date, str):
            run_date = datetime.fromisoformat(run_date).date()
        elif run_date is None:
            run_date = datetime.now().date()
        
        # Build obligation lookup for targets
        obligation_targets = self._build_obligation_targets(obligations)
        
        # Get high risk obligations
        high_risk_obligations = [
            r for r in obligation_risks 
            if r.get("risk_level") == "high"
        ]
        
        # Calculate allocations
        allocations = []
        remaining = today_income
        adjustments = []
        
        # Sort buckets by priority
        sorted_buckets = sorted(
            self.default_buckets.items(),
            key=lambda x: x[1]["priority"]
        )
        
        for bucket_name, config in sorted_buckets:
            if remaining <= 0:
                break
            
            # Calculate target allocation
            base_allocation = today_income * config["allocation_pct"]
            
            # Adjust for high-risk obligations
            if bucket_name in ["rent", "emi"]:
                # Check if this bucket has a high-risk obligation
                high_risk_for_bucket = [
                    r for r in high_risk_obligations
                    if r.get("category", "").lower() == bucket_name
                ]
                
                if high_risk_for_bucket:
                    # Increase allocation
                    shortfall = high_risk_for_bucket[0].get("shortfall_amount", 0)
                    days_until = high_risk_for_bucket[0].get("days_until_due", 30)
                    
                    # Try to cover shortfall in remaining days
                    if days_until > 0:
                        extra_needed = shortfall / days_until
                        if extra_needed > 0:
                            base_allocation += extra_needed
                            adjustments.append(
                                f"Increased {bucket_name} by ₹{extra_needed:.0f}/day to cover shortfall"
                            )
            
            # Check bucket current balance vs target
            current_balance = bucket_balances.get(bucket_name, 0)
            target = obligation_targets.get(bucket_name, 0)
            
            # If bucket is already at target, reduce allocation
            if target > 0 and current_balance >= target:
                base_allocation = base_allocation * 0.3  # Maintenance mode
            
            # Ensure we don't over-allocate
            allocation = min(base_allocation, remaining)
            
            if allocation > 0:
                allocations.append({
                    "bucket_name": bucket_name,
                    "amount": round(allocation, 0),
                    "reason": f"Daily allocation ({config['allocation_pct']*100:.0f}%)",
                    "icon": config["icon"],
                })
                remaining -= allocation
        
        # Safe to spend is the remaining amount after all allocations
        safe_to_spend = max(0, remaining)
        
        # Create allocation plan
        allocation_plan = {
            "date": run_date.isoformat(),
            "total_income": today_income,
            "allocations": allocations,
            "safe_to_spend": round(safe_to_spend, 0),
            "adjustments_made": adjustments,
        }
        
        # Update bucket balances in state
        new_bucket_balances = bucket_balances.copy()
        for alloc in allocations:
            bucket_name = alloc["bucket_name"]
            amount = alloc["amount"]
            new_bucket_balances[bucket_name] = new_bucket_balances.get(bucket_name, 0) + amount
        
        # Update state
        state["today_allocation"] = allocation_plan
        state["bucket_balances"] = new_bucket_balances
        
        return state
    
    def _build_obligation_targets(self, obligations: List[Dict]) -> Dict[str, float]:
        """Build target amounts for each bucket based on obligations."""
        targets = {}
        
        for obligation in obligations:
            if not obligation.get("is_active", True):
                continue
            
            bucket_name = obligation.get("bucket_name", obligation.get("category", "other"))
            amount = float(obligation.get("amount", 0))
            
            if bucket_name in targets:
                targets[bucket_name] += amount
            else:
                targets[bucket_name] = amount
        
        return targets


# Function for LangGraph node
def bucket_allocation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node wrapper for Bucket Allocation Agent."""
    agent = BucketAllocationAgent()
    return agent.run(state)
