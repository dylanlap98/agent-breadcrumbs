"""
LangChain integration for agent-breadcrumbs
Non-invasive logging for all LangChain operations
"""

from typing import Dict, List, Any, Optional
from uuid import UUID

try:
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.outputs import LLMResult

    LANGCHAIN_AVAILABLE = True
except ImportError:
    BaseCallbackHandler = object
    LLMResult = object
    LANGCHAIN_AVAILABLE = False

from ..logger import AgentLogger


class AgentBreadcrumbsCallback(BaseCallbackHandler):
    """
    Non-invasive LangChain callback for automatic logging

    Works with:
    - Regular invoke() calls
    - Streaming (.stream(), .astream())
    - Agents and tools
    - Batch processing
    - Any LangChain model or chain

    Usage:
        from agent_breadcrumbs.integrations.langchain import enable_breadcrumbs
        from langchain.chat_models import init_chat_model

        callback = enable_breadcrumbs()
        model = init_chat_model("gpt-4o", callbacks=[callback])
        response = model.invoke("Hello!")  # Automatically logged!
    """

    def __init__(self, logger: AgentLogger = None, log_tools: bool = True):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is not installed.")

        super().__init__()
        self.logger = logger or AgentLogger()
        self.log_tools = log_tools
        self.runs = {}  # Track runs by ID

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts - store the prompt"""
        self.runs[str(run_id)] = {
            "prompts": prompts,
            "model_name": self._extract_model_name(serialized),
            "metadata": metadata or {},
            "tags": tags or [],
        }

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when LLM completes - log the interaction"""
        run_info = self.runs.get(str(run_id), {})

        prompts = run_info.get("prompts", [])
        prompt_text = " ".join(prompts) if prompts else "Unknown prompt"

        response_text = self._extract_response_text(response)

        model_name = self._extract_real_model_name(response, run_info)

        prompt_tokens = None
        completion_tokens = None
        total_tokens = None

        if response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            prompt_tokens = token_usage.get("prompt_tokens")
            completion_tokens = token_usage.get("completion_tokens")
            total_tokens = token_usage.get("total_tokens")

        # Log the interaction
        self.logger.log_llm_call(
            prompt=prompt_text,
            response=response_text,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            token_count=total_tokens,
            langchain_integration=True,
            langchain_tags=run_info.get("tags", []),
            **run_info.get("metadata", {}),
        )

        # Cleanup
        if str(run_id) in self.runs:
            del self.runs[str(run_id)]

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts"""
        if not self.log_tools:
            return

        tool_name = serialized.get("name", "unknown_tool")

        self.runs[str(run_id)] = {
            "tool_name": tool_name,
            "tool_input": input_str,
            "start_time": kwargs.get("start_time"),
        }

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool completes"""
        if not self.log_tools:
            return

        run_info = self.runs.get(str(run_id), {})
        tool_name = run_info.get("tool_name", "unknown_tool")
        tool_input = run_info.get("tool_input", "")

        self.logger.log_tool_use(
            tool_name=tool_name,
            tool_input={"input": tool_input},
            tool_output={"output": output},
            langchain_tool=True,
        )

        # Cleanup
        if str(run_id) in self.runs:
            del self.runs[str(run_id)]

    def _extract_real_model_name(
        self, response: LLMResult, run_info: Dict[str, Any]
    ) -> str:
        """Extract the real model name, prioritizing LangChain metadata over class names"""

        if response.llm_output:
            ls_model_name = response.llm_output.get("ls_model_name")
            if ls_model_name and ls_model_name != "unknown":
                return ls_model_name

            model_name = response.llm_output.get("model_name")
            if model_name and model_name != "unknown":
                return model_name

            model = response.llm_output.get("model")
            if model and model != "unknown":
                return model

        fallback_name = run_info.get("model_name", "unknown")

        if fallback_name in ["ChatOpenAI", "OpenAI", "AzureChatOpenAI"]:
            if response.llm_output:
                for key, value in response.llm_output.items():
                    if isinstance(value, str) and (
                        "gpt" in value.lower() or "claude" in value.lower()
                    ):
                        return value

            return "unknown"

        return fallback_name

    def _extract_model_name(self, serialized: Dict[str, Any]) -> str:
        """Extract model name from serialized LLM info"""
        if not serialized:
            return "unknown"

        model_id = serialized.get("id", [])
        if isinstance(model_id, list) and model_id:
            return model_id[-1]
        elif isinstance(model_id, str):
            return model_id

        return serialized.get(
            "model_name", serialized.get("model", serialized.get("name", "unknown"))
        )

    def _extract_response_text(self, response: LLMResult) -> str:
        """Extract response text from LLMResult"""
        if not response.generations:
            return "No response"

        if not response.generations[0]:
            return "Empty response"

        generation = response.generations[0][0]

        if hasattr(generation, "text"):
            return generation.text
        elif hasattr(generation, "message") and hasattr(generation.message, "content"):
            return generation.message.content
        else:
            return str(generation)


def enable_breadcrumbs(
    logger: AgentLogger = None, log_tools: bool = True
) -> AgentBreadcrumbsCallback:
    """
    Enable agent-breadcrumbs logging for LangChain with one line

    Args:
        logger: Optional AgentLogger instance. If None, creates a new one.
        log_tools: Whether to log tool/function calls (default: True)

    Returns:
        AgentBreadcrumbsCallback instance to pass to LangChain

    Usage:
        callback = enable_breadcrumbs()
        model = init_chat_model("gpt-4o", callbacks=[callback])
        # Use LangChain normally - everything gets logged!

    Raises:
        ImportError: If LangChain is not installed
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is not installed.")

    return AgentBreadcrumbsCallback(logger=logger, log_tools=log_tools)


def check_langchain_available() -> bool:
    """Check if LangChain is available for integration"""
    return LANGCHAIN_AVAILABLE
