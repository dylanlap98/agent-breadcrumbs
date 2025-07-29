"""
JSON storage backend for trace events
"""

import json
import threading
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ..models.trace import TraceEvent


class JSONStorage:
    """
    Storage backend that writes traces to JSON/JSONL files
    Provides richer data structure than CSV
    """

    def __init__(
        self,
        file_path: str = "agent_traces.jsonl",
        format_type: str = "jsonl",  # jsonl or json
        buffer_size: int = 100,
        flush_interval: float = 5.0,
    ):
        self.file_path = Path(file_path)
        self.format_type = format_type
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval

        # Buffer for async writes
        self.buffer: List[TraceEvent] = []
        self.buffer_lock = threading.Lock()

        # Auto-flush thread
        self.flush_thread = None
        self.stop_flush_thread = False

        self._initialize_file()
        self._start_flush_thread()

    def _initialize_file(self):
        """Initialize file if it doesn't exist"""
        if not self.file_path.exists():
            # Create directory if it doesn't exist
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            # Initialize based on format
            if self.format_type == "json":
                # Create empty JSON array
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump([], f)
            else:
                # Create empty JSONL file
                self.file_path.touch()

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
            if self.format_type == "json":
                self._flush_json()
            else:
                self._flush_jsonl()

            # Clear buffer
            self.buffer.clear()

        except Exception as e:
            print(f"Error flushing JSON buffer: {e}")

    def _flush_jsonl(self):
        """Flush buffer to JSONL format"""
        with open(self.file_path, "a", encoding="utf-8") as f:
            for trace in self.buffer:
                trace_dict = trace.to_dict()
                f.write(json.dumps(trace_dict, default=str) + "\n")

    def _flush_json(self):
        """Flush buffer to JSON format"""
        # Load existing data
        existing_traces = []
        if self.file_path.exists() and self.file_path.stat().st_size > 0:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    existing_traces = json.load(f)
            except json.JSONDecodeError:
                existing_traces = []

        # Add new traces
        for trace in self.buffer:
            existing_traces.append(trace.to_dict())

        # Write back to file
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(existing_traces, f, indent=2, default=str)

    def load_traces(self, session_id: Optional[str] = None) -> List[TraceEvent]:
        """Load traces from JSON file"""
        traces = []

        if not self.file_path.exists():
            return traces

        try:
            if self.format_type == "json":
                traces = self._load_json()
            else:
                traces = self._load_jsonl()

            # Filter by session if specified
            if session_id:
                traces = [t for t in traces if t.session_id == session_id]

        except Exception as e:
            print(f"Error loading traces from JSON: {e}")

        return traces

    def _load_json(self) -> List[TraceEvent]:
        """Load traces from JSON format"""
        traces = []

        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

            for trace_dict in data:
                trace = TraceEvent.from_dict(trace_dict)
                traces.append(trace)

        return traces

    def _load_jsonl(self) -> List[TraceEvent]:
        """Load traces from JSONL format"""
        traces = []

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        trace_dict = json.loads(line)
                        trace = TraceEvent.from_dict(trace_dict)
                        traces.append(trace)
                    except json.JSONDecodeError:
                        continue

        return traces

    def get_sessions(self) -> List[str]:
        """Get list of all session IDs"""
        traces = self.load_traces()
        sessions = set(t.session_id for t in traces if t.session_id)
        return list(sessions)

    def clear(self):
        """Clear all traces"""
        with self.buffer_lock:
            self.buffer.clear()

        # Recreate empty file
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
            "format_type": self.format_type,
            "file_path": str(self.file_path),
            "file_size": self.file_path.stat().st_size
            if self.file_path.exists()
            else 0,
        }

    def export_to_csv(self, csv_path: str):
        """Export JSON traces to CSV format for dashboard compatibility"""
        traces = self.load_traces()

        from .csv_storage import CSVStorage

        csv_storage = CSVStorage(csv_path)

        try:
            csv_storage.store_traces(traces)
            csv_storage.flush()
        finally:
            csv_storage.close()

    def query_traces(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        action_type: Optional[str] = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
    ) -> List[TraceEvent]:
        """Query traces with filters"""
        traces = self.load_traces()

        filtered_traces = []
        for trace in traces:
            # Apply filters
            if start_time and trace.timestamp < start_time:
                continue
            if end_time and trace.timestamp > end_time:
                continue
            if model_name and trace.model_name != model_name:
                continue
            if provider and trace.provider != provider:
                continue
            if action_type and trace.action_type != action_type:
                continue
            if min_cost and (not trace.cost_usd or trace.cost_usd < min_cost):
                continue
            if max_cost and (not trace.cost_usd or trace.cost_usd > max_cost):
                continue

            filtered_traces.append(trace)

        return filtered_traces
