"""
OpenAI SDK interceptor - patches the OpenAI Python SDK directly
"""

import json
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from ..models.trace import TraceEvent, ToolCall, ToolResponse, TokenUsage
from ..models.config import TracerConfig


class HTTPInterceptor:
    """
    HTTP interceptor that patches the OpenAI Python SDK directly
    This is more reliable than patching HTTP libraries
    """

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
        print("🔍 HTTP Interceptor started - patching OpenAI SDK...")

        try:
            self._patch_openai_sdk()
            print("   ✅ Patched OpenAI SDK")
        except ImportError:
            print("   ⚠️ OpenAI SDK not available")
        except Exception as e:
            print(f"   ❌ Error patching OpenAI SDK: {e}")

        print("🔍 HTTP Interceptor active - OpenAI calls will be captured")

    def stop(self):
        """Stop intercepting and restore original methods"""
        if not self.active:
            return

        self.active = False
        self._unpatch_openai_sdk()
        print("🛑 HTTP Interceptor stopped")

    def _patch_openai_sdk(self):
        """Patch the OpenAI SDK completion methods"""
        try:
            import openai
            from openai.resources.chat.completions import Completions

            # Store original method
            original_create = Completions.create
            self.original_methods["openai_create"] = original_create

            def traced_create(completions_self, **kwargs):
                print(f"🔍 Intercepting OpenAI chat completion")
                start_time = time.time()

                # Capture request data
                request_data = dict(kwargs)

                # Make the actual API call
                try:
                    response = original_create(completions_self, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000

                    # Convert response to dict for processing
                    response_data = {}
                    try:
                        if hasattr(response, "model_dump"):
                            response_data = response.model_dump()
                        elif hasattr(response, "dict"):
                            response_data = response.dict()
                        elif hasattr(response, "__dict__"):
                            response_data = response.__dict__
                        else:
                            # Handle the response object manually
                            response_data = {
                                "choices": [],
                                "usage": {},
                                "model": getattr(response, "model", "unknown"),
                            }

                            # Extract choices
                            if hasattr(response, "choices") and response.choices:
                                choices_data = []
                                for choice in response.choices:
                                    choice_data = {}
                                    if hasattr(choice, "message"):
                                        message = choice.message
                                        choice_data["message"] = {
                                            "content": getattr(
                                                message, "content", None
                                            ),
                                            "role": getattr(
                                                message, "role", "assistant"
                                            ),
                                            "tool_calls": [],
                                        }

                                        # Handle tool calls
                                        if (
                                            hasattr(message, "tool_calls")
                                            and message.tool_calls
                                        ):
                                            tool_calls_data = []
                                            for tc in message.tool_calls:
                                                tc_data = {
                                                    "id": getattr(tc, "id", None),
                                                    "function": {
                                                        "name": getattr(
                                                            tc.function, "name", ""
                                                        )
                                                        if hasattr(tc, "function")
                                                        else "",
                                                        "arguments": getattr(
                                                            tc.function,
                                                            "arguments",
                                                            "{}",
                                                        )
                                                        if hasattr(tc, "function")
                                                        else "{}",
                                                    },
                                                }
                                                tool_calls_data.append(tc_data)
                                            choice_data["message"]["tool_calls"] = (
                                                tool_calls_data
                                            )

                                    choices_data.append(choice_data)
                                response_data["choices"] = choices_data

                            # Extract usage
                            if hasattr(response, "usage"):
                                usage = response.usage
                                response_data["usage"] = {
                                    "prompt_tokens": getattr(
                                        usage, "prompt_tokens", None
                                    ),
                                    "completion_tokens": getattr(
                                        usage, "completion_tokens", None
                                    ),
                                    "total_tokens": getattr(
                                        usage, "total_tokens", None
                                    ),
                                }

                    except Exception as parse_error:
                        print(
                            f"⚠️ Error parsing response, using fallback: {parse_error}"
                        )
                        # Create minimal response data
                        response_data = {
                            "choices": [
                                {
                                    "message": {
                                        "content": "Response parsing failed",
                                        "role": "assistant",
                                    }
                                }
                            ],
                            "usage": {},
                            "model": request_data.get("model", "unknown"),
                        }

                    # Create trace event
                    trace = self._create_trace_from_openai(
                        request_data, response_data, duration_ms
                    )
                    self.trace_callback(trace)

                    print(
                        f"📊 Captured OpenAI trace: {trace.user_input[:50] if trace.user_input else 'API call'}..."
                    )

                    return response

                except Exception as e:
                    print(f"❌ Error in OpenAI interceptor: {e}")
                    import traceback

                    traceback.print_exc()
                    # Still return the original response even if tracing fails
                    return original_create(completions_self, **kwargs)

            # Apply the patch
            Completions.create = traced_create

        except ImportError:
            print("⚠️ OpenAI SDK not available for patching")
            raise

    def _unpatch_openai_sdk(self):
        """Restore original OpenAI SDK methods"""
        if "openai_create" in self.original_methods:
            try:
                from openai.resources.chat.completions import Completions

                Completions.create = self.original_methods["openai_create"]
            except ImportError:
                pass

    def _create_trace_from_openai(
        self,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        duration_ms: float,
    ) -> TraceEvent:
        """Create trace event from OpenAI request/response"""

        try:
            # Parse request
            user_input = None
            system_prompt = None
            model_name = request_data.get("model", "unknown")

            messages = request_data.get("messages", [])
            if messages:  # Check if messages is not None
                for msg in messages:
                    if isinstance(msg, dict):  # Ensure msg is a dict
                        role = msg.get("role")
                        content = msg.get("content")

                        if role == "user":
                            user_input = content
                        elif role == "system":
                            system_prompt = content

            # Parse response
            ai_response = None
            tool_calls = []
            token_usage = None

            # Extract usage - handle None case
            usage = response_data.get("usage")
            if usage and isinstance(usage, dict):
                token_usage = TokenUsage(
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                    total_tokens=usage.get("total_tokens"),
                )

            # Extract response content - handle None case
            choices = response_data.get("choices")
            if choices and isinstance(choices, list) and len(choices) > 0:
                choice = choices[0]
                if isinstance(choice, dict):
                    message = choice.get("message")
                    if isinstance(message, dict):
                        # Text response
                        ai_response = message.get("content")

                        # Tool calls - handle None case
                        tool_calls_data = message.get("tool_calls")
                        if tool_calls_data and isinstance(tool_calls_data, list):
                            for tc in tool_calls_data:
                                if isinstance(tc, dict):
                                    function = tc.get("function", {})
                                    if isinstance(function, dict):
                                        try:
                                            arguments_str = function.get(
                                                "arguments", "{}"
                                            )
                                            arguments = (
                                                json.loads(arguments_str)
                                                if arguments_str
                                                else {}
                                            )
                                        except:
                                            arguments = {}

                                        tool_calls.append(
                                            ToolCall(
                                                name=function.get("name", ""),
                                                arguments=arguments,
                                                call_id=tc.get("id"),
                                            )
                                        )

            # Calculate cost
            cost_usd = None
            if token_usage and token_usage.total_tokens:
                cost_usd = self._calculate_cost(token_usage, model_name)

            # Create trace
            trace = TraceEvent(
                session_id=self.config.session_id or "default",
                action_type="llm_call",
                user_input=user_input,
                system_prompt=system_prompt,
                ai_response=ai_response,
                tool_calls=tool_calls,
                model_name=model_name,
                provider="openai",
                token_usage=token_usage,
                cost_usd=cost_usd,
                duration_ms=duration_ms,
                raw_request=request_data if self.config.include_metadata else None,
                raw_response=response_data if self.config.include_metadata else None,
            )

            return trace

        except Exception as e:
            print(f"⚠️ Error creating trace, using fallback: {e}")
            # Create a minimal trace if parsing fails
            return TraceEvent(
                session_id=self.config.session_id or "default",
                action_type="llm_call",
                user_input="Error parsing request",
                ai_response="Error parsing response",
                model_name=request_data.get("model", "unknown"),
                provider="openai",
                duration_ms=duration_ms,
            )

    def _calculate_cost(
        self, token_usage: TokenUsage, model_name: str
    ) -> Optional[float]:
        """Calculate cost based on OpenAI pricing"""
        if not token_usage.total_tokens:
            return None

        # OpenAI pricing per 1K tokens (as of 2024)
        pricing = {
            "gpt-4o-mini": 0.00015,
            "gpt-4o": 0.005,
            "gpt-4-turbo": 0.01,
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
        }

        # Find matching model
        for model_key, price_per_1k in pricing.items():
            if model_key in model_name.lower():
                return (token_usage.total_tokens / 1000) * price_per_1k

        # Default pricing if model not found
        return (token_usage.total_tokens / 1000) * 0.002
