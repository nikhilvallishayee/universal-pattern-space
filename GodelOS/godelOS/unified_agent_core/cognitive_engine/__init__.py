"""
GodelOS Cognitive Engine Package

This package implements the CognitiveEngine component of the UnifiedAgentCore
architecture, which is responsible for thought processing, reflection, and ideation.

Key components:
- ThoughtStream: Manages and prioritizes thoughts
- ReflectionEngine: Provides self-analysis capabilities
- IdeationEngine: Generates creative ideas
- MetacognitiveMonitor: Monitors cognitive processes
"""

from godelOS.unified_agent_core.cognitive_engine.interfaces import (
    CognitiveEngineInterface,
    ThoughtInterface,
    ReflectionEngineInterface,
    IdeationEngineInterface,
    MetacognitiveMonitorInterface
)