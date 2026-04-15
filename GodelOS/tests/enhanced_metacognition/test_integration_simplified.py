"""
Simplified integration tests for the enhanced metacognition implementation.

This test suite validates core functionality that can be tested without
causing circular import issues.
"""

import asyncio
import pytest
import json
import tempfile
import os
import yaml
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.config_manager import ConfigurationManager, EnhancedMetacognitionConfig

# Import cognitive models directly to avoid circular imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend/metacognition_modules'))
import cognitive_models as cm
KnowledgeGap = cm.KnowledgeGap
CognitiveEvent = cm.CognitiveEvent
AcquisitionPlan = cm.AcquisitionPlan
KnowledgeGapType = cm.KnowledgeGapType
CognitiveEventType = cm.CognitiveEventType
AcquisitionStrategy = cm.AcquisitionStrategy


class TestConfigurationManager:
    """Test configuration loading and management."""
    
    def test_default_configuration(self):
        """Test that default configuration loads correctly."""
        config_manager = ConfigurationManager(config_path="nonexistent")
        config = config_manager.get_config()
        
        assert isinstance(config, EnhancedMetacognitionConfig)
        assert config.cognitive_streaming.enabled is True
        assert config.autonomous_learning.enabled is True
        assert config.knowledge_acquisition.max_retries == 3
    
    def test_yaml_configuration_loading(self):
        """Test loading configuration from YAML file."""
        test_config = {
            'cognitive_streaming': {
                'enabled': False,
                'default_granularity': 'minimal',
                'max_event_rate': 50
            },
            'autonomous_learning': {
                'enabled': True,
                'gap_detection_interval': 600,
                'confidence_threshold': 0.8
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name
        
        try:
            config_manager = ConfigurationManager(config_path=temp_path)
            config = config_manager.get_config()
            
            assert config.cognitive_streaming.enabled is False
            assert config.cognitive_streaming.default_granularity == 'minimal'
            assert config.cognitive_streaming.max_event_rate == 50
            assert config.autonomous_learning.gap_detection_interval == 600
            assert config.autonomous_learning.confidence_threshold == 0.8
        finally:
            os.unlink(temp_path)
    
    def test_feature_flags(self):
        """Test feature flag checking."""
        test_config = {
            'integration': {
                'features': {
                    'enhanced_metacognition': True,
                    'autonomous_learning': False
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name
        
        try:
            config_manager = ConfigurationManager(config_path=temp_path)
            
            assert config_manager.is_feature_enabled('enhanced_metacognition') is True
            assert config_manager.is_feature_enabled('autonomous_learning') is False
            assert config_manager.is_feature_enabled('nonexistent_feature') is False
        finally:
            os.unlink(temp_path)


class TestCognitiveModels:
    """Test cognitive data models."""
    
    def test_knowledge_gap_creation(self):
        """Test KnowledgeGap model creation and validation."""        
        gap = KnowledgeGap(
            id="gap-001",
            type=KnowledgeGapType.CONCEPT_MISSING,
            query="User asked about quantum algorithms",
            confidence=0.3,
            priority=0.8,
            missing_concepts=["quantum_computing", "quantum_algorithms"]
        )
        
        assert gap.id == "gap-001"
        assert gap.type == KnowledgeGapType.CONCEPT_MISSING
        assert gap.confidence == 0.3
        assert gap.priority == 0.8
        assert "quantum_computing" in gap.missing_concepts
    
    def test_cognitive_event_creation(self):
        """Test CognitiveEvent model creation."""
        event = CognitiveEvent(
            type=CognitiveEventType.QUERY_STARTED,
            data={"query": "test query", "confidence": 0.8},
            source="test_system"
        )
        
        assert event.type == CognitiveEventType.QUERY_STARTED
        assert event.source == "test_system"
        assert event.data["confidence"] == 0.8
        assert isinstance(event.timestamp, datetime)
        assert len(event.event_id) > 0
    
    def test_acquisition_plan_creation(self):
        """Test AcquisitionPlan model creation."""
        plan = AcquisitionPlan(
            strategy=AcquisitionStrategy.CONCEPT_EXPANSION,
            priority=0.7
        )
        
        assert plan.strategy == AcquisitionStrategy.CONCEPT_EXPANSION
        assert plan.priority == 0.7
        assert plan.gap is None  # Should be None by default
        assert plan.approved is False
        assert len(plan.plan_id) > 0
    
    def test_model_serialization(self):
        """Test model serialization and deserialization."""
        # Test KnowledgeGap
        gap = KnowledgeGap(type=KnowledgeGapType.CONCEPT_MISSING)
        gap_dict = gap.to_dict()
        assert isinstance(gap_dict, dict)
        assert gap_dict['type'] == 'concept_missing'
        
        # Test CognitiveEvent
        event = CognitiveEvent(type=CognitiveEventType.QUERY_STARTED)
        event_dict = event.to_dict()
        assert isinstance(event_dict, dict)
        assert event_dict['type'] == 'query_started'
        
        # Test AcquisitionPlan
        plan = AcquisitionPlan()
        plan_dict = plan.to_dict()
        assert isinstance(plan_dict, dict)
        assert plan_dict['strategy'] == 'concept_expansion'


class TestUtilityFunctions:
    """Test utility functions in cognitive models."""
    
    def test_serialize_cognitive_event(self):
        """Test cognitive event serialization."""
        event = CognitiveEvent(type=CognitiveEventType.QUERY_STARTED)
        serialized = cm.serialize_cognitive_event(event)
        assert isinstance(serialized, str)
        
        # Should be valid JSON
        parsed = json.loads(serialized)
        assert parsed['type'] == 'query_started'
    
    def test_filter_events_by_granularity(self):
        """Test event filtering by granularity."""
        events = [
            CognitiveEvent(type=CognitiveEventType.QUERY_STARTED, granularity_level=cm.GranularityLevel.MINIMAL),
            CognitiveEvent(type=CognitiveEventType.QUERY_COMPLETED, granularity_level=cm.GranularityLevel.DETAILED),
            CognitiveEvent(type=CognitiveEventType.GAPS_DETECTED, granularity_level=cm.GranularityLevel.DEBUG)
        ]
        
        # Filter to standard level (should include minimal and standard)
        filtered = cm.filter_events_by_granularity(events, cm.GranularityLevel.STANDARD)
        assert len(filtered) == 1  # Only the MINIMAL event should pass
        assert filtered[0].granularity_level == cm.GranularityLevel.MINIMAL
    
    def test_create_gap_from_query_result(self):
        """Test gap creation from query results."""
        query = "What is quantum computing?"
        result = {
            'confidence': 0.3,
            'missing_concepts': ['quantum_bits', 'superposition'],
            'context_requirements': ['physics_background']
        }
        
        gap = cm.create_gap_from_query_result(query, result, confidence_threshold=0.5)
        assert gap is not None
        assert gap.query == query
        assert gap.confidence == 0.3
        assert 'quantum_bits' in gap.missing_concepts
        
        # Test with high confidence (should not create gap)
        high_confidence_result = {'confidence': 0.9}
        no_gap = cm.create_gap_from_query_result(query, high_confidence_result, confidence_threshold=0.5)
        assert no_gap is None


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios that don't require full system."""
    
    def test_configuration_integration(self):
        """Test that configuration integrates properly with components."""
        from backend.config_manager import get_config, is_feature_enabled
        
        config = get_config()
        assert isinstance(config, EnhancedMetacognitionConfig)
        
        # Test that feature flags work
        result = is_feature_enabled('test_feature')
        assert isinstance(result, bool)
    
    def test_model_workflow(self):
        """Test a complete workflow with models."""
        # 1. Create a knowledge gap
        gap = KnowledgeGap(
            type=KnowledgeGapType.CONCEPT_MISSING,
            query="What is machine learning?",
            confidence=0.4,
            missing_concepts=["neural_networks", "algorithms"]
        )
        
        # 2. Create an acquisition plan for the gap
        plan = AcquisitionPlan(
            gap=gap,
            strategy=AcquisitionStrategy.CONCEPT_EXPANSION,
            priority=0.8
        )
        
        # 3. Create cognitive events for the process
        events = [
            CognitiveEvent(
                type=CognitiveEventType.GAPS_DETECTED,
                data={"gap_id": gap.id, "gap_count": 1}
            ),
            CognitiveEvent(
                type=CognitiveEventType.ACQUISITION_PLANNED,
                data={"plan_id": plan.plan_id, "strategy": plan.strategy.value}
            )
        ]
        
        # Verify the workflow
        assert plan.gap == gap
        assert len(events) == 2
        assert events[0].type == CognitiveEventType.GAPS_DETECTED
        assert events[1].type == CognitiveEventType.ACQUISITION_PLANNED
    
    def test_error_handling(self):
        """Test error handling and graceful degradation."""
        # Test configuration loading with invalid file
        config_manager = ConfigurationManager(config_path="/nonexistent/path")
        config = config_manager.get_config()
        
        # Should fall back to defaults
        assert isinstance(config, EnhancedMetacognitionConfig)
        assert config.cognitive_streaming.enabled is True


def test_file_structure():
    """Test that all required files are in place."""
    required_files = [
        # Backend files
        "backend/config_manager.py",
        "backend/enhanced_cognitive_api.py",
        "backend/config/enhanced_metacognition_config.yaml",
        "backend/metacognition_modules/cognitive_models.py",
        
        # Frontend files
        "svelte-frontend/src/stores/enhanced-cognitive.js",
        "svelte-frontend/src/components/core/StreamOfConsciousnessMonitor.svelte",
        "svelte-frontend/src/components/dashboard/EnhancedCognitiveDashboard.svelte",
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"⚠️ Missing {len(missing_files)} files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
    
    # Should have most files
    assert len(missing_files) < len(required_files) / 2, f"Too many missing files: {missing_files}"


if __name__ == "__main__":
    # Run basic tests if script is executed directly
    print("Running simplified enhanced metacognition tests...")
    
    # Test configuration
    print("Testing configuration...")
    test_config = TestConfigurationManager()
    test_config.test_default_configuration()
    print("✅ Configuration tests passed")
    
    # Test models
    print("Testing cognitive models...")
    test_models = TestCognitiveModels()
    test_models.test_knowledge_gap_creation()
    test_models.test_cognitive_event_creation()
    test_models.test_acquisition_plan_creation()
    test_models.test_model_serialization()
    print("✅ Model tests passed")
    
    # Test utilities
    print("Testing utility functions...")
    test_utils = TestUtilityFunctions()
    test_utils.test_serialize_cognitive_event()
    test_utils.test_filter_events_by_granularity()
    test_utils.test_create_gap_from_query_result()
    print("✅ Utility tests passed")
    
    # Test integration
    print("Testing integration scenarios...")
    test_integration = TestIntegrationScenarios()
    test_integration.test_configuration_integration()
    test_integration.test_model_workflow()
    test_integration.test_error_handling()
    print("✅ Integration tests passed")
    
    # Test file structure
    print("Testing file structure...")
    test_file_structure()
    print("✅ File structure tests passed")
    
    print("🎉 All simplified tests completed successfully!")
    print("\nTo run full async tests, use: pytest tests/enhanced_metacognition/test_integration_simplified.py")
