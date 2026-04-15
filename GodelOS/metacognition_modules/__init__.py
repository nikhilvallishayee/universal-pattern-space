"""
Enhanced Metacognition Modules Package.

This package provides autonomous knowledge acquisition and real-time
cognitive streaming capabilities for the GödelOS system.
"""

# Import cognitive models first (no dependencies)
from .cognitive_models import (
    KnowledgeGap,
    CognitiveEvent,
    AcquisitionPlan,
    AcquisitionResult,
    CognitiveEventType,
    GranularityLevel,
    KnowledgeGapType,
    AcquisitionStrategy,
    StreamingMetrics,
    AutonomousLearningMetrics,
    serialize_cognitive_event,
    deserialize_cognitive_event,
    filter_events_by_granularity,
    create_gap_from_query_result
)

# Note: Import manager separately to avoid circular dependencies
# from .enhanced_metacognition_manager import EnhancedMetacognitionManager

from .knowledge_gap_detector import KnowledgeGapDetector

from .autonomous_knowledge_acquisition import AutonomousKnowledgeAcquisition

from .stream_coordinator import StreamOfConsciousnessCoordinator

from .enhanced_self_monitoring import (
    EnhancedSelfMonitoringModule,
    AutonomousLearningHealthMetrics,
    CognitiveStreamingHealthMetrics
)

__all__ = [
    # Main manager
    'EnhancedMetacognitionManager',
    'AutonomousLearningConfig',
    'CognitiveStreamingConfig',
    
    # Core models
    'KnowledgeGap',
    'CognitiveEvent',
    'AcquisitionPlan',
    'AcquisitionResult',
    'CognitiveEventType',
    'GranularityLevel',
    'KnowledgeGapType',
    'AcquisitionStrategy',
    'StreamingMetrics',
    'AutonomousLearningMetrics',
    
    # Utility functions
    'serialize_cognitive_event',
    'deserialize_cognitive_event',
    'filter_events_by_granularity',
    'create_gap_from_query_result',
    
    # Core components
    'KnowledgeGapDetector',
    'AutonomousKnowledgeAcquisition',
    'StreamOfConsciousnessCoordinator',
    
    # Enhanced monitoring
    'EnhancedSelfMonitoringModule',
    'AutonomousLearningHealthMetrics',
    'CognitiveStreamingHealthMetrics'
]

__version__ = "1.0.0"
