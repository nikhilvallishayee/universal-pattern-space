"""
GodelOS Unified Knowledge Store Package

This package implements the UnifiedKnowledgeStore component of the UnifiedAgentCore
architecture, which provides integrated knowledge management across different
memory types.

Key components:
- SemanticMemory: Stores conceptual knowledge
- EpisodicMemory: Stores experiential knowledge with temporal aspects
- WorkingMemory: Stores active, temporary knowledge with priority management
- KnowledgeIntegrator: Integrates knowledge across memory types
"""

from godelOS.unified_agent_core.knowledge_store.interfaces import (
    UnifiedKnowledgeStoreInterface,
    MemoryInterface,
    SemanticMemoryInterface,
    EpisodicMemoryInterface,
    WorkingMemoryInterface,
    KnowledgeIntegratorInterface
)