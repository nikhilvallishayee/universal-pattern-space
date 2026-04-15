"""
Unit tests for the SelfMonitoringModule.
"""

import unittest
from unittest.mock import MagicMock, patch
import time

from godelOS.metacognition.self_monitoring import (
    SelfMonitoringModule,
    ReasoningEvent,
    PerformanceAnomaly,
    AnomalyType
)
from godelOS.symbol_grounding.internal_state_monitor import (
    InternalStateMonitor,
    ResourceStatus,
    ModuleStatus
)


class TestSelfMonitoringModule(unittest.TestCase):
    """Test cases for the SelfMonitoringModule."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks
        self.mock_internal_state_monitor = MagicMock(spec=InternalStateMonitor)
        self.mock_kr_interface = MagicMock()
        self.mock_type_system = MagicMock()
        
        # Configure mocks
        self.mock_kr_interface.list_contexts.return_value = []
        self.mock_internal_state_monitor.get_current_state_summary.return_value = {
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
                }
            }
        }
        
        # Create SelfMonitoringModule instance
        self.monitoring_module = SelfMonitoringModule(
            internal_state_monitor=self.mock_internal_state_monitor,
            kr_system_interface=self.mock_kr_interface,
            type_system=self.mock_type_system,
            history_window_size=10,
            anomaly_detection_interval_sec=0.1,
            performance_metrics_interval_sec=0.1
        )
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop monitoring if it was started
        if hasattr(self, 'monitoring_module'):
            self.monitoring_module.stop_monitoring()
    
    def test_initialization(self):
        """Test initialization of SelfMonitoringModule."""
        # Verify context creation
        self.mock_kr_interface.create_context.assert_called_once()
        
        # Verify attributes
        self.assertEqual(self.monitoring_module.internal_state_monitor, self.mock_internal_state_monitor)
        self.assertEqual(self.monitoring_module.kr_interface, self.mock_kr_interface)
        self.assertEqual(self.monitoring_module.type_system, self.mock_type_system)
        self.assertEqual(self.monitoring_module.history_window_size, 10)
        self.assertEqual(len(self.monitoring_module.reasoning_history), 0)
        self.assertEqual(len(self.monitoring_module.anomaly_history), 0)
    
    def test_record_reasoning_event(self):
        """Test recording a reasoning event."""
        # Record a reasoning event
        self.monitoring_module.record_reasoning_event(
            strategy_name="TestStrategy",
            successful=True,
            duration_ms=100.0,
            goal_id="test_goal"
        )
        
        # Verify event was recorded
        self.assertEqual(len(self.monitoring_module.reasoning_history), 1)
        self.assertEqual(self.monitoring_module.strategy_success_counts["TestStrategy"], 1)
        self.assertEqual(self.monitoring_module.strategy_failure_counts["TestStrategy"], 0)
        self.assertEqual(self.monitoring_module.strategy_durations["TestStrategy"], [100.0])
        
        # Record a failed reasoning event
        self.monitoring_module.record_reasoning_event(
            strategy_name="TestStrategy",
            successful=False,
            duration_ms=200.0,
            goal_id="test_goal"
        )
        
        # Verify event was recorded
        self.assertEqual(len(self.monitoring_module.reasoning_history), 2)
        self.assertEqual(self.monitoring_module.strategy_success_counts["TestStrategy"], 1)
        self.assertEqual(self.monitoring_module.strategy_failure_counts["TestStrategy"], 1)
        self.assertEqual(self.monitoring_module.strategy_durations["TestStrategy"], [100.0, 200.0])
    
    def test_get_strategy_success_rate(self):
        """Test getting strategy success rate."""
        # Record events
        self.monitoring_module.record_reasoning_event(
            strategy_name="TestStrategy",
            successful=True,
            duration_ms=100.0,
            goal_id="test_goal"
        )
        self.monitoring_module.record_reasoning_event(
            strategy_name="TestStrategy",
            successful=True,
            duration_ms=150.0,
            goal_id="test_goal"
        )
        self.monitoring_module.record_reasoning_event(
            strategy_name="TestStrategy",
            successful=False,
            duration_ms=200.0,
            goal_id="test_goal"
        )
        
        # Get success rate
        success_rate = self.monitoring_module.get_strategy_success_rate("TestStrategy")
        
        # Verify success rate
        self.assertEqual(success_rate, 2/3)
        
        # Test with unknown strategy
        unknown_rate = self.monitoring_module.get_strategy_success_rate("UnknownStrategy")
        self.assertEqual(unknown_rate, 0.0)
    
    def test_get_strategy_average_duration(self):
        """Test getting strategy average duration."""
        # Record events
        self.monitoring_module.record_reasoning_event(
            strategy_name="TestStrategy",
            successful=True,
            duration_ms=100.0,
            goal_id="test_goal"
        )
        self.monitoring_module.record_reasoning_event(
            strategy_name="TestStrategy",
            successful=True,
            duration_ms=200.0,
            goal_id="test_goal"
        )
        
        # Get average duration
        avg_duration = self.monitoring_module.get_strategy_average_duration("TestStrategy")
        
        # Verify average duration
        self.assertEqual(avg_duration, 150.0)
        
        # Test with unknown strategy
        unknown_duration = self.monitoring_module.get_strategy_average_duration("UnknownStrategy")
        self.assertEqual(unknown_duration, 0.0)
    
    def test_timeout_anomaly_detection(self):
        """Test detection of reasoning timeout anomalies."""
        # Set a low timeout threshold
        self.monitoring_module.anomaly_thresholds["reasoning_timeout_ms"] = 100.0
        
        # Record an event that exceeds the timeout
        self.monitoring_module.record_reasoning_event(
            strategy_name="TestStrategy",
            successful=False,
            duration_ms=200.0,
            goal_id="test_goal"
        )
        
        # Verify anomaly was detected
        self.assertEqual(len(self.monitoring_module.anomaly_history), 1)
        anomaly = self.monitoring_module.anomaly_history[0]
        self.assertEqual(anomaly.anomaly_type, AnomalyType.REASONING_TIMEOUT.value)
        self.assertEqual(anomaly.affected_component, "Reasoning strategy TestStrategy")
    
    @patch('time.sleep', return_value=None)  # Mock sleep to speed up test
    def test_anomaly_detection_loop(self, mock_sleep):
        """Test the anomaly detection loop."""
        # Configure mock to return high CPU usage
        self.mock_internal_state_monitor.get_current_state_summary.return_value = {
            "system_resources": {
                "CPU": {"value": 95.0, "status": ResourceStatus.CRITICAL.value},
                "Memory": {"value": 60.0, "status": ResourceStatus.MODERATE.value}
            },
            "module_states": {}
        }
        
        # Set up a callback to detect anomalies
        anomalies_detected = []
        def anomaly_callback(anomaly):
            anomalies_detected.append(anomaly)
        
        self.monitoring_module.register_anomaly_callback(anomaly_callback)
        
        # Run the anomaly detection loop once
        self.monitoring_module._detect_anomalies()
        
        # Verify anomaly was detected
        self.assertEqual(len(self.monitoring_module.anomaly_history), 1)
        self.assertEqual(len(anomalies_detected), 1)
        
        anomaly = self.monitoring_module.anomaly_history[0]
        self.assertEqual(anomaly.anomaly_type, AnomalyType.RESOURCE_SATURATION.value)
        self.assertEqual(anomaly.affected_component, "CPU")
    
    def test_get_performance_metrics(self):
        """Test getting performance metrics."""
        # Configure mock to return specific metrics
        self.mock_internal_state_monitor.get_current_state_summary.return_value = {
            "system_resources": {
                "CPU": {"value": 50.0, "status": ResourceStatus.MODERATE.value}
            },
            "module_states": {
                "InferenceEngine": {
                    "status": ModuleStatus.ACTIVE.value,
                    "metrics": {"active_tasks": 2}
                }
            }
        }
        
        # Calculate performance metrics
        self.monitoring_module._calculate_performance_metrics()
        
        # Get metrics
        metrics = self.monitoring_module.get_performance_metrics()
        
        # Verify metrics
        self.assertIn("system_resources", metrics)
        self.assertIn("module_states", metrics)
        self.assertIn("CPU", metrics["system_resources"])
        self.assertIn("InferenceEngine", metrics["module_states"])
    
    def test_get_recent_anomalies(self):
        """Test getting recent anomalies."""
        # Create some anomalies
        for i in range(5):
            self.monitoring_module._record_anomaly(
                anomaly_type=AnomalyType.RESOURCE_SATURATION,
                severity=0.5,
                affected_component=f"Component{i}",
                description=f"Test anomaly {i}",
                metrics={"test": i}
            )
        
        # Get all anomalies
        all_anomalies = self.monitoring_module.get_recent_anomalies()
        self.assertEqual(len(all_anomalies), 5)
        
        # Get limited anomalies
        limited_anomalies = self.monitoring_module.get_recent_anomalies(limit=3)
        self.assertEqual(len(limited_anomalies), 3)
        
        # Verify most recent anomalies are returned
        self.assertEqual(limited_anomalies[0].affected_component, "Component2")
        self.assertEqual(limited_anomalies[1].affected_component, "Component3")
        self.assertEqual(limited_anomalies[2].affected_component, "Component4")
    
    @patch('threading.Thread')
    def test_start_stop_monitoring(self, mock_thread):
        """Test starting and stopping monitoring."""
        # Start monitoring
        self.monitoring_module.start_monitoring()
        
        # Verify threads were started
        self.assertEqual(mock_thread.call_count, 2)
        mock_thread.return_value.start.assert_called()
        
        # Stop monitoring
        self.monitoring_module.stop_monitoring()
        
        # Verify stop event was set
        self.assertTrue(self.monitoring_module.stop_threads.is_set())


if __name__ == '__main__':
    unittest.main()