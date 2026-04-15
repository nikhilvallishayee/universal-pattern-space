"""
Unit tests for the MetaKnowledgeBase.
"""

import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os
import time
import json

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


class TestMetaKnowledgeBase(unittest.TestCase):
    """Test cases for the MetaKnowledgeBase."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks
        self.mock_kr_interface = MagicMock()
        self.mock_type_system = MagicMock()
        
        # Configure mocks
        self.mock_kr_interface.list_contexts.return_value = []
        
        # Add assert_statement method to the mock
        # This is needed because unittest.mock treats methods starting with "assert" specially
        self.mock_kr_interface.assert_statement = MagicMock()
        self.mock_kr_interface.retract_matching = MagicMock()
        
        # Create a temporary directory for persistence
        self.temp_dir = tempfile.mkdtemp()
        
        # Create MetaKnowledgeBase instance
        self.meta_knowledge = MetaKnowledgeBase(
            kr_system_interface=self.mock_kr_interface,
            type_system=self.mock_type_system,
            meta_knowledge_context_id="TEST_META_KNOWLEDGE",
            persistence_directory=self.temp_dir
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up the temporary directory
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        
        os.rmdir(self.temp_dir)
    
    def test_initialization(self):
        """Test initialization of MetaKnowledgeBase."""
        # Verify context creation
        self.mock_kr_interface.create_context.assert_called_once_with(
            "TEST_META_KNOWLEDGE", None, "meta_knowledge"
        )
        
        # Verify repositories are initialized
        self.assertIsNotNone(self.meta_knowledge.component_performance_repo)
        self.assertIsNotNone(self.meta_knowledge.reasoning_strategy_repo)
        self.assertIsNotNone(self.meta_knowledge.resource_usage_repo)
        self.assertIsNotNone(self.meta_knowledge.failure_pattern_repo)
        self.assertIsNotNone(self.meta_knowledge.system_capability_repo)
        self.assertIsNotNone(self.meta_knowledge.optimization_hint_repo)
    
    def test_add_component_performance_model(self):
        """Test adding a component performance model."""
        # Add a component performance model
        entry_id = self.meta_knowledge.add_component_performance_model(
            component_id="TestComponent",
            average_response_time_ms=50.0,
            throughput_per_second=100.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.2, "Memory": 0.3},
            performance_factors={"batch_size": 0.5},
            confidence=0.9
        )
        
        # Verify entry was added
        self.assertIsNotNone(entry_id)
        self.assertIn("component_performance_TestComponent", entry_id)
        
        # Verify entry can be retrieved
        model = self.meta_knowledge.get_component_performance_model("TestComponent")
        self.assertIsNotNone(model)
        self.assertEqual(model.component_id, "TestComponent")
        self.assertEqual(model.average_response_time_ms, 50.0)
        self.assertEqual(model.throughput_per_second, 100.0)
        self.assertEqual(model.failure_rate, 0.05)
        self.assertEqual(model.resource_usage, {"CPU": 0.2, "Memory": 0.3})
        self.assertEqual(model.performance_factors, {"batch_size": 0.5})
        self.assertEqual(model.confidence, 0.9)
        
        # Verify entry was persisted
        persisted_files = os.listdir(self.temp_dir)
        self.assertEqual(len(persisted_files), 1)
        
        # Verify KR system assertion
        self.mock_kr_interface.assert_statement.assert_called_once()
    
    def test_add_reasoning_strategy_model(self):
        """Test adding a reasoning strategy model."""
        # Add a reasoning strategy model
        entry_id = self.meta_knowledge.add_reasoning_strategy_model(
            strategy_name="TestStrategy",
            success_rate=0.8,
            average_duration_ms=100.0,
            applicable_problem_types=["type1", "type2"],
            preconditions=["precond1"],
            resource_requirements={"CPU": 0.3},
            effectiveness_by_domain={"domain1": 0.9}
        )
        
        # Verify entry was added
        self.assertIsNotNone(entry_id)
        self.assertIn("reasoning_strategy_TestStrategy", entry_id)
        
        # Verify entry can be retrieved
        model = self.meta_knowledge.get_reasoning_strategy_model("TestStrategy")
        self.assertIsNotNone(model)
        self.assertEqual(model.strategy_name, "TestStrategy")
        self.assertEqual(model.success_rate, 0.8)
        self.assertEqual(model.average_duration_ms, 100.0)
        self.assertEqual(model.applicable_problem_types, ["type1", "type2"])
        self.assertEqual(model.preconditions, ["precond1"])
        self.assertEqual(model.resource_requirements, {"CPU": 0.3})
        self.assertEqual(model.effectiveness_by_domain, {"domain1": 0.9})
    
    def test_add_resource_usage_pattern(self):
        """Test adding a resource usage pattern."""
        # Add a resource usage pattern
        entry_id = self.meta_knowledge.add_resource_usage_pattern(
            resource_name="CPU",
            average_usage=0.5,
            peak_usage=0.8,
            usage_trend="increasing",
            periodic_patterns={"daily": {"peak": "12:00", "trough": "03:00"}},
            correlations={"Memory": 0.7}
        )
        
        # Verify entry was added
        self.assertIsNotNone(entry_id)
        self.assertIn("resource_usage_CPU", entry_id)
        
        # Verify entry can be retrieved
        pattern = self.meta_knowledge.get_resource_usage_pattern("CPU")
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.resource_name, "CPU")
        self.assertEqual(pattern.average_usage, 0.5)
        self.assertEqual(pattern.peak_usage, 0.8)
        self.assertEqual(pattern.usage_trend, "increasing")
        self.assertEqual(pattern.periodic_patterns, {"daily": {"peak": "12:00", "trough": "03:00"}})
        self.assertEqual(pattern.correlations, {"Memory": 0.7})
    
    def test_add_failure_pattern(self):
        """Test adding a failure pattern."""
        # Add a failure pattern
        entry_id = self.meta_knowledge.add_failure_pattern(
            pattern_name="TestFailure",
            affected_components=["ComponentA", "ComponentB"],
            symptoms=["high_latency", "timeout"],
            root_causes=["resource_contention"],
            frequency=0.05,
            severity=0.8,
            mitigation_strategies=["increase_resources"]
        )
        
        # Verify entry was added
        self.assertIsNotNone(entry_id)
        self.assertIn("failure_pattern_TestFailure", entry_id)
        
        # Verify entry can be retrieved
        patterns = self.meta_knowledge.get_failure_patterns_for_component("ComponentA")
        self.assertEqual(len(patterns), 1)
        pattern = patterns[0]
        self.assertEqual(pattern.pattern_name, "TestFailure")
        self.assertEqual(pattern.affected_components, ["ComponentA", "ComponentB"])
        self.assertEqual(pattern.symptoms, ["high_latency", "timeout"])
        self.assertEqual(pattern.root_causes, ["resource_contention"])
        self.assertEqual(pattern.frequency, 0.05)
        self.assertEqual(pattern.severity, 0.8)
        self.assertEqual(pattern.mitigation_strategies, ["increase_resources"])
    
    def test_add_system_capability(self):
        """Test adding a system capability."""
        # Add a system capability
        entry_id = self.meta_knowledge.add_system_capability(
            capability_name="TestCapability",
            capability_description="A test capability",
            performance_level=0.7,
            reliability=0.9,
            resource_requirements={"CPU": 0.3, "Memory": 0.2},
            dependencies=["OtherCapability"],
            limitations=["limited_scale"]
        )
        
        # Verify entry was added
        self.assertIsNotNone(entry_id)
        self.assertIn("system_capability_TestCapability", entry_id)
        
        # Verify entry can be retrieved
        capability = self.meta_knowledge.get_system_capability("TestCapability")
        self.assertIsNotNone(capability)
        self.assertEqual(capability.capability_name, "TestCapability")
        self.assertEqual(capability.capability_description, "A test capability")
        self.assertEqual(capability.performance_level, 0.7)
        self.assertEqual(capability.reliability, 0.9)
        self.assertEqual(capability.resource_requirements, {"CPU": 0.3, "Memory": 0.2})
        self.assertEqual(capability.dependencies, ["OtherCapability"])
        self.assertEqual(capability.limitations, ["limited_scale"])
    
    def test_add_optimization_hint(self):
        """Test adding an optimization hint."""
        # Add an optimization hint
        entry_id = self.meta_knowledge.add_optimization_hint(
            target_component="TestComponent",
            optimization_type="parameter_tuning",
            expected_improvement=0.2,
            implementation_difficulty=0.3,
            preconditions=["stable_load"],
            side_effects=["increased_memory"]
        )
        
        # Verify entry was added
        self.assertIsNotNone(entry_id)
        self.assertIn("optimization_hint_TestComponent_parameter_tuning", entry_id)
        
        # Verify entry can be retrieved
        hints = self.meta_knowledge.get_optimization_hints_for_component("TestComponent")
        self.assertEqual(len(hints), 1)
        hint = hints[0]
        self.assertEqual(hint.target_component, "TestComponent")
        self.assertEqual(hint.optimization_type, "parameter_tuning")
        self.assertEqual(hint.expected_improvement, 0.2)
        self.assertEqual(hint.implementation_difficulty, 0.3)
        self.assertEqual(hint.preconditions, ["stable_load"])
        self.assertEqual(hint.side_effects, ["increased_memory"])
    
    def test_update_entry(self):
        """Test updating a meta-knowledge entry."""
        # Add an entry
        entry_id = self.meta_knowledge.add_component_performance_model(
            component_id="TestComponent",
            average_response_time_ms=50.0,
            throughput_per_second=100.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.2}
        )
        
        # Get the entry
        model = self.meta_knowledge.get_component_performance_model("TestComponent")
        
        # Modify the entry
        model.average_response_time_ms = 40.0
        model.throughput_per_second = 120.0
        
        # Update the entry
        self.meta_knowledge.update_entry(model)
        
        # Verify entry was updated
        updated_model = self.meta_knowledge.get_component_performance_model("TestComponent")
        self.assertEqual(updated_model.average_response_time_ms, 40.0)
        self.assertEqual(updated_model.throughput_per_second, 120.0)
        
        # Verify KR system update
        self.assertEqual(self.mock_kr_interface.retract_matching.call_count, 1)
        self.assertEqual(self.mock_kr_interface.assert_statement.call_count, 2)  # Initial + update
    
    def test_remove_entry(self):
        """Test removing a meta-knowledge entry."""
        # Add an entry
        entry_id = self.meta_knowledge.add_component_performance_model(
            component_id="TestComponent",
            average_response_time_ms=50.0,
            throughput_per_second=100.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.2}
        )
        
        # Verify entry exists
        self.assertIsNotNone(self.meta_knowledge.get_entry(entry_id))
        
        # Remove the entry
        result = self.meta_knowledge.remove_entry(entry_id)
        
        # Verify removal was successful
        self.assertTrue(result)
        self.assertIsNone(self.meta_knowledge.get_entry(entry_id))
        self.assertIsNone(self.meta_knowledge.get_component_performance_model("TestComponent"))
        
        # Verify KR system retraction
        self.assertEqual(self.mock_kr_interface.retract_matching.call_count, 1)
    
    def test_get_entries_by_type(self):
        """Test getting entries by type."""
        # Add entries of different types
        self.meta_knowledge.add_component_performance_model(
            component_id="Component1",
            average_response_time_ms=50.0,
            throughput_per_second=100.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.2}
        )
        self.meta_knowledge.add_component_performance_model(
            component_id="Component2",
            average_response_time_ms=60.0,
            throughput_per_second=90.0,
            failure_rate=0.06,
            resource_usage={"CPU": 0.3}
        )
        self.meta_knowledge.add_reasoning_strategy_model(
            strategy_name="Strategy1",
            success_rate=0.8,
            average_duration_ms=100.0,
            applicable_problem_types=["type1"],
            preconditions=[],
            resource_requirements={}
        )
        
        # Get entries by type
        component_models = self.meta_knowledge.get_entries_by_type(MetaKnowledgeType.COMPONENT_PERFORMANCE)
        strategy_models = self.meta_knowledge.get_entries_by_type(MetaKnowledgeType.REASONING_STRATEGY)
        
        # Verify correct entries were returned
        self.assertEqual(len(component_models), 2)
        self.assertEqual(len(strategy_models), 1)
        
        component_ids = [model.component_id for model in component_models]
        self.assertIn("Component1", component_ids)
        self.assertIn("Component2", component_ids)
        
        strategy_names = [model.strategy_name for model in strategy_models]
        self.assertIn("Strategy1", strategy_names)
    
    def test_search_entries(self):
        """Test searching for entries."""
        # Add entries with different keywords
        self.meta_knowledge.add_component_performance_model(
            component_id="FastComponent",
            average_response_time_ms=10.0,
            throughput_per_second=200.0,
            failure_rate=0.01,
            resource_usage={"CPU": 0.5}
        )
        self.meta_knowledge.add_component_performance_model(
            component_id="SlowComponent",
            average_response_time_ms=100.0,
            throughput_per_second=50.0,
            failure_rate=0.1,
            resource_usage={"CPU": 0.2}
        )
        
        # Search for entries
        fast_entries = self.meta_knowledge.search_entries(["fast"])
        slow_entries = self.meta_knowledge.search_entries(["slow"])
        component_entries = self.meta_knowledge.search_entries(["component"])
        
        # Verify correct entries were returned
        self.assertEqual(len(fast_entries), 1)
        self.assertEqual(len(slow_entries), 1)
        self.assertEqual(len(component_entries), 2)
        
        self.assertEqual(fast_entries[0].component_id, "FastComponent")
        self.assertEqual(slow_entries[0].component_id, "SlowComponent")
    
    def test_export_to_json(self):
        """Test exporting entries to JSON."""
        # Add some entries
        self.meta_knowledge.add_component_performance_model(
            component_id="TestComponent",
            average_response_time_ms=50.0,
            throughput_per_second=100.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.2}
        )
        self.meta_knowledge.add_reasoning_strategy_model(
            strategy_name="TestStrategy",
            success_rate=0.8,
            average_duration_ms=100.0,
            applicable_problem_types=["type1"],
            preconditions=[],
            resource_requirements={}
        )
        
        # Export to JSON
        export_path = os.path.join(self.temp_dir, "export.json")
        self.meta_knowledge.export_to_json(export_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(export_path))
        
        # Verify file contains expected data
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data), 2)
        
        # Check for component performance model
        component_entries = [entry for entry in data if "component_id" in entry]
        self.assertEqual(len(component_entries), 1)
        self.assertEqual(component_entries[0]["component_id"], "TestComponent")
        
        # Check for reasoning strategy model
        strategy_entries = [entry for entry in data if "strategy_name" in entry]
        self.assertEqual(len(strategy_entries), 1)
        self.assertEqual(strategy_entries[0]["strategy_name"], "TestStrategy")


if __name__ == '__main__':
    unittest.main()