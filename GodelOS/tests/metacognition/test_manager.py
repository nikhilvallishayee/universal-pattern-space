"""
Unit tests for the MetacognitionManager.
"""

import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os
import time
import threading

from godelOS.metacognition.manager import (
    MetacognitionManager,
    MetacognitivePhase,
    MetacognitiveMode,
    MetacognitiveEvent
)


class TestMetacognitionManager(unittest.TestCase):
    """Test cases for the MetacognitionManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks
        self.mock_kr_interface = MagicMock()
        self.mock_type_system = MagicMock()
        self.mock_internal_state_monitor = MagicMock()
        
        # Configure mocks
        self.mock_kr_interface.list_contexts.return_value = []
        
        # Create a temporary directory for modules
        self.temp_dir = tempfile.mkdtemp()
        
        # Create MetacognitionManager instance
        self.manager = MetacognitionManager(
            kr_system_interface=self.mock_kr_interface,
            type_system=self.mock_type_system,
            internal_state_monitor=self.mock_internal_state_monitor,
            modules_directory=self.temp_dir
        )
        
        # Mock the components
        self.manager.self_monitoring = MagicMock()
        self.manager.meta_knowledge = MagicMock()
        self.manager.diagnostician = MagicMock()
        self.manager.modification_planner = MagicMock()
        self.manager.module_library = MagicMock()
        
        # Set initialized flag
        self.manager.is_initialized = True
    
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
        """Test initialization of MetacognitionManager."""
        # Create a fresh manager for this test
        manager = MetacognitionManager(
            kr_system_interface=self.mock_kr_interface,
            type_system=self.mock_type_system
        )
        
        # Test initialization
        self.assertFalse(manager.is_initialized)
        
        # Mock component initialization
        with patch('godelOS.metacognition.manager.InternalStateMonitor'), \
             patch('godelOS.metacognition.manager.SelfMonitoringModule'), \
             patch('godelOS.metacognition.manager.MetaKnowledgeBase'), \
             patch('godelOS.metacognition.manager.CognitiveDiagnostician'), \
             patch('godelOS.metacognition.manager.ModuleLibraryActivator'), \
             patch('godelOS.metacognition.manager.SelfModificationPlanner'):
            
            success = manager.initialize()
            
            # Verify initialization
            self.assertTrue(success)
            self.assertTrue(manager.is_initialized)
            self.assertIsNotNone(manager.self_monitoring)
            self.assertIsNotNone(manager.meta_knowledge)
            self.assertIsNotNone(manager.diagnostician)
            self.assertIsNotNone(manager.modification_planner)
            self.assertIsNotNone(manager.module_library)
    
    def test_start_stop(self):
        """Test starting and stopping the metacognition system."""
        # Test starting
        with patch.object(self.manager.internal_state_monitor, 'start_monitoring'), \
             patch.object(self.manager.self_monitoring, 'start_monitoring'), \
             patch.object(threading, 'Thread') as mock_thread:
            
            success = self.manager.start()
            
            # Verify starting
            self.assertTrue(success)
            self.assertTrue(self.manager.is_running)
            self.manager.internal_state_monitor.start_monitoring.assert_called_once()
            self.manager.self_monitoring.start_monitoring.assert_called_once()
            mock_thread.assert_called_once()
            mock_thread.return_value.start.assert_called_once()
        
        # Test stopping
        with patch.object(self.manager.internal_state_monitor, 'stop_monitoring'), \
             patch.object(self.manager.self_monitoring, 'stop_monitoring'):
            
            success = self.manager.stop()
            
            # Verify stopping
            self.assertTrue(success)
            self.assertFalse(self.manager.is_running)
            self.manager.internal_state_monitor.stop_monitoring.assert_called_once()
            self.manager.self_monitoring.stop_monitoring.assert_called_once()
            self.assertTrue(self.manager.stop_cycle.is_set())
    
    def test_set_mode(self):
        """Test setting the operational mode."""
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
        
        # Verify event was logged
        self.assertEqual(len(self.manager.event_history), 2)
        self.assertEqual(self.manager.event_history[0].event_type, "mode_changed")
        self.assertEqual(self.manager.event_history[1].event_type, "mode_changed")
    
    def test_metacognitive_cycle(self):
        """Test the metacognitive cycle."""
        # Configure mocks
        self.manager.diagnostician.generate_report.return_value = MagicMock(
            findings=[MagicMock(), MagicMock()]  # Two findings
        )
        
        from godelOS.metacognition.modification_planner import ModificationStatus
        
        # Create a mock proposal with the proper status
        mock_proposal = MagicMock()
        mock_proposal.proposal_id = "test_proposal"
        mock_proposal.status = ModificationStatus.APPROVED  # Use the enum value, not the string
        
        self.manager.modification_planner.generate_proposals_from_diagnostic_report.return_value = [mock_proposal]
        
        # Execute cycle in autonomous mode
        self.manager.current_mode = MetacognitiveMode.AUTONOMOUS
        self.manager._execute_metacognitive_cycle()
        
        # Verify cycle execution
        self.assertEqual(self.manager.diagnostician.generate_report.call_count, 1)
        self.assertEqual(
            self.manager.modification_planner.generate_proposals_from_diagnostic_report.call_count, 1
        )
        self.assertEqual(self.manager.modification_planner.evaluate_proposal.call_count, 1)
        self.assertEqual(self.manager.modification_planner.create_execution_plan.call_count, 1)
        self.assertEqual(self.manager.modification_planner.execute_plan.call_count, 1)
        
        # Verify events were logged
        phase_events = [e for e in self.manager.event_history if e.event_type == "phase_started"]
        self.assertEqual(len(phase_events), 4)  # monitoring, diagnosing, planning, modifying
        
        # Verify cycle in passive mode (no modifications)
        self.manager.event_history.clear()
        self.manager.current_mode = MetacognitiveMode.PASSIVE
        
        # Reset mock call counts
        self.manager.diagnostician.generate_report.reset_mock()
        self.manager.modification_planner.generate_proposals_from_diagnostic_report.reset_mock()
        self.manager.modification_planner.evaluate_proposal.reset_mock()
        self.manager.modification_planner.create_execution_plan.reset_mock()
        self.manager.modification_planner.execute_plan.reset_mock()
        
        # Execute cycle
        self.manager._execute_metacognitive_cycle()
        
        # Verify no modifications were made
        self.assertEqual(self.manager.diagnostician.generate_report.call_count, 1)
        self.assertEqual(
            self.manager.modification_planner.generate_proposals_from_diagnostic_report.call_count, 1
        )
        self.assertEqual(self.manager.modification_planner.evaluate_proposal.call_count, 1)
        self.assertEqual(self.manager.modification_planner.create_execution_plan.call_count, 0)
        self.assertEqual(self.manager.modification_planner.execute_plan.call_count, 0)
    
    def test_anomaly_handling(self):
        """Test handling of anomalies."""
        # Configure mock
        self.manager.current_phase = MetacognitivePhase.IDLE
        self.manager.current_mode = MetacognitiveMode.SEMI_AUTONOMOUS
        
        # Create a mock anomaly
        anomaly = MagicMock()
        anomaly.anomaly_type = "resource_saturation"
        anomaly.severity = 0.8
        anomaly.affected_component = "CPU"
        anomaly.description = "CPU usage is critical"
        
        # Handle anomaly with patched _execute_metacognitive_cycle
        with patch.object(self.manager, '_execute_metacognitive_cycle') as mock_execute_cycle:
            self.manager._on_anomaly_detected(anomaly)
            
            # Verify cycle was triggered
            mock_execute_cycle.assert_called_once()
        
        # Verify event was logged
        self.assertEqual(len(self.manager.event_history), 1)
        self.assertEqual(self.manager.event_history[0].event_type, "anomaly_detected")
    
    def test_event_subscription(self):
        """Test subscribing to events."""
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
    
    def test_get_recent_events(self):
        """Test getting recent events."""
        # Generate some events
        for i in range(10):
            self.manager._log_event(f"event_{i}", {"index": i})
        
        # Get all events
        all_events = self.manager.get_recent_events()
        self.assertEqual(len(all_events), 10)
        
        # Get limited events
        limited_events = self.manager.get_recent_events(limit=5)
        self.assertEqual(len(limited_events), 5)
        
        # Get events by type
        type_events = self.manager.get_recent_events(event_type="event_5")
        self.assertEqual(len(type_events), 1)
        self.assertEqual(type_events[0].event_type, "event_5")
    
    def test_get_current_status(self):
        """Test getting current status."""
        # Get status
        status = self.manager.get_current_status()
        
        # Verify status
        self.assertIsInstance(status, dict)
        self.assertEqual(status["is_initialized"], True)
        self.assertEqual(status["is_running"], False)
        self.assertEqual(status["current_mode"], self.manager.current_mode.value)
        self.assertEqual(status["current_phase"], self.manager.current_phase.value)
        self.assertEqual(status["components"]["self_monitoring"], True)
        self.assertEqual(status["components"]["meta_knowledge"], True)
        self.assertEqual(status["components"]["diagnostician"], True)
        self.assertEqual(status["components"]["modification_planner"], True)
        self.assertEqual(status["components"]["module_library"], True)
    
    def test_modification_proposal_management(self):
        """Test managing modification proposals."""
        # Configure mock
        mock_proposal = MagicMock()
        mock_proposal.proposal_id = "test_proposal"
        mock_proposal.status = "proposed"
        
        self.manager.modification_planner.get_proposal.return_value = mock_proposal
        self.manager.modification_planner.proposals = {"test_proposal": mock_proposal}
        
        # Test approving proposal
        success = self.manager.approve_modification_proposal("test_proposal")
        self.assertTrue(success)
        self.assertEqual(mock_proposal.status, "approved")
        
        # Verify event was logged
        self.assertEqual(len(self.manager.event_history), 1)
        self.assertEqual(self.manager.event_history[0].event_type, "proposal_approved")
        
        # Test rejecting proposal
        mock_proposal.status = "proposed"  # Reset status
        self.manager.event_history.clear()  # Clear events
        
        success = self.manager.reject_modification_proposal("test_proposal", "Test reason")
        self.assertTrue(success)
        self.assertEqual(mock_proposal.status, "rejected")
        
        # Verify event was logged
        self.assertEqual(len(self.manager.event_history), 1)
        self.assertEqual(self.manager.event_history[0].event_type, "proposal_rejected")
        self.assertEqual(self.manager.event_history[0].details["reason"], "Test reason")
    
    def test_execute_modification(self):
        """Test executing a modification."""
        # Configure mocks
        mock_proposal = MagicMock()
        mock_proposal.proposal_id = "test_proposal"
        mock_proposal.status = "approved"
        
        mock_plan = MagicMock()
        mock_plan.plan_id = "test_plan"
        
        mock_result = MagicMock()
        mock_result.result_id = "test_result"
        mock_result.success = True
        
        self.manager.modification_planner.get_proposal.return_value = mock_proposal
        self.manager.modification_planner.create_execution_plan.return_value = mock_plan
        self.manager.modification_planner.execute_plan.return_value = mock_result
        
        # Execute modification
        success, message = self.manager.execute_modification("test_proposal")
        
        # Verify execution
        self.assertTrue(success)
        self.manager.modification_planner.get_proposal.assert_called_once_with("test_proposal")
        self.manager.modification_planner.create_execution_plan.assert_called_once_with("test_proposal")
        self.manager.modification_planner.execute_plan.assert_called_once()
        
        # Verify event was logged
        self.assertEqual(len(self.manager.event_history), 1)
        self.assertEqual(self.manager.event_history[0].event_type, "modification_executed")
        self.assertEqual(self.manager.event_history[0].details["proposal_id"], "test_proposal")
        self.assertEqual(self.manager.event_history[0].details["plan_id"], "test_plan")
        self.assertEqual(self.manager.event_history[0].details["result_id"], "test_result")
        self.assertEqual(self.manager.event_history[0].details["success"], True)


if __name__ == '__main__':
    unittest.main()