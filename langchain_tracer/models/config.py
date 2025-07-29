"""
Configuration model for HTTP tracer
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import uuid


@dataclass
class TracerConfig:
    """Configuration for HTTP-level tracing"""

    # Output settings
    output_file: str = "agent_traces.csv"
    output_format: str = "csv"  # csv, json, jsonl

    # Session management
    session_id: Optional[str] = None
    auto_session: bool = True  # Auto-generate session IDs

    # Tracing behavior
    trace_streaming: bool = True  # Capture streaming responses
    include_system_prompts: bool = True
    include_metadata: bool = True
    capture_tool_calls: bool = True
    capture_tool_responses: bool = True

    # Dashboard settings
    dashboard_enabled: bool = True
    dashboard_port: int = 8080
    dashboard_host: str = "localhost"

    # HTTP interception
    intercept_openai: bool = True
    intercept_anthropic: bool = True
    intercept_other_llms: bool = True

    # Filtering
    exclude_endpoints: List[str] = None
    include_endpoints: List[str] = None
    min_token_threshold: int = 0  # Only log calls with >= tokens

    # Performance
    async_logging: bool = True
    buffer_size: int = 100
    flush_interval: float = 5.0  # seconds

    # Privacy & Security
    redact_sensitive_data: bool = False
    sensitive_patterns: List[str] = None

    def __post_init__(self):
        """Post-initialization processing"""
        if self.session_id is None and self.auto_session:
            self.session_id = str(uuid.uuid4())

        if self.exclude_endpoints is None:
            self.exclude_endpoints = []

        if self.include_endpoints is None:
            self.include_endpoints = []

        if self.sensitive_patterns is None:
            self.sensitive_patterns = [
                r"api[_-]?key",
                r"password",
                r"token",
                r"secret",
                r"auth",
            ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "output_file": self.output_file,
            "output_format": self.output_format,
            "session_id": self.session_id,
            "auto_session": self.auto_session,
            "trace_streaming": self.trace_streaming,
            "include_system_prompts": self.include_system_prompts,
            "include_metadata": self.include_metadata,
            "capture_tool_calls": self.capture_tool_calls,
            "capture_tool_responses": self.capture_tool_responses,
            "dashboard_enabled": self.dashboard_enabled,
            "dashboard_port": self.dashboard_port,
            "dashboard_host": self.dashboard_host,
            "intercept_openai": self.intercept_openai,
            "intercept_anthropic": self.intercept_anthropic,
            "intercept_other_llms": self.intercept_other_llms,
            "exclude_endpoints": self.exclude_endpoints,
            "include_endpoints": self.include_endpoints,
            "min_token_threshold": self.min_token_threshold,
            "async_logging": self.async_logging,
            "buffer_size": self.buffer_size,
            "flush_interval": self.flush_interval,
            "redact_sensitive_data": self.redact_sensitive_data,
            "sensitive_patterns": self.sensitive_patterns,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TracerConfig":
        """Create config from dictionary"""
        return cls(**data)
