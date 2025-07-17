"""
Agent Breadcrumbs - Follow the trail of your AI agents

A simple, transparent library for logging LLM agent interactions.
Perfect for building training datasets, debugging agent behavior,
and understanding AI decision-making processes.
"""

from .logger import AgentLogger, setup_logging
from .schemas import AgentAction, TokenUsage
from .adapters.csv_adapter import CSVAdapter

try:
    from .integrations.langchain import AgentBreadcrumbsCallback, enable_breadcrumbs

    LANGCHAIN_INTEGRATION = True
except ImportError:
    AgentBreadcrumbsCallback = None
    enable_breadcrumbs = None
    LANGCHAIN_INTEGRATION = False

__version__ = "0.1.0"
__all__ = [
    "AgentLogger",
    "AgentAction",
    "CSVAdapter",
    "TokenUsage",
    "setup_logging",
    "quick_logger",
    "AgentBreadcrumbsCallback",
    "enable_breadcrumbs",
]


def quick_logger(file_path: str = "agent_breadcrumbs.csv") -> AgentLogger:
    """Create a logger with CSV adapter"""
    return AgentLogger(adapter=CSVAdapter(file_path))
