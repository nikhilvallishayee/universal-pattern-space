"""
Integration tests for the Metacognition & Self-Improvement System.

These tests verify the interaction between different metacognition components
and their integration with other GödelOS modules.
"""

import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os
import time
import threading

from godelOS.metacognition.self_monitoring import SelfMonitoringModule
from godelOS.metacognition.meta_knowledge import MetaKnowledgeBase
from godelOS.metacognition.diagnostician import CognitiveDiagnostician
from godelOS.metacognition.modification_planner import SelfModificationPlanner
from godelOS.metacognition.module_library import ModuleLibraryActivator
from godelOS.metacognition.manager import MetacognitionManager, MetacognitivePhase, MetacognitiveMode
from godelOS.symbol_grounding.internal_state_monitor import InternalStateMonitor, ResourceStatus, ModuleStatus


class TestMetacognitionIntegration(unittest.TestCase):
    """Integration tests for the Metacognition & Self-Improvement System."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks
        self.mock_kr_interface = MagicMock()
        self.mock_type_system = MagicMock()
        
        # Configure mocks
        self.mock_kr_interface.list_contexts.return_value = []
        self.mock_kr_interface.assert_statement = MagicMock(return_value=True)
        self.mock_kr_interface.retract_statement = MagicMock(return_value=True)
        
        # Create a temporary directory for persistence
        self.temp_dir = tempfile.mkdtemp()
        self.modules_dir = os.path.join(self.temp_dir, "modules")
        os.makedirs(self.modules_dir, exist_ok=True)
        
        # Create components
        self.internal_state_monitor = InternalStateMonitor(
            kr_system_interface=self.mock_kr_interface,
            type_system=self.mock_type_system
        )
        
        # Mock the internal state monitor's get_current_state_summary method
        self.internal_state_monitor.get_current_state_summary = MagicMock(return_value={
            "system_resources": {
                "CPU": {"value": 50.0, "status": ResourceStatus.MODERATE.value},
                "Memory": {"value": 60.0, "status": ResourceStatus.MODERATE.value}
            },
            "module_states": {
                "InferenceEngine": {
                    "status": ModuleStatus.ACTIVE.value,
                    "metrics": {
                        "active_tasks": 2,
                        "inference_steps_per_second": 100.0,
                        "average_proof_time_ms": 50.0
                    }
                },
                "KRSystem": {
                    "status": ModuleStatus.ACTIVE.value,
                    "metrics": {
                        "query_rate_per_second": 50.0,
                        "statement_count": 1000
                    }
                }
            }
        })
        
        self.self_monitoring = SelfMonitoringModule(
            internal_state_monitor=self.internal_state_monitor,
            kr_system_interface=self.mock_kr_interface,
            type_system=self.mock_type_system,
            history_window_size=10,
            anomaly_detection_interval_sec=0.1,
            performance_metrics_interval_sec=0.1
        )
        
        self.meta_knowledge = MetaKnowledgeBase(
            kr_system_interface=self.mock_kr_interface,
            type_system=self.mock_type_system,
            persistence_directory=os.path.join(self.temp_dir, "meta_knowledge")
        )
        
        self.diagnostician = CognitiveDiagnostician(
            self_monitoring_module=self.self_monitoring,
            meta_knowledge_base=self.meta_knowledge
        )
        
        self.module_library = ModuleLibraryActivator(
            modules_directory=self.modules_dir
        )
        
        self.modification_planner = SelfModificationPlanner(
            diagnostician=self.diagnostician,
            meta_knowledge_base=self.meta_knowledge
        )
        
        # Create MetacognitionManager
        self.manager = MetacognitionManager(
            kr_system_interface=self.mock_kr_interface,
            type_system=self.mock_type_system,
            internal_state_monitor=self.internal_state_monitor,
            modules_directory=self.modules_dir
        )
        
        # Initialize components manually for testing
        self.manager.self_monitoring = self.self_monitoring
        self.manager.meta_knowledge = self.meta_knowledge
        self.manager.diagnostician = self.diagnostician
        self.manager.module_library = self.module_library
        self.manager.modification_planner = self.modification_planner
        self.manager.is_initialized = True
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up the temporary directory
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.unlink(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        
        os.rmdir(self.temp_dir)
    
    def test_metacognitive_cycle(self):
        """Test the complete metacognitive cycle."""
        # Set up test conditions
        
        # 1. Add some meta-knowledge
        self.meta_knowledge.add_component_performance_model(
            component_id="InferenceEngine",
            average_response_time_ms=40.0,
            throughput_per_second=120.0,
            failure_rate=0.05,
            resource_usage={"CPU": 0.3, "Memory": 0.2}
        )
        
        self.meta_knowledge.add_reasoning_strategy_model(
            strategy_name="ResolutionProver",
            success_rate=0.8,
            average_duration_ms=100.0,
            applicable_problem_types=["deduction"],
            preconditions=[],
            resource_requirements={"CPU": 0.2}
        )
        
        # 2. Record some reasoning events
        self.self_monitoring.record_reasoning_event(
            strategy_name="ResolutionProver",
            successful=True,
            duration_ms=90.0,
            goal_id="test_goal_1"
        )
        
        self.self_monitoring.record_reasoning_event(
            strategy_name="ResolutionProver",
            successful=False,
            duration_ms=200.0,
            goal_id="test_goal_2"
        )
        
        # 3. Add a performance anomaly
        self.self_monitoring._record_anomaly(
            anomaly_type="resource_saturation",
            severity=0.7,
            affected_component="CPU",
            description="CPU usage is high",
            metrics={"value": 90.0, "threshold": 80.0}
        )
        
        # 4. Execute metacognitive cycle
        with patch.object(self.manager, '_get_current_system_state') as mock_get_state, \
             patch.object(self.diagnostician, 'diagnose') as mock_diagnose, \
             patch.object(self.modification_planner, 'generate_proposals_from_diagnostic_report') as mock_generate_proposals, \
             patch.object(self.modification_planner, 'evaluate_proposal') as mock_evaluate_proposal, \
             patch.object(self.modification_planner, 'create_execution_plan') as mock_create_plan, \
             patch.object(self.modification_planner, 'execute_plan') as mock_execute_plan:
            
            # Configure mock to return a system state
            mock_get_state.return_value = {
                "monitoring_data": self.self_monitoring.get_performance_metrics(),
                "active_modules": {},
                "metacognition": {
                    "mode": self.manager.current_mode.value,
                    "phase": self.manager.current_phase.value
                },
                "timestamp": time.time()
            }
            
            # Configure mock to return findings
            from godelOS.metacognition.diagnostician import DiagnosticFinding, DiagnosisType, SeverityLevel
            mock_finding = DiagnosticFinding(
                finding_id="test_finding",
                diagnosis_type=DiagnosisType.PERFORMANCE_BOTTLENECK,
                severity=SeverityLevel.MEDIUM,
                affected_components=["InferenceEngine"],
                description="Test finding",
                evidence={},
                recommendations=["Test recommendation"]
            )
            mock_diagnose.return_value = [mock_finding]
            
            # Configure mock to return approved proposals
            from godelOS.metacognition.modification_planner import ModificationProposal, ModificationStatus
            mock_proposal = MagicMock(spec=ModificationProposal)
            mock_proposal.proposal_id = "test_proposal"
            mock_proposal.status = ModificationStatus.APPROVED
            mock_generate_proposals.return_value = [mock_proposal]
            
            # Add the proposal to the planner's proposals dictionary
            self.modification_planner.proposals = {"test_proposal": mock_proposal}
            
            # Configure mock to return evaluation results
            mock_evaluate_proposal.return_value = {"risk": "low", "impact": "medium"}
            
            # Configure mocks for execution plan and result
            mock_plan = MagicMock()
            mock_plan.plan_id = "test_plan"
            mock_create_plan.return_value = mock_plan
            
            mock_result = MagicMock()
            mock_result.result_id = "test_result"
            mock_result.success = True
            mock_execute_plan.return_value = mock_result
            
            # Set manager to autonomous mode
            self.manager.set_mode(MetacognitiveMode.AUTONOMOUS)
            
            # Execute cycle
            self.manager._execute_metacognitive_cycle()
        
        # Verify cycle execution
        self.assertEqual(len(self.manager.event_history), 8)  # 4 phase changes + 1 diagnostic report + 1 proposals generated + 1 mode change + 1 modification executed
        
        # Verify phases were executed
        phases = [e.details["phase"] for e in self.manager.event_history if e.event_type == "phase_started"]
        self.assertEqual(phases, [
            MetacognitivePhase.MONITORING.value,
            MetacognitivePhase.DIAGNOSING.value,
            MetacognitivePhase.PLANNING.value,
            MetacognitivePhase.MODIFYING.value
        ])
    
    def test_anomaly_detection_to_diagnosis(self):
        """Test the flow from anomaly detection to diagnosis."""
        # Set up a callback to detect when diagnosis is triggered
        diagnosis_triggered = threading.Event()
        
        def on_diagnosis_start(event):
            if event.event_type == "phase_started" and event.details["phase"] == MetacognitivePhase.DIAGNOSING.value:
                diagnosis_triggered.set()
        
        self.manager.subscribe_to_event("phase_started", on_diagnosis_start)
        
        # Set manager to semi-autonomous mode
        self.manager.set_mode(MetacognitiveMode.SEMI_AUTONOMOUS)
        self.manager.current_phase = MetacognitivePhase.IDLE
        
        # Simulate anomaly detection
        with patch.object(self.manager, '_execute_metacognitive_cycle') as mock_execute_cycle:
            mock_execute_cycle.side_effect = lambda: diagnosis_triggered.set()
            
            # Trigger anomaly
            anomaly = MagicMock()
            anomaly.anomaly_type = "resource_saturation"
            anomaly.severity = 0.8
            anomaly.affected_component = "CPU"
            anomaly.description = "CPU usage is critical"
            
            self.manager._on_anomaly_detected(anomaly)
            
            # Wait for diagnosis to be triggered
            triggered = diagnosis_triggered.wait(timeout=1.0)
            
            # Verify diagnosis was triggered
            self.assertTrue(triggered)
            mock_execute_cycle.assert_called_once()
    
    def test_manager_initialization_and_lifecycle(self):
        """Test the initialization and lifecycle of the MetacognitionManager."""
        # Create a fresh manager for this test
        manager = MetacognitionManager(
            kr_system_interface=self.mock_kr_interface,
            type_system=self.mock_type_system,
            modules_directory=self.modules_dir
        )
        
        # Test initialization
        self.assertFalse(manager.is_initialized)
        success = manager.initialize()
        self.assertTrue(success)
        self.assertTrue(manager.is_initialized)
        
        # Test starting
        self.assertFalse(manager.is_running)
        with patch.object(manager, '_metacognitive_cycle_loop'):  # Prevent actual thread execution
            success = manager.start()
            self.assertTrue(success)
            self.assertTrue(manager.is_running)
        
        # Test stopping
        with patch.object(manager.stop_cycle, 'set'), \
             patch.object(manager.internal_state_monitor, 'stop_monitoring'), \
             patch.object(manager.self_monitoring, 'stop_monitoring'):
            success = manager.stop()
            self.assertTrue(success)
            self.assertFalse(manager.is_running)
    
    def test_mode_changes(self):
        """Test changing the operational mode of the metacognition system."""
        # Test setting mode by string
        success = self.manager.set_mode("autonomous")
        self.assertTrue(success)
        self.assertEqual(self.manager.current_mode, MetacognitiveMode.AUTONOMOUS)
        
        # Test setting mode by enum
        success = self.manager.set_mode(MetacognitiveMode.PASSIVE)
        self.assertTrue(success)
        self.assertEqual(self.manager.current_mode, MetacognitiveMode.PASSIVE)
        
        # Test invalid mode
        success = self.manager.set_mode("invalid_mode")
        self.assertFalse(success)  # Should return False for invalid mode
    
    def test_event_subscription(self):
        """Test subscribing to metacognitive events."""
        # Set up event counters
        all_events = []
        phase_events = []
        
        # Define callbacks
        def all_events_callback(event):
            all_events.append(event)
        
        def phase_events_callback(event):
            phase_events.append(event)
        
        # Subscribe to events
        self.manager.subscribe_to_event("*", all_events_callback)
        self.manager.subscribe_to_event("phase_started", phase_events_callback)
        
        # Generate some events
        self.manager._log_event("test_event", {"test": "data"})
        self.manager._log_event("phase_started", {"phase": "testing"})
        self.manager._log_event("another_event", {})
        
        # Verify callbacks were called
        self.assertEqual(len(all_events), 3)
        self.assertEqual(len(phase_events), 1)
        
        # Test unsubscribing
        success = self.manager.unsubscribe_from_event("*", all_events_callback)
        self.assertTrue(success)
        
        # Generate another event
        self.manager._log_event("test_event", {})
        
        # Verify callback was not called
        self.assertEqual(len(all_events), 3)  # Still 3, not 4
    
    def test_proposal_approval_and_execution(self):
        """Test approving and executing modification proposals."""
        # Create a mock proposal
        proposal = MagicMock()
        proposal.proposal_id = "test_proposal"
        proposal.status = "proposed"
        
        # Add proposal to planner
        self.modification_planner.proposals = {"test_proposal": proposal}
        
        # Test approval
        success = self.manager.approve_modification_proposal("test_proposal")
        self.assertTrue(success)
        self.assertEqual(proposal.status, "approved")
        
        # Test execution
        with patch.object(self.modification_planner, 'create_execution_plan') as mock_create_plan, \
             patch.object(self.modification_planner, 'execute_plan') as mock_execute_plan:
            
            # Configure mocks
            mock_plan = MagicMock()
            mock_plan.plan_id = "test_plan"
            mock_create_plan.return_value = mock_plan
            
            mock_result = MagicMock()
            mock_result.result_id = "test_result"
            mock_result.success = True
            mock_execute_plan.return_value = mock_result
            
            # Execute proposal
            success, message = self.manager.execute_modification("test_proposal")
            
            # Verify execution
            self.assertTrue(success)
            mock_create_plan.assert_called_once_with("test_proposal")
            mock_execute_plan.assert_called_once()


if __name__ == '__main__':
    unittest.main()