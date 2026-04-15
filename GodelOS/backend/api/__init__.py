"""
GodelOS Unified API Package

This package contains the unified API contracts and routing for the GodelOS system:
- Versioned API endpoints following the architectural specification
- Legacy compatibility endpoints
- Streaming endpoints for real-time updates
"""

from .unified_api import unified_api_router, legacy_api_router

__all__ = [
    "unified_api_router",
    "legacy_api_router"
]
