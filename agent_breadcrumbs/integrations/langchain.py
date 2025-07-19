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
    """

    def __init__(self, logger: AgentLogger = None, log_tools: bool = True):
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is not installed.")

        super().__init__()
        self.logger = logger or AgentLogger()
        self.log_tools = log_tools
        self.runs = {}

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
        import time

        self.runs[str(run_id)] = {
            "prompts": prompts,
            "model_name": self._extract_model_name(serialized),
            "metadata": metadata or {},
            "tags": tags or [],
            "start_time": time.time(),  # Record start time
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
        import time

        run_info = self.runs.get(str(run_id), {})

        prompts = run_info.get("prompts", [])
        prompt_text = " ".join(prompts) if prompts else "Unknown prompt"
        response_text = self._extract_response_text(response)

        model_name = self._extract_real_model_name(response, run_info)

        start_time = run_info.get("start_time")
        duration_ms = None
        if start_time:
            duration_ms = (time.time() - start_time) * 1000

        prompt_tokens = None
        completion_tokens = None
        total_tokens = None

        token_usage = self._extract_real_token_usage(response, run_info, kwargs)
        if token_usage:
            prompt_tokens = token_usage.get("prompt_tokens")
            completion_tokens = token_usage.get("completion_tokens")
            total_tokens = token_usage.get("total_tokens")

        self._handle_tool_calls_in_response(response, run_info)

        # Log the interaction
        self.logger.log_llm_call(
            prompt=prompt_text,
            response=response_text,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            token_count=total_tokens,
            duration_ms=duration_ms,
            langchain_integration=True,
            langchain_streaming=response.llm_output is None,
            langchain_tags=run_info.get("tags", []),
            **run_info.get("metadata", {}),
        )

        # Cleanup
        if str(run_id) in self.runs:
            del self.runs[str(run_id)]

    def _handle_tool_calls_in_response(
        self, response: LLMResult, run_info: Dict[str, Any]
    ) -> None:
        """Check if the LLM response contains tool calls and log them"""

        if not response.generations:
            return

        for generation_list in response.generations:
            for generation in generation_list:
                if hasattr(generation, "message") and hasattr(
                    generation.message, "tool_calls"
                ):
                    tool_calls = generation.message.tool_calls

                    if tool_calls:
                        for tool_call in tool_calls:
                            self._log_planned_tool_call(tool_call, run_info)

    def _log_planned_tool_call(
        self, tool_call: Dict[str, Any], run_info: Dict[str, Any]
    ) -> None:
        """Log a tool call that the LLM wants to make"""

        tool_name = tool_call.get("name", "unknown_tool")
        tool_args = tool_call.get("args", {})
        tool_id = tool_call.get("id", "unknown_id")

        self.logger.log_tool_use(
            tool_name=tool_name,
            tool_input={
                "planned_args": tool_args,
                "tool_call_id": tool_id,
                "call_type": "planned",
            },
            tool_output={
                "status": "planned_by_llm",
                "note": "LLM requested this tool call but execution depends on agent framework",
            },
            langchain_tool_planning=True,
            **run_info.get("metadata", {}),
        )

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
        import time

        self.runs[str(run_id)] = {
            "tool_name": tool_name,
            "tool_input": input_str,
            "start_time": time.time(),
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

        import time

        run_info = self.runs.get(str(run_id), {})
        tool_name = run_info.get("tool_name", "unknown_tool")
        tool_input = run_info.get("tool_input", "")

        start_time = run_info.get("start_time")
        duration_ms = None
        if start_time:
            duration_ms = (time.time() - start_time) * 1000

        self.logger.log_tool_use(
            tool_name=tool_name,
            tool_input={"input": tool_input},
            tool_output={"output": output},
            duration_ms=duration_ms,
            langchain_tool=True,
        )

        # Cleanup
        if str(run_id) in self.runs:
            del self.runs[str(run_id)]

    def _extract_real_model_name(
        self, response: LLMResult, run_info: Dict[str, Any]
    ) -> str:
        """Extract the real model name - works for both streaming and regular calls"""

        if response.llm_output:
            model_name = response.llm_output.get("model_name")
            if model_name and model_name != "unknown":
                return model_name

            ls_model_name = response.llm_output.get("ls_model_name")
            if ls_model_name and ls_model_name != "unknown":
                return ls_model_name

            model = response.llm_output.get("model")
            if model and model != "unknown":
                return model

        metadata = run_info.get("metadata", {})
        if "ls_model_name" in metadata:
            return metadata["ls_model_name"]

        fallback_name = run_info.get("model_name", "unknown")

        if fallback_name in ["ChatOpenAI", "OpenAI", "AzureChatOpenAI"]:
            return "unknown"

        return fallback_name

    def _extract_real_token_usage(
        self, response: LLMResult, run_info: Dict[str, Any], kwargs: Dict[str, Any]
    ) -> Optional[Dict[str, int]]:
        """Extract real token usage from various providers and formats"""

        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            return self._normalize_token_usage(usage, "openai")

        if response.llm_output and "usage" in response.llm_output:
            usage = response.llm_output["usage"]
            return self._normalize_token_usage(usage, "anthropic")

        if response.llm_output and "usage_metadata" in response.llm_output:
            usage = response.llm_output["usage_metadata"]
            return self._normalize_token_usage(usage, "google")

        if response.generations:
            for generation_list in response.generations:
                for generation in generation_list:
                    if (
                        hasattr(generation, "generation_info")
                        and generation.generation_info
                    ):
                        if "usage" in generation.generation_info:
                            usage = generation.generation_info["usage"]
                            return self._normalize_token_usage(usage, "anthropic")
                        if "token_usage" in generation.generation_info:
                            usage = generation.generation_info["token_usage"]
                            return self._normalize_token_usage(usage, "openai")

                    if hasattr(generation, "message") and hasattr(
                        generation.message, "usage_metadata"
                    ):
                        usage = generation.message.usage_metadata
                        if hasattr(usage, "__dict__"):
                            usage_dict = {
                                "input_tokens": getattr(usage, "input_tokens", None),
                                "output_tokens": getattr(usage, "output_tokens", None),
                                "total_tokens": getattr(usage, "total_tokens", None),
                            }
                            return self._normalize_token_usage(usage_dict, "anthropic")

        if "token_usage" in kwargs:
            return self._normalize_token_usage(kwargs["token_usage"], "openai")
        if "usage" in kwargs:
            return self._normalize_token_usage(kwargs["usage"], "anthropic")

        metadata = run_info.get("metadata", {})
        for usage_key in ["token_usage", "usage", "usage_metadata"]:
            if usage_key in metadata:
                provider = (
                    "anthropic"
                    if usage_key == "usage"
                    else "google"
                    if usage_key == "usage_metadata"
                    else "openai"
                )
                return self._normalize_token_usage(metadata[usage_key], provider)

        return None

    def _normalize_token_usage(
        self, usage: Dict[str, Any], provider: str
    ) -> Dict[str, int]:
        """Normalize different provider token usage formats to standard format"""

        if provider == "openai":
            return {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
            }

        elif provider == "anthropic":
            input_tokens = usage.get("input_tokens")
            output_tokens = usage.get("output_tokens")
            total_tokens = None
            if input_tokens and output_tokens:
                total_tokens = input_tokens + output_tokens

            return {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": total_tokens,
            }

        elif provider == "google":
            prompt_tokens = usage.get("prompt_token_count")
            completion_tokens = usage.get("candidates_token_count")
            total_tokens = None
            if prompt_tokens and completion_tokens:
                total_tokens = prompt_tokens + completion_tokens

            return {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }

        if "prompt_tokens" in usage:
            return self._normalize_token_usage(usage, "openai")
        elif "input_tokens" in usage:
            return self._normalize_token_usage(usage, "anthropic")
        elif "prompt_token_count" in usage:
            return self._normalize_token_usage(usage, "google")

        return {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}

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

    Usage:
        callback = enable_breadcrumbs()
        model = init_chat_model("gpt-4o", callbacks=[callback])
        # Use LangChain normally - everything gets logged!
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is not installed.")

    return AgentBreadcrumbsCallback(logger=logger, log_tools=log_tools)


def check_langchain_available() -> bool:
    """Check if LangChain is available for integration"""
    return LANGCHAIN_AVAILABLE
