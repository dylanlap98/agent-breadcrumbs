"""
Data models for trace events
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import uuid
import json


@dataclass
class ToolCall:
    """Represents a tool/function call"""

    name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "arguments": self.arguments, "call_id": self.call_id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCall":
        return cls(
            name=data["name"], arguments=data["arguments"], call_id=data.get("call_id")
        )


@dataclass
class ToolResponse:
    """Represents a tool/function response"""

    call_id: Optional[str]
    name: str
    content: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "name": self.name,
            "content": self.content,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolResponse":
        return cls(
            call_id=data.get("call_id"),
            name=data["name"],
            content=data["content"],
            error=data.get("error"),
        )


@dataclass
class TokenUsage:
    """Token usage information"""

    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenUsage":
        return cls(
            prompt_tokens=data.get("prompt_tokens"),
            completion_tokens=data.get("completion_tokens"),
            total_tokens=data.get("total_tokens"),
        )


@dataclass
class TraceEvent:
    """
    A single trace event representing one LLM interaction
    """

    # Identifiers
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Action details
    action_type: str = "llm_call"  # llm_call, tool_use, etc.

    # Content
    user_input: Optional[str] = None
    system_prompt: Optional[str] = None
    ai_response: Optional[str] = None

    # Tool interactions
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_responses: List[ToolResponse] = field(default_factory=list)

    # LLM details
    model_name: Optional[str] = None
    provider: Optional[str] = None

    # Usage metrics
    token_usage: Optional[TokenUsage] = None
    cost_usd: Optional[float] = None
    duration_ms: Optional[float] = None

    # Raw data for debugging
    raw_request: Optional[Dict[str, Any]] = None
    raw_response: Optional[Dict[str, Any]] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "action_id": self.action_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type,
            "user_input": self.user_input,
            "system_prompt": self.system_prompt,
            "ai_response": self.ai_response,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "tool_responses": [tr.to_dict() for tr in self.tool_responses],
            "model_name": self.model_name,
            "provider": self.provider,
            "token_usage": self.token_usage.to_dict() if self.token_usage else None,
            "cost_usd": self.cost_usd,
            "duration_ms": self.duration_ms,
            "raw_request": self.raw_request,
            "raw_response": self.raw_response,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceEvent":
        """Create from dictionary"""
        # Parse timestamp
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.utcnow()

        # Parse tool calls
        tool_calls = []
        if data.get("tool_calls"):
            tool_calls = [ToolCall.from_dict(tc) for tc in data["tool_calls"]]

        # Parse tool responses
        tool_responses = []
        if data.get("tool_responses"):
            tool_responses = [
                ToolResponse.from_dict(tr) for tr in data["tool_responses"]
            ]

        # Parse token usage
        token_usage = None
        if data.get("token_usage"):
            token_usage = TokenUsage.from_dict(data["token_usage"])

        return cls(
            action_id=data.get("action_id", str(uuid.uuid4())),
            session_id=data.get("session_id", ""),
            timestamp=timestamp,
            action_type=data.get("action_type", "llm_call"),
            user_input=data.get("user_input"),
            system_prompt=data.get("system_prompt"),
            ai_response=data.get("ai_response"),
            tool_calls=tool_calls,
            tool_responses=tool_responses,
            model_name=data.get("model_name"),
            provider=data.get("provider"),
            token_usage=token_usage,
            cost_usd=data.get("cost_usd"),
            duration_ms=data.get("duration_ms"),
            raw_request=data.get("raw_request"),
            raw_response=data.get("raw_response"),
            metadata=data.get("metadata", {}),
        )

    def to_csv_row(self) -> Dict[str, Any]:
        """Convert to CSV-compatible row (matches existing format)"""
        # Serialize complex fields to JSON strings
        input_data = {}
        if self.user_input:
            input_data["prompt"] = self.user_input
        if self.system_prompt:
            input_data["system"] = self.system_prompt
        if self.tool_responses:
            input_data["tool_responses"] = [tr.content for tr in self.tool_responses]

        output_data = {}
        if self.ai_response:
            output_data["response"] = self.ai_response
        if self.tool_calls:
            # Format tool calls in the expected format
            tool_call_str = ", ".join(
                [
                    f"{tc.name}({', '.join([f'{k}={v}' for k, v in tc.arguments.items()])})"
                    for tc in self.tool_calls
                ]
            )
            output_data["response"] = (
                f"🔧 Decided to call tool{'s' if len(self.tool_calls) > 1 else ''}: {tool_call_str}"
            )

        return {
            "action_id": self.action_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type,
            "input_data": json.dumps(input_data),
            "output_data": json.dumps(output_data),
            "model_name": self.model_name or "",
            "prompt_tokens": self.token_usage.prompt_tokens
            if self.token_usage
            else None,
            "completion_tokens": self.token_usage.completion_tokens
            if self.token_usage
            else None,
            "total_tokens": self.token_usage.total_tokens if self.token_usage else None,
            "cost_usd": self.cost_usd,
            "duration_ms": self.duration_ms,
            "metadata": json.dumps(self.metadata),
        }
