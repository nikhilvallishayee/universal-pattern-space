"""Compatibility shim: re-exports WebSocketManager from unified_server."""

from backend.unified_server import WebSocketManager

__all__ = ["WebSocketManager"]
