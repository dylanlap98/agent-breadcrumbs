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

    def __str__(self) -> str:
        """Human readable string representation"""
        args_str = ", ".join([f"{k}={v}" for k, v in self.arguments.items()])
        return f"{self.name}({args_str})"


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

    def __str__(self) -> str:
        """Human readable string representation"""
        if self.error:
            return f"{self.name}: ERROR - {self.error}"
        return f"{self.name}: {self.content[:100]}{'...' if len(self.content) > 100 else ''}"


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
    TraceEvent for LLM interaction
    """

    # Identifiers
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Action details
    action_type: str = "llm_call"

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

    def to_csv_row(self) -> Dict[str, Any]:
        """TARGETED FIX: Guaranteed proper CSV output with no empty fields"""

        # Build input_data structure
        input_data = {}

        if self.user_input:
            input_data["prompt"] = self.user_input

        if self.system_prompt:
            input_data["system"] = self.system_prompt

        if self.tool_responses:
            input_data["tool_responses"] = [str(tr) for tr in self.tool_responses]

        # Build output_data structure
        output_data = {}
        call_type = self.metadata.get("call_type", "UNKNOWN")

        if call_type == "INITIAL_TOOL_DECISION" and self.tool_calls:
            # This is the tool decision call
            tool_call_strs = [str(tc) for tc in self.tool_calls]
            if len(tool_call_strs) == 1:
                output_data["response"] = (
                    f"🔧 Decided to call tool: {tool_call_strs[0]}"
                )
            else:
                output_data["response"] = (
                    f"🔧 Decided to call tools: {', '.join(tool_call_strs)}"
                )
            output_data["decision_type"] = "tool_selection"

        elif call_type == "FINAL_RESPONSE" and self.ai_response:
            # This is the final response after tool execution
            output_data["response"] = self.ai_response
            output_data["response_type"] = "final_answer"
            if self.tool_responses:
                output_data["based_on_tools"] = [tr.name for tr in self.tool_responses]

        elif call_type == "DIRECT_RESPONSE" and self.ai_response:
            # Direct response without tools
            output_data["response"] = self.ai_response
            output_data["response_type"] = "direct_answer"

        elif self.ai_response:
            # Any other AI response
            output_data["response"] = self.ai_response
            output_data["response_type"] = "general"

        elif self.tool_calls:
            # Tool calls without clear context
            tool_call_strs = [str(tc) for tc in self.tool_calls]
            output_data["response"] = f"🔧 Tool calls: {', '.join(tool_call_strs)}"
            output_data["response_type"] = "tool_calls"

        elif self.tool_responses:
            # Tool responses without clear context
            output_data["tool_results"] = [str(tr) for tr in self.tool_responses]
            output_data["response_type"] = "tool_results"

        else:
            # Absolute fallback - never leave empty
            output_data["response"] = (
                f"Processing {call_type}" if call_type != "UNKNOWN" else "Processing..."
            )
            output_data["response_type"] = "processing"

        # Enhanced metadata with call type info
        enhanced_metadata = dict(self.metadata)
        enhanced_metadata["call_type"] = call_type
        if self.tool_calls:
            enhanced_metadata["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.tool_responses:
            enhanced_metadata["tool_responses"] = [
                tr.to_dict() for tr in self.tool_responses
            ]

        # Determine conversation flow based on call type
        conversation_flow = self._determine_conversation_flow_by_call_type(call_type)

        # Build the complete CSV row
        csv_row = {
            "action_id": self.action_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type,
            "input_data": json.dumps(input_data) if input_data else "{}",
            "output_data": json.dumps(output_data),  # GUARANTEED not empty
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
            "metadata": json.dumps(enhanced_metadata),
            # Enhanced fields
            "user_input": self.user_input or "",
            "ai_response": self.ai_response or "",
            "tool_calls_summary": self._format_tool_calls_summary(),
            "tool_results_summary": self._format_tool_results_summary(),
            "conversation_flow": conversation_flow,
        }

        return csv_row

    def _determine_conversation_flow_by_call_type(self, call_type: str) -> str:
        """TARGETED FIX: Determine flow based on call type"""
        if call_type == "INITIAL_TOOL_DECISION":
            return "1_TOOL_DECISION"
        elif call_type == "FINAL_RESPONSE":
            return "3_FINAL_RESPONSE"
        elif call_type == "DIRECT_RESPONSE":
            return "1_DIRECT_RESPONSE"
        elif self.tool_responses and not self.ai_response:
            return "2_TOOL_PROCESSING"
        elif self.ai_response and self.tool_responses:
            return "3_FINAL_RESPONSE"
        elif self.tool_calls:
            return "1_TOOL_DECISION"
        elif self.ai_response:
            return "3_FINAL_RESPONSE"
        else:
            return "0_UNKNOWN"

    def _format_tool_calls_summary(self) -> str:
        """Create a readable summary of tool calls"""
        if not self.tool_calls:
            return ""

        summaries = []
        for tc in self.tool_calls:
            summaries.append(str(tc))

        return " | ".join(summaries)

    def _format_tool_results_summary(self) -> str:
        """Create a readable summary of tool results"""
        if not self.tool_responses:
            return ""

        summaries = []
        for tr in self.tool_responses:
            result_preview = (
                tr.content[:100] + "..." if len(tr.content) > 100 else tr.content
            )
            summaries.append(f"{tr.name} -> {result_preview}")

        return " | ".join(summaries)

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

    def get_summary(self) -> str:
        """Get a human-readable summary of this trace"""
        call_type = self.metadata.get("call_type", "UNKNOWN")

        if call_type == "INITIAL_TOOL_DECISION":
            tools = ", ".join([tc.name for tc in self.tool_calls])
            return f"Tool Decision: {tools}"
        elif call_type == "FINAL_RESPONSE":
            return f"Final Response: {self.ai_response[:100] if self.ai_response else 'No response'}..."
        elif call_type == "DIRECT_RESPONSE":
            return f"Direct Response: {self.ai_response[:100] if self.ai_response else 'No response'}..."
        else:
            return f"LLM Call ({call_type}): {self.action_type}"

    def is_tool_call_step(self) -> bool:
        """Check if this trace represents a tool call decision"""
        return (
            bool(self.tool_calls)
            or self.metadata.get("call_type") == "INITIAL_TOOL_DECISION"
        )

    def is_final_response(self) -> bool:
        """Check if this trace represents a final response to the user"""
        return self.metadata.get("call_type") == "FINAL_RESPONSE" or (
            bool(self.ai_response) and not self.tool_calls
        )

    def has_tool_results(self) -> bool:
        """Check if this trace contains tool execution results"""
        return bool(self.tool_responses)
