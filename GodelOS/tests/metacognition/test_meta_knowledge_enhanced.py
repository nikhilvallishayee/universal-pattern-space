"""
Enhanced unit tests for the MetaKnowledgeBase component.

This file extends the basic tests in test_meta_knowledge.py with more thorough
testing of complex methods and edge cases, focusing on:
1. Complex query and update operations
2. Concurrent access and thread safety
3. Performance under high load
4. Error handling and recovery
5. Integration with the KR system
"""

import unittest
from unittest.mock import MagicMock, patch, call
import tempfile
import os
import time
import json
import threading
import concurrent.futures
from typing import Dict, List, Optional, Set, Any

from godelOS.metacognition.meta_knowledge import (
    MetaKnowledgeBase,
    MetaKnowledgeType,
    MetaKnowledgeEntry,
    ComponentPerformanceModel,
    ReasoningStrategyModel,
    ResourceUsagePattern,
    LearningEffectivenessModel,
    FailurePattern,
    SystemCapability,
    OptimizationHint,
    MetaKnowledgeRepository
)

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker


class TestMetaKnowledgeBaseEnhanced(unittest.TestCase):
    """Enhanced test cases for the MetaKnowledgeBase with complex scenarios and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks
        self.mock_kr_interface = MagicMock()
        self.mock_type_system = MagicMock()
        
        # Configure mocks
        self.mock_kr_interface.list_contexts.return_value = []
        
        # Add assert_statement method to the mock
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
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
    
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
    
    def test_complex_search_with_multiple_criteria(self):
        """Test searching for entries with multiple complex criteria."""
        # Add various entries
        self.meta_knowledge.add_component_performance_model(
            component_id="FastComponent",
            average_response_time_ms=10.0,
            throughput_per_second=200.0,
            failure_rate=0.01,
            resource_usage={"CPU": 0.5, "Memory": 0.3},
            performance_factors={"batch_size": 0.8, "parallelism": 0.9},
            confidence=0.95
        )
        
        self.meta_knowledge.add_component_performance_model(
            component_id="SlowComponent",
            average_response_time_ms=100.0,
            throughput_per_second=50.0,
            failure_rate=0.1,
            resource_usage={"CPU": 0.2, "Memory": 0.1},
            performance_factors={"batch_size": 0.3, "parallelism": 0.2},
            confidence=0.8
        )
        
        self.meta_knowledge.add_component_performance_model(
            component_id="MediumComponent",
            average_response_time_ms=50.0,
            throughput_per_second=100.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.3, "Memory": 0.2},
            performance_factors={"batch_size": 0.5, "parallelism": 0.6},
            confidence=0.9
        )
        
        # Perform a complex search with multiple criteria
        # Start timing
        start_time = time.time()
        
        # Search for entries matching multiple keywords
        results = self.meta_knowledge.search_entries(["fast", "component"])
        
        # End timing
        search_time = time.time() - start_time
        print(f"Complex search time: {search_time * 1000:.2f} ms")
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].component_id, "FastComponent")
        
        # Search with multiple criteria
        start_time = time.time()
        
        # Get all component performance models
        all_models = self.meta_knowledge.get_entries_by_type(MetaKnowledgeType.COMPONENT_PERFORMANCE)
        
        # Filter based on multiple criteria
        filtered_models = [
            model for model in all_models
            if (model.average_response_time_ms < 60.0 and
                model.throughput_per_second > 80.0 and
                model.failure_rate < 0.06 and
                model.resource_usage.get("CPU", 0) > 0.2)
        ]
        
        # End timing
        filter_time = time.time() - start_time
        print(f"Complex filter time: {filter_time * 1000:.2f} ms")
        
        # Verify results
        self.assertEqual(len(filtered_models), 2)
        component_ids = [model.component_id for model in filtered_models]
        self.assertIn("FastComponent", component_ids)
        self.assertIn("MediumComponent", component_ids)
    
    def test_concurrent_access(self):
        """Test concurrent access to the meta-knowledge base."""
        # Number of concurrent operations
        num_concurrent = 10
        
        # Function to add a component performance model
        def add_component(index):
            return self.meta_knowledge.add_component_performance_model(
                component_id=f"Component{index}",
                average_response_time_ms=float(index * 10),
                throughput_per_second=float(200 - index * 10),
                failure_rate=float(index) / 100.0,
                resource_usage={"CPU": float(index) / 20.0}
            )
        
        # Function to get a component performance model
        def get_component(index):
            return self.meta_knowledge.get_component_performance_model(f"Component{index}")
        
        # Start timing
        start_time = time.time()
        
        # Use ThreadPoolExecutor to run operations concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            # Add components concurrently
            add_futures = [executor.submit(add_component, i) for i in range(num_concurrent)]
            add_results = [future.result() for future in concurrent.futures.as_completed(add_futures)]
            
            # Get components concurrently
            get_futures = [executor.submit(get_component, i) for i in range(num_concurrent)]
            get_results = [future.result() for future in concurrent.futures.as_completed(get_futures)]
        
        # End timing
        concurrent_time = time.time() - start_time
        print(f"Concurrent operations time: {concurrent_time * 1000:.2f} ms")
        
        # Verify results
        self.assertEqual(len(add_results), num_concurrent)
        self.assertEqual(len(get_results), num_concurrent)
        
        # Verify that all components were added and retrieved correctly
        for i in range(num_concurrent):
            component = self.meta_knowledge.get_component_performance_model(f"Component{i}")
            self.assertIsNotNone(component)
            self.assertEqual(component.component_id, f"Component{i}")
            self.assertEqual(component.average_response_time_ms, float(i * 10))
            self.assertEqual(component.throughput_per_second, float(200 - i * 10))
            self.assertEqual(component.failure_rate, float(i) / 100.0)
            self.assertEqual(component.resource_usage, {"CPU": float(i) / 20.0})
    
    def test_performance_with_large_dataset(self):
        """Test performance with a large dataset."""
        # Number of entries to add
        num_entries = 100
        
        # Start timing for adding entries
        start_time = time.time()
        
        # Add multiple entries
        for i in range(num_entries):
            self.meta_knowledge.add_component_performance_model(
                component_id=f"Component{i}",
                average_response_time_ms=float(i),
                throughput_per_second=float(200 - i),
                failure_rate=float(i) / 1000.0,
                resource_usage={"CPU": float(i) / 200.0}
            )
        
        # End timing for adding entries
        add_time = time.time() - start_time
        print(f"Time to add {num_entries} entries: {add_time * 1000:.2f} ms")
        print(f"Average time per entry: {(add_time * 1000) / num_entries:.2f} ms")
        
        # Start timing for retrieving entries
        start_time = time.time()
        
        # Retrieve all entries
        all_entries = self.meta_knowledge.get_entries_by_type(MetaKnowledgeType.COMPONENT_PERFORMANCE)
        
        # End timing for retrieving entries
        retrieve_time = time.time() - start_time
        print(f"Time to retrieve {len(all_entries)} entries: {retrieve_time * 1000:.2f} ms")
        
        # Verify results
        self.assertEqual(len(all_entries), num_entries)
        
        # Start timing for searching entries
        start_time = time.time()
        
        # Search for entries with a specific pattern
        search_results = self.meta_knowledge.search_entries(["Component5"])
        
        # End timing for searching entries
        search_time = time.time() - start_time
        print(f"Time to search for entries: {search_time * 1000:.2f} ms")
        
        # Verify search results (should find Component5, Component50, Component51, etc.)
        self.assertGreater(len(search_results), 0)
        
        # Start timing for exporting to JSON
        start_time = time.time()
        
        # Export to JSON
        export_path = os.path.join(self.temp_dir, "export_large.json")
        self.meta_knowledge.export_to_json(export_path)
        
        # End timing for exporting to JSON
        export_time = time.time() - start_time
        print(f"Time to export {num_entries} entries to JSON: {export_time * 1000:.2f} ms")
        
        # Verify export file was created
        self.assertTrue(os.path.exists(export_path))
        
        # Verify file contains expected data
        with open(export_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data), num_entries)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        # Add a component performance model
        component_id = "TestComponent"
        entry_id = self.meta_knowledge.add_component_performance_model(
            component_id=component_id,
            average_response_time_ms=50.0,
            throughput_per_second=100.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.2}
        )
        
        # Test handling of non-existent entry
        non_existent_id = "non_existent_id"
        self.assertIsNone(self.meta_knowledge.get_entry(non_existent_id))
        
        # Test handling of invalid entry type
        with self.assertRaises(KeyError):
            self.meta_knowledge.get_entries_by_type("INVALID_TYPE")
        
        # Test handling of persistence errors
        with patch('builtins.open', side_effect=IOError("Simulated IO error")):
            # Should not raise an exception, but should log an error
            self.meta_knowledge._persist_entry(self.meta_knowledge.get_entry(entry_id))
        
        # Test handling of KR system errors
        self.mock_kr_interface.assert_statement.side_effect = Exception("Simulated KR system error")
        
        # Should not raise an exception when KR system fails
        try:
            self.meta_knowledge.add_component_performance_model(
                component_id="ErrorComponent",
                average_response_time_ms=50.0,
                throughput_per_second=100.0,
                failure_rate=0.05,
                resource_usage={"CPU": 0.2}
            )
        except Exception:
            self.fail("add_component_performance_model raised an exception when KR system failed")
        
        # Reset the side effect
        self.mock_kr_interface.assert_statement.side_effect = None
        
        # Test recovery after KR system error
        recovery_id = self.meta_knowledge.add_component_performance_model(
            component_id="RecoveryComponent",
            average_response_time_ms=50.0,
            throughput_per_second=100.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.2}
        )
        
        # Verify recovery was successful
        self.assertIsNotNone(recovery_id)
        self.assertIsNotNone(self.meta_knowledge.get_entry(recovery_id))
    
    def test_kr_system_integration(self):
        """Test integration with the KR system."""
        # Add a component performance model
        component_id = "TestComponent"
        entry_id = self.meta_knowledge.add_component_performance_model(
            component_id=component_id,
            average_response_time_ms=50.0,
            throughput_per_second=100.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.2, "Memory": 0.3},
            performance_factors={"batch_size": 0.5},
            confidence=0.9
        )
        
        # Verify KR system assertion
        self.mock_kr_interface.assert_statement.assert_called_once()
        
        # Get the component model
        model = self.meta_knowledge.get_component_performance_model(component_id)
        
        # Modify the model
        model.average_response_time_ms = 40.0
        model.throughput_per_second = 120.0
        
        # Update the model
        self.meta_knowledge.update_entry(model)
        
        # Verify KR system update
        self.assertEqual(self.mock_kr_interface.retract_matching.call_count, 1)
        self.assertEqual(self.mock_kr_interface.assert_statement.call_count, 2)  # Initial + update
        
        # Remove the model
        self.meta_knowledge.remove_entry(entry_id)
        
        # Verify KR system removal
        self.assertEqual(self.mock_kr_interface.retract_matching.call_count, 2)
        
        # Add multiple entries of different types
        self.meta_knowledge.add_component_performance_model(
            component_id="Component1",
            average_response_time_ms=50.0,
            throughput_per_second=100.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.2}
        )
        
        self.meta_knowledge.add_reasoning_strategy_model(
            strategy_name="Strategy1",
            success_rate=0.8,
            average_duration_ms=100.0,
            applicable_problem_types=["type1"],
            preconditions=["precond1"],
            resource_requirements={"CPU": 0.3}
        )
        
        self.meta_knowledge.add_failure_pattern(
            pattern_name="Pattern1",
            affected_components=["Component1"],
            symptoms=["high_latency"],
            root_causes=["resource_contention"],
            frequency=0.05,
            severity=0.8
        )
        
        # Verify KR system assertions for different types
        # Reset the mock to clear previous calls
        self.mock_kr_interface.assert_statement.reset_mock()
        
        # Add one more entry to check the assertion
        self.meta_knowledge.add_system_capability(
            capability_name="Capability1",
            capability_description="A test capability",
            performance_level=0.7,
            reliability=0.9,
            resource_requirements={"CPU": 0.3}
        )
        
        # Verify KR system assertion was called with the correct context
        args, kwargs = self.mock_kr_interface.assert_statement.call_args
        self.assertEqual(kwargs.get('context_id'), "TEST_META_KNOWLEDGE")
    
    def test_complex_repository_operations(self):
        """Test complex operations on the MetaKnowledgeRepository."""
        # Create a repository
        repo = MetaKnowledgeRepository(ComponentPerformanceModel)
        
        # Add multiple entries
        entries = []
        for i in range(10):
            entry = ComponentPerformanceModel.create(
                component_id=f"Component{i}",
                average_response_time_ms=float(i * 10),
                throughput_per_second=float(200 - i * 10),
                failure_rate=float(i) / 100.0,
                resource_usage={"CPU": float(i) / 20.0}
            )
            repo.add(entry)
            entries.append(entry)
        
        # Test find_by_attribute with various attributes
        # Find by component_id
        results = repo.find_by_attribute("component_id", "Component5")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].component_id, "Component5")
        
        # Find by approximate response time (custom function)
        results = [entry for entry in repo.list_all() 
                  if 40.0 <= entry.average_response_time_ms <= 60.0]
        self.assertEqual(len(results), 3)  # Component4, Component5, Component6
        
        # Test update
        entry_to_update = results[0]
        entry_to_update.average_response_time_ms = 45.0
        repo.update(entry_to_update)
        
        # Verify update
        updated_entry = repo.get(entry_to_update.entry_id)
        self.assertEqual(updated_entry.average_response_time_ms, 45.0)
        
        # Test remove
        repo.remove(entry_to_update.entry_id)
        
        # Verify removal
        self.assertIsNone(repo.get(entry_to_update.entry_id))
        
        # Test list_all
        all_entries = repo.list_all()
        self.assertEqual(len(all_entries), 9)  # 10 - 1 removed
    
    def test_optimization_hint_complex_operations(self):
        """Test complex operations with OptimizationHint entries."""
        # Add multiple optimization hints for different components
        components = ["ComponentA", "ComponentB", "ComponentC"]
        optimization_types = ["parameter_tuning", "resource_allocation", "algorithm_selection"]
        
        for component in components:
            for opt_type in optimization_types:
                self.meta_knowledge.add_optimization_hint(
                    target_component=component,
                    optimization_type=opt_type,
                    expected_improvement=0.2,
                    implementation_difficulty=0.3,
                    preconditions=["stable_load"],
                    side_effects=["increased_memory"]
                )
        
        # Get optimization hints for a specific component
        hints_a = self.meta_knowledge.get_optimization_hints_for_component("ComponentA")
        self.assertEqual(len(hints_a), 3)
        
        # Verify optimization types
        opt_types = [hint.optimization_type for hint in hints_a]
        self.assertIn("parameter_tuning", opt_types)
        self.assertIn("resource_allocation", opt_types)
        self.assertIn("algorithm_selection", opt_types)
        
        # Get all optimization hints
        all_hints = self.meta_knowledge.get_entries_by_type(MetaKnowledgeType.OPTIMIZATION_HINT)
        self.assertEqual(len(all_hints), 9)  # 3 components * 3 optimization types
        
        # Test complex filtering
        # Find hints with high expected improvement and low implementation difficulty
        filtered_hints = [
            hint for hint in all_hints
            if hint.expected_improvement > 0.15 and hint.implementation_difficulty < 0.35
        ]
        self.assertEqual(len(filtered_hints), 9)  # All hints match these criteria
        
        # Find hints for ComponentA with specific optimization type
        filtered_hints = [
            hint for hint in all_hints
            if hint.target_component == "ComponentA" and hint.optimization_type == "parameter_tuning"
        ]
        self.assertEqual(len(filtered_hints), 1)
        
        # Update a hint
        hint_to_update = filtered_hints[0]
        hint_to_update.expected_improvement = 0.3
        hint_to_update.implementation_difficulty = 0.2
        self.meta_knowledge.update_entry(hint_to_update)
        
        # Verify update
        updated_hint = self.meta_knowledge.get_entry(hint_to_update.entry_id)
        self.assertEqual(updated_hint.expected_improvement, 0.3)
        self.assertEqual(updated_hint.implementation_difficulty, 0.2)
    
    def test_failure_pattern_complex_operations(self):
        """Test complex operations with FailurePattern entries."""
        # Add multiple failure patterns affecting different components
        components = [
            ["ComponentA", "ComponentB"],
            ["ComponentB", "ComponentC"],
            ["ComponentA", "ComponentC"],
            ["ComponentA", "ComponentB", "ComponentC"]
        ]
        
        pattern_names = ["HighLatency", "Timeout", "ResourceExhaustion", "CascadingFailure"]
        
        for i, (pattern_name, affected_comps) in enumerate(zip(pattern_names, components)):
            self.meta_knowledge.add_failure_pattern(
                pattern_name=pattern_name,
                affected_components=affected_comps,
                symptoms=["symptom1", "symptom2"],
                root_causes=["cause1", "cause2"],
                frequency=0.05 + (i * 0.01),
                severity=0.7 + (i * 0.05),
                mitigation_strategies=["strategy1", "strategy2"]
            )
        
        # Get failure patterns for a specific component
        patterns_a = self.meta_knowledge.get_failure_patterns_for_component("ComponentA")
        self.assertEqual(len(patterns_a), 3)  # HighLatency, ResourceExhaustion, CascadingFailure
        
        # Get all failure patterns
        all_patterns = self.meta_knowledge.get_entries_by_type(MetaKnowledgeType.FAILURE_PATTERN)
        self.assertEqual(len(all_patterns), 4)
        
        # Test complex filtering
        # Find patterns with high severity
        # Use a small epsilon to account for floating-point precision
        epsilon = 1e-10
        high_severity_patterns = [
            pattern for pattern in all_patterns
            if pattern.severity >= 0.8 - epsilon
        ]
        self.assertEqual(len(high_severity_patterns), 2)  # ResourceExhaustion, CascadingFailure
        
        # Find patterns affecting multiple components
        multi_component_patterns = [
            pattern for pattern in all_patterns
            if len(pattern.affected_components) > 2
        ]
        self.assertEqual(len(multi_component_patterns), 1)  # CascadingFailure
        
        # Find patterns affecting both ComponentA and ComponentB
        a_and_b_patterns = [
            pattern for pattern in all_patterns
            if "ComponentA" in pattern.affected_components and "ComponentB" in pattern.affected_components
        ]
        self.assertEqual(len(a_and_b_patterns), 2)  # HighLatency, CascadingFailure
        
        # Update a pattern
        pattern_to_update = a_and_b_patterns[0]
        pattern_to_update.severity = 0.9
        pattern_to_update.frequency = 0.1
        self.meta_knowledge.update_entry(pattern_to_update)
        
        # Verify update
        updated_pattern = self.meta_knowledge.get_entry(pattern_to_update.entry_id)
        self.assertEqual(updated_pattern.severity, 0.9)
        self.assertEqual(updated_pattern.frequency, 0.1)


if __name__ == "__main__":
    unittest.main()