from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class AgentAction(BaseModel):
    """Schema for logging agent actions"""

    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action_type: str  # "llm_call", "tool_use", "reasoning", "response"
    input_data: str  # JSON string for CSV compatibility
    output_data: str  # JSON string for CSV compatibility
    token_count: Optional[int] = None
    model_name: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: str = "{}"  # JSON string for additional info

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
