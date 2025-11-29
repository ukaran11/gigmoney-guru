"""
GigMoney Guru - Chat API

Conversational AI interface for the financial coach.
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional, List
from beanie import PydanticObjectId

from app.api.auth import get_current_user
from app.models.user import User
from app.models.chat import ChatMessage
from app.llm.client import LLMClient, get_llm_client
from app.orchestrator.state import load_financial_context
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ChatRequest(BaseModel):
    """Chat request."""
    message: str = Field(..., min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    """Chat response."""
    message: str
    message_type: str = "coaching"
    context: Optional[Dict[str, Any]] = None


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message")
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """Send a message to the AI financial coach."""
    user_id = str(current_user.id)
    user_oid = PydanticObjectId(user_id)
    
    # Save user message
    user_message = ChatMessage(
        user_id=user_oid,
        role="user",
        content=request.message,
        message_type="user_query",
    )
    await user_message.save()
    
    # Load financial context for personalized response
    context = await load_financial_context(user_id, datetime.now().date())
    
    # Get recent chat history
    recent_messages = await ChatMessage.find(
        ChatMessage.user_id == user_oid
    ).sort("-created_at").limit(10).to_list()
    
    # Build conversation history
    history = []
    for msg in reversed(recent_messages[:-1]):  # Exclude current message
        history.append({"role": msg.role, "content": msg.content})
    
    # Build system prompt with financial context
    # Calculate 7-day income from history
    total_income_7d = sum(e['amount'] for e in context.get('income_history', []))
    active_goals = context.get('goals', [])
    
    system_prompt = f"""You are GigMoney Guru, a friendly bilingual (English/Hinglish) AI financial coach 
for gig workers in India. You help users manage irregular income, save smartly, and avoid debt traps.

Current user context:
- Name: {current_user.name}
- Preferred language: {current_user.preferred_language}
- Total income (30 days): ₹{total_income_7d}
- Current buckets: {context.get('bucket_balances', {})}
- Active goals: {len(active_goals)}
- Total balance: ₹{context.get('total_balance', 0)}

Your personality:
- Warm and encouraging, like a supportive friend
- Use simple language, mix Hindi phrases naturally if user prefers Hinglish
- Give specific, actionable advice based on their actual numbers
- Be concise but helpful
- Use emojis sparingly but effectively 🎯

Guidelines:
- If asked about budgeting, refer to their bucket system (Essentials, Flex, Goals, Emergency)
- If they seem stressed about money, be empathetic and offer practical steps
- Explain concepts simply, avoid financial jargon
- Always tie advice back to their specific situation
"""

    # Generate AI response
    try:
        llm_client = get_llm_client()
        ai_response = await llm_client.generate_text(
            prompt=request.message,
            system_prompt=system_prompt,
            temperature=0.7,
        )
    except Exception as e:
        print(f"Chat LLM Error: {e}")
        ai_response = "I'm having trouble right now. Please try again in a moment!"
    
    # Determine message type based on content
    message_type = "coaching"
    if any(word in request.message.lower() for word in ["advance", "loan", "borrow"]):
        message_type = "advance_info"
    elif any(word in request.message.lower() for word in ["goal", "save", "saving"]):
        message_type = "goal_update"
    elif any(word in request.message.lower() for word in ["bill", "rent", "due", "payment"]):
        message_type = "warning"
    
    # Save AI response
    ai_message = ChatMessage(
        user_id=user_oid,
        role="assistant",
        content=ai_response,
        message_type=message_type,
    )
    await ai_message.save()
    
    return ChatResponse(
        message=ai_response,
        message_type=message_type,
        context={
            "total_balance": context.get('total_balance', 0),
            "has_advances": len(context.get('active_advances', [])) > 0,
        }
    )


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    before: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get chat history for the user."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    query = ChatMessage.find(ChatMessage.user_id == user_oid)
    
    if before:
        try:
            before_date = datetime.fromisoformat(before)
            query = query.find(ChatMessage.created_at < before_date)
        except ValueError:
            pass
    
    messages = await query.sort("-created_at").limit(limit).to_list()
    
    return {
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "message_type": m.message_type,
                "created_at": m.created_at.isoformat(),
            }
            for m in reversed(messages)  # Return in chronological order
        ]
    }


@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user)
):
    """Clear all chat history for the user."""
    user_oid = PydanticObjectId(str(current_user.id))
    
    result = await ChatMessage.find(
        ChatMessage.user_id == user_oid
    ).delete()
    
    return {
        "success": True,
        "message": "Chat history cleared",
    }


@router.post("/quick-action")
async def quick_action(
    action: str,
    current_user: User = Depends(get_current_user)
):
    """Handle quick action buttons from the UI."""
    user_id = str(current_user.id)
    context = await load_financial_context(user_id, datetime.now().date())
    
    # Extract values from context dict
    bucket_balances = context.get('bucket_balances', {})
    goals = context.get('goals', [])
    obligations = context.get('obligations', [])
    active_advances = context.get('active_advances', [])
    total_balance = context.get('total_balance', 0)
    
    responses = {
        "check_status": f"""Here's your financial snapshot:
💰 Total Balance: ₹{total_balance}
📊 Buckets: {len(bucket_balances)} active
🎯 Active Goals: {len(goals)}
{'⚠️ Watch out: You have ' + str(len(obligations)) + ' obligations!' if obligations else '✅ No urgent obligations.'}""",

        "get_advice": f"""Based on your current situation:
{'📈 Great job managing your finances!' if total_balance > 5000 else '📉 Consider building more buffer.'}
💡 Tip: Keep tracking your income daily for better insights.
Keep using GigMoney Guru to stay on top of things!""",

        "check_advance": f"""Micro-Advance Status:
{'⚠️ You have ' + str(len(active_advances)) + ' active advance(s).' if active_advances else '✅ No active advances.'}
Fee: Just 1% (that's ₹10 on ₹1000)""",

        "view_goals": "\n".join([
            f"🎯 {g['name']}: ₹{g['current_amount']}/₹{g['target_amount']} ({int(g['current_amount']/g['target_amount']*100) if g['target_amount'] > 0 else 0}%)"
            for g in goals
        ]) if goals else "No active goals yet. Want to set one? 🎯",
    }
    
    response = responses.get(action, "I didn't understand that action. Try asking me directly!")
    
    return {
        "message": response,
        "action": action,
    }
