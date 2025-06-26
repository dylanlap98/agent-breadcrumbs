import csv
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base import BaseAdapter
from ..schemas import AgentAction


class CSVAdapter(BaseAdapter):
    """CSV file adapter for transparent, human-readable logging"""

    def __init__(self, file_path: str = "agent_logs.csv"):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not self.file_path.exists():
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "action_id",
                        "session_id",
                        "timestamp",
                        "action_type",
                        "input_data",
                        "output_data",
                        "token_count",
                        "model_name",
                        "duration_ms",
                        "metadata",
                    ]
                )

    def log_action(self, action: AgentAction) -> str:
        """Append action to CSV file"""
        with open(self.file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    action.action_id,
                    action.session_id,
                    action.timestamp.isoformat(),
                    action.action_type,
                    action.input_data,
                    action.output_data,
                    action.token_count,
                    action.model_name,
                    action.duration_ms,
                    action.metadata,
                ]
            )
        return action.action_id

    def get_session_actions(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[AgentAction]:
        """Get all actions for a specific session"""
        actions = []
        if not self.file_path.exists():
            return actions

        with open(self.file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["session_id"] == session_id:
                    actions.append(self._row_to_action(row))
                    if limit and len(actions) >= limit:
                        break
        return actions

    def get_all_actions(self, limit: Optional[int] = None) -> List[AgentAction]:
        """Get all logged actions"""
        actions = []
        if not self.file_path.exists():
            return actions

        with open(self.file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                actions.append(self._row_to_action(row))
                if limit and len(actions) >= limit:
                    break
        return actions

    def _row_to_action(self, row: Dict[str, str]) -> AgentAction:
        """Convert CSV row to AgentAction"""
        return AgentAction(
            action_id=row["action_id"],
            session_id=row["session_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            action_type=row["action_type"],
            input_data=row["input_data"],
            output_data=row["output_data"],
            token_count=int(row["token_count"]) if row["token_count"] else None,
            model_name=row["model_name"] if row["model_name"] else None,
            duration_ms=float(row["duration_ms"]) if row["duration_ms"] else None,
            metadata=row["metadata"],
        )
