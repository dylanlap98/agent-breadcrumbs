"""
Agent Breadcrumbs Tracer - HTTP-level tracing for complete observability

A traceability-focused observability module that captures complete LLM interactions
by intercepting HTTP calls rather than wrapping framework components.

This is an alternative to the wrapper-based approach in agent_breadcrumbs.logger
"""

from .core.tracer import HTTPTracer
from .models.config import TracerConfig
from .storage.csv_storage import CSVStorage
from .storage.json_storage import JSONStorage

__version__ = "0.1.0"

# Global tracer instance
_tracer = None


def enable_http_tracing(config: TracerConfig = None, storage=None) -> HTTPTracer:
    """
    Enable HTTP-level tracing with one line of code.

    This approach intercepts HTTP calls to LLM providers for complete observability,
    as an alternative to the wrapper-based agent_breadcrumbs.logger approach.

    Args:
        config: TracerConfig instance with tracing settings
        storage: Storage backend (defaults to CSVStorage)

    Returns:
        HTTPTracer instance

    Example:
        >>> from langchain_tracer import enable_http_tracing
        >>> enable_http_tracing()
        >>>
        >>> # Now use LangChain normally - everything gets traced
        >>> from langchain.chat_models import ChatOpenAI
        >>> model = ChatOpenAI()
        >>> model.invoke("Hello world")
    """
    global _tracer

    if config is None:
        config = TracerConfig()

    if storage is None:
        storage = CSVStorage(config.output_file)

    _tracer = HTTPTracer(config=config, storage=storage)
    _tracer.start()

    return _tracer


def disable_http_tracing():
    """Disable HTTP tracing and cleanup resources."""
    global _tracer
    if _tracer:
        _tracer.stop()
        _tracer = None


def get_http_tracer() -> HTTPTracer:
    """Get the current HTTP tracer instance."""
    return _tracer


def get_session_traces(session_id: str = None):
    """Get traces for a specific session or current session."""
    if _tracer:
        return _tracer.get_session_traces(session_id)
    return []


def get_all_traces():
    """Get all traces across all sessions."""
    if _tracer:
        return _tracer.get_all_traces()
    return []


def export_traces(format: str = "csv", output_file: str = None):
    """
    Export traces to a file.

    Args:
        format: Export format ("csv", "json", "jsonl")
        output_file: Output file path (auto-generated if None)
    """
    if _tracer:
        return _tracer.export_traces(format, output_file)


# Convenience exports
__all__ = [
    "enable_http_tracing",
    "disable_http_tracing",
    "get_http_tracer",
    "get_session_traces",
    "get_all_traces",
    "export_traces",
    "HTTPTracer",
    "TracerConfig",
    "CSVStorage",
    "JSONStorage",
]
