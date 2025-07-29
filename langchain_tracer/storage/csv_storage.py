"""
CSV storage backend for trace events
"""

import csv
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import threading
import time
from datetime import datetime

from ..models.trace import TraceEvent


class CSVStorage:
    """
    Storage backend that writes traces to CSV files
    Compatible with existing dashboard format
    """

    def __init__(
        self,
        file_path: str = "agent_traces.csv",
        buffer_size: int = 100,
        flush_interval: float = 5.0,
    ):
        self.file_path = Path(file_path)
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval

        # Buffer for async writes
        self.buffer: List[TraceEvent] = []
        self.buffer_lock = threading.Lock()

        # Auto-flush thread
        self.flush_thread = None
        self.stop_flush_thread = False

        # CSV headers (compatible with existing format)
        self.headers = [
            "action_id",
            "session_id",
            "timestamp",
            "action_type",
            "input_data",
            "output_data",
            "model_name",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cost_usd",
            "duration_ms",
            "metadata",
        ]

        self._initialize_file()
        self._start_flush_thread()

    def _initialize_file(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not self.file_path.exists():
            # Create directory if it doesn't exist
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write headers
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writeheader()

    def _start_flush_thread(self):
        """Start background thread for periodic flushing"""
        self.flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self.flush_thread.start()

    def _flush_loop(self):
        """Background loop for flushing buffer"""
        while not self.stop_flush_thread:
            time.sleep(self.flush_interval)
            self.flush()

    def store_trace(self, trace: TraceEvent):
        """Store a single trace event"""
        with self.buffer_lock:
            self.buffer.append(trace)

            # Flush if buffer is full
            if len(self.buffer) >= self.buffer_size:
                self._flush_buffer()

    def store_traces(self, traces: List[TraceEvent]):
        """Store multiple trace events"""
        with self.buffer_lock:
            self.buffer.extend(traces)

            # Flush if buffer is full
            if len(self.buffer) >= self.buffer_size:
                self._flush_buffer()

    def flush(self):
        """Flush buffer to disk"""
        with self.buffer_lock:
            if self.buffer:
                self._flush_buffer()

    def _flush_buffer(self):
        """Internal method to flush buffer (assumes lock is held)"""
        if not self.buffer:
            return

        try:
            # Convert traces to CSV rows
            rows = []
            for trace in self.buffer:
                row = trace.to_csv_row()
                rows.append(row)

            # Write to CSV
            with open(self.file_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                for row in rows:
                    # Ensure all fields are present
                    csv_row = {header: row.get(header, "") for header in self.headers}
                    writer.writerow(csv_row)

            # Clear buffer
            self.buffer.clear()

        except Exception as e:
            print(f"Error flushing CSV buffer: {e}")

    def load_traces(self, session_id: Optional[str] = None) -> List[TraceEvent]:
        """Load traces from CSV file"""
        traces = []

        if not self.file_path.exists():
            return traces

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert CSV row back to TraceEvent
                    trace = self._csv_row_to_trace(row)

                    # Filter by session if specified
                    if session_id is None or trace.session_id == session_id:
                        traces.append(trace)

        except Exception as e:
            print(f"Error loading traces from CSV: {e}")

        return traces

    def _csv_row_to_trace(self, row: Dict[str, str]) -> TraceEvent:
        """Convert CSV row back to TraceEvent"""
        # Parse JSON fields
        try:
            input_data = json.loads(row.get("input_data", "{}"))
        except json.JSONDecodeError:
            input_data = {}

        try:
            output_data = json.loads(row.get("output_data", "{}"))
        except json.JSONDecodeError:
            output_data = {}

        try:
            metadata = json.loads(row.get("metadata", "{}"))
        except json.JSONDecodeError:
            metadata = {}

        # Parse timestamp
        timestamp_str = row.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            timestamp = datetime.utcnow()

        # Create TraceEvent
        trace = TraceEvent(
            action_id=row.get("action_id", ""),
            session_id=row.get("session_id", ""),
            timestamp=timestamp,
            action_type=row.get("action_type", "llm_call"),
            user_input=input_data.get("prompt"),
            system_prompt=input_data.get("system"),
            ai_response=output_data.get("response"),
            model_name=row.get("model_name", ""),
            duration_ms=float(row.get("duration_ms", 0))
            if row.get("duration_ms")
            else None,
            cost_usd=float(row.get("cost_usd", 0)) if row.get("cost_usd") else None,
            metadata=metadata,
        )

        # Parse token usage
        if any(
            row.get(f) for f in ["prompt_tokens", "completion_tokens", "total_tokens"]
        ):
            from ..models.trace import TokenUsage

            trace.token_usage = TokenUsage(
                prompt_tokens=int(row.get("prompt_tokens", 0))
                if row.get("prompt_tokens")
                else None,
                completion_tokens=int(row.get("completion_tokens", 0))
                if row.get("completion_tokens")
                else None,
                total_tokens=int(row.get("total_tokens", 0))
                if row.get("total_tokens")
                else None,
            )

        return trace

    def get_sessions(self) -> List[str]:
        """Get list of all session IDs"""
        sessions = set()

        if not self.file_path.exists():
            return list(sessions)

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    session_id = row.get("session_id")
                    if session_id:
                        sessions.add(session_id)

        except Exception as e:
            print(f"Error getting sessions from CSV: {e}")

        return list(sessions)

    def clear(self):
        """Clear all traces"""
        with self.buffer_lock:
            self.buffer.clear()

        # Recreate file with just headers
        self._initialize_file()

    def close(self):
        """Close storage and cleanup"""
        # Stop flush thread
        self.stop_flush_thread = True
        if self.flush_thread and self.flush_thread.is_alive():
            self.flush_thread.join(timeout=1.0)

        # Final flush
        self.flush()

    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        traces = self.load_traces()

        if not traces:
            return {
                "total_traces": 0,
                "total_sessions": 0,
                "total_cost": 0.0,
                "total_tokens": 0,
                "avg_duration": 0.0,
            }

        total_cost = sum(t.cost_usd for t in traces if t.cost_usd)
        total_tokens = sum(
            t.token_usage.total_tokens
            for t in traces
            if t.token_usage and t.token_usage.total_tokens
        )
        durations = [t.duration_ms for t in traces if t.duration_ms]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        sessions = set(t.session_id for t in traces)

        return {
            "total_traces": len(traces),
            "total_sessions": len(sessions),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "avg_duration": avg_duration,
            "file_path": str(self.file_path),
            "file_size": self.file_path.stat().st_size
            if self.file_path.exists()
            else 0,
        }
