"""
GigMoney Guru - Enhanced ReAct Agent with TRUE Agentic Capabilities

Implements advanced agentic patterns:
1. PLANNING - Generate multi-step plans before execution, revise as needed
2. SELF-REFLECTION - Validate actions succeeded, retry or adjust if not
3. AGENT DEBATE - Multiple perspectives before final decision
4. LEARNING - Track outcomes and adjust behavior based on what worked

This is a more sophisticated version of the ReAct agent.
"""
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
from datetime import datetime, timedelta
from beanie import PydanticObjectId
from app.config import settings
from app.agents.tools import AGENT_TOOLS, ToolExecutor
import json

# Import for learning/feedback
from app.models.decision import AgentDecision


# ============================================================================
# PHASE 1: PLANNING PROMPTS
# ============================================================================

PLANNER_SYSTEM_PROMPT = """You are a PLANNING agent for GigMoney Guru. Your job is to create a multi-step plan BEFORE taking any actions.

Given the user's financial situation, create a structured plan with:
1. What data needs to be gathered
2. What analysis needs to be done
3. What actions might be needed
4. What the expected outcomes are

You must output a JSON plan with this structure:
{{
  "situation_summary": "Brief assessment of current state",
  "goals": ["Goal 1", "Goal 2"],
  "steps": [
    {{
      "step_id": 1,
      "action": "get_bucket_balances",
      "purpose": "Understand current savings distribution",
      "expected_outcome": "Map of bucket balances",
      "contingency": "If all buckets empty, flag critical risk"
    }},
    ...
  ],
  "success_criteria": "How we know the analysis is complete",
  "risks": ["Risk 1 to watch for", "Risk 2"]
}}

Create 6-10 steps. Be specific about contingencies (what to do if something unexpected happens).
"""

PLAN_REVISION_PROMPT = """Based on execution so far, should the plan be revised?

Current Plan: {plan}
Steps Completed: {completed_steps}
Results So Far: {results}
Unexpected Findings: {unexpected}

If revision needed, output:
{{
  "needs_revision": true,
  "reason": "Why revision is needed",
  "revised_steps": [...new remaining steps...],
  "new_risks": ["newly identified risks"]
}}

If no revision needed:
{{
  "needs_revision": false,
  "continue_with": "step_id to continue with"
}}
"""


# ============================================================================
# PHASE 2: SELF-REFLECTION PROMPTS
# ============================================================================

REFLECTION_PROMPT = """You just executed an action. Reflect on whether it succeeded.

Action Taken: {action}
Arguments: {arguments}
Result: {result}
Expected Outcome: {expected}

Analyze:
1. Did the action succeed? (true/false)
2. Did we get the expected outcome?
3. Any surprises or anomalies?
4. Should we retry or take corrective action?

Output JSON:
{{
  "success": true/false,
  "outcome_matched": true/false,
  "anomalies": ["any unexpected findings"],
  "corrective_action": null or {{"action": "tool_name", "reason": "why"}},
  "learnings": ["what we learned from this"],
  "confidence": 0.0-1.0
}}
"""


# ============================================================================
# PHASE 3: DEBATE/NEGOTIATION PROMPTS  
# ============================================================================

DEBATE_PERSPECTIVES = [
    {
        "name": "Conservative Advisor",
        "persona": "You prioritize safety and avoiding risk. You prefer saving over spending, building emergency funds, and being cautious about advances.",
        "bias": "risk_averse"
    },
    {
        "name": "Growth Advisor", 
        "persona": "You focus on opportunity and growth. You look for ways to increase income, invest in goals, and take calculated risks for better outcomes.",
        "bias": "opportunity_seeking"
    },
    {
        "name": "Practical Advisor",
        "persona": "You focus on what's realistic for a gig worker. You understand irregular income, immediate needs, and balance short-term survival with long-term goals.",
        "bias": "pragmatic"
    }
]

DEBATE_PROMPT = """You are the {perspective_name}. {persona}

Given this financial situation:
{situation}

And this proposed recommendation:
{recommendation}

Provide your perspective as JSON:
{{
  "agreement_level": 0-100,
  "support_points": ["why you agree"],
  "concerns": ["your concerns or objections"],
  "alternative_suggestion": "your alternative if you disagree",
  "priority_adjustment": "what should be prioritized differently"
}}
"""

SYNTHESIS_PROMPT = """You are the FINAL DECISION MAKER. Multiple advisors have debated.

Original Recommendation: {original}

Advisor Perspectives:
{perspectives}

Synthesize the best decision:
1. What points of agreement exist?
2. What concerns are valid?
3. What's the final recommendation?

Output as JSON:
{{
  "final_recommendation": "the synthesized recommendation",
  "incorporated_from": ["which advisor perspectives were included"],
  "rejected_concerns": [{{"concern": "...", "reason": "why rejected"}}],
  "confidence": 0.0-1.0,
  "key_insight": "Final insight in Hinglish for user"
}}
"""


# ============================================================================
# PHASE 4: LEARNING PROMPTS
# ============================================================================

LEARNING_PROMPT = """Analyze past decisions and their outcomes to improve future behavior.

Past Decisions:
{past_decisions}

Outcomes (if known):
{outcomes}

Current Situation:
{current_situation}

Learn from history:
{{
  "patterns_detected": ["pattern 1", "pattern 2"],
  "successful_strategies": ["what worked before"],
  "failed_strategies": ["what didn't work"],
  "adjusted_behavior": "how to behave differently based on learnings",
  "confidence_adjustment": "increase/decrease confidence in certain recommendations"
}}
"""


# ============================================================================
# ENHANCED REACT AGENT
# ============================================================================

class EnhancedReActAgent:
    """
    Enhanced ReAct Agent with:
    - Multi-step planning with revision
    - Self-reflection after each action
    - Multi-perspective debate before final decisions
    - Learning from past outcomes
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.max_iterations = 20
        self.min_tool_calls = 5
        self.enable_planning = True
        self.enable_reflection = True
        self.enable_debate = True
        self.enable_learning = True
    
    async def run(self, state: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the enhanced agentic pipeline.
        """
        tool_executor = ToolExecutor(state, user_id=user_id)
        
        # Initialize tracking
        state["agentic_features"] = {
            "planning": self.enable_planning,
            "reflection": self.enable_reflection,
            "debate": self.enable_debate,
            "learning": self.enable_learning
        }
        
        # =====================================================================
        # PHASE 0: LEARNING FROM PAST
        # =====================================================================
        learnings = None
        if self.enable_learning and user_id:
            learnings = await self._learn_from_past(user_id, state)
            state["learnings"] = learnings
        
        # =====================================================================
        # PHASE 1: PLANNING
        # =====================================================================
        plan = None
        if self.enable_planning:
            plan = await self._create_plan(state, learnings)
            state["execution_plan"] = plan
        
        # =====================================================================
        # PHASE 2: EXECUTION WITH REFLECTION
        # =====================================================================
        execution_results = await self._execute_with_reflection(
            state, tool_executor, plan, user_id
        )
        
        # =====================================================================
        # PHASE 3: DEBATE BEFORE FINAL DECISION
        # =====================================================================
        if self.enable_debate and execution_results.get("proposed_recommendation"):
            debate_result = await self._run_debate(
                state, 
                execution_results["proposed_recommendation"]
            )
            state["debate_result"] = debate_result
            
            # Use synthesized recommendation
            if debate_result.get("final_recommendation"):
                state["key_insight"] = debate_result.get("key_insight", state.get("key_insight"))
                state["recommended_action"] = debate_result["final_recommendation"]
                state["confidence_score"] = int(debate_result.get("confidence", 0.7) * 100)
        
        # =====================================================================
        # PHASE 4: SAVE LEARNINGS FOR FUTURE
        # =====================================================================
        if self.enable_learning and user_id:
            await self._save_execution_learnings(user_id, state, execution_results)
        
        return state
    
    # =========================================================================
    # PLANNING METHODS
    # =========================================================================
    
    async def _create_plan(self, state: Dict[str, Any], learnings: Optional[Dict] = None) -> Dict:
        """Create a multi-step execution plan."""
        context = self._build_planning_context(state, learnings)
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            plan = json.loads(response.choices[0].message.content)
            plan["created_at"] = datetime.now().isoformat()
            plan["revision_count"] = 0
            return plan
            
        except Exception as e:
            return {
                "error": str(e),
                "steps": self._default_plan_steps(),
                "revision_count": 0
            }
    
    async def _revise_plan_if_needed(
        self, 
        plan: Dict, 
        completed_steps: List[Dict],
        results: Dict,
        unexpected: List[str]
    ) -> Dict:
        """Check if plan needs revision based on execution results."""
        if not unexpected:
            return {"needs_revision": False}
        
        prompt = PLAN_REVISION_PROMPT.format(
            plan=json.dumps(plan, indent=2),
            completed_steps=json.dumps(completed_steps, indent=2),
            results=json.dumps(results, indent=2),
            unexpected=json.dumps(unexpected)
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a plan revision expert. Analyze and revise if needed."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            return {"needs_revision": False}
    
    def _build_planning_context(self, state: Dict, learnings: Optional[Dict]) -> str:
        """Build context for planning."""
        today_income = state.get("today_income", 0)
        bucket_balances = state.get("bucket_balances", {})
        obligations = state.get("obligations", [])
        
        context = f"""
Financial Situation:
- Today's Income: ₹{today_income}
- Bucket Balances: {json.dumps(bucket_balances)}
- Obligations: {len(obligations)} bills tracked
- Date: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        if learnings:
            context += f"""
Past Learnings:
- Patterns: {learnings.get('patterns_detected', [])}
- Successful Strategies: {learnings.get('successful_strategies', [])}
- Adjusted Behavior: {learnings.get('adjusted_behavior', 'None')}
"""
        
        return context
    
    def _default_plan_steps(self) -> List[Dict]:
        """Default plan if planning fails."""
        return [
            {"step_id": 1, "action": "get_bucket_balances", "purpose": "Check savings"},
            {"step_id": 2, "action": "get_upcoming_obligations", "purpose": "Check bills"},
            {"step_id": 3, "action": "calculate_shortfall", "purpose": "Find gaps"},
            {"step_id": 4, "action": "analyze_spending_pattern", "purpose": "Check spending"},
            {"step_id": 5, "action": "set_risk_score", "purpose": "Assess risk"},
            {"step_id": 6, "action": "complete_analysis", "purpose": "Finalize"}
        ]
    
    # =========================================================================
    # EXECUTION WITH REFLECTION
    # =========================================================================
    
    async def _execute_with_reflection(
        self,
        state: Dict[str, Any],
        tool_executor: ToolExecutor,
        plan: Optional[Dict],
        user_id: Optional[str]
    ) -> Dict:
        """Execute plan with self-reflection after each action."""
        
        from app.agents.react_agent import REACT_SYSTEM_PROMPT
        
        messages = [
            {"role": "system", "content": REACT_SYSTEM_PROMPT},
            {"role": "user", "content": self._build_execution_context(state, plan)}
        ]
        
        iteration = 0
        analysis_complete = False
        tool_call_count = 0
        reasoning_chain = []
        reflections = []
        unexpected_findings = []
        completed_steps = []
        proposed_recommendation = None
        
        while iteration < self.max_iterations and not analysis_complete:
            iteration += 1
            
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=AGENT_TOOLS,
                    tool_choice="auto",
                    temperature=0.4
                )
                
                message = response.choices[0].message
                
                if message.tool_calls:
                    if message.content:
                        reasoning_chain.append({
                            "iteration": iteration,
                            "thought": message.content[:500]
                        })
                    
                    messages.append({
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })
                    
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        tool_call_count += 1
                        
                        # Execute the tool
                        result = await tool_executor.execute(tool_name, arguments)
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                        
                        # =====================================================
                        # SELF-REFLECTION after each action
                        # =====================================================
                        if self.enable_reflection:
                            expected = self._get_expected_outcome(plan, tool_name)
                            reflection = await self._reflect_on_action(
                                tool_name, arguments, result, expected
                            )
                            reflections.append(reflection)
                            
                            # Track anomalies for plan revision
                            if reflection.get("anomalies"):
                                unexpected_findings.extend(reflection["anomalies"])
                            
                            # If action failed, add corrective guidance
                            if not reflection.get("success", True):
                                corrective = reflection.get("corrective_action")
                                if corrective:
                                    messages.append({
                                        "role": "user",
                                        "content": f"Previous action had issues. Consider: {corrective.get('reason')}. You may want to {corrective.get('action')}."
                                    })
                        
                        # Track completed steps
                        completed_steps.append({
                            "tool": tool_name,
                            "result_summary": str(result)[:200]
                        })
                        
                        # Check for completion
                        if tool_name == "complete_analysis":
                            if result.get("complete"):
                                analysis_complete = True
                                proposed_recommendation = result.get("insight")
                            elif result.get("error"):
                                messages.append({
                                    "role": "user",
                                    "content": "Keep going! Need more thorough analysis."
                                })
                        
                        # Capture recommendation for debate
                        if tool_name == "complete_analysis" and result.get("insight"):
                            proposed_recommendation = result.get("insight")
                    
                    # =========================================================
                    # PLAN REVISION check after some progress
                    # =========================================================
                    if self.enable_planning and plan and tool_call_count % 3 == 0:
                        revision = await self._revise_plan_if_needed(
                            plan, completed_steps, 
                            {"latest": result}, 
                            unexpected_findings[-3:] if unexpected_findings else []
                        )
                        if revision.get("needs_revision"):
                            plan["steps"] = revision.get("revised_steps", plan["steps"])
                            plan["revision_count"] = plan.get("revision_count", 0) + 1
                            state["plan_revisions"] = plan.get("revision_count")
                
                else:
                    # No tool calls
                    if message.content:
                        state["agent_final_message"] = message.content
                        reasoning_chain.append({
                            "iteration": iteration,
                            "thought": message.content[:500]
                        })
                    
                    if not analysis_complete and tool_call_count < self.min_tool_calls:
                        messages.append({
                            "role": "user",
                            "content": f"Only {tool_call_count} tools called. Need at least 5. Continue analysis."
                        })
                    else:
                        analysis_complete = True
                        
            except Exception as e:
                state["agent_error"] = str(e)
                break
        
        # Store results
        state["tool_calls_log"] = tool_executor.tool_calls_log
        state["react_iterations"] = iteration
        state["total_tool_calls"] = tool_call_count
        state["reasoning_chain"] = reasoning_chain
        state["reflections"] = reflections
        state["unexpected_findings"] = unexpected_findings
        
        if not state.get("key_insight") and tool_call_count > 0:
            state["key_insight"] = "Analysis complete - aapka financial health check ho gaya hai."
        
        return {
            "completed_steps": completed_steps,
            "proposed_recommendation": proposed_recommendation or state.get("key_insight"),
            "reflections": reflections,
            "unexpected_findings": unexpected_findings
        }
    
    async def _reflect_on_action(
        self, 
        action: str, 
        arguments: Dict, 
        result: Dict,
        expected: str
    ) -> Dict:
        """Self-reflect on whether an action succeeded."""
        prompt = REFLECTION_PROMPT.format(
            action=action,
            arguments=json.dumps(arguments),
            result=json.dumps(result)[:500],
            expected=expected
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a self-reflection module. Analyze action outcomes honestly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            return {"success": True, "confidence": 0.5}
    
    def _get_expected_outcome(self, plan: Optional[Dict], tool_name: str) -> str:
        """Get expected outcome from plan for a tool."""
        if not plan or "steps" not in plan:
            return "Successful execution"
        
        for step in plan.get("steps", []):
            if step.get("action") == tool_name:
                return step.get("expected_outcome", "Successful execution")
        
        return "Successful execution"
    
    def _build_execution_context(self, state: Dict, plan: Optional[Dict]) -> str:
        """Build context for execution phase."""
        today_income = state.get("today_income", 0)
        bucket_balances = state.get("bucket_balances", {})
        total_balance = sum(bucket_balances.values()) if bucket_balances else 0
        
        context = f"""
## Current Situation
- Today's Income: ₹{today_income}
- Total Bucket Balance: ₹{total_balance}
- Date: {state.get('current_date', 'Today')}
"""
        
        if plan and "steps" in plan:
            context += f"""
## Your Plan (follow this!)
{json.dumps(plan['steps'], indent=2)}

## Success Criteria
{plan.get('success_criteria', 'Complete thorough analysis')}
"""
        
        if state.get("learnings"):
            context += f"""
## Learnings from Past
- Apply these learnings: {state['learnings'].get('adjusted_behavior', 'None')}
"""
        
        context += """
START executing the plan. Begin with get_bucket_balances!
"""
        return context
    
    # =========================================================================
    # DEBATE METHODS
    # =========================================================================
    
    async def _run_debate(self, state: Dict, recommendation: str) -> Dict:
        """Run multi-perspective debate on the recommendation."""
        situation = self._summarize_situation(state)
        perspectives = []
        
        # Get each advisor's perspective
        for advisor in DEBATE_PERSPECTIVES:
            perspective = await self._get_advisor_perspective(
                advisor["name"],
                advisor["persona"],
                situation,
                recommendation
            )
            perspective["advisor"] = advisor["name"]
            perspectives.append(perspective)
        
        # Synthesize final decision
        synthesis = await self._synthesize_debate(recommendation, perspectives)
        synthesis["individual_perspectives"] = perspectives
        
        return synthesis
    
    async def _get_advisor_perspective(
        self, 
        name: str, 
        persona: str, 
        situation: str,
        recommendation: str
    ) -> Dict:
        """Get one advisor's perspective."""
        prompt = DEBATE_PROMPT.format(
            perspective_name=name,
            persona=persona,
            situation=situation,
            recommendation=recommendation
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            return {"agreement_level": 70, "concerns": [], "support_points": []}
    
    async def _synthesize_debate(self, original: str, perspectives: List[Dict]) -> Dict:
        """Synthesize debate into final decision."""
        prompt = SYNTHESIS_PROMPT.format(
            original=original,
            perspectives=json.dumps(perspectives, indent=2)
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You synthesize multiple advisor perspectives into one final recommendation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except:
            return {
                "final_recommendation": original,
                "confidence": 0.6,
                "key_insight": original
            }
    
    def _summarize_situation(self, state: Dict) -> str:
        """Summarize current situation for debate."""
        return f"""
- Total Balance: ₹{sum(state.get('bucket_balances', {}).values())}
- Risk Score: {state.get('risk_score', 'Unknown')}
- Today's Income: ₹{state.get('today_income', 0)}
- Obligations: {len(state.get('obligations', []))} tracked
- Key Findings: {state.get('unexpected_findings', [])}
"""
    
    # =========================================================================
    # LEARNING METHODS
    # =========================================================================
    
    async def _learn_from_past(self, user_id: str, state: Dict) -> Dict:
        """Learn from past decisions and outcomes."""
        try:
            # Get past decisions from last 14 days
            from_date = datetime.utcnow() - timedelta(days=14)
            past_decisions = await AgentDecision.find(
                AgentDecision.user_id == PydanticObjectId(user_id),
                AgentDecision.created_at >= from_date
            ).sort("-created_at").limit(20).to_list()
            
            if not past_decisions:
                return {"patterns_detected": [], "adjusted_behavior": "No history yet"}
            
            # Format decisions for analysis
            decisions_text = "\n".join([
                f"- {d.decision_type}: {d.decision_value} (outcome: {d.output_summary.get('outcome', 'unknown')})"
                for d in past_decisions
            ])
            
            # Analyze patterns
            prompt = LEARNING_PROMPT.format(
                past_decisions=decisions_text,
                outcomes="See decision outcomes above",
                current_situation=self._summarize_situation(state)
            )
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You analyze patterns in past decisions to improve future behavior."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                "error": str(e),
                "patterns_detected": [],
                "adjusted_behavior": "Unable to analyze history"
            }
    
    async def _save_execution_learnings(
        self, 
        user_id: str, 
        state: Dict,
        execution_results: Dict
    ) -> None:
        """Save learnings from this execution for future reference."""
        try:
            # Create a learning record
            learning_decision = AgentDecision(
                user_id=PydanticObjectId(user_id),
                agent_name="enhanced_react_agent",
                run_id=f"learn_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                run_date=datetime.utcnow(),
                decision_type="execution_learning",
                decision_value=f"Completed with {state.get('total_tool_calls', 0)} tools",
                output_summary={
                    "risk_score": state.get("risk_score"),
                    "key_insight": state.get("key_insight", "")[:200],
                    "reflections_count": len(execution_results.get("reflections", [])),
                    "unexpected_findings": execution_results.get("unexpected_findings", [])[:5],
                    "debate_confidence": state.get("debate_result", {}).get("confidence"),
                    "plan_revisions": state.get("plan_revisions", 0)
                }
            )
            await learning_decision.insert()
        except Exception:
            pass  # Don't fail main execution for learning save failure


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

enhanced_react_agent = EnhancedReActAgent()


async def run_enhanced_react_agent(
    state: Dict[str, Any], 
    user_id: Optional[str] = None,
    features: Optional[Dict[str, bool]] = None
) -> Dict[str, Any]:
    """
    Run the enhanced ReAct agent with advanced agentic features.
    
    Args:
        state: Current financial state
        user_id: User ID for persistence
        features: Optional dict to enable/disable features:
            - planning: Multi-step planning (default: True)
            - reflection: Self-reflection after actions (default: True)
            - debate: Multi-perspective debate (default: True)
            - learning: Learn from past (default: True)
    """
    agent = EnhancedReActAgent()
    
    # Configure features if provided
    if features:
        agent.enable_planning = features.get("planning", True)
        agent.enable_reflection = features.get("reflection", True)
        agent.enable_debate = features.get("debate", True)
        agent.enable_learning = features.get("learning", True)
    
    return await agent.run(state, user_id=user_id)
