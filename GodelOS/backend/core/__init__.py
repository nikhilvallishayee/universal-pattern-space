"""
GodelOS Core Architecture Components

This package contains the core components of the modernized GodelOS architecture:
- CognitiveManager: Central orchestrator for all cognitive processes
- AgenticDaemonSystem: Autonomous background processing and system evolution
"""

import logging as _logging

try:
    from .cognitive_manager import CognitiveManager, get_cognitive_manager
    from .agentic_daemon_system import AgenticDaemonSystem, get_agentic_daemon_system

    __all__ = [
        "CognitiveManager",
        "get_cognitive_manager",
        "AgenticDaemonSystem",
        "get_agentic_daemon_system",
    ]
except ImportError as _exc:
    _logging.getLogger(__name__).warning(
        "Core architecture imports unavailable (optional dependency missing): %s", _exc
    )
    __all__ = []
