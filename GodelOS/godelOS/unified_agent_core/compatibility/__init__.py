"""
GodelOS Compatibility Package

This package provides compatibility adapters for existing GodelOS components
to work with the new UnifiedAgentCore architecture. These adapters ensure
backward compatibility while enabling the new architecture's capabilities.

Key components:
- MetacognitionAdapter: Adapts the existing MetacognitionManager to work with the new CognitiveEngine
- KnowledgeStoreAdapter: Adapts the existing KnowledgeStore to work with the new UnifiedKnowledgeStore
"""

from godelOS.unified_agent_core.compatibility.metacognition_adapter import MetacognitionAdapter
from godelOS.unified_agent_core.compatibility.knowledge_store_adapter import KnowledgeStoreAdapter