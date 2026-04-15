"""
Module 9: Common Sense & Context System

This module implements common sense reasoning and context-aware operations for GödelOS.
It provides interfaces to external knowledge bases, context management, contextualized
knowledge retrieval, and default reasoning capabilities.

Components:
- ExternalCommonSenseKB_Interface (ECSKI): Interface to external common sense knowledge bases
- ContextEngine (CE): Manages the current context of reasoning and interaction
- ContextualizedRetriever (CR): Implements context-aware knowledge retrieval
- DefaultReasoningModule (DRM): Implements default reasoning mechanisms
- CommonSenseContextManager: Coordinates the different common sense and context components
"""

from godelOS.common_sense.external_kb_interface import ExternalCommonSenseKB_Interface
from godelOS.common_sense.context_engine import ContextEngine
from godelOS.common_sense.contextualized_retriever import ContextualizedRetriever
from godelOS.common_sense.default_reasoning import DefaultReasoningModule
from godelOS.common_sense.manager import CommonSenseContextManager

__all__ = [
    'ExternalCommonSenseKB_Interface',
    'ContextEngine',
    'ContextualizedRetriever',
    'DefaultReasoningModule',
    'CommonSenseContextManager',
]