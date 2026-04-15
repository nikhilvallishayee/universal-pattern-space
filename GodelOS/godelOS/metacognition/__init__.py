"""
Metacognition & Self-Improvement System for GödelOS.

This module implements the Metacognition & Self-Improvement System (Module 7) of GödelOS,
which enables the system to monitor its own cognitive processes, diagnose issues,
and make improvements to its own operation.

Components:
1. SelfMonitoringModule (SMM) - Monitors system performance, resource usage, and cognitive operations
2. MetaKnowledgeBase (MKB) - Stores and manages meta-knowledge about the system's own operation
3. CognitiveDiagnostician (CD) - Analyzes monitoring data to diagnose cognitive issues
4. SelfModificationPlanner (SMP) - Plans modifications to improve system performance
5. ModuleLibraryActivator (MLA) - Manages a library of alternative module implementations
6. MetacognitionManager - Coordinates the different metacognition components
"""

from godelOS.metacognition.self_monitoring import (
    SelfMonitoringModule,
    ReasoningEvent,
    PerformanceAnomaly,
    AnomalyType
)
from godelOS.metacognition.meta_knowledge import (
    MetaKnowledgeBase,
    MetaKnowledgeType,
    MetaKnowledgeEntry,
    ComponentPerformanceModel,
    ReasoningStrategyModel,
    ResourceUsagePattern,
    FailurePattern,
    SystemCapability,
    OptimizationHint
)
from godelOS.metacognition.diagnostician import (
    CognitiveDiagnostician,
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosisType,
    SeverityLevel
)
from godelOS.metacognition.modification_planner import (
    SelfModificationPlanner,
    ModificationProposal,
    ModificationParameter,
    ExecutionPlan,
    ModificationResult,
    ModificationType,
    ModificationStatus,
    SafetyRiskLevel
)
from godelOS.metacognition.module_library import (
    ModuleLibraryActivator,
    ModuleStatus,
    ModuleVersion,
    ModuleMetadata,
    ModuleInstance
)
from godelOS.metacognition.manager import (
    MetacognitionManager,
    MetacognitivePhase,
    MetacognitiveMode,
    MetacognitiveEvent
)

__all__ = [
    # Self-Monitoring Module
    'SelfMonitoringModule',
    'ReasoningEvent',
    'PerformanceAnomaly',
    'AnomalyType',
    
    # Meta-Knowledge Base
    'MetaKnowledgeBase',
    'MetaKnowledgeType',
    'MetaKnowledgeEntry',
    'ComponentPerformanceModel',
    'ReasoningStrategyModel',
    'ResourceUsagePattern',
    'FailurePattern',
    'SystemCapability',
    'OptimizationHint',
    
    # Cognitive Diagnostician
    'CognitiveDiagnostician',
    'DiagnosticFinding',
    'DiagnosticReport',
    'DiagnosisType',
    'SeverityLevel',
    
    # Self-Modification Planner
    'SelfModificationPlanner',
    'ModificationProposal',
    'ModificationParameter',
    'ExecutionPlan',
    'ModificationResult',
    'ModificationType',
    'ModificationStatus',
    'SafetyRiskLevel',
    
    # Module Library & Activator
    'ModuleLibraryActivator',
    'ModuleStatus',
    'ModuleVersion',
    'ModuleMetadata',
    'ModuleInstance',
    
    # Metacognition Manager
    'MetacognitionManager',
    'MetacognitivePhase',
    'MetacognitiveMode',
    'MetacognitiveEvent'
]