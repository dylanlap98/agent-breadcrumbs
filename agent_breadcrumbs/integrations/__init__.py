"""
Integrations with popular AI/LLM frameworks
"""

try:
    from .langchain import (
        AgentBreadcrumbsCallback,
        enable_breadcrumbs,
        check_langchain_available,
    )

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    AgentBreadcrumbsCallback = None
    enable_breadcrumbs = None
    check_langchain_available = lambda: False

__all__ = [
    "AgentBreadcrumbsCallback",
    "enable_breadcrumbs",
    "check_langchain_available",
    "LANGCHAIN_AVAILABLE",
]
