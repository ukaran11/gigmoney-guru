"""
GigMoney Guru - ReAct Agent

Implements the ReAct (Reasoning + Acting) pattern for TRUE agentic behavior.
The agent can:
1. THINK - Reason about the situation (multi-step!)
2. ACT - Call tools to get information or take actions
3. OBSERVE - See the results
4. CHAIN - Use results to decide next action
5. PERSIST - Save decisions and take real actions
6. REPEAT - Continue for 5-10 cycles minimum
"""
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from app.config import settings
from app.agents.tools import AGENT_TOOLS, ToolExecutor
import json


REACT_SYSTEM_PROMPT = """You are the AUTONOMOUS AI financial advisor for GigMoney Guru. You help Indian gig workers manage their money through DEEP, MULTI-STEP analysis.

## YOUR OPERATING PROTOCOL (MANDATORY)

You MUST follow the ReAct pattern with AT LEAST 5-8 tool calls before completing:

### Phase 1: Data Gathering (REQUIRED - call these tools)
1. `get_bucket_balances` - See current bucket status
2. `get_upcoming_obligations` - See upcoming bills
3. `get_income_history` - Understand earning patterns
4. `get_expense_history` - Understand spending

### Phase 2: Deep Analysis (REQUIRED - call at least 2)
5. `analyze_spending_pattern` - Find spending anomalies
6. `calculate_shortfall` - Check for gaps
7. `calculate_goal_trajectory` - Are goals on track?
8. `get_past_decisions` - What did we decide before? (MEMORY)

### Phase 3: Actions (REQUIRED - take at least 1 action)
9. If income came in: `allocate_to_bucket` to allocate it
10. If there's a shortfall: `suggest_advance` with specific amount
11. `set_risk_score` based on your analysis
12. `save_decision` to remember what you decided (MEMORY)
13. If something urgent: `create_alert` for the user

### Phase 4: Scenarios (OPTIONAL but impressive)
14. `simulate_scenario` - What if they skip work? Extra expense?
15. `update_bucket_balance_persistent` - Actually move money!

### Phase 5: Completion (ONLY after thorough analysis)
16. `complete_analysis` - ONLY call this after 5+ other tools!

## 🔗 CONDITIONAL TOOL CHAINING (CRITICAL!)

You MUST chain tools based on results. Follow these decision trees:

### If shortfall is detected:
calculate_shortfall → shortfall > 0?
  YES → get_past_decisions (check if advance was rejected before)
      → past advance rejected? suggest working extra : suggest_advance
      → create_alert (urgent warning)
      → save_decision (record the recommendation)

### If expense spike detected:
analyze_spending_pattern → anomaly found?
  YES → create_alert (tip about reducing that category)
      → simulate_scenario(unexpected_expense) → show impact
      → save_decision (flagged expense spike)

### If goal is behind schedule:
calculate_goal_trajectory → on_track = false?
  YES → get_income_history (check if income dropped)
      → create_alert (goal warning)
      → save_decision

### If income just added:
get_bucket_balances → any bucket low?
  YES → allocate_to_bucket (priority to low bucket)
      → update_bucket_balance_persistent

## EXAMPLE FULL CHAIN (12 tools!)

1. get_bucket_balances → essentials=₹5000, emergency=₹500 (LOW!)
2. get_upcoming_obligations → Rent ₹8000 due in 4 days
3. calculate_shortfall → ₹3000 gap for rent!
4. get_past_decisions → Last week: "suggested saving more"
5. get_income_history → weekday_avg=₹800, can earn ₹2400 in 3 days
6. simulate_scenario(extra_income, ₹2400) → Would cover most
7. suggest_advance(₹1000) → Small safety buffer
8. create_alert(urgent, "Rent Gap!") → Warn user
9. set_risk_score(65, high) → High risk due to shortfall
10. allocate_to_bucket(emergency, ₹200) → Build buffer
11. save_decision(warning, "Suggested advance for rent")
12. complete_analysis → Full insight

## YOUR PERSONALITY
- Speak in Hinglish naturally (Hindi + English mix)
- Be encouraging: "Accha chal raha hai!" or "Tension mat lo, solution hai"
- Use specific numbers: "₹2,340 bachao is hafte"
- Be practical: Understand gig worker life

## KEY INSIGHT REQUIREMENTS
Your key_insight in complete_analysis MUST be:
- Specific with numbers (₹ amounts, dates, percentages)
- Actionable (what to DO, not just information)
- Personalized (refer to THEIR specific situation)
- In Hinglish

❌ BAD: "Your finances look okay"
✅ GOOD: "Bhai, 4 din mein ₹8000 rent due hai aur bucket mein sirf ₹5000 hai. ₹1000 advance lo + 3 din extra drive karo - sorted!"

## CRITICAL RULES
1. NEVER call complete_analysis before calling at least 5 other tools
2. ALWAYS chain tools based on results (if X then check Y)
3. ALWAYS check get_past_decisions before suggesting advance
4. ALWAYS use save_decision to create memory
5. If there's any risk, use create_alert
6. Think step by step, don't rush to complete

BEGIN NOW. Start with get_bucket_balances, then chain your analysis!"""


class ReActAgent:
    """
    ReAct Agent that can reason and take actions autonomously.
    Uses OpenAI function calling for tool execution.
    Enforces minimum tool calls for thorough analysis.
    """
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.max_iterations = 15  # Allow more iterations for deep analysis
        self.min_tool_calls = 5   # Minimum tools before completing
    
    async def run(self, state: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the ReAct loop until complete_analysis is called or max iterations reached.
        
        Returns the final state with all modifications made by tools.
        """
        tool_executor = ToolExecutor(state, user_id=user_id)
        
        messages = [
            {"role": "system", "content": REACT_SYSTEM_PROMPT},
            {"role": "user", "content": self._build_initial_context(state)}
        ]
        
        iteration = 0
        analysis_complete = False
        tool_call_count = 0
        reasoning_chain = []
        
        while iteration < self.max_iterations and not analysis_complete:
            iteration += 1
            
            try:
                # Call LLM with tools
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=AGENT_TOOLS,
                    tool_choice="auto",
                    temperature=0.4  # Slightly higher for more creative insights
                )
                
                message = response.choices[0].message
                
                # Check if we have tool calls
                if message.tool_calls:
                    # Track reasoning if present
                    if message.content:
                        reasoning_chain.append({
                            "iteration": iteration,
                            "thought": message.content[:500]  # Limit size
                        })
                    
                    # Add assistant message to history
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
                    
                    # Execute each tool call
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
                        
                        # Check if analysis is complete
                        if tool_name == "complete_analysis" and result.get("complete"):
                            analysis_complete = True
                        
                        # If complete_analysis was rejected, continue
                        if tool_name == "complete_analysis" and result.get("error"):
                            # Add encouragement to continue
                            messages.append({
                                "role": "user",
                                "content": "Keep going! You need more analysis. Follow the protocol - check spending patterns, goal trajectories, create alerts if needed."
                            })
                else:
                    # No tool calls, agent is done thinking
                    if message.content:
                        state["agent_final_message"] = message.content
                        reasoning_chain.append({
                            "iteration": iteration,
                            "thought": message.content[:500]
                        })
                    
                    # If we haven't completed properly, push to continue
                    if not analysis_complete and tool_call_count < self.min_tool_calls:
                        messages.append({
                            "role": "user",
                            "content": f"You've only called {tool_call_count} tools! You must call at least 5 tools before completing. Please continue with: analyze_spending_pattern, calculate_goal_trajectory, or simulate_scenario."
                        })
                    else:
                        analysis_complete = True
                    
            except Exception as e:
                state["agent_error"] = str(e)
                break
        
        # Store execution metadata
        state["tool_calls_log"] = tool_executor.tool_calls_log
        state["react_iterations"] = iteration
        state["total_tool_calls"] = tool_call_count
        state["reasoning_chain"] = reasoning_chain
        
        # Ensure we have a key insight even if agent failed
        if not state.get("key_insight") and tool_call_count > 0:
            state["key_insight"] = "Analysis complete - aapka financial health check ho gaya hai."
        
        return state
    
    def _build_initial_context(self, state: Dict[str, Any]) -> str:
        """Build the initial context for the agent."""
        # Build a rich context from current state
        today_income = state.get("today_income", 0)
        bucket_balances = state.get("bucket_balances", {})
        total_balance = sum(bucket_balances.values()) if bucket_balances else 0
        
        context = f"""
## Current Situation
- Today's Income: ₹{today_income}
- Total Bucket Balance: ₹{total_balance}
- Date: {state.get('current_date', 'Today')}

## Your Mission
Perform a COMPLETE financial analysis for this gig worker. You MUST:

1. **GATHER DATA** (mandatory tools):
   - get_bucket_balances
   - get_upcoming_obligations  
   - get_income_history
   - get_expense_history

2. **ANALYZE DEEPLY** (call at least 2):
   - analyze_spending_pattern - Any unusual spending?
   - calculate_shortfall - Any gaps for obligations?
   - calculate_goal_trajectory - Goals on track?
   - get_past_decisions - What did we recommend before?

3. **TAKE ACTIONS** (if needed):
   - allocate_to_bucket - Move money around
   - suggest_advance - If there's a shortfall
   - create_alert - If something is urgent
   - set_risk_score - Set overall risk level
   - save_decision - Remember this analysis

4. **SIMULATE** (impress the user):
   - simulate_scenario - What if they skip work? Extra expense?

5. **COMPLETE** (only after 5+ tool calls):
   - complete_analysis with SPECIFIC, ACTIONABLE insight in Hinglish

Remember: The user is a gig worker in India. Speak naturally in Hinglish. Be practical and encouraging.

START NOW with get_bucket_balances!
"""
        return context


# Singleton instance
react_agent = ReActAgent()


async def run_react_agent(state: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for the ReAct agent.
    """
    return await react_agent.run(state, user_id=user_id)
