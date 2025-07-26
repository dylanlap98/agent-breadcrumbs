"""
LangChain integration for agent-breadcrumbs
Non-invasive logging for LangChain operations
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
    Simple, reliable callback for LLM observability

    Focuses on what LangChain reliably provides:
    - LLM calls and responses (including tool call decisions)
    - Token usage and costs
    - Complete conversation flow

    Perfect for beginners who want to understand what their LLMs are doing.
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
        """Called when LLM starts"""
        import time

        # Extract the complete prompt including any tool responses
        complete_prompt = self._extract_complete_prompt(prompts, kwargs)

        self.runs[str(run_id)] = {
            "prompts": prompts,
            "complete_prompt": complete_prompt,
            "model_name": self._extract_model_name(serialized),
            "metadata": metadata or {},
            "tags": tags or [],
            "start_time": time.time(),
        }

    def _extract_complete_prompt(
        self, prompts: List[str], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract the complete prompt including conversation history and tool responses"""

        # Try to get the complete prompt from various LangChain sources
        if prompts and len(prompts) > 0:
            prompt_text = prompts[0]

            # Check if this looks like it has tool responses
            if "Tool:" in prompt_text or "tool_calls" in prompt_text.lower():
                return self._parse_flat_prompt_to_structured(prompt_text)

            # Check kwargs for additional context
            if "invocation_params" in kwargs:
                messages = kwargs["invocation_params"].get("messages", [])
                if messages:
                    return self._reconstruct_conversation(messages)

            # Check for messages in kwargs directly
            if "messages" in kwargs:
                return self._reconstruct_conversation(kwargs["messages"])

        # Fallback to original prompts
        if prompts:
            return self._parse_flat_prompt_to_structured(" ".join(prompts))
        else:
            return {"prompt": "Unknown prompt"}

    def _parse_flat_prompt_to_structured(self, prompt_text: str) -> Dict[str, Any]:
        """Parse a flat prompt string into structured format"""
        structured = {}

        parts = prompt_text.split("\n")
        current_role = None
        current_content = []

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if part.startswith("System:"):
                if current_role and current_content:
                    structured[current_role] = "\n".join(current_content).strip()
                current_role = "system"
                current_content = [part[7:].strip()]  # Remove "System:"
            elif part.startswith("Human:"):
                if current_role and current_content:
                    structured[current_role] = "\n".join(current_content).strip()
                current_role = "human"
                current_content = [part[6:].strip()]  # Remove "Human:"
            elif part.startswith("AI:"):
                if current_role and current_content:
                    structured[current_role] = "\n".join(current_content).strip()
                current_role = "ai"
                current_content = [part[3:].strip()]  # Remove "AI:"
            elif part.startswith("Tool:"):
                if current_role and current_content:
                    structured[current_role] = "\n".join(current_content).strip()
                current_role = "tool"
                current_content = [part[5:].strip()]  # Remove "Tool:"
            else:
                if current_content:
                    current_content.append(part)
                else:
                    current_role = "human"
                    current_content = [part]

        if current_role and current_content:
            structured[current_role] = "\n".join(current_content).strip()

        return structured

    def _reconstruct_conversation(
        self, messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Reconstruct the full conversation from messages"""
        structured = {}
        ai_responses = []
        tool_responses = []

        for message in messages:
            role = message.get("role", "unknown")
            content = message.get("content", "")

            if role == "system":
                structured["system"] = content
            elif role == "user" or role == "human":
                structured["human"] = content
            elif role == "assistant" or role == "ai":
                ai_responses.append(content)

                # Check for tool calls in the message
                if "tool_calls" in message:
                    for tool_call in message["tool_calls"]:
                        if isinstance(tool_call, dict):
                            tool_name = tool_call.get("function", {}).get(
                                "name", "unknown_tool"
                            )
                            tool_args = tool_call.get("function", {}).get(
                                "arguments", "{}"
                            )
                            ai_responses.append(f"Tool Call: {tool_name}({tool_args})")
            elif role == "tool":
                # This is a tool response
                tool_responses.append(content)

        if ai_responses:
            structured["ai"] = "\n".join(filter(None, ai_responses))

        if tool_responses:
            structured["tool"] = "\n".join(tool_responses)

        return structured

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

        # Use the complete prompt that includes tool responses
        prompt_data = run_info.get("complete_prompt", {"prompt": "Unknown prompt"})
        response_text = self._extract_complete_response(response)

        model_name = self._extract_real_model_name(response, run_info)

        start_time = run_info.get("start_time")
        duration_ms = None
        if start_time:
            duration_ms = (time.time() - start_time) * 1000

        token_usage = self._extract_real_token_usage(response, run_info, kwargs)
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None

        if token_usage:
            prompt_tokens = token_usage.get("prompt_tokens")
            completion_tokens = token_usage.get("completion_tokens")
            total_tokens = token_usage.get("total_tokens")

        # Log the interaction
        self.logger.log_llm_call(
            prompt=prompt_data,
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

        try:
            import json

            if tool_input.startswith("{") or tool_input.startswith("["):
                parsed_input = json.loads(tool_input)
            else:
                parsed_input = tool_input
        except:
            parsed_input = tool_input

        # Log tool execution (if callback fires)
        self.logger.log_tool_use(
            tool_name=tool_name,
            tool_input={"input": parsed_input},
            tool_output={"result": output},
            duration_ms=duration_ms,
            langchain_tool_callback=True,
        )

        # Cleanup
        if str(run_id) in self.runs:
            del self.runs[str(run_id)]

    def _extract_complete_response(self, response: LLMResult) -> str:
        """Extract response including tool call decisions"""
        if not response.generations:
            return "No response"

        if not response.generations[0]:
            return "Empty response"

        generation = response.generations[0][0]

        text_content = ""
        if hasattr(generation, "text") and generation.text:
            text_content = generation.text
        elif hasattr(generation, "message") and hasattr(generation.message, "content"):
            text_content = generation.message.content or ""

        tool_calls_info = []

        if hasattr(generation, "message"):
            message = generation.message

            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.get("name", "unknown_tool")
                    tool_args = tool_call.get("args", {})
                    tool_calls_info.append(
                        {
                            "name": tool_name,
                            "args": tool_args,
                        }
                    )

            elif hasattr(message, "additional_kwargs") and message.additional_kwargs:
                additional = message.additional_kwargs
                if "tool_calls" in additional:
                    for tool_call in additional["tool_calls"]:
                        if isinstance(tool_call, dict) and "function" in tool_call:
                            function = tool_call["function"]
                            tool_name = function.get("name", "unknown_tool")
                            try:
                                import json

                                tool_args = json.loads(function.get("arguments", "{}"))
                            except:
                                tool_args = function.get("arguments", "{}")
                            tool_calls_info.append(
                                {
                                    "name": tool_name,
                                    "args": tool_args,
                                }
                            )

        if tool_calls_info and not text_content:
            if len(tool_calls_info) == 1:
                tool = tool_calls_info[0]
                args_str = ", ".join(f"{k}={v}" for k, v in tool["args"].items())
                return f"🔧 Decided to call tool: {tool['name']}({args_str})"
            else:
                calls = []
                for tool in tool_calls_info:
                    args_str = ", ".join(f"{k}={v}" for k, v in tool["args"].items())
                    calls.append(f"{tool['name']}({args_str})")
                return f"🔧 Decided to call tools: {', '.join(calls)}"

        elif tool_calls_info and text_content:
            # Text + tool calls
            calls = []
            for tool in tool_calls_info:
                args_str = ", ".join(f"{k}={v}" for k, v in tool["args"].items())
                calls.append(f"{tool['name']}({args_str})")
            return f"{text_content}\n\n🔧 Tool calls: {', '.join(calls)}"

        elif text_content:
            return text_content

        else:
            return str(generation)

    def _extract_real_model_name(
        self, response: LLMResult, run_info: Dict[str, Any]
    ) -> str:
        """Extract the actual model name"""
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
        """Extract token usage"""
        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            return self._normalize_token_usage(usage, "openai")

        if response.llm_output and "usage" in response.llm_output:
            usage = response.llm_output["usage"]
            return self._normalize_token_usage(usage, "anthropic")

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

        return None

    def _normalize_token_usage(
        self, usage: Dict[str, Any], provider: str
    ) -> Dict[str, int]:
        """Normalize token usage formats"""
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
        return {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}

    def _extract_model_name(self, serialized: Dict[str, Any]) -> str:
        """Extract model name from serialized info"""
        if not serialized:
            return "unknown"

        model_id = serialized.get("id", [])
        if isinstance(model_id, list) and model_id:
            return model_id[-1]
        elif isinstance(model_id, str):
            return model_id

        return serialized.get("model_name", serialized.get("model", "unknown"))


def enable_breadcrumbs(
    logger: AgentLogger = None, log_tools: bool = True
) -> AgentBreadcrumbsCallback:
    """
    Enable simple, reliable LLM observability

    Perfect for beginners - shows LLM decisions, costs, and conversation flow
    without complex setup or fragile hacks.

    Usage:
        callback = enable_breadcrumbs()
        model = init_chat_model("gpt-4o", callbacks=[callback])

        # See what your LLM is thinking!
        history = callback.logger.get_session_history()
    """
    if not LANGCHAIN_AVAILABLE:
        raise ImportError("LangChain is not installed.")

    return AgentBreadcrumbsCallback(logger=logger, log_tools=log_tools)


def check_langchain_available() -> bool:
    """Check if LangChain is available for integration"""
    return LANGCHAIN_AVAILABLE
