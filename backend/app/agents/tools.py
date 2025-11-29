"""
GigMoney Guru - Agent Tools

Tools that agents can call to take actions and query data.
This enables TRUE agentic behavior with:
- Tool calling that ACTUALLY modifies data in MongoDB
- Memory system to remember past decisions
- Alert creation that persists
- Rich contextual analysis
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from beanie import PydanticObjectId
import uuid

# Import models for persistence
from app.models.bucket import Bucket
from app.models.decision import AgentDecision

# Tool definitions for OpenAI function calling
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_bucket_balances",
            "description": "Get current balances of all money buckets (essentials, flex, goals, emergency)",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_obligations",
            "description": "Get list of upcoming bills and payments with due dates and amounts",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days to look ahead (default 30)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_income_history",
            "description": "Get income history to analyze earning patterns",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days of history (default 30)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expense_history",
            "description": "Get expense history to analyze spending patterns",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days of history (default 30)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "allocate_to_bucket",
            "description": "Allocate money to a specific bucket",
            "parameters": {
                "type": "object",
                "properties": {
                    "bucket_name": {
                        "type": "string",
                        "description": "Name of bucket (essentials, flex, goals, emergency)"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to allocate in INR"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for this allocation"
                    }
                },
                "required": ["bucket_name", "amount", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_shortfall",
            "description": "Calculate if there's a shortfall for upcoming obligations",
            "parameters": {
                "type": "object",
                "properties": {
                    "obligation_name": {
                        "type": "string",
                        "description": "Name of the obligation to check"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_advance",
            "description": "Suggest a micro-advance if user has a shortfall",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Amount of advance needed"
                    },
                    "purpose": {
                        "type": "string",
                        "description": "What the advance is for"
                    },
                    "repayment_days": {
                        "type": "integer",
                        "description": "Days until repayment (default 7)"
                    }
                },
                "required": ["amount", "purpose"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_goals_progress",
            "description": "Get progress on savings goals",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_message_to_user",
            "description": "Send a message or alert to the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message content in Hinglish"
                    },
                    "message_type": {
                        "type": "string",
                        "enum": ["info", "warning", "success", "tip"],
                        "description": "Type of message"
                    },
                    "priority": {
                        "type": "integer",
                        "description": "Priority 1-5 (1 is highest)"
                    }
                },
                "required": ["message", "message_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_risk_score",
            "description": "Set the overall financial risk score",
            "parameters": {
                "type": "object",
                "properties": {
                    "score": {
                        "type": "integer",
                        "description": "Risk score 0-100"
                    },
                    "level": {
                        "type": "string",
                        "enum": ["low", "moderate", "high", "critical"],
                        "description": "Risk level"
                    },
                    "reasons": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Reasons for this risk level"
                    }
                },
                "required": ["score", "level"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "complete_analysis",
            "description": "Mark analysis as complete and provide final summary. ONLY call this after you have called at least 5 other tools and done thorough analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "safe_to_spend": {
                        "type": "number",
                        "description": "Amount safe to spend today in INR"
                    },
                    "key_insight": {
                        "type": "string",
                        "description": "Most important insight for user. MUST be specific, actionable, and personalized. Example: 'Aapka rent ka ₹8000 due hai 5 din mein, aur aapke paas sirf ₹6000 hai - ₹2000 ka gap hai!'"
                    },
                    "recommended_action": {
                        "type": "string",
                        "description": "What user should do next. MUST be concrete. Example: 'Kal extra 2 hours drive karke ₹800 kama sakte ho'"
                    },
                    "confidence_score": {
                        "type": "number",
                        "description": "How confident you are in this analysis (0-100)"
                    }
                },
                "required": ["safe_to_spend", "key_insight", "recommended_action", "confidence_score"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_past_decisions",
            "description": "Get past agent decisions and recommendations to maintain memory and context",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days of history (default 7)"
                    },
                    "decision_type": {
                        "type": "string",
                        "description": "Filter by decision type (allocation, warning, advance_offer)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_decision",
            "description": "Save an important decision for future memory and learning",
            "parameters": {
                "type": "object",
                "properties": {
                    "decision_type": {
                        "type": "string",
                        "enum": ["allocation", "warning", "advance_offer", "insight", "goal_update"],
                        "description": "Type of decision"
                    },
                    "decision_value": {
                        "type": "string",
                        "description": "Brief description of the decision"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Why this decision was made"
                    },
                    "impact_amount": {
                        "type": "number",
                        "description": "Financial impact in INR (if applicable)"
                    }
                },
                "required": ["decision_type", "decision_value", "reasoning"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_alert",
            "description": "Create a persistent alert for the user that will be shown prominently",
            "parameters": {
                "type": "object",
                "properties": {
                    "alert_type": {
                        "type": "string",
                        "enum": ["urgent", "warning", "info", "success", "tip"],
                        "description": "Severity/type of alert"
                    },
                    "title": {
                        "type": "string",
                        "description": "Short title in Hinglish (max 50 chars)"
                    },
                    "message": {
                        "type": "string",
                        "description": "Full message in Hinglish"
                    },
                    "action_url": {
                        "type": "string",
                        "description": "Optional: URL/route for action button"
                    },
                    "expires_hours": {
                        "type": "integer",
                        "description": "Hours until alert expires (default 24)"
                    }
                },
                "required": ["alert_type", "title", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_spending_pattern",
            "description": "Deep analysis of spending patterns to find savings opportunities",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category to analyze (food, fuel, entertainment, etc.) or 'all'"
                    },
                    "comparison_days": {
                        "type": "integer",
                        "description": "Compare with this many days ago (default 7)"
                    }
                },
                "required": ["category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_goal_trajectory",
            "description": "Calculate if user is on track for goals and what adjustments are needed",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_name": {
                        "type": "string",
                        "description": "Name of goal to analyze, or 'all'"
                    }
                },
                "required": ["goal_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "simulate_scenario",
            "description": "Simulate a financial scenario (what-if analysis)",
            "parameters": {
                "type": "object",
                "properties": {
                    "scenario_type": {
                        "type": "string",
                        "enum": ["extra_income", "unexpected_expense", "skip_work", "advance_repayment"],
                        "description": "Type of scenario to simulate"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount involved in the scenario"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Days to simulate for"
                    }
                },
                "required": ["scenario_type", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_bucket_balance_persistent",
            "description": "Permanently update a bucket balance in the database. USE THIS for real allocations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bucket_name": {
                        "type": "string",
                        "description": "Name of bucket to update"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to add (positive) or remove (negative)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for this change"
                    }
                },
                "required": ["bucket_name", "amount", "reason"]
            }
        }
    }
]


class ToolExecutor:
    """
    Executes tool calls from the agent.
    Each tool has access to the current state and can modify it.
    Tools can PERSIST changes to MongoDB for true agentic behavior.
    """
    
    def __init__(self, state: Dict[str, Any], user_id: Optional[str] = None):
        self.state = state
        self.user_id = user_id
        self.run_id = str(uuid.uuid4())
        self.tool_calls_log = []
        self.tools_called_count = 0
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return the result."""
        self.tools_called_count += 1
        self.tool_calls_log.append({
            "tool": tool_name,
            "arguments": arguments,
            "timestamp": datetime.now().isoformat(),
            "sequence": self.tools_called_count
        })
        
        # Route to appropriate tool handler
        handlers = {
            "get_bucket_balances": self._get_bucket_balances,
            "get_upcoming_obligations": self._get_upcoming_obligations,
            "get_income_history": self._get_income_history,
            "get_expense_history": self._get_expense_history,
            "allocate_to_bucket": self._allocate_to_bucket,
            "calculate_shortfall": self._calculate_shortfall,
            "suggest_advance": self._suggest_advance,
            "get_goals_progress": self._get_goals_progress,
            "send_message_to_user": self._send_message_to_user,
            "set_risk_score": self._set_risk_score,
            "complete_analysis": self._complete_analysis,
            # NEW agentic tools
            "get_past_decisions": self._get_past_decisions,
            "save_decision": self._save_decision,
            "create_alert": self._create_alert,
            "analyze_spending_pattern": self._analyze_spending_pattern,
            "calculate_goal_trajectory": self._calculate_goal_trajectory,
            "simulate_scenario": self._simulate_scenario,
            "update_bucket_balance_persistent": self._update_bucket_balance_persistent,
        }
        
        handler = handlers.get(tool_name)
        if handler:
            return await handler(arguments)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    async def _get_bucket_balances(self, args: Dict) -> Dict[str, Any]:
        """Get current bucket balances."""
        balances = self.state.get("bucket_balances", {})
        return {
            "buckets": balances,
            "total": sum(balances.values()),
            "details": [
                {"name": k, "balance": v} for k, v in balances.items()
            ]
        }
    
    async def _get_upcoming_obligations(self, args: Dict) -> Dict[str, Any]:
        """Get upcoming obligations."""
        obligations = self.state.get("obligations", [])
        obligation_risks = self.state.get("obligation_risks", [])
        
        return {
            "obligations": [
                {
                    "name": o.get("name"),
                    "amount": o.get("amount"),
                    "due_day": o.get("due_day"),
                    "bucket": o.get("bucket_name"),
                    "risk": next(
                        (r.get("risk_level") for r in obligation_risks 
                         if r.get("obligation_name") == o.get("name")),
                        "low"
                    )
                }
                for o in obligations
            ],
            "total_monthly": sum(o.get("amount", 0) for o in obligations)
        }
    
    async def _get_income_history(self, args: Dict) -> Dict[str, Any]:
        """Get income history."""
        income_history = self.state.get("income_history", [])
        income_patterns = self.state.get("income_patterns", {})
        
        return {
            "recent_income": income_history[-10:] if income_history else [],
            "weekday_average": income_patterns.get("weekday_average", 0),
            "weekend_average": income_patterns.get("weekend_average", 0),
            "trend": income_patterns.get("trend_direction", "flat"),
            "today_income": self.state.get("today_income", 0)
        }
    
    async def _get_expense_history(self, args: Dict) -> Dict[str, Any]:
        """Get expense history."""
        expense_history = self.state.get("expense_history", [])
        
        # Group by category
        by_category = {}
        for exp in expense_history:
            cat = exp.get("category", "other")
            by_category[cat] = by_category.get(cat, 0) + exp.get("amount", 0)
        
        return {
            "recent_expenses": expense_history[-10:] if expense_history else [],
            "by_category": by_category,
            "total": sum(by_category.values())
        }
    
    async def _allocate_to_bucket(self, args: Dict) -> Dict[str, Any]:
        """Allocate money to a bucket."""
        bucket_name = args.get("bucket_name")
        amount = args.get("amount", 0)
        reason = args.get("reason", "")
        
        # Update bucket balance
        if "bucket_balances" not in self.state:
            self.state["bucket_balances"] = {}
        
        current = self.state["bucket_balances"].get(bucket_name, 0)
        self.state["bucket_balances"][bucket_name] = current + amount
        
        # Track allocation
        if "allocations_made" not in self.state:
            self.state["allocations_made"] = []
        
        self.state["allocations_made"].append({
            "bucket": bucket_name,
            "amount": amount,
            "reason": reason
        })
        
        return {
            "success": True,
            "bucket": bucket_name,
            "new_balance": self.state["bucket_balances"][bucket_name],
            "allocated": amount
        }
    
    async def _calculate_shortfall(self, args: Dict) -> Dict[str, Any]:
        """Calculate shortfall for obligations."""
        obligation_risks = self.state.get("obligation_risks", [])
        
        total_shortfall = 0
        shortfalls = []
        
        for risk in obligation_risks:
            shortfall = risk.get("shortfall_amount", 0)
            if shortfall > 0:
                total_shortfall += shortfall
                shortfalls.append({
                    "obligation": risk.get("obligation_name"),
                    "shortfall": shortfall,
                    "days_until_due": risk.get("days_until_due"),
                    "risk_level": risk.get("risk_level")
                })
        
        return {
            "has_shortfall": total_shortfall > 0,
            "total_shortfall": total_shortfall,
            "shortfalls": shortfalls
        }
    
    async def _suggest_advance(self, args: Dict) -> Dict[str, Any]:
        """Suggest a micro-advance."""
        amount = args.get("amount", 0)
        purpose = args.get("purpose", "")
        repayment_days = args.get("repayment_days", 7)
        
        # Calculate fee (2% for 7 days)
        fee_rate = 0.02 * (repayment_days / 7)
        fee = amount * fee_rate
        
        proposal = {
            "needed": True,
            "principal": amount,
            "fee": round(fee, 2),
            "total_repayable": round(amount + fee, 2),
            "purpose": purpose,
            "repayment_days": repayment_days,
            "repayment_date": (datetime.now() + timedelta(days=repayment_days)).strftime("%Y-%m-%d")
        }
        
        self.state["advance_proposal"] = proposal
        
        return proposal
    
    async def _get_goals_progress(self, args: Dict) -> Dict[str, Any]:
        """Get goals progress."""
        goals = self.state.get("goals", [])
        
        return {
            "goals": [
                {
                    "name": g.get("name"),
                    "target": g.get("target_amount"),
                    "current": g.get("current_amount"),
                    "progress": round(g.get("current_amount", 0) / max(g.get("target_amount", 1), 1) * 100, 1),
                    "target_date": g.get("target_date")
                }
                for g in goals
            ]
        }
    
    async def _send_message_to_user(self, args: Dict) -> Dict[str, Any]:
        """Send a message to the user."""
        message = args.get("message", "")
        message_type = args.get("message_type", "info")
        priority = args.get("priority", 3)
        
        if "messages" not in self.state:
            self.state["messages"] = []
        
        self.state["messages"].append({
            "content": message,
            "message_type": message_type,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"sent": True, "message": message}
    
    async def _set_risk_score(self, args: Dict) -> Dict[str, Any]:
        """Set the risk score."""
        score = args.get("score", 0)
        level = args.get("level", "low")
        reasons = args.get("reasons", [])
        
        self.state["risk_score"] = score
        self.state["risk_level"] = level
        self.state["risk_reasons"] = reasons
        
        return {"score": score, "level": level}
    
    async def _complete_analysis(self, args: Dict) -> Dict[str, Any]:
        """Complete the analysis - requires thorough work first."""
        # Check if enough tools were called
        if self.tools_called_count < 5:
            return {
                "error": "NOT ENOUGH ANALYSIS! You have only called {0} tools. Call at least 5 tools (get balances, obligations, income, expenses, and more) before completing. Keep analyzing!".format(self.tools_called_count),
                "tools_called": self.tools_called_count,
                "suggestion": "Call get_bucket_balances, get_upcoming_obligations, get_income_history, get_expense_history, analyze_spending_pattern, calculate_shortfall first"
            }
        
        safe_to_spend = args.get("safe_to_spend", 0)
        key_insight = args.get("key_insight", "")
        recommended_action = args.get("recommended_action", "")
        confidence_score = args.get("confidence_score", 70)
        
        # Validate insight quality
        if len(key_insight) < 30:
            return {
                "error": "Key insight is too short! Provide a detailed, actionable insight in Hinglish with specific numbers.",
                "example": "Aapka rent ka ₹8000 due hai 5 din mein, aur aapke paas sirf ₹6000 hai. Kal extra drive karke ₹2000 kama lo!"
            }
        
        self.state["safe_to_spend"] = safe_to_spend
        self.state["key_insight"] = key_insight
        self.state["recommended_action"] = recommended_action
        self.state["confidence_score"] = confidence_score
        self.state["analysis_complete"] = True
        self.state["tools_used"] = self.tools_called_count
        
        return {
            "complete": True,
            "safe_to_spend": safe_to_spend,
            "insight": key_insight,
            "action": recommended_action,
            "confidence": confidence_score,
            "tools_used": self.tools_called_count
        }

    # ==================== NEW AGENTIC TOOLS ====================
    
    async def _get_past_decisions(self, args: Dict) -> Dict[str, Any]:
        """Get past decisions for memory/context - actually queries MongoDB."""
        days = args.get("days", 7)
        decision_type = args.get("decision_type")
        
        # Try to query from database
        try:
            if self.user_id:
                from_date = datetime.utcnow() - timedelta(days=days)
                query = {
                    "user_id": PydanticObjectId(self.user_id),
                    "created_at": {"$gte": from_date}
                }
                if decision_type:
                    query["decision_type"] = decision_type
                
                decisions = await AgentDecision.find(query).sort("-created_at").limit(10).to_list()
                
                return {
                    "decisions": [
                        {
                            "type": d.decision_type,
                            "value": d.decision_value,
                            "agent": d.agent_name,
                            "date": d.created_at.isoformat() if d.created_at else None
                        }
                        for d in decisions
                    ],
                    "count": len(decisions),
                    "memory_active": True
                }
        except Exception as e:
            pass
        
        # Fallback to state-based memory
        past = self.state.get("past_decisions", [])
        return {
            "decisions": past[-10:],
            "count": len(past),
            "memory_active": False,
            "note": "Using session memory"
        }
    
    async def _save_decision(self, args: Dict) -> Dict[str, Any]:
        """Save a decision to memory - persists to MongoDB."""
        decision_type = args.get("decision_type")
        decision_value = args.get("decision_value")
        reasoning = args.get("reasoning")
        impact_amount = args.get("impact_amount", 0)
        
        decision_record = {
            "type": decision_type,
            "value": decision_value,
            "reasoning": reasoning,
            "impact": impact_amount,
            "timestamp": datetime.now().isoformat()
        }
        
        # Try to persist to MongoDB
        try:
            if self.user_id:
                db_decision = AgentDecision(
                    user_id=PydanticObjectId(self.user_id),
                    agent_name="react_agent",
                    run_id=self.run_id,
                    run_date=datetime.utcnow(),
                    decision_type=decision_type,
                    decision_value=decision_value,
                    output_summary={
                        "reasoning": reasoning,
                        "impact_amount": impact_amount
                    }
                )
                await db_decision.insert()
                decision_record["persisted"] = True
        except Exception as e:
            decision_record["persisted"] = False
        
        # Also store in state
        if "decisions_made" not in self.state:
            self.state["decisions_made"] = []
        self.state["decisions_made"].append(decision_record)
        
        return {
            "saved": True,
            "decision": decision_record
        }
    
    async def _create_alert(self, args: Dict) -> Dict[str, Any]:
        """Create a persistent alert for the user."""
        alert_type = args.get("alert_type", "info")
        title = args.get("title", "")
        message = args.get("message", "")
        action_url = args.get("action_url")
        expires_hours = args.get("expires_hours", 24)
        
        alert = {
            "id": str(uuid.uuid4())[:8],
            "type": alert_type,
            "title": title,
            "message": message,
            "action_url": action_url,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
            "read": False
        }
        
        if "alerts" not in self.state:
            self.state["alerts"] = []
        self.state["alerts"].append(alert)
        
        # Priority alerts go to main messages too
        if alert_type in ["urgent", "warning"]:
            if "messages" not in self.state:
                self.state["messages"] = []
            self.state["messages"].append({
                "content": f"⚠️ {title}: {message}",
                "message_type": alert_type,
                "priority": 1 if alert_type == "urgent" else 2
            })
        
        return {
            "created": True,
            "alert_id": alert["id"],
            "type": alert_type,
            "will_expire": alert["expires_at"]
        }
    
    async def _analyze_spending_pattern(self, args: Dict) -> Dict[str, Any]:
        """Deep analysis of spending patterns."""
        category = args.get("category", "all")
        comparison_days = args.get("comparison_days", 7)
        
        expense_history = self.state.get("expense_history", [])
        
        # Current period spending
        current_total = 0
        current_by_cat = {}
        
        # Comparison period
        comparison_total = 0
        comparison_by_cat = {}
        
        now = datetime.now()
        for exp in expense_history:
            exp_date = exp.get("date")
            if isinstance(exp_date, str):
                try:
                    exp_date = datetime.fromisoformat(exp_date.replace("Z", ""))
                except:
                    continue
            
            cat = exp.get("category", "other")
            amount = exp.get("amount", 0)
            
            if category != "all" and cat != category:
                continue
            
            days_ago = (now - exp_date).days if exp_date else 999
            
            if days_ago < comparison_days:
                current_total += amount
                current_by_cat[cat] = current_by_cat.get(cat, 0) + amount
            elif days_ago < comparison_days * 2:
                comparison_total += amount
                comparison_by_cat[cat] = comparison_by_cat.get(cat, 0) + amount
        
        # Calculate changes
        change_pct = 0
        if comparison_total > 0:
            change_pct = ((current_total - comparison_total) / comparison_total) * 100
        
        # Find anomalies
        anomalies = []
        for cat, amount in current_by_cat.items():
            prev = comparison_by_cat.get(cat, 0)
            if prev > 0 and amount > prev * 1.5:
                anomalies.append({
                    "category": cat,
                    "current": amount,
                    "previous": prev,
                    "increase_pct": round(((amount - prev) / prev) * 100)
                })
        
        return {
            "period_days": comparison_days,
            "current_spend": current_total,
            "previous_spend": comparison_total,
            "change_percent": round(change_pct, 1),
            "trend": "up" if change_pct > 10 else ("down" if change_pct < -10 else "stable"),
            "by_category": current_by_cat,
            "anomalies": anomalies,
            "insight": f"{'Spending badh gaya hai!' if change_pct > 20 else 'Spending control mein hai'}"
        }
    
    async def _calculate_goal_trajectory(self, args: Dict) -> Dict[str, Any]:
        """Calculate goal progress and what's needed."""
        goal_name = args.get("goal_name", "all")
        
        goals = self.state.get("goals", [])
        results = []
        
        for goal in goals:
            if goal_name != "all" and goal.get("name") != goal_name:
                continue
            
            target = goal.get("target_amount", 0)
            current = goal.get("current_amount", 0)
            target_date_str = goal.get("target_date")
            
            remaining = target - current
            progress_pct = (current / target * 100) if target > 0 else 0
            
            # Calculate days remaining
            days_remaining = 30  # default
            if target_date_str:
                try:
                    target_date = datetime.fromisoformat(target_date_str.replace("Z", ""))
                    days_remaining = (target_date - datetime.now()).days
                except:
                    pass
            
            # Calculate required daily savings
            daily_needed = remaining / max(days_remaining, 1)
            weekly_needed = daily_needed * 7
            
            # Is it achievable?
            income_patterns = self.state.get("income_patterns", {})
            avg_daily_income = income_patterns.get("weekday_average", 500)
            
            achievable = daily_needed < (avg_daily_income * 0.3)  # Can save 30% of income
            
            results.append({
                "name": goal.get("name"),
                "target": target,
                "current": current,
                "remaining": remaining,
                "progress_percent": round(progress_pct, 1),
                "days_left": days_remaining,
                "daily_savings_needed": round(daily_needed),
                "weekly_savings_needed": round(weekly_needed),
                "on_track": achievable,
                "recommendation": f"Roz ₹{round(daily_needed)} bachao" if achievable else f"Goal extend karo ya target kam karo"
            })
        
        return {
            "goals_analyzed": len(results),
            "trajectories": results,
            "all_on_track": all(r["on_track"] for r in results)
        }
    
    async def _simulate_scenario(self, args: Dict) -> Dict[str, Any]:
        """Simulate financial scenarios."""
        scenario_type = args.get("scenario_type")
        amount = args.get("amount", 0)
        days = args.get("days", 7)
        
        bucket_balances = self.state.get("bucket_balances", {})
        obligations = self.state.get("obligations", [])
        income_patterns = self.state.get("income_patterns", {})
        
        total_balance = sum(bucket_balances.values())
        avg_daily = income_patterns.get("weekday_average", 500)
        
        if scenario_type == "extra_income":
            projected_balance = total_balance + amount
            days_buffer_gained = amount / avg_daily if avg_daily > 0 else 0
            return {
                "scenario": "extra_income",
                "amount": amount,
                "current_balance": total_balance,
                "projected_balance": projected_balance,
                "buffer_days_gained": round(days_buffer_gained, 1),
                "recommendation": f"₹{amount} se emergency fund badhao ya goal complete karo"
            }
        
        elif scenario_type == "unexpected_expense":
            projected_balance = total_balance - amount
            can_cover = projected_balance >= 0
            shortfall = max(0, amount - total_balance)
            return {
                "scenario": "unexpected_expense",
                "amount": amount,
                "current_balance": total_balance,
                "projected_balance": projected_balance,
                "can_cover": can_cover,
                "shortfall": shortfall,
                "recommendation": f"{'Cover ho jayega' if can_cover else f'₹{shortfall} ka gap hai - advance lo'}"
            }
        
        elif scenario_type == "skip_work":
            income_loss = avg_daily * days
            projected_balance = total_balance - income_loss
            return {
                "scenario": "skip_work",
                "days": days,
                "income_loss": round(income_loss),
                "current_balance": total_balance,
                "projected_balance": round(projected_balance),
                "affordable": projected_balance > 0,
                "recommendation": f"{days} din chhuti se ₹{round(income_loss)} ka loss hoga"
            }
        
        elif scenario_type == "advance_repayment":
            repayment_impact = total_balance - amount
            return {
                "scenario": "advance_repayment",
                "repayment_amount": amount,
                "current_balance": total_balance,
                "after_repayment": repayment_impact,
                "safe_to_repay": repayment_impact > (avg_daily * 3),  # Keep 3 days buffer
                "recommendation": f"Repayment ke baad ₹{repayment_impact} bachega"
            }
        
        return {"error": f"Unknown scenario type: {scenario_type}"}
    
    async def _update_bucket_balance_persistent(self, args: Dict) -> Dict[str, Any]:
        """Actually update bucket balance in MongoDB."""
        bucket_name = args.get("bucket_name")
        amount = args.get("amount", 0)
        reason = args.get("reason", "")
        
        # First update in state
        if "bucket_balances" not in self.state:
            self.state["bucket_balances"] = {}
        
        current = self.state["bucket_balances"].get(bucket_name, 0)
        new_balance = current + amount
        self.state["bucket_balances"][bucket_name] = new_balance
        
        # Try to persist to MongoDB
        persisted = False
        try:
            if self.user_id:
                bucket = await Bucket.find_one({
                    "user_id": PydanticObjectId(self.user_id),
                    "name": bucket_name
                })
                if bucket:
                    bucket.current_balance += amount
                    bucket.last_allocation_at = datetime.utcnow()
                    bucket.updated_at = datetime.utcnow()
                    await bucket.save()
                    persisted = True
        except Exception as e:
            pass
        
        # Track the change
        if "bucket_changes" not in self.state:
            self.state["bucket_changes"] = []
        
        self.state["bucket_changes"].append({
            "bucket": bucket_name,
            "change": amount,
            "new_balance": new_balance,
            "reason": reason,
            "persisted": persisted,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "success": True,
            "bucket": bucket_name,
            "previous_balance": current,
            "change": amount,
            "new_balance": new_balance,
            "persisted_to_db": persisted,
            "reason": reason
        }
