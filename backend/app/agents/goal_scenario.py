"""
GigMoney Guru - Goal & Scenario Agent

Manages savings goals and runs what-if simulations:
- Track goal progress
- Run scenarios (extra hours, reduce spending)
- Compare baseline vs scenario outcomes
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import math


class GoalScenarioAgent:
    """
    Agent that manages goals and runs what-if scenarios.
    
    Input:
        - goals: User's savings goals
        - income_patterns: From Income Pattern Agent
        - today_allocation: From Bucket Allocation Agent
        
    Output:
        - goal_scenarios: Analysis for each goal
    """
    
    def __init__(self):
        self.name = "goal_scenario"
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze goals and run default scenarios.
        
        Algorithm:
        1. For each goal:
           a. Calculate current progress
           b. Project completion date at current rate
           c. Run standard scenarios
           d. Compare outcomes
        """
        goals = state.get("goals", [])
        income_patterns = state.get("income_patterns", {})
        today_allocation = state.get("today_allocation", {})
        run_date = state.get("run_date")
        
        if isinstance(run_date, str):
            run_date = datetime.fromisoformat(run_date).date()
        elif run_date is None:
            run_date = datetime.now().date()
        
        goal_scenarios = []
        
        for goal in goals:
            if goal.get("status") != "active":
                continue
            
            scenario = self._analyze_goal(goal, income_patterns, run_date)
            goal_scenarios.append(scenario)
        
        state["goal_scenarios"] = goal_scenarios
        
        return state
    
    def _analyze_goal(
        self,
        goal: Dict[str, Any],
        income_patterns: Dict[str, Any],
        run_date: date
    ) -> Dict[str, Any]:
        """Analyze a single goal."""
        goal_id = str(goal.get("_id", goal.get("id", "")))
        name = goal.get("name", "Goal")
        target = float(goal.get("target_amount", 0))
        current = float(goal.get("current_amount", 0))
        monthly_contribution = float(goal.get("monthly_contribution", 0))
        target_date_str = goal.get("target_date")
        
        # Calculate progress
        progress = (current / target * 100) if target > 0 else 0
        remaining = max(0, target - current)
        
        # Parse target date
        target_date = None
        if target_date_str:
            if isinstance(target_date_str, str):
                target_date = datetime.fromisoformat(target_date_str.replace("Z", "+00:00")).date()
            elif isinstance(target_date_str, datetime):
                target_date = target_date_str.date()
        
        # Calculate projected completion at current rate
        if monthly_contribution > 0:
            months_needed = remaining / monthly_contribution
            projected_completion = run_date + timedelta(days=months_needed * 30)
        else:
            projected_completion = None
        
        # Check if on track
        on_track = False
        days_difference = 0
        
        if target_date and projected_completion:
            days_difference = (target_date - projected_completion).days
            on_track = days_difference >= 0
        
        return {
            "goal_id": goal_id,
            "goal_name": name,
            "target_amount": target,
            "current_amount": current,
            "progress_percentage": round(progress, 1),
            "remaining_amount": remaining,
            "monthly_contribution": monthly_contribution,
            "projected_completion_date": projected_completion.isoformat() if projected_completion else None,
            "target_date": target_date.isoformat() if target_date else None,
            "on_track": on_track,
            "days_difference": days_difference,
        }
    
    def run_scenario(
        self,
        goal: Dict[str, Any],
        scenario_type: str,
        params: Dict[str, Any],
        income_patterns: Dict[str, Any],
        run_date: date
    ) -> Dict[str, Any]:
        """
        Run a what-if scenario for a goal.
        
        Scenario types:
        - extra_hours: Work more hours per week
        - reduce_expense: Cut spending in a category
        - custom: Custom income/expense changes
        """
        goal_id = str(goal.get("_id", goal.get("id", "")))
        name = goal.get("name", "Goal")
        target = float(goal.get("target_amount", 0))
        current = float(goal.get("current_amount", 0))
        monthly_contribution = float(goal.get("monthly_contribution", 0))
        remaining = max(0, target - current)
        
        # Calculate baseline
        if monthly_contribution > 0:
            baseline_months = remaining / monthly_contribution
            baseline_completion = run_date + timedelta(days=baseline_months * 30)
        else:
            baseline_months = float('inf')
            baseline_completion = None
        
        # Calculate scenario
        if scenario_type == "extra_hours":
            extra_hours = params.get("extra_hours_per_week", 4)
            hourly_rate = params.get("hourly_rate", 150)
            
            extra_monthly = extra_hours * hourly_rate * 4  # 4 weeks/month
            scenario_contribution = monthly_contribution + (extra_monthly * 0.3)  # 30% goes to savings
            
            description = f"Work {extra_hours} extra hours/week at ₹{hourly_rate}/hr"
            
        elif scenario_type == "reduce_expense":
            category = params.get("expense_category", "eating_out")
            reduction = params.get("reduction_amount", 500)
            
            scenario_contribution = monthly_contribution + (reduction * 4)  # Weekly to monthly
            
            description = f"Reduce {category} spending by ₹{reduction}/week"
            
        elif scenario_type == "custom":
            income_change = params.get("monthly_income_change", 0)
            expense_change = params.get("monthly_expense_change", 0)
            
            net_change = income_change - expense_change
            scenario_contribution = monthly_contribution + (net_change * 0.3)
            
            description = f"Custom: +₹{income_change} income, -₹{expense_change} expenses"
        else:
            scenario_contribution = monthly_contribution
            description = "No changes"
        
        # Calculate scenario completion
        if scenario_contribution > 0:
            scenario_months = remaining / scenario_contribution
            scenario_completion = run_date + timedelta(days=scenario_months * 30)
        else:
            scenario_months = float('inf')
            scenario_completion = None
        
        # Calculate difference
        if baseline_completion and scenario_completion:
            days_saved = (baseline_completion - scenario_completion).days
        else:
            days_saved = 0
        
        # Build comparison
        comparisons = [
            {
                "metric": "Monthly Contribution",
                "baseline_value": monthly_contribution,
                "scenario_value": scenario_contribution,
                "difference": scenario_contribution - monthly_contribution,
                "improvement_percentage": (
                    ((scenario_contribution - monthly_contribution) / monthly_contribution * 100)
                    if monthly_contribution > 0 else 0
                ),
            },
            {
                "metric": "Months to Goal",
                "baseline_value": baseline_months if baseline_months != float('inf') else -1,
                "scenario_value": scenario_months if scenario_months != float('inf') else -1,
                "difference": baseline_months - scenario_months if baseline_months != float('inf') else 0,
                "improvement_percentage": (
                    ((baseline_months - scenario_months) / baseline_months * 100)
                    if baseline_months not in [float('inf'), 0] else 0
                ),
            },
        ]
        
        # Generate recommendation
        if days_saved > 30:
            recommendation = f"🎯 Great option! Goal {math.ceil(days_saved/30)} months jaldi complete hoga."
        elif days_saved > 0:
            recommendation = f"👍 Achha hai! {days_saved} din pehle goal complete ho jayega."
        else:
            recommendation = "This scenario doesn't significantly change your timeline."
        
        return {
            "scenario_type": scenario_type,
            "scenario_description": description,
            "goal_id": goal_id,
            "goal_name": name,
            "comparisons": comparisons,
            "baseline_completion_date": baseline_completion.isoformat() if baseline_completion else None,
            "scenario_completion_date": scenario_completion.isoformat() if scenario_completion else None,
            "days_saved": days_saved,
            "recommendation": recommendation,
        }


# Function for LangGraph node
def goal_scenario_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node wrapper for Goal Scenario Agent."""
    agent = GoalScenarioAgent()
    return agent.run(state)
