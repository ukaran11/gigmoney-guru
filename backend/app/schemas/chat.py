"""
GigMoney Guru - Chat Schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class QuickReplyButton(BaseModel):
    """Quick reply button for chat."""
    text: str
    action: str
    payload: Optional[dict] = None


class ChatMessageCreate(BaseModel):
    """Send message request."""
    content: str = Field(..., min_length=1, max_length=1000)
    action: Optional[str] = None  # For quick reply actions
    payload: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "What if I work more this weekend?"
            }
        }


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    id: str
    role: str  # "user", "guru", "system"
    content: str
    message_type: str  # "text", "alert", "offer", "summary"
    quick_replies: List[QuickReplyButton] = []
    related_to: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history response."""
    messages: List[ChatMessageResponse]
    has_more: bool = False
    next_cursor: Optional[str] = None
