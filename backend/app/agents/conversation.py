"""
GigMoney Guru - Conversation Agent

Generates friendly, bilingual (Hinglish) messages using LLM:
- Daily summaries
- Warnings
- Advance offers
- Goal updates
"""
from typing import Dict, Any, List
from datetime import datetime, date
from app.llm.client import get_llm_client
from app.llm.prompts import PromptTemplates


class ConversationAgent:
    """
    Agent that generates natural language messages using LLM.
    
    Input:
        - Full context from previous agents
        
    Output:
        - messages: List of messages for the chat UI
    """
    
    def __init__(self):
        self.name = "conversation"
        self.prompts = PromptTemplates()
    
    async def run_async(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate conversation messages (async version for LLM calls).
        """
        llm = get_llm_client()
        messages = []
        
        # Get context
        user_name = state.get("user_name", "")
        run_date = state.get("run_date", datetime.now().date().isoformat())
        today_income = state.get("today_income", 0)
        today_allocation = state.get("today_allocation", {})
        obligation_risks = state.get("obligation_risks", [])
        advance_proposal = state.get("advance_proposal", {})
        goal_scenarios = state.get("goal_scenarios", [])
        warnings = state.get("warnings", [])
        
        # 1. Generate daily summary
        if today_income > 0 or today_allocation:
            summary_msg = await self._generate_daily_summary(
                llm, user_name, run_date, today_income, 
                today_allocation, obligation_risks, warnings
            )
            messages.append(summary_msg)
        
        # 2. Generate warning if any high-risk obligations
        high_risk = [r for r in obligation_risks if r.get("risk_level") == "high"]
        if high_risk:
            warning_msg = await self._generate_warning(llm, high_risk[0])
            messages.append(warning_msg)
        
        # 3. Generate advance offer if needed
        if advance_proposal.get("needed"):
            offer_msg = await self._generate_advance_offer(llm, advance_proposal)
            messages.append(offer_msg)
        
        # 4. Generate goal updates for goals with significant progress
        for goal in goal_scenarios:
            if goal.get("progress_percentage", 0) > 0:
                goal_msg = await self._generate_goal_update(llm, goal)
                messages.append(goal_msg)
                break  # Only one goal update per day
        
        state["messages"] = messages
        
        return state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync version with fallback messages (when LLM not available).
        """
        messages = []
        
        # Get context
        user_name = state.get("user_name", "")
        today_income = state.get("today_income", 0)
        today_allocation = state.get("today_allocation", {})
        obligation_risks = state.get("obligation_risks", [])
        advance_proposal = state.get("advance_proposal", {})
        
        # Generate fallback messages
        if today_income > 0:
            safe_to_spend = today_allocation.get("safe_to_spend", 0)
            allocations = today_allocation.get("allocations", [])
            alloc_summary = ", ".join([
                f"{a['icon']} ₹{a['amount']:.0f}" 
                for a in allocations[:3]
            ])
            
            messages.append({
                "content": (
                    f"Aaj ka update, {user_name}! 💰 "
                    f"₹{today_income:.0f} kamaya. "
                    f"Allocations: {alloc_summary}. "
                    f"Safe to spend: ₹{safe_to_spend:.0f}."
                ),
                "message_type": "summary",
                "quick_replies": PromptTemplates.QUICK_REPLIES_DAILY,
                "priority": 1,
            })
        
        # Warning for high risk
        high_risk = [r for r in obligation_risks if r.get("risk_level") == "high"]
        if high_risk:
            risk = high_risk[0]
            messages.append({
                "content": (
                    f"⚠️ Heads up! {risk.get('obligation_name')} "
                    f"{risk.get('days_until_due')} din mein due hai. "
                    f"₹{risk.get('shortfall_amount', 0):.0f} ki kami ho sakti hai."
                ),
                "message_type": "alert",
                "quick_replies": PromptTemplates.QUICK_REPLIES_WARNING,
                "priority": 2,
            })
        
        # Advance offer
        if advance_proposal.get("needed"):
            messages.append({
                "content": (
                    f"💡 Suggestion: ₹{advance_proposal.get('principal', 0):.0f} "
                    f"ka advance le lo {advance_proposal.get('obligation_name')} ke liye. "
                    f"No hidden fees, {advance_proposal.get('repayment_date')} ko auto-repay."
                ),
                "message_type": "offer",
                "quick_replies": PromptTemplates.QUICK_REPLIES_ADVANCE,
                "priority": 3,
            })
        
        state["messages"] = messages
        
        return state
    
    async def _generate_daily_summary(
        self, llm, user_name, run_date, today_income, 
        today_allocation, obligation_risks, warnings
    ) -> Dict[str, Any]:
        """Generate daily summary message."""
        allocations = today_allocation.get("allocations", [])
        alloc_str = ", ".join([
            f"{a.get('bucket_name', '')}: ₹{a.get('amount', 0):.0f}"
            for a in allocations
        ])
        
        upcoming = [
            f"{r.get('obligation_name')} ({r.get('days_until_due')} days)"
            for r in obligation_risks[:3]
        ]
        
        prompt = PromptTemplates.DAILY_SUMMARY.format(
            user_name=user_name,
            date=run_date,
            today_earnings=today_income,
            earnings_breakdown="Today's earnings",
            allocations=alloc_str,
            safe_to_spend=today_allocation.get("safe_to_spend", 0),
            upcoming_obligations=", ".join(upcoming) if upcoming else "None this week",
            warnings="; ".join(warnings) if warnings else "None"
        )
        
        try:
            content = await llm.generate_text(
                prompt,
                system_prompt=PromptTemplates.SYSTEM_CONVERSATION,
                temperature=0.7
            )
        except:
            content = f"Aaj ₹{today_income:.0f} kamaya! Safe to spend: ₹{today_allocation.get('safe_to_spend', 0):.0f}"
        
        return {
            "content": content,
            "message_type": "summary",
            "quick_replies": PromptTemplates.QUICK_REPLIES_DAILY,
            "priority": 1,
        }
    
    async def _generate_warning(self, llm, risk: Dict) -> Dict[str, Any]:
        """Generate warning message."""
        prompt = PromptTemplates.WARNING_MESSAGE.format(
            warning_type="shortfall",
            obligation_name=risk.get("obligation_name", "payment"),
            amount_needed=risk.get("amount", 0),
            current_balance=risk.get("current_bucket_balance", 0),
            shortfall=risk.get("shortfall_amount", 0),
            days_until_due=risk.get("days_until_due", 0),
            suggested_action="Consider working extra hours or a micro-advance"
        )
        
        try:
            content = await llm.generate_text(
                prompt,
                system_prompt=PromptTemplates.SYSTEM_CONVERSATION,
                temperature=0.6
            )
        except:
            content = f"⚠️ {risk.get('obligation_name')} mein ₹{risk.get('shortfall_amount', 0):.0f} ki kami ho sakti hai."
        
        return {
            "content": content,
            "message_type": "alert",
            "quick_replies": PromptTemplates.QUICK_REPLIES_WARNING,
            "priority": 2,
        }
    
    async def _generate_advance_offer(self, llm, proposal: Dict) -> Dict[str, Any]:
        """Generate advance offer message."""
        prompt = PromptTemplates.ADVANCE_OFFER.format(
            purpose=proposal.get("purpose", "shortfall"),
            obligation_name=proposal.get("obligation_name", "payment"),
            principal=proposal.get("principal", 0),
            repayment_date=proposal.get("repayment_date", "this weekend"),
            repayment_source=proposal.get("repayment_source", "weekend earnings"),
            risk_level=proposal.get("risk_score", "low"),
            impact_explanation=proposal.get("impact_explanation", "")
        )
        
        try:
            content = await llm.generate_text(
                prompt,
                system_prompt=PromptTemplates.SYSTEM_CONVERSATION,
                temperature=0.6
            )
        except:
            content = (
                f"💡 ₹{proposal.get('principal', 0):.0f} ka advance available hai. "
                f"No hidden fees, {proposal.get('repayment_date')} ko repay."
            )
        
        return {
            "content": content,
            "message_type": "offer",
            "quick_replies": PromptTemplates.QUICK_REPLIES_ADVANCE,
            "priority": 3,
        }
    
    async def _generate_goal_update(self, llm, goal: Dict) -> Dict[str, Any]:
        """Generate goal progress message."""
        prompt = PromptTemplates.GOAL_PROGRESS.format(
            goal_name=goal.get("goal_name", "Goal"),
            target_amount=goal.get("target_amount", 0),
            current_amount=goal.get("current_amount", 0),
            progress_percentage=goal.get("progress_percentage", 0),
            target_date=goal.get("target_date", "No target date"),
            on_track="Yes" if goal.get("on_track") else "Needs attention"
        )
        
        try:
            content = await llm.generate_text(
                prompt,
                system_prompt=PromptTemplates.SYSTEM_CONVERSATION,
                temperature=0.7
            )
        except:
            content = (
                f"🎯 {goal.get('goal_name')}: "
                f"{goal.get('progress_percentage', 0):.0f}% complete! "
                f"₹{goal.get('remaining_amount', 0):.0f} baaki hai."
            )
        
        return {
            "content": content,
            "message_type": "text",
            "quick_replies": PromptTemplates.QUICK_REPLIES_GOAL,
            "priority": 5,
        }


# Function for LangGraph node
def conversation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node wrapper for Conversation Agent."""
    agent = ConversationAgent()
    return agent.run(state)


async def conversation_node_async(state: Dict[str, Any]) -> Dict[str, Any]:
    """Async LangGraph node wrapper for Conversation Agent."""
    agent = ConversationAgent()
    return await agent.run_async(state)
