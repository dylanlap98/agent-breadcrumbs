"""
Main HTTP tracer class that orchestrates tracing
"""

import asyncio
import threading
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import atexit

from ..models.trace import TraceEvent
from ..models.config import TracerConfig
from ..storage.csv_storage import CSVStorage
from ..storage.json_storage import JSONStorage
from .http_interceptor import HTTPInterceptor


class HTTPTracer:
    """
    Main tracer class that coordinates HTTP interception and storage
    """

    def __init__(self, config: TracerConfig = None, storage=None):
        self.config = config or TracerConfig()

        # Initialize storage
        if storage is None:
            if self.config.output_format.lower() == "csv":
                storage = CSVStorage(
                    self.config.output_file,
                    buffer_size=self.config.buffer_size,
                    flush_interval=self.config.flush_interval,
                )
            else:
                storage = JSONStorage(
                    self.config.output_file,
                    format_type=self.config.output_format,
                    buffer_size=self.config.buffer_size,
                    flush_interval=self.config.flush_interval,
                )

        self.storage = storage

        # Initialize interceptor
        self.interceptor = HTTPInterceptor(
            config=self.config, trace_callback=self._handle_trace
        )

        # State
        self.active = False
        self.dashboard_server = None

        # Register cleanup
        atexit.register(self.stop)

    def start(self):
        """Start HTTP tracing"""
        if self.active:
            return

        print(f"🔍 Starting Agent Breadcrumbs HTTP Tracer")
        print(f"   Session ID: {self.config.session_id}")
        print(f"   Output: {self.config.output_file}")
        print(f"   Format: {self.config.output_format}")

        # Start interceptor
        self.interceptor.start()

        # Start dashboard if enabled
        if self.config.dashboard_enabled:
            self._start_dashboard()

        self.active = True
        print(f"✅ HTTP Tracer active - all LLM calls will be traced")

    def stop(self):
        """Stop HTTP tracing and cleanup"""
        if not self.active:
            return

        print("🛑 Stopping Agent Breadcrumbs HTTP Tracer")

        # Stop interceptor
        self.interceptor.stop()

        # Stop dashboard
        if self.dashboard_server:
            self._stop_dashboard()

        # Close storage
        if self.storage:
            self.storage.close()

        self.active = False
        print("✅ HTTP Tracer stopped")

    def _handle_trace(self, trace: TraceEvent):
        """Handle incoming trace events"""
        # Add cost calculation if missing
        if trace.cost_usd is None and trace.token_usage:
            trace.cost_usd = self._calculate_cost(trace)

        # Store trace
        self.storage.store_trace(trace)

        # Print to console for development
        if trace.user_input:
            print(
                f"💬 Traced: {trace.user_input[:50]}{'...' if len(trace.user_input) > 50 else ''}"
            )
        elif trace.tool_calls:
            tools = ", ".join([tc.name for tc in trace.tool_calls])
            print(f"🔧 Traced: Tool calls - {tools}")

    def _calculate_cost(self, trace: TraceEvent) -> Optional[float]:
        """Calculate cost based on token usage and model"""
        if not trace.token_usage or not trace.model_name:
            return None

        # Simplified cost calculation - extend based on actual pricing
        cost_per_1k_tokens = {
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.00015,
            "gpt-3.5-turbo": 0.002,
            "claude-3-opus": 0.015,
            "claude-3-sonnet": 0.003,
            "claude-3-haiku": 0.00025,
        }

        model_key = None
        for key in cost_per_1k_tokens.keys():
            if key in trace.model_name.lower():
                model_key = key
                break

        if model_key and trace.token_usage.total_tokens:
            cost_per_token = cost_per_1k_tokens[model_key] / 1000
            return trace.token_usage.total_tokens * cost_per_token

        return None

    def _start_dashboard(self):
        """Start the dashboard server"""
        try:
            from ..dashboard.server import DashboardServer

            self.dashboard_server = DashboardServer(
                storage=self.storage,
                host=self.config.dashboard_host,
                port=self.config.dashboard_port,
            )

            # Start in separate thread
            dashboard_thread = threading.Thread(
                target=self.dashboard_server.start, daemon=True
            )
            dashboard_thread.start()

            print(
                f"📊 Dashboard available at http://{self.config.dashboard_host}:{self.config.dashboard_port}"
            )

        except ImportError:
            print(
                "⚠️  Dashboard dependencies not available. Install with: pip install agent-breadcrumbs[dashboard]"
            )
        except Exception as e:
            print(f"⚠️  Could not start dashboard: {e}")

    def _stop_dashboard(self):
        """Stop the dashboard server"""
        if self.dashboard_server:
            try:
                self.dashboard_server.stop()
            except Exception as e:
                print(f"Warning: Error stopping dashboard: {e}")

    def get_session_traces(self, session_id: Optional[str] = None) -> List[TraceEvent]:
        """Get traces for a specific session"""
        if session_id is None:
            session_id = self.config.session_id

        return self.storage.load_traces(session_id=session_id)

    def get_all_traces(self) -> List[TraceEvent]:
        """Get all traces across all sessions"""
        return self.storage.load_traces()

    def get_sessions(self) -> List[str]:
        """Get list of all session IDs"""
        return self.storage.get_sessions()

    def export_traces(
        self, format: str = "csv", output_file: Optional[str] = None
    ) -> str:
        """Export traces to a file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"agent_traces_export_{timestamp}.{format}"

        traces = self.get_all_traces()

        if format.lower() == "csv":
            from ..storage.csv_storage import CSVStorage

            export_storage = CSVStorage(output_file)
            export_storage.store_traces(traces)
            export_storage.close()

        elif format.lower() in ["json", "jsonl"]:
            from ..storage.json_storage import JSONStorage

            export_storage = JSONStorage(output_file, format_type=format.lower())
            export_storage.store_traces(traces)
            export_storage.close()

        else:
            raise ValueError(f"Unsupported export format: {format}")

        print(f"📁 Exported {len(traces)} traces to {output_file}")
        return output_file

    def get_stats(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        stats = self.storage.get_stats()
        stats.update(
            {
                "active": self.active,
                "session_id": self.config.session_id,
                "dashboard_enabled": self.config.dashboard_enabled,
                "dashboard_url": f"http://{self.config.dashboard_host}:{self.config.dashboard_port}"
                if self.config.dashboard_enabled
                else None,
            }
        )
        return stats

    def print_summary(self):
        """Print a summary of traced interactions"""
        stats = self.get_stats()

        print("\n" + "=" * 50)
        print("📊 Agent Breadcrumbs Tracing Summary")
        print("=" * 50)
        print(f"Total Traces: {stats['total_traces']}")
        print(f"Sessions: {stats['total_sessions']}")
        print(f"Total Cost: ${stats['total_cost']:.6f}")
        print(f"Total Tokens: {stats['total_tokens']:,}")
        print(f"Avg Duration: {stats['avg_duration']:.0f}ms")
        print(f"Output File: {stats.get('file_path', 'N/A')}")

        if stats.get("dashboard_url"):
            print(f"Dashboard: {stats['dashboard_url']}")

        print("=" * 50)

    def new_session(self) -> str:
        """Start a new session and return the session ID"""
        import uuid

        new_session_id = str(uuid.uuid4())
        self.config.session_id = new_session_id
        print(f"🆕 Started new session: {new_session_id}")
        return new_session_id

    def set_session(self, session_id: str):
        """Set the current session ID"""
        self.config.session_id = session_id
        print(f"🔄 Switched to session: {session_id}")

    def flush(self):
        """Force flush any buffered traces to storage"""
        if self.storage:
            self.storage.flush()
            print("💾 Flushed traces to storage")

    def clear_traces(self, confirm: bool = False):
        """Clear all stored traces (requires confirmation)"""
        if not confirm:
            print("⚠️  Use clear_traces(confirm=True) to confirm deletion of all traces")
            return

        if self.storage:
            self.storage.clear()
            print("🗑️  Cleared all traces")
