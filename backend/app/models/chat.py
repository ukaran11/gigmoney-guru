"""
GigMoney Guru - Chat Message Model
"""
from datetime import datetime
from typing import Optional, List
from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel


class QuickReply(BaseModel):
    """Quick reply button."""
    text: str
    action: str
    payload: Optional[dict] = None


class ChatMessage(Document):
    """Chat message in conversation thread."""
    
    user_id: PydanticObjectId = Field(...)
    
    # Message content
    role: str = Field(...)  # "user", "guru", "system"
    content: str = Field(...)
    
    # For guru messages - structured context
    message_type: str = Field(default="text")  # "text", "alert", "offer", "summary"
    
    # Quick replies for guru messages
    quick_replies: List[dict] = Field(default_factory=list)
    
    # Metadata
    related_to: Optional[str] = None  # "daily_summary", "advance_offer", "goal_update"
    agent_source: Optional[str] = None  # Which agent generated this
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    
    class Settings:
        name = "chat_messages"
        indexes = [
            "user_id",
            "created_at",
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "role": "guru",
                "content": "Aaj aapne ₹2500 kamaya! 🎉 Maine ₹400 rent ke liye set aside kar diya.",
                "message_type": "text",
                "quick_replies": [
                    {"text": "Show details", "action": "show_details"},
                    {"text": "Ok, thanks!", "action": "acknowledge"}
                ]
            }
        }
