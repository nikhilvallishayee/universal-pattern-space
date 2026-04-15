"""
Unit tests for the InternalStateMonitor component.
"""

import unittest
from unittest.mock import MagicMock, patch, call
import time
import threading
import json

from godelOS.symbol_grounding.internal_state_monitor import (
    InternalStateMonitor,
    SystemMetricAccessAPI,
    ModuleIntrospectionAPI,
    InferenceEngineAPI,
    LearningSystemAPI,
    KRSystemAPI,
    InternalStatePredicateSchema,
    SystemMetric,
    ModuleState,
    ResourceStatus,
    ModuleStatus
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import AST_Node, ConstantNode, VariableNode, ApplicationNode


class TestSystemMetricAccessAPI(unittest.TestCase):
    """Tests for the SystemMetricAccessAPI class."""
    
    @patch('psutil.cpu_percent')
    def test_get_cpu_load(self, mock_cpu_percent):
        """Test getting CPU load."""
        mock_cpu_percent.return_value = 50.0
        
        cpu_load = SystemMetricAccessAPI.get_cpu_load()
        
        self.assertEqual(cpu_load, 50.0)
        mock_cpu_percent.assert_called_once_with(interval=0.1)
    
    @patch('psutil.virtual_memory')
    def test_get_memory_usage(self, mock_virtual_memory):
        """Test getting memory usage."""
        mock_memory = MagicMock()
        mock_memory.total = 16000000000
        mock_memory.available = 8000000000
        mock_memory.percent = 50.0
        mock_memory.used = 8000000000
        mock_memory.free = 8000000000
        mock_virtual_memory.return_value = mock_memory
        
        memory_usage = SystemMetricAccessAPI.get_memory_usage()
        
        self.assertEqual(memory_usage["total"], 16000000000)
        self.assertEqual(memory_usage["available"], 8000000000)
        self.assertEqual(memory_usage["percent"], 50.0)
        self.assertEqual(memory_usage["used"], 8000000000)
        self.assertEqual(memory_usage["free"], 8000000000)
        mock_virtual_memory.assert_called_once()
    
    @patch('psutil.disk_usage')
    def test_get_disk_usage(self, mock_disk_usage):
        """Test getting disk usage."""
        mock_disk = MagicMock()
        mock_disk.total = 500000000000
        mock_disk.used = 250000000000
        mock_disk.free = 250000000000
        mock_disk.percent = 50.0
        mock_disk_usage.return_value = mock_disk
        
        disk_usage = SystemMetricAccessAPI.get_disk_usage()
        
        self.assertEqual(disk_usage["total"], 500000000000)
        self.assertEqual(disk_usage["used"], 250000000000)
        self.assertEqual(disk_usage["free"], 250000000000)
        self.assertEqual(disk_usage["percent"], 50.0)
        mock_disk_usage.assert_called_once_with('/')


class TestModuleIntrospectionAPIs(unittest.TestCase):
    """Tests for the module introspection API classes."""
    
    def test_inference_engine_api(self):
        """Test the InferenceEngineAPI class."""
        # Test with mock inference engine
        mock_inference_engine = MagicMock()
        mock_inference_engine.get_active_tasks.return_value = ["task1", "task2"]
        mock_inference_engine.get_inference_rate.return_value = 100
        mock_inference_engine.get_average_proof_time.return_value = 50
        
        api = InferenceEngineAPI(mock_inference_engine)
        state = api.get_module_state()
        
        self.assertEqual(state.module_id, "InferenceEngine")
        self.assertEqual(state.status, ModuleStatus.ACTIVE)
        self.assertEqual(state.metrics["active_tasks"], 2)
        self.assertEqual(state.metrics["inference_steps_per_second"], 100)
        self.assertEqual(state.metrics["average_proof_time_ms"], 50)
        
        # Test without inference engine
        api = InferenceEngineAPI()
        state = api.get_module_state()
        
        self.assertEqual(state.module_id, "InferenceEngine")
        self.assertEqual(state.status, ModuleStatus.IDLE)
        self.assertEqual(state.metrics["active_tasks"], 0)
    
    def test_learning_system_api(self):
        """Test the LearningSystemAPI class."""
        # Test with mock learning system
        mock_learning_system = MagicMock()
        mock_learning_system.get_active_learning_processes.return_value = ["process1"]
        mock_learning_system.get_rules_learned_count.return_value = 10
        mock_learning_system.get_learning_cycles_completed.return_value = 5
        
        api = LearningSystemAPI(mock_learning_system)
        state = api.get_module_state()
        
        self.assertEqual(state.module_id, "LearningSystem")
        self.assertEqual(state.status, ModuleStatus.ACTIVE)
        self.assertEqual(state.metrics["active_learning_processes"], 1)
        self.assertEqual(state.metrics["rules_learned"], 10)
        self.assertEqual(state.metrics["learning_cycles_completed"], 5)
        
        # Test without learning system
        api = LearningSystemAPI()
        state = api.get_module_state()
        
        self.assertEqual(state.module_id, "LearningSystem")
        self.assertEqual(state.status, ModuleStatus.IDLE)
        self.assertEqual(state.metrics["active_learning_processes"], 0)
    
    def test_kr_system_api(self):
        """Test the KRSystemAPI class."""
        # Test with mock KR system
        mock_kr_system = MagicMock()
        mock_kr_system.list_contexts.return_value = ["context1", "context2"]
        mock_kr_system.get_query_rate.return_value = 50
        mock_kr_system.get_statement_count.return_value = 1000
        
        api = KRSystemAPI(mock_kr_system)
        state = api.get_module_state()
        
        self.assertEqual(state.module_id, "KRSystem")
        self.assertEqual(state.status, ModuleStatus.ACTIVE)
        self.assertEqual(state.metrics["context_count"], 2)
        self.assertEqual(state.metrics["query_rate_per_second"], 50)
        self.assertEqual(state.metrics["statement_count"], 1000)
        
        # Test without KR system
        api = KRSystemAPI()
        state = api.get_module_state()
        
        self.assertEqual(state.module_id, "KRSystem")
        self.assertEqual(state.status, ModuleStatus.IDLE)
        self.assertEqual(state.metrics["context_count"], 0)


class TestInternalStatePredicateSchema(unittest.TestCase):
    """Tests for the InternalStatePredicateSchema class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock type system
        self.type_system = MagicMock(spec=TypeSystemManager)
        self.entity_type = MagicMock()
        self.prop_type = MagicMock()
        self.float_type = MagicMock()
        self.int_type = MagicMock()
        self.string_type = MagicMock()
        
        self.type_system.get_type.side_effect = lambda name: {
            "Entity": self.entity_type,
            "Object": self.entity_type,
            "Proposition": self.prop_type,
            "Float": self.float_type,
            "Real": self.float_type,
            "Integer": self.int_type,
            "Int": self.int_type,
            "String": self.string_type
        }.get(name)
        
        # Create predicate schema
        self.schema = InternalStatePredicateSchema(self.type_system)
    
    def test_create_system_resource_level_predicate(self):
        """Test creating a SystemResourceLevel predicate."""
        predicate = self.schema.create_system_resource_level_predicate(
            resource_name="CPU",
            current_value=75.5,
            unit="Percent",
            status=ResourceStatus.HIGH
        )
        
        self.assertIsInstance(predicate, ApplicationNode)
        self.assertEqual(predicate.operator.name, "SystemResourceLevel")
        self.assertEqual(len(predicate.arguments), 4)
        self.assertEqual(predicate.arguments[0].name, "CPU")
        self.assertEqual(predicate.arguments[1].name, "75.5")
        self.assertEqual(predicate.arguments[2].name, "Percent")
        self.assertEqual(predicate.arguments[3].name, "high")
    
    def test_create_cognitive_operation_count_predicate(self):
        """Test creating a CognitiveOperationCount predicate."""
        predicate = self.schema.create_cognitive_operation_count_predicate(
            operation_type="InferenceSteps",
            count=100,
            time_unit="PerSecond"
        )
        
        self.assertIsInstance(predicate, ApplicationNode)
        self.assertEqual(predicate.operator.name, "CognitiveOperationCount")
        self.assertEqual(len(predicate.arguments), 3)
        self.assertEqual(predicate.arguments[0].name, "InferenceSteps")
        self.assertEqual(predicate.arguments[1].name, "100")
        self.assertEqual(predicate.arguments[2].name, "PerSecond")
    
    def test_create_module_status_predicate(self):
        """Test creating a ModuleStatus predicate."""
        predicate = self.schema.create_module_status_predicate(
            module_id="InferenceEngine",
            status=ModuleStatus.ACTIVE
        )
        
        self.assertIsInstance(predicate, ApplicationNode)
        self.assertEqual(predicate.operator.name, "ModuleStatus")
        self.assertEqual(len(predicate.arguments), 2)
        self.assertEqual(predicate.arguments[0].name, "InferenceEngine")
        self.assertEqual(predicate.arguments[1].name, "active")


class TestInternalStateMonitor(unittest.TestCase):
    """Tests for the InternalStateMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock KR interface
        self.kr_interface = MagicMock(spec=KnowledgeStoreInterface)
        self.kr_interface.list_contexts.return_value = []
        
        # Create mock type system
        self.type_system = MagicMock(spec=TypeSystemManager)
        self.entity_type = MagicMock()
        self.prop_type = MagicMock()
        self.float_type = MagicMock()
        self.int_type = MagicMock()
        self.string_type = MagicMock()
        
        self.type_system.get_type.side_effect = lambda name: {
            "Entity": self.entity_type,
            "Object": self.entity_type,
            "Proposition": self.prop_type,
            "Float": self.float_type,
            "Real": self.float_type,
            "Integer": self.int_type,
            "Int": self.int_type,
            "String": self.string_type
        }.get(name)
        
        # Create mock system metric API
        self.system_metric_api_patcher = patch('godelOS.symbol_grounding.internal_state_monitor.SystemMetricAccessAPI')
        self.mock_system_metric_api = self.system_metric_api_patcher.start()
        
        # Create mock module APIs
        self.mock_inference_engine_api = MagicMock(spec=InferenceEngineAPI)
        self.mock_learning_system_api = MagicMock(spec=LearningSystemAPI)
        self.mock_kr_system_api = MagicMock(spec=KRSystemAPI)
        
        self.module_apis = {
            "InferenceEngine": self.mock_inference_engine_api,
            "LearningSystem": self.mock_learning_system_api,
            "KRSystem": self.mock_kr_system_api
        }
        
        # Create the internal state monitor
        self.ism = InternalStateMonitor(
            kr_system_interface=self.kr_interface,
            type_system=self.type_system,
            internal_state_context_id="INTERNAL_STATE_CONTEXT",
            module_apis=self.module_apis,
            poll_interval_sec=1.0  # Short interval for testing
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.system_metric_api_patcher.stop()
    
    def test_init(self):
        """Test initialization."""
        # Check that the internal state context was created
        self.kr_interface.create_context.assert_called_once_with(
            "INTERNAL_STATE_CONTEXT", None, "internal_state"
        )
        
        # Check that predicate schema was initialized
        self.assertIsNotNone(self.ism.predicate_schema)
        
        # Check that module APIs were initialized
        self.assertEqual(len(self.ism.module_apis), 3)
        self.assertIn("InferenceEngine", self.ism.module_apis)
        self.assertIn("LearningSystem", self.ism.module_apis)
        self.assertIn("KRSystem", self.ism.module_apis)
    
    @patch('godelOS.symbol_grounding.internal_state_monitor.InternalStateMonitor._collect_system_metrics')
    @patch('godelOS.symbol_grounding.internal_state_monitor.InternalStateMonitor._collect_module_states')
    @patch('godelOS.symbol_grounding.internal_state_monitor.InternalStateMonitor._assert_state_facts')
    def test_perform_monitoring_cycle(self, mock_assert_state_facts, mock_collect_module_states, mock_collect_system_metrics):
        """Test performing a monitoring cycle."""
        # Mock system metrics
        mock_collect_system_metrics.return_value = [
            SystemMetric(name="CPU", value=50.0, unit="Percent", status=ResourceStatus.MODERATE),
            SystemMetric(name="Memory", value=30.0, unit="Percent", status=ResourceStatus.LOW)
        ]
        
        # Mock module states
        mock_collect_module_states.return_value = [
            ModuleState(module_id="InferenceEngine", status=ModuleStatus.ACTIVE, metrics={"inference_steps_per_second": 100}),
            ModuleState(module_id="LearningSystem", status=ModuleStatus.IDLE, metrics={})
        ]
        
        # Perform monitoring cycle
        self.ism.perform_monitoring_cycle()
        
        # Check that system metrics and module states were collected
        mock_collect_system_metrics.assert_called_once()
        mock_collect_module_states.assert_called_once()
        
        # Check that state facts were asserted
        mock_assert_state_facts.assert_called_once()
        args = mock_assert_state_facts.call_args[0]
        state_facts = args[0]
        
        # Should have 5 facts: 2 system metrics + 2 module states + 1 cognitive operation count
        self.assertEqual(len(state_facts), 5)
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics(self, mock_disk_usage, mock_virtual_memory, mock_cpu_percent):
        """Test collecting system metrics."""
        # Mock CPU load
        mock_cpu_percent.return_value = 50.0
        
        # Mock memory usage
        mock_memory = MagicMock()
        mock_memory.total = 16000000000
        mock_memory.available = 8000000000
        mock_memory.percent = 50.0
        mock_memory.used = 8000000000
        mock_memory.free = 8000000000
        mock_virtual_memory.return_value = mock_memory
        
        # Mock disk usage
        mock_disk = MagicMock()
        mock_disk.total = 500000000000
        mock_disk.used = 250000000000
        mock_disk.free = 250000000000
        mock_disk.percent = 50.0
        mock_disk_usage.return_value = mock_disk
        
        # Collect system metrics
        metrics = self.ism._collect_system_metrics()
        
        # Check that metrics were collected correctly
        self.assertEqual(len(metrics), 3)
        
        # Check CPU metric
        cpu_metric = next(m for m in metrics if m.name == "CPU")
        self.assertEqual(cpu_metric.value, 50.0)
        self.assertEqual(cpu_metric.unit, "Percent")
        self.assertEqual(cpu_metric.status, ResourceStatus.MODERATE)
        
        # Check memory metric
        memory_metric = next(m for m in metrics if m.name == "Memory")
        self.assertEqual(memory_metric.value, 50.0)
        self.assertEqual(memory_metric.unit, "Percent")
        self.assertEqual(memory_metric.status, ResourceStatus.MODERATE)
        
        # Check disk metric
        disk_metric = next(m for m in metrics if m.name == "Disk")
        self.assertEqual(disk_metric.value, 50.0)
        self.assertEqual(disk_metric.unit, "Percent")
        self.assertEqual(disk_metric.status, ResourceStatus.MODERATE)
    
    def test_collect_module_states(self):
        """Test collecting module states."""
        # Mock module states
        inference_engine_state = ModuleState(
            module_id="InferenceEngine",
            status=ModuleStatus.ACTIVE,
            metrics={"active_tasks": 2, "inference_steps_per_second": 100}
        )
        learning_system_state = ModuleState(
            module_id="LearningSystem",
            status=ModuleStatus.IDLE,
            metrics={"active_learning_processes": 0}
        )
        kr_system_state = ModuleState(
            module_id="KRSystem",
            status=ModuleStatus.ACTIVE,
            metrics={"context_count": 5, "query_rate_per_second": 50}
        )
        
        self.mock_inference_engine_api.get_module_state.return_value = inference_engine_state
        self.mock_learning_system_api.get_module_state.return_value = learning_system_state
        self.mock_kr_system_api.get_module_state.return_value = kr_system_state
        
        # Collect module states
        states = self.ism._collect_module_states()
        
        # Check that states were collected correctly
        self.assertEqual(len(states), 3)
        
        # Check inference engine state
        ie_state = next(s for s in states if s.module_id == "InferenceEngine")
        self.assertEqual(ie_state.status, ModuleStatus.ACTIVE)
        self.assertEqual(ie_state.metrics["active_tasks"], 2)
        self.assertEqual(ie_state.metrics["inference_steps_per_second"], 100)
        
        # Check learning system state
        ls_state = next(s for s in states if s.module_id == "LearningSystem")
        self.assertEqual(ls_state.status, ModuleStatus.IDLE)
        self.assertEqual(ls_state.metrics["active_learning_processes"], 0)
        
        # Check KR system state
        kr_state = next(s for s in states if s.module_id == "KRSystem")
        self.assertEqual(kr_state.status, ModuleStatus.ACTIVE)
        self.assertEqual(kr_state.metrics["context_count"], 5)
        self.assertEqual(kr_state.metrics["query_rate_per_second"], 50)
    
    def test_assert_state_facts(self):
        """Test asserting state facts to the KR system."""
        # Create mock facts
        mock_fact1 = MagicMock(spec=AST_Node)
        mock_fact2 = MagicMock(spec=AST_Node)
        
        # Set string representation for facts
        mock_fact1.__str__.return_value = "Fact1"
        mock_fact2.__str__.return_value = "Fact2"
        
        # Assert facts
        self.ism._assert_state_facts([mock_fact1, mock_fact2])
        
        # Check that facts were added to the KR system
        self.kr_interface.add_statement.assert_has_calls([
            call(mock_fact1, "INTERNAL_STATE_CONTEXT"),
            call(mock_fact2, "INTERNAL_STATE_CONTEXT")
        ])
        
        # Check that facts were added to the previous state facts cache
        self.assertIn("Fact1", self.ism.previous_state_facts)
        self.assertIn("Fact2", self.ism.previous_state_facts)
    
    def test_get_current_state_summary(self):
        """Test getting a summary of the current internal state."""
        # Mock system metrics
        cpu_metric = SystemMetric(name="CPU", value=50.0, unit="Percent", status=ResourceStatus.MODERATE)
        memory_metric = SystemMetric(name="Memory", value=30.0, unit="Percent", status=ResourceStatus.LOW)
        
        # Mock module states
        ie_state = ModuleState(
            module_id="InferenceEngine",
            status=ModuleStatus.ACTIVE,
            metrics={"active_tasks": 2, "inference_steps_per_second": 100}
        )
        ls_state = ModuleState(
            module_id="LearningSystem",
            status=ModuleStatus.IDLE,
            metrics={"active_learning_processes": 0}
        )
        
        # Mock _collect_system_metrics and _collect_module_states
        self.ism._collect_system_metrics = MagicMock(return_value=[cpu_metric, memory_metric])
        self.ism._collect_module_states = MagicMock(return_value=[ie_state, ls_state])
        
        # Get current state summary
        summary = self.ism.get_current_state_summary()
        
        # Check that summary contains expected data
        self.assertIn("system_metrics", summary)
        self.assertIn("module_states", summary)
        self.assertIn("timestamp", summary)
        
        # Check system metrics
        self.assertIn("CPU", summary["system_metrics"])
        self.assertEqual(summary["system_metrics"]["CPU"]["value"], 50.0)
        self.assertEqual(summary["system_metrics"]["CPU"]["status"], "moderate")
        
        self.assertIn("Memory", summary["system_metrics"])
        self.assertEqual(summary["system_metrics"]["Memory"]["value"], 30.0)
        self.assertEqual(summary["system_metrics"]["Memory"]["status"], "low")
        
        # Check module states
        self.assertIn("InferenceEngine", summary["module_states"])
        self.assertEqual(summary["module_states"]["InferenceEngine"]["status"], "active")
        self.assertEqual(summary["module_states"]["InferenceEngine"]["metrics"]["active_tasks"], 2)
        
        self.assertIn("LearningSystem", summary["module_states"])
        self.assertEqual(summary["module_states"]["LearningSystem"]["status"], "idle")
        self.assertEqual(summary["module_states"]["LearningSystem"]["metrics"]["active_learning_processes"], 0)


if __name__ == '__main__':
    unittest.main()