from asyncio.log import logger
import json
import time
from typing import Dict, Any, Optional
import uuid
from .schemas import AgentAction
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
        **metadata,
    ) -> str:
        """Log an LLM API call"""
        return self._log_action(
            action_type="llm_call",
            input_data={"prompt": prompt},
            output_data={"response": response},
            model_name=model_name,
            token_count=token_count,
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
            model_name=model_name,
            duration_ms=duration_ms,
            metadata=json.dumps(metadata, default=str),
        )

        action_id = self.adapter.log_action(action)
        return action_id

    def get_session_history(self, limit: Optional[int] = None):
        """Get current session's action history"""
        return self.adapter.get_session_actions(self.session_id, limit)

    def start_new_session(self) -> str:
        """Start a new logging session"""
        self.session_id = str(uuid.uuid4())
        return self.session_id
