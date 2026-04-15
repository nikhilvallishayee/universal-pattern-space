"""
GödelOS Scalability & Efficiency System.

This module provides components for ensuring that GödelOS can handle large-scale
knowledge bases and perform efficient reasoning. It includes:

1. Persistent Knowledge Base Backend & Router (Module 6.1)
2. Query Optimizer (Module 6.2)
3. Rule Compiler (Module 6.3)
4. Parallel Inference Manager (Module 6.4)
5. Caching & Memoization Layer (Module 6.5)
"""

from godelOS.scalability.persistent_kb import PersistentKBBackend, KBRouter
from godelOS.scalability.query_optimizer import QueryOptimizer
from godelOS.scalability.rule_compiler import RuleCompiler
from godelOS.scalability.parallel_inference import ParallelInferenceManager
from godelOS.scalability.caching import CachingSystem
from godelOS.scalability.manager import ScalabilityManager

__all__ = [
    'PersistentKBBackend',
    'KBRouter',
    'QueryOptimizer',
    'RuleCompiler',
    'ParallelInferenceManager',
    'CachingSystem',
    'ScalabilityManager',
]