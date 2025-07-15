from asyncio.log import logger
import json
import time
from typing import Dict, Any, Optional
import uuid
from .schemas import AgentAction, TokenUsage
from .adapters.csv_adapter import CSVAdapter


class AgentLogger:
    """Main interface for logging agent interactions"""

    def __init__(self, adapter=None, session_id: Optional[str] = None):
        self.adapter = adapter or CSVAdapter()
        self.session_id = session_id or str(uuid.uuid4())

    def log_llm_call(
        self,
        prompt: str,
        response: str,
        model_name: Optional[str] = None,
        token_count: Optional[int] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        **metadata,
    ) -> str:
        """Log an LLM API call"""

        # Create token usage object
        token_usage = None
        if prompt_tokens is not None or completion_tokens is not None:
            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=token_count
                or ((prompt_tokens or 0) + (completion_tokens or 0)),
            )

        return self._log_action(
            action_type="llm_call",
            input_data={"prompt": prompt},
            output_data={"response": response},
            model_name=model_name,
            token_count=token_count,
            token_usage=token_usage,
            **metadata,
        )

    def log_llm_call_from_openai_response(
        self,
        prompt: str,
        openai_response,
        **metadata,
    ) -> str:
        """Convenience method to log from OpenAI response object"""

        response_text = openai_response.choices[0].message.content
        model_name = openai_response.model

        usage = openai_response.usage
        token_usage = None
        if usage:
            token_usage = TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
            )

        return self._log_action(
            action_type="llm_call",
            input_data={"prompt": prompt},
            output_data={"response": response_text},
            model_name=model_name,
            token_count=usage.total_tokens if usage else None,
            token_usage=token_usage,
            **metadata,
        )

    def log_tool_use(
        self, tool_name: str, tool_input: Dict[str, Any], tool_output: Any, **metadata
    ) -> str:
        """Log a tool/function call"""
        return self._log_action(
            action_type="tool_use",
            input_data={"tool": tool_name, "input": tool_input},
            output_data={"output": tool_output},
            **metadata,
        )

    def log_reasoning(self, thought_process: str, decision: str, **metadata) -> str:
        """Log agent reasoning/thinking"""
        return self._log_action(
            action_type="reasoning",
            input_data={"thought_process": thought_process},
            output_data={"decision": decision},
            **metadata,
        )

    def _log_action(
        self,
        action_type: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        model_name: Optional[str] = None,
        token_count: Optional[int] = None,
        token_usage: Optional[TokenUsage] = None,
        duration_ms: Optional[float] = None,
        **metadata,
    ) -> str:
        """Internal method to log any action"""
        start_time = time.time()

        if duration_ms is None:
            duration_ms = (time.time() - start_time) * 1000

        logger.info(f"Logging action: {action_type}, duration: {duration_ms:.2f} ms")

        action = AgentAction(
            session_id=self.session_id,
            action_type=action_type,
            input_data=json.dumps(input_data, default=str),
            output_data=json.dumps(output_data, default=str),
            token_count=token_count,
            token_usage=token_usage,
            model_name=model_name,
            duration_ms=duration_ms,
            metadata=json.dumps(metadata, default=str),
        )

        action.calculate_cost()

        action_id = self.adapter.log_action(action)
        return action_id

    def get_session_history(self, limit: Optional[int] = None):
        """Get current session's action history"""
        return self.adapter.get_session_actions(self.session_id, limit)

    def get_session_cost_summary(self) -> Dict[str, Any]:
        """Get cost breakdown for current session"""
        actions = self.get_session_history()

        total_cost = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        model_breakdown = {}

        for action in actions:
            if action.cost_usd:
                total_cost += action.cost_usd

            if action.token_usage:
                total_prompt_tokens += action.token_usage.prompt_tokens or 0
                total_completion_tokens += action.token_usage.completion_tokens or 0

                # Model breakdown
                if action.model_name:
                    if action.model_name not in model_breakdown:
                        model_breakdown[action.model_name] = {
                            "calls": 0,
                            "cost": 0,
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                        }

                    model_breakdown[action.model_name]["calls"] += 1
                    model_breakdown[action.model_name]["cost"] += action.cost_usd or 0
                    model_breakdown[action.model_name]["prompt_tokens"] += (
                        action.token_usage.prompt_tokens or 0
                    )
                    model_breakdown[action.model_name]["completion_tokens"] += (
                        action.token_usage.completion_tokens or 0
                    )

        return {
            "session_id": self.session_id,
            "total_cost_usd": round(total_cost, 4),
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "model_breakdown": model_breakdown,
        }

    def start_new_session(self) -> str:
        """Start a new logging session"""
        self.session_id = str(uuid.uuid4())
        return self.session_id
