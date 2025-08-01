import json
import time
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime

from ..models.trace import TraceEvent, ToolCall, ToolResponse, TokenUsage
from ..models.config import TracerConfig


class HTTPInterceptor:
    def __init__(
        self, config: TracerConfig, trace_callback: Callable[[TraceEvent], None]
    ):
        self.config = config
        self.trace_callback = trace_callback
        self.active = False
        self.original_methods = {}

    def start(self):
        """Start intercepting OpenAI SDK calls"""
        if self.active:
            return

        self.active = True
        print("🔍 TARGETED FIX: Starting HTTP Interceptor...")

        try:
            self._patch_openai_sdk()
            print("   ✅ Applied TARGETED FIX patches")
        except ImportError:
            print("   ⚠️ OpenAI SDK not available")
        except Exception as e:
            print(f"   ❌ Error patching OpenAI SDK: {e}")

        print("🔍 TARGETED FIX active - will capture ALL agent steps")

    def stop(self):
        """Stop intercepting and restore original methods"""
        if not self.active:
            return

        self.active = False
        self._unpatch_openai_sdk()
        print("🛑 TARGETED FIX stopped")

    def _patch_openai_sdk(self):
        """Patch the OpenAI SDK completion methods"""
        try:
            import openai
            from openai.resources.chat.completions import Completions

            # Store original method
            original_create = Completions.create
            self.original_methods["openai_create"] = original_create

            def traced_create(completions_self, **kwargs):
                start_time = time.time()
                request_data = dict(kwargs)

                # Analyze the request to understand what type of call this is
                call_type = self._analyze_request_type(request_data)
                print(f"🔍 [TARGETED] Intercepting {call_type} call")

                try:
                    response = original_create(completions_self, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000

                    # Parse response with call type context
                    response_data = self._parse_response_with_context(
                        response, call_type
                    )

                    # Create trace with proper classification
                    trace = self._create_trace_with_context(
                        request_data, response_data, duration_ms, call_type
                    )

                    self.trace_callback(trace)

                    # Log what we captured
                    self._log_capture_result(trace, call_type)

                    return response

                except Exception as e:
                    print(f"❌ [TARGETED] Error in interceptor: {e}")
                    import traceback

                    traceback.print_exc()
                    return original_create(completions_self, **kwargs)

            # Apply the patch
            Completions.create = traced_create

        except ImportError:
            print("⚠️ OpenAI SDK not available for patching")
            raise

    def _to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert SDK-specific objects to plain dictionaries."""
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return {}

    def _analyze_request_type(self, request_data: Dict[str, Any]) -> str:
        """Analyze the request to determine what type of LangChain call this is"""
        messages = request_data.get("messages", [])

        # Check for tools in the request
        has_tools = bool(request_data.get("tools") or request_data.get("functions"))

        # Check message patterns
        has_user_message = any(msg.get("role") == "user" for msg in messages)
        has_tool_messages = any(msg.get("role") == "tool" for msg in messages)
        has_assistant_messages = any(msg.get("role") == "assistant" for msg in messages)

        # Classify the call type
        if has_user_message and has_tools and not has_tool_messages:
            return "INITIAL_TOOL_DECISION"  # LLM deciding which tools to use
        elif has_tool_messages and has_tools:
            return "FINAL_RESPONSE"  # LLM processing tool results to give final answer
        elif has_user_message and not has_tools:
            return "DIRECT_RESPONSE"  # Direct response without tools
        else:
            return "UNKNOWN"

    def _parse_response_with_context(self, response, call_type: str) -> Dict[str, Any]:
        """Parse response with awareness of call type"""
        try:
            # Newer OpenAI SDK versions may return plain dicts, pydantic models
            # or custom objects. Convert everything to a standard dictionary so
            # that downstream parsing works reliably.
            if isinstance(response, dict):
                data = response
            elif hasattr(response, "model_dump"):
                data = response.model_dump()
            elif hasattr(response, "dict"):
                data = response.dict()
            else:
                # Manual parsing for objects that don't expose a dict interface
                data = self._manual_parse_response(response)

            print(f"✅ [TARGETED] Parsed {call_type} response successfully")
            return data

        except Exception as e:
            print(f"❌ [TARGETED] Failed to parse {call_type} response: {e}")
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"Parse error for {call_type}: {str(e)}",
                            "role": "assistant",
                        }
                    }
                ],
                "usage": {},
                "model": "unknown",
            }

    def _manual_parse_response(self, response) -> Dict[str, Any]:
        """Manual response parsing when automatic methods fail"""
        data = {
            "choices": [],
            "usage": {},
            "model": getattr(response, "model", "unknown"),
        }

        # Parse choices
        if hasattr(response, "choices") and response.choices:
            choices_data = []
            for choice in response.choices:
                choice_data = {
                    "message": {"content": None, "role": "assistant", "tool_calls": []}
                }

                if hasattr(choice, "message"):
                    message = choice.message
                    choice_data["message"]["content"] = getattr(
                        message, "content", None
                    )
                    choice_data["message"]["role"] = getattr(
                        message, "role", "assistant"
                    )

                    # Parse tool calls
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        tool_calls_data = []
                        for tc in message.tool_calls:
                            tc_data = {
                                "id": getattr(tc, "id", None),
                                "type": getattr(tc, "type", "function"),
                                "function": {
                                    "name": getattr(tc.function, "name", "")
                                    if hasattr(tc, "function")
                                    else "",
                                    "arguments": getattr(tc.function, "arguments", "{}")
                                    if hasattr(tc, "function")
                                    else "{}",
                                },
                            }
                            tool_calls_data.append(tc_data)
                        choice_data["message"]["tool_calls"] = tool_calls_data

                choices_data.append(choice_data)
            data["choices"] = choices_data

        # Parse usage
        if hasattr(response, "usage"):
            usage = response.usage
            data["usage"] = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }

        return data

    def _create_trace_with_context(
        self,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        duration_ms: float,
        call_type: str,
    ) -> TraceEvent:
        """Create trace with proper context awareness"""

        # Extract basic info
        model_name = request_data.get("model", "unknown")
        messages = request_data.get("messages", [])

        # Parse messages
        user_input = None
        system_prompt = None
        tool_responses = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "user":
                user_input = content
            elif role == "system":
                system_prompt = content
            elif role == "tool":
                tool_name = msg.get("name", "unknown_tool")
                call_id = msg.get("tool_call_id")
                tool_responses.append(
                    ToolResponse(call_id=call_id, name=tool_name, content=content or "")
                )

        # Parse response
        ai_response = None
        tool_calls = []
        token_usage = None

        # Token usage (support both chat.completions and responses APIs)
        usage = response_data.get("usage", {})
        if usage:
            prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
            completion_tokens = usage.get("completion_tokens") or usage.get(
                "output_tokens"
            )
            total_tokens = usage.get("total_tokens")
            if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
                total_tokens = prompt_tokens + completion_tokens

            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

        # Response content and tool calls
        choices = response_data.get("choices")
        if choices:
            # Chat Completions style response
            choice = self._to_dict(choices[0])
            message = self._to_dict(choice.get("message", {}))
            ai_response = message.get("content") or choice.get("text")

            # Content blocks may be a list
            if isinstance(ai_response, list):
                ai_response = " ".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in ai_response
                ).strip() or None

            tool_calls_data = message.get("tool_calls", []) or []
            for tc in tool_calls_data:
                tc = self._to_dict(tc)
                function = self._to_dict(tc.get("function", {}))
                args = function.get("arguments", "{}")
                try:
                    arguments = json.loads(args) if isinstance(args, str) else args
                except Exception:
                    arguments = {}

                tool_calls.append(
                    ToolCall(
                        name=function.get("name", "unknown_function"),
                        arguments=arguments,
                        call_id=tc.get("id"),
                    )
                )
        else:
            # Responses API style response or other non-choice formats
            messages = (
                response_data.get("output")
                or response_data.get("response")
                or response_data.get("messages")
                or []
            )

            if messages:
                msg = self._to_dict(messages[0])
                content_blocks = msg.get("content", [])
                text_parts: List[str] = []
                for block in content_blocks:
                    block = self._to_dict(block)
                    btype = block.get("type")
                    if btype in ("text", "output_text"):
                        text_parts.append(block.get("text") or "")
                    elif btype in ("tool_call", "function_call", "tool"):
                        args = block.get("arguments") or block.get("input") or "{}"
                        try:
                            arguments = (
                                json.loads(args) if isinstance(args, str) else args or {}
                            )
                        except Exception:
                            arguments = {}
                        name = (
                            block.get("name")
                            or block.get("tool_name")
                            or block.get("function", {}).get("name")
                            or "unknown_function"
                        )
                        tool_calls.append(
                            ToolCall(
                                name=name,
                                arguments=arguments,
                                call_id=block.get("id"),
                            )
                        )
                ai_response = " ".join(text_parts).strip() or None

            if not ai_response:
                ai_response = response_data.get("output_text") or response_data.get("content")

        # Determine action type based on call type and content
        if call_type == "INITIAL_TOOL_DECISION" and tool_calls:
            action_type = "tool_decision"
        elif call_type == "FINAL_RESPONSE" and ai_response:
            action_type = "tool_response_processing"
        elif call_type == "DIRECT_RESPONSE":
            action_type = "llm_call"
        else:
            action_type = "llm_call"

        # Calculate cost
        cost_usd = None
        if token_usage and token_usage.total_tokens:
            cost_usd = self._calculate_cost(token_usage, model_name)

        # Create trace
        trace = TraceEvent(
            session_id=self.config.session_id or "default",
            action_type=action_type,
            user_input=user_input
            if call_type in ["INITIAL_TOOL_DECISION", "DIRECT_RESPONSE"]
            else None,
            system_prompt=system_prompt,
            ai_response=ai_response,
            tool_calls=tool_calls,
            tool_responses=tool_responses,
            model_name=model_name,
            provider="openai",
            token_usage=token_usage,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            metadata={
                "call_type": call_type,
                "conversation_id": f"conv_{hash(str(user_input or 'unknown')) % 10000}",
            },
        )

        return trace

    def _log_capture_result(self, trace: TraceEvent, call_type: str):
        """Log what we successfully captured"""
        if call_type == "INITIAL_TOOL_DECISION":
            if trace.tool_calls:
                tools = ", ".join([tc.name for tc in trace.tool_calls])
                print(f"✅ [TARGETED] Captured TOOL DECISION: {tools}")
            else:
                print(
                    f"⚠️ [TARGETED] Expected tool calls in INITIAL_TOOL_DECISION but found none"
                )

        elif call_type == "FINAL_RESPONSE":
            if trace.ai_response:
                print(
                    f"✅ [TARGETED] Captured FINAL RESPONSE: {trace.ai_response[:50]}..."
                )
            else:
                print(
                    f"⚠️ [TARGETED] Expected AI response in FINAL_RESPONSE but found none"
                )

        elif call_type == "DIRECT_RESPONSE":
            print(
                f"✅ [TARGETED] Captured DIRECT RESPONSE: {trace.ai_response[:50] if trace.ai_response else 'No content'}..."
            )

        else:
            print(f"⚠️ [TARGETED] Captured UNKNOWN call type: {call_type}")

    def _calculate_cost(
        self, token_usage: TokenUsage, model_name: str
    ) -> Optional[float]:
        """Calculate cost based on OpenAI pricing"""
        if not token_usage.total_tokens:
            return None

        pricing = {
            "gpt-4o-mini": 0.00015,
            "gpt-4o": 0.005,
            "gpt-4-turbo": 0.01,
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
        }

        for model_key, price_per_1k in pricing.items():
            if model_key in model_name.lower():
                return (token_usage.total_tokens / 1000) * price_per_1k

        return (token_usage.total_tokens / 1000) * 0.002

    def _unpatch_openai_sdk(self):
        """Restore original OpenAI SDK methods"""
        if "openai_create" in self.original_methods:
            try:
                from openai.resources.chat.completions import Completions

                Completions.create = self.original_methods["openai_create"]
            except ImportError:
                pass
