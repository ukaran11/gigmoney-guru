"""
GigMoney Guru - Agent Decision Model
"""
from datetime import datetime
from typing import Optional, Dict, Any
from beanie import Document, PydanticObjectId
from pydantic import Field


class AgentDecision(Document):
    """Log of agent decisions for observability and explainability."""
    
    user_id: PydanticObjectId = Field(...)
    
    # Which agent
    agent_name: str = Field(...)  # "income_pattern", "obligation_risk", etc.
    
    # Run context
    run_id: str = Field(...)  # UUID for the full agent graph run
    run_date: datetime = Field(...)  # The date being processed
    
    # Input/Output
    input_summary: Dict[str, Any] = Field(default_factory=dict)
    output_summary: Dict[str, Any] = Field(default_factory=dict)
    
    # Decision details
    decision_type: Optional[str] = None  # "allocation", "warning", "advance_offer", etc.
    decision_value: Optional[str] = None  # Brief description
    
    # For LLM agents
    prompt_used: Optional[str] = None
    llm_response: Optional[str] = None
    
    # Metrics
    execution_time_ms: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "agent_decisions"
        indexes = [
            "user_id",
            "agent_name",
            "run_id",
            "run_date",
        ]
        
    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "bucket_allocation",
                "run_id": "abc123",
                "decision_type": "allocation",
                "decision_value": "Allocated ₹500 to rent bucket"
            }
        }
