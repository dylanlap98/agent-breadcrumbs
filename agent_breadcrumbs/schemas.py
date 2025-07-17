from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid
import logging

# Set up logger
cost_logger = logging.getLogger("agent_breadcrumbs.cost")
cost_logger.setLevel(logging.WARNING)


class TokenUsage(BaseModel):
    """Detailed token usage breakdown"""

    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

    def calculate_cost(self, model_name: str) -> Optional[float]:
        """Calculate cost in USD based on current OpenAI pricing"""
        if not self.prompt_tokens or not self.completion_tokens:
            cost_logger.warning(
                f"Cannot calculate cost for model '{model_name}': missing token counts "
                f"(prompt_tokens={self.prompt_tokens}, completion_tokens={self.completion_tokens})"
            )
            return None

        # Current OpenAI pricing (as of 2024/2025) - per 1K tokens
        pricing = {
            "gpt-4o": {"input": 0.0025, "output": 0.010},  # $2.50/$10.00 per 1M tokens
            "gpt-4o-mini": {
                "input": 0.00015,
                "output": 0.0006,
            },  # $0.15/$0.60 per 1M tokens
            "gpt-4": {"input": 0.03, "output": 0.06},  # $30/$60 per 1M tokens
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},  # $10/$30 per 1M tokens
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},  # $1/$2 per 1M tokens
            # GPT-4.1 series (2025) - Updated with correct pricing
            "gpt-4.1": {"input": 0.002, "output": 0.008},  # $2.00/$8.00 per 1M tokens
            "gpt-4.1-mini": {
                "input": 0.0004,
                "output": 0.0016,
            },  # $0.40/$1.60 per 1M tokens
            "gpt-4.1-nano": {
                "input": 0.0001,
                "output": 0.0004,
            },  # $0.10/$0.40 per 1M tokens
        }

        # Handle versioned model names (e.g., "gpt-4.1-mini-2025-04-14" -> "gpt-4.1-mini")
        # Sort by length DESC to match longest prefix first
        model_base = model_name
        for base_name in sorted(pricing.keys(), key=len, reverse=True):
            if model_name.startswith(base_name):
                model_base = base_name
                break

        # FIX: Check model_base, not model_name!
        if model_base not in pricing:
            cost_logger.warning(
                f"Model '{model_name}' not found in pricing database. "
                f"Available models: {list(pricing.keys())}. "
                f"Cost calculation skipped. Consider adding pricing data for this model."
            )
            return None

        # FIX: Use model_base for pricing lookup!
        input_cost = (self.prompt_tokens / 1000) * pricing[model_base]["input"]
        output_cost = (self.completion_tokens / 1000) * pricing[model_base]["output"]

        total_cost = input_cost + output_cost

        # Log successful calculation at debug level
        cost_logger.debug(
            f"Cost calculated for {model_name}: "
            f"${input_cost:.6f} (input) + ${output_cost:.6f} (output) = ${total_cost:.6f}"
        )

        return total_cost


class AgentAction(BaseModel):
    """Schema for logging agent actions with enhanced token tracking"""

    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action_type: str  # "llm_call", "tool_use", "reasoning", "response"
    input_data: str  # JSON string for CSV compatibility
    output_data: str  # JSON string for CSV compatibility

    token_usage: Optional[TokenUsage] = None

    token_count: Optional[int] = None

    model_name: Optional[str] = None
    duration_ms: Optional[float] = None
    cost_usd: Optional[float] = None  # Calculated cost
    metadata: str = "{}"  # JSON string for additional info

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

    def calculate_cost(self) -> Optional[float]:
        """Calculate and cache the cost for this action"""
        if self.token_usage and self.model_name:
            self.cost_usd = self.token_usage.calculate_cost(self.model_name)
        return self.cost_usd
