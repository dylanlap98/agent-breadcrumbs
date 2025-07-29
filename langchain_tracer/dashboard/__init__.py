"""
Dashboard server for viewing traces
"""

try:
    from .server import DashboardServer, start_dashboard

    __all__ = ["DashboardServer", "start_dashboard"]
except ImportError:
    # Dashboard dependencies not available
    def start_dashboard(*args, **kwargs):
        print("⚠️  Dashboard dependencies not available")
        print("💡 Install with: pip install flask flask-cors")

    __all__ = ["start_dashboard"]
