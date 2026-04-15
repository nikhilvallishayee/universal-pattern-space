"""
Knowledge Store Interface.

This module provides a unified API for storing, retrieving, updating, and deleting
knowledge from the underlying knowledge base backend(s).
"""

from godelOS.core_kr.knowledge_store.interface import (
    KnowledgeStoreInterface,
    KnowledgeStoreBackend,
    InMemoryKnowledgeStore,
    DynamicContextModel,
    CachingMemoizationLayer
)
try:
    from godelOS.core_kr.knowledge_store.chroma_store import ChromaKnowledgeStore
except ImportError:  # chromadb not installed in slim CI environments
    ChromaKnowledgeStore = None  # type: ignore[assignment,misc]

try:
    from godelOS.core_kr.knowledge_store.hot_reloader import OntologyHotReloader
except ImportError:
    OntologyHotReloader = None  # type: ignore[assignment,misc]

__all__ = [
    "KnowledgeStoreInterface",
    "KnowledgeStoreBackend",
    "InMemoryKnowledgeStore",
    "ChromaKnowledgeStore",
    "OntologyHotReloader",
    "DynamicContextModel",
    "CachingMemoizationLayer"
]