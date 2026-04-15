# -*- coding: utf-8 -*-
"""
GödelOS Backend Package

FastAPI backend that interfaces with the GödelOS system to provide:
- Natural language query processing
- Knowledge base management  
- Real-time cognitive state monitoring
- WebSocket streaming for cognitive events
"""

__version__ = "1.0.0"
__author__ = "GödelOS Team"
__description__ = "Backend API for the GödelOS web demonstration interface"

# Lazy imports to avoid circular dependencies
def get_app():
    """Get the FastAPI app instance."""
    from .main import app
    return app

def get_integration():
    """Get the GodelOS integration instance."""
    from .godelos_integration import GodelOSIntegration
    return GodelOSIntegration

def get_websocket_manager():
    """Get the WebSocket manager instance."""
    from .websocket_manager import WebSocketManager
    return WebSocketManager

# Only import models (no circular dependencies)
from .models import *  # noqa: F401,F403 (re-export models for convenience)

# Note: Do not expose names that are not defined at module import time to avoid
# confusing import errors during test collection. Consumers should import
# concrete objects from their defining modules (e.g., backend.config_manager).
