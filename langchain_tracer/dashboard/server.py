"""
Simple dashboard server for viewing traces
This integrates with the existing React dashboard in the dashboard/ folder
"""

import os
import json
import threading
import time
from typing import Optional, Any, Dict
from pathlib import Path
import mimetypes

try:
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    from urllib.parse import urlparse, parse_qs

    STANDARD_LIB_AVAILABLE = True
except ImportError:
    STANDARD_LIB_AVAILABLE = False

try:
    import flask
    from flask import Flask, jsonify, send_from_directory, request
    from flask_cors import CORS

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class DashboardServer:
    """
    Simple dashboard server that serves the existing React dashboard
    and provides API endpoints for trace data
    """

    def __init__(self, storage, host: str = "localhost", port: int = 8080):
        self.storage = storage
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False

        # Find dashboard files
        self.dashboard_path = self._find_dashboard_path()

        if FLASK_AVAILABLE:
            self.app = self._create_flask_app()
        elif STANDARD_LIB_AVAILABLE:
            self.app = None  # Will use simple HTTP server
        else:
            raise ImportError("No web server library available")

    def _find_dashboard_path(self) -> Optional[Path]:
        """Find the React dashboard files"""
        # Look for dashboard folder relative to this file
        current_dir = Path(__file__).parent.parent.parent
        dashboard_path = current_dir / "dashboard"

        if dashboard_path.exists() and (dashboard_path / "index.html").exists():
            return dashboard_path

        # Look for built dashboard
        dist_path = dashboard_path / "dist"
        if dist_path.exists() and (dist_path / "index.html").exists():
            return dist_path

        print(f"⚠️  Dashboard files not found at {dashboard_path}")
        return None

    def _create_flask_app(self) -> Flask:
        """Create Flask app with API endpoints"""
        app = Flask(__name__)
        CORS(app)  # Enable CORS for React dev server

        @app.route("/api/traces")
        def get_traces():
            """Get all traces or traces for a specific session"""
            session_id = request.args.get("session_id")
            traces = self.storage.load_traces(session_id=session_id)

            # Convert to CSV-compatible format for existing dashboard
            csv_traces = []
            for trace in traces:
                csv_traces.append(trace.to_csv_row())

            return jsonify(csv_traces)

        @app.route("/api/sessions")
        def get_sessions():
            """Get list of all sessions"""
            sessions = self.storage.get_sessions()
            return jsonify(sessions)

        @app.route("/api/stats")
        def get_stats():
            """Get tracing statistics"""
            stats = self.storage.get_stats()
            return jsonify(stats)

        @app.route("/api/export")
        def export_traces():
            """Export traces to CSV"""
            format_type = request.args.get("format", "csv")

            # Create temporary export
            import tempfile
            import uuid

            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f".{format_type}",
                prefix=f"traces_export_{uuid.uuid4().hex[:8]}_",
            )
            temp_file.close()

            try:
                if format_type == "csv":
                    from ..storage.csv_storage import CSVStorage

                    export_storage = CSVStorage(temp_file.name)
                    traces = self.storage.load_traces()
                    export_storage.store_traces(traces)
                    export_storage.close()

                return send_from_directory(
                    os.path.dirname(temp_file.name),
                    os.path.basename(temp_file.name),
                    as_attachment=True,
                    download_name=f"agent_traces.{format_type}",
                )
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        # Serve dashboard files
        if self.dashboard_path:

            @app.route("/")
            def serve_dashboard():
                return send_from_directory(str(self.dashboard_path), "index.html")

            @app.route("/<path:filename>")
            def serve_static(filename):
                return send_from_directory(str(self.dashboard_path), filename)
        else:

            @app.route("/")
            def no_dashboard():
                return """
                <html>
                <head><title>Agent Breadcrumbs Dashboard</title></head>
                <body>
                    <h1>Agent Breadcrumbs Dashboard</h1>
                    <p>Dashboard files not found. The dashboard should be in the 'dashboard' folder.</p>
                    <h2>API Endpoints:</h2>
                    <ul>
                        <li><a href="/api/traces">/api/traces</a> - Get all traces</li>
                        <li><a href="/api/sessions">/api/sessions</a> - Get all sessions</li>
                        <li><a href="/api/stats">/api/stats</a> - Get statistics</li>
                    </ul>
                </body>
                </html>
                """

        return app

    def start(self):
        """Start the dashboard server"""
        if self.running:
            return

        self.running = True

        try:
            if FLASK_AVAILABLE and self.app:
                # Use Flask
                self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
            else:
                # Use simple HTTP server
                self._start_simple_server()

        except Exception as e:
            print(f"❌ Failed to start dashboard server: {e}")
            self.running = False

    def _start_simple_server(self):
        """Start simple HTTP server as fallback"""
        if not STANDARD_LIB_AVAILABLE:
            print("❌ No web server available")
            return

        class TraceDashboardHandler(SimpleHTTPRequestHandler):
            def __init__(self, *args, storage=None, dashboard_path=None, **kwargs):
                self.storage = storage
                self.dashboard_path = dashboard_path
                super().__init__(*args, **kwargs)

            def do_GET(self):
                if self.path.startswith("/api/"):
                    self.handle_api_request()
                else:
                    self.serve_dashboard_file()

            def handle_api_request(self):
                """Handle API requests"""
                try:
                    if self.path == "/api/traces":
                        traces = self.storage.load_traces()
                        csv_traces = [trace.to_csv_row() for trace in traces]
                        self.send_json_response(csv_traces)

                    elif self.path == "/api/sessions":
                        sessions = self.storage.get_sessions()
                        self.send_json_response(sessions)

                    elif self.path == "/api/stats":
                        stats = self.storage.get_stats()
                        self.send_json_response(stats)

                    else:
                        self.send_error(404, "API endpoint not found")

                except Exception as e:
                    self.send_error(500, f"Server error: {e}")

            def serve_dashboard_file(self):
                """Serve dashboard files"""
                if not self.dashboard_path:
                    self.send_simple_dashboard()
                    return

                # Serve files from dashboard directory
                if self.path == "/":
                    file_path = self.dashboard_path / "index.html"
                else:
                    file_path = self.dashboard_path / self.path.lstrip("/")

                if file_path.exists() and file_path.is_file():
                    self.send_file(file_path)
                else:
                    self.send_error(404, "File not found")

            def send_json_response(self, data):
                """Send JSON response"""
                response = json.dumps(data, default=str).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(response)

            def send_file(self, file_path):
                """Send file response"""
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()

                    self.send_response(200)

                    # Set content type
                    content_type, _ = mimetypes.guess_type(str(file_path))
                    if content_type:
                        self.send_header("Content-Type", content_type)

                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)

                except Exception as e:
                    self.send_error(500, f"Error serving file: {e}")

            def send_simple_dashboard(self):
                """Send simple HTML dashboard"""
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Agent Breadcrumbs Dashboard</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; }
                        .header { background: #f0f0f0; padding: 20px; border-radius: 8px; }
                        .api-list { margin: 20px 0; }
                        .api-list a { display: block; margin: 10px 0; padding: 10px; background: #e8f4fd; border-radius: 4px; text-decoration: none; }
                        .api-list a:hover { background: #d1ecf1; }
                        .stats { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>🔍 Agent Breadcrumbs Dashboard</h1>
                        <p>HTTP-level tracing for complete LLM observability</p>
                    </div>
                    
                    <div class="stats">
                        <h2>📊 Quick Stats</h2>
                        <p id="stats-content">Loading statistics...</p>
                    </div>
                    
                    <div class="api-list">
                        <h2>🔗 API Endpoints</h2>
                        <a href="/api/traces">📋 /api/traces - View all traces</a>
                        <a href="/api/sessions">👥 /api/sessions - List sessions</a>  
                        <a href="/api/stats">📊 /api/stats - Get statistics</a>
                    </div>
                    
                    <div>
                        <h2>💡 Next Steps</h2>
                        <ul>
                            <li>Build the React dashboard by running: <code>cd dashboard && npm run build</code></li>
                            <li>Use the CSV file directly with the existing dashboard</li>
                            <li>Access the raw data via the API endpoints above</li>
                        </ul>
                    </div>
                    
                    <script>
                        // Load stats
                        fetch('/api/stats')
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('stats-content').innerHTML = 
                                    `Total Traces: ${data.total_traces}<br>` +
                                    `Total Sessions: ${data.total_sessions}<br>` +
                                    `Total Cost: ${data.total_cost?.toFixed(6) || '0.000000'}<br>` +
                                    `Total Tokens: ${data.total_tokens?.toLocaleString() || '0'}`;
                            })
                            .catch(error => {
                                document.getElementById('stats-content').innerHTML = 'Error loading stats';
                            });
                    </script>
                </body>
                </html>
                """

                response = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

        # Create handler with storage
        def handler_factory(*args, **kwargs):
            return TraceDashboardHandler(
                *args,
                storage=self.storage,
                dashboard_path=self.dashboard_path,
                **kwargs,
            )

        # Start server
        try:
            self.server = HTTPServer((self.host, self.port), handler_factory)
            print(f"📊 Dashboard server starting at http://{self.host}:{self.port}")
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("🛑 Dashboard server stopped by user")
        except Exception as e:
            print(f"❌ Dashboard server error: {e}")
        finally:
            self.running = False

    def stop(self):
        """Stop the dashboard server"""
        if not self.running:
            return

        self.running = False

        if self.server:
            self.server.shutdown()
            self.server.server_close()

        print("🛑 Dashboard server stopped")


def start_dashboard(storage=None, host: str = "localhost", port: int = 8080):
    """
    Convenience function to start dashboard server

    Args:
        storage: Storage backend (will create CSVStorage if None)
        host: Server host
        port: Server port
    """
    if storage is None:
        from ..storage.csv_storage import CSVStorage

        storage = CSVStorage()

    server = DashboardServer(storage, host, port)

    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    finally:
        server.stop()


if __name__ == "__main__":
    # Test the dashboard server
    print("🧪 Testing Dashboard Server")

    # Create test storage with mock data
    from ..storage.csv_storage import CSVStorage
    from ..models.trace import TraceEvent, TokenUsage

    storage = CSVStorage("test_dashboard_traces.csv")

    # Add some test data
    test_traces = [
        TraceEvent(
            session_id="test_session_1",
            user_input="What is machine learning?",
            ai_response="Machine learning is a subset of artificial intelligence...",
            model_name="gpt-4o-mini",
            provider="openai",
            token_usage=TokenUsage(
                prompt_tokens=20, completion_tokens=50, total_tokens=70
            ),
            cost_usd=0.000105,
            duration_ms=750.0,
        ),
        TraceEvent(
            session_id="test_session_1",
            user_input="Explain neural networks",
            ai_response="Neural networks are computational models inspired by biological neural networks...",
            model_name="gpt-4o-mini",
            provider="openai",
            token_usage=TokenUsage(
                prompt_tokens=25, completion_tokens=60, total_tokens=85
            ),
            cost_usd=0.000128,
            duration_ms=820.0,
        ),
    ]

    for trace in test_traces:
        storage.store_trace(trace)
    storage.flush()

    print("📊 Test data created")
    print("🚀 Starting dashboard server...")
    print("📱 Open http://localhost:8080 in your browser")
    print("⏹️  Press Ctrl+C to stop")

    try:
        start_dashboard(storage, port=8080)
    finally:
        # Cleanup
        import os

        if os.path.exists("test_dashboard_traces.csv"):
            os.remove("test_dashboard_traces.csv")
            print("🧹 Cleaned up test files")
