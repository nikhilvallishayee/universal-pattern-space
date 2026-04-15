"""
GödelOS Cognitive Transparency Module

This module provides comprehensive cognitive transparency capabilities for the GödelOS system,
including real-time reasoning stream tracking, provenance management, and uncertainty quantification.

Key Components:
- CognitiveTransparencyManager: Central orchestrator for transparency operations
- ReasoningStreamTracker: Real-time reasoning step tracking and streaming
- ProvenanceTrackingManager: Complete audit trail management
- UncertaintyQuantificationEngine: Confidence calculation and propagation

The transparency system operates in a hybrid mode, providing both real-time high-level
progress indicators and detailed post-completion analysis.
"""

from godelOS.cognitive_transparency.manager import CognitiveTransparencyManager
from godelOS.cognitive_transparency.stream_tracker import ReasoningStreamTracker
from godelOS.cognitive_transparency.models import (
    ReasoningStep,
    ReasoningSession,
    ReasoningSummary,
    DecisionPoint,
    TransparencyLevel,
    StepType,
    DetailLevel
)

__all__ = [
    'CognitiveTransparencyManager',
    'ReasoningStreamTracker',
    'ReasoningStep',
    'ReasoningSession',
    'ReasoningSummary',
    'DecisionPoint',
    'TransparencyLevel',
    'StepType',
    'DetailLevel'
]

__version__ = "1.0.0"