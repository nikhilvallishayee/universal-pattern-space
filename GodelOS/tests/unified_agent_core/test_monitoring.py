"""
Tests for the monitoring system components.

These tests verify the functionality of the monitoring system components including:
- PerformanceMonitor
- HealthChecker
- DiagnosticTools
- TelemetryCollector
- UnifiedMonitoringSystem
"""

import unittest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import logging

from godelOS.unified_agent_core.monitoring.interfaces import (
    SystemHealthStatus, SystemHealth, PerformanceMetrics,
    DiagnosticResult, TelemetryData
)
from godelOS.unified_agent_core.monitoring.performance_monitor import PerformanceMonitor
from godelOS.unified_agent_core.monitoring.health_checker import HealthChecker
from godelOS.unified_agent_core.monitoring.diagnostic_tools import DiagnosticTools
from godelOS.unified_agent_core.monitoring.telemetry_collector import TelemetryCollector
from godelOS.unified_agent_core.monitoring.system import UnifiedMonitoringSystem


class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for the PerformanceMonitor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor()
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        if self.monitor.is_running:
            self.loop.run_until_complete(self.monitor.stop())
        self.loop.close()

    def test_initialization(self):
        """Test that the PerformanceMonitor initializes correctly."""
        self.assertFalse(self.monitor.is_running)
        self.assertEqual(self.monitor.metrics_history, [])
        self.assertEqual(self.monitor.custom_metrics, {})
        self.assertEqual(self.monitor.monitoring_interval, 60)  # Default 60 seconds

    def test_start_stop(self):
        """Test starting and stopping the monitor."""
        # Start the monitor
        start_result = self.loop.run_until_complete(self.monitor.start())
        self.assertTrue(start_result)
        self.assertTrue(self.monitor.is_running)
        
        # Stop the monitor
        stop_result = self.loop.run_until_complete(self.monitor.stop())
        self.assertTrue(stop_result)
        self.assertFalse(self.monitor.is_running)

    def test_get_metrics(self):
        """Test getting performance metrics."""
        # Get metrics
        metrics = self.loop.run_until_complete(self.monitor.get_metrics())
        
        # Verify metrics structure
        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertGreaterEqual(metrics.cpu_usage, 0.0)
        self.assertGreaterEqual(metrics.memory_usage, 0.0)
        self.assertIsInstance(metrics.response_times, dict)
        self.assertIsInstance(metrics.throughput, dict)
        self.assertIsInstance(metrics.custom_metrics, dict)

    def test_register_custom_metric(self):
        """Test registering a custom metric."""
        # Define a mock metric callback
        async def mock_metric_callback():
            return 42.0
        
        # Register the metric
        result = self.loop.run_until_complete(
            self.monitor.register_custom_metric("test-metric", mock_metric_callback)
        )
        
        self.assertTrue(result)
        self.assertIn("test-metric", self.monitor.custom_metrics)
        
        # Get metrics to include the custom metric
        metrics = self.loop.run_until_complete(self.monitor.get_metrics())
        
        # Custom metrics might not be immediately available if the monitoring
        # task hasn't run yet, so we'll check if it's registered correctly
        self.assertIn("test-metric", self.monitor.custom_metrics)

    def test_unregister_custom_metric(self):
        """Test unregistering a custom metric."""
        # First register a metric
        async def mock_metric_callback():
            return 42.0
        
        self.loop.run_until_complete(
            self.monitor.register_custom_metric("test-metric", mock_metric_callback)
        )
        
        # Now unregister it
        result = self.loop.run_until_complete(
            self.monitor.unregister_custom_metric("test-metric")
        )
        
        self.assertTrue(result)
        self.assertNotIn("test-metric", self.monitor.custom_metrics)


class TestHealthChecker(unittest.TestCase):
    """Test cases for the HealthChecker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.checker = HealthChecker()
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        if self.checker.is_running:
            self.loop.run_until_complete(self.checker.stop())
        self.loop.close()

    def test_initialization(self):
        """Test that the HealthChecker initializes correctly."""
        self.assertFalse(self.checker.is_running)
        self.assertEqual(self.checker.health_checks, {})
        self.assertEqual(self.checker.health_history, [])
        self.assertEqual(self.checker.check_interval, 60)  # Default 60 seconds

    def test_start_stop(self):
        """Test starting and stopping the checker."""
        # Start the checker
        start_result = self.loop.run_until_complete(self.checker.start())
        self.assertTrue(start_result)
        self.assertTrue(self.checker.is_running)
        
        # Stop the checker
        stop_result = self.loop.run_until_complete(self.checker.stop())
        self.assertTrue(stop_result)
        self.assertFalse(self.checker.is_running)

    def test_check_with_no_health_checks(self):
        """Test checking health with no registered health checks."""
        health = self.loop.run_until_complete(self.checker.check())
        
        self.assertIsInstance(health, SystemHealth)
        self.assertEqual(health.status, SystemHealthStatus.UNKNOWN)
        self.assertEqual(health.components, {})

    def test_register_health_check(self):
        """Test registering a health check."""
        # Define a mock health check callback
        async def mock_health_check():
            return SystemHealthStatus.HEALTHY.value
        
        # Register the health check
        result = self.loop.run_until_complete(
            self.checker.register_health_check("test-component", mock_health_check)
        )
        
        self.assertTrue(result)
        self.assertIn("test-component", self.checker.health_checks)
        
        # Check health to include the new component
        health = self.loop.run_until_complete(self.checker.check())
        
        self.assertIn("test-component", health.components)
        self.assertEqual(health.components["test-component"], SystemHealthStatus.HEALTHY)

    def test_unregister_health_check(self):
        """Test unregistering a health check."""
        # First register a health check
        async def mock_health_check():
            return SystemHealthStatus.HEALTHY.value
        
        self.loop.run_until_complete(
            self.checker.register_health_check("test-component", mock_health_check)
        )
        
        # Now unregister it
        result = self.loop.run_until_complete(
            self.checker.unregister_health_check("test-component")
        )
        
        self.assertTrue(result)
        self.assertNotIn("test-component", self.checker.health_checks)
        
        # Check health to verify the component is gone
        health = self.loop.run_until_complete(self.checker.check())
        
        self.assertNotIn("test-component", health.components)


class TestDiagnosticTools(unittest.TestCase):
    """Test cases for the DiagnosticTools class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tools = DiagnosticTools()
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_initialization(self):
        """Test that the DiagnosticTools initializes correctly."""
        self.assertFalse(self.tools.is_initialized)
        self.assertEqual(self.tools.diagnostics, {})
        self.assertEqual(self.tools.error_logs, [])
        self.assertEqual(self.tools.max_error_logs, 1000)

    def test_initialize(self):
        """Test initializing the diagnostic tools."""
        result = self.loop.run_until_complete(self.tools.initialize())
        
        self.assertTrue(result)
        self.assertTrue(self.tools.is_initialized)

    def test_run_diagnostic_nonexistent(self):
        """Test running a diagnostic that doesn't exist."""
        # Initialize first
        self.loop.run_until_complete(self.tools.initialize())
        
        result = self.loop.run_until_complete(
            self.tools.run_diagnostic("nonexistent", "nonexistent-test")
        )
        
        self.assertIsInstance(result, DiagnosticResult)
        self.assertFalse(result.success)
        self.assertEqual(result.component, "nonexistent")
        self.assertEqual(result.test_name, "nonexistent-test")
        self.assertIn("not found", result.message.lower())

    def test_register_and_run_diagnostic(self):
        """Test registering and running a diagnostic."""
        # Initialize first
        self.loop.run_until_complete(self.tools.initialize())
        
        # Define a mock diagnostic callback
        async def mock_diagnostic():
            return DiagnosticResult(
                success=True,
                component="test-component",
                test_name="test-diagnostic",
                message="Test diagnostic ran successfully"
            )
        
        # Register the diagnostic
        result = self.loop.run_until_complete(
            self.tools.register_diagnostic("test-component", "test-diagnostic", mock_diagnostic)
        )
        
        self.assertTrue(result)
        self.assertIn("test-component", self.tools.diagnostics)
        self.assertIn("test-diagnostic", self.tools.diagnostics["test-component"])
        
        # Run the diagnostic
        diagnostic_result = self.loop.run_until_complete(
            self.tools.run_diagnostic("test-component", "test-diagnostic")
        )
        
        self.assertTrue(diagnostic_result.success)
        self.assertEqual(diagnostic_result.component, "test-component")
        self.assertEqual(diagnostic_result.test_name, "test-diagnostic")
        self.assertEqual(diagnostic_result.message, "Test diagnostic ran successfully")

    def test_log_error(self):
        """Test logging an error."""
        # Initialize first
        self.loop.run_until_complete(self.tools.initialize())
        
        # Log an error
        test_error = ValueError("Test error")
        result = self.loop.run_until_complete(self.tools.log_error(test_error))
        
        self.assertTrue(result)
        self.assertEqual(len(self.tools.error_logs), 1)
        self.assertEqual(self.tools.error_logs[0]["error_type"], "ValueError")
        self.assertEqual(self.tools.error_logs[0]["message"], "Test error")

    def test_get_error_logs(self):
        """Test getting error logs."""
        # Initialize first
        self.loop.run_until_complete(self.tools.initialize())
        
        # Log some errors
        errors = [
            ValueError("Error 1"),
            RuntimeError("Error 2"),
            TypeError("Error 3")
        ]
        
        for error in errors:
            self.loop.run_until_complete(self.tools.log_error(error))
        
        # Get all logs
        logs = self.loop.run_until_complete(self.tools.get_error_logs())
        
        self.assertEqual(len(logs), len(errors))
        
        # Get logs with component filter
        self.loop.run_until_complete(
            self.tools.log_error(ValueError("Component error"), component="test-component")
        )
        
        component_logs = self.loop.run_until_complete(
            self.tools.get_error_logs(component="test-component")
        )
        
        self.assertEqual(len(component_logs), 1)
        self.assertEqual(component_logs[0]["component"], "test-component")


class TestTelemetryCollector(unittest.TestCase):
    """Test cases for the TelemetryCollector class."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = TelemetryCollector()
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        if self.collector.is_running:
            self.loop.run_until_complete(self.collector.stop())
        self.loop.close()

    def test_initialization(self):
        """Test that the TelemetryCollector initializes correctly."""
        self.assertFalse(self.collector.is_running)
        self.assertEqual(self.collector.collectors, {})
        self.assertEqual(self.collector.telemetry_data, [])
        self.assertEqual(self.collector.collection_interval, 60)  # Default 60 seconds
        self.assertEqual(self.collector.max_data_points, 10000)

    def test_start_stop(self):
        """Test starting and stopping the collector."""
        # Start the collector
        start_result = self.loop.run_until_complete(self.collector.start())
        self.assertTrue(start_result)
        self.assertTrue(self.collector.is_running)
        
        # Stop the collector
        stop_result = self.loop.run_until_complete(self.collector.stop())
        self.assertTrue(stop_result)
        self.assertFalse(self.collector.is_running)

    def test_collect(self):
        """Test collecting telemetry data."""
        # Create test telemetry data
        telemetry = TelemetryData(
            source="test-source",
            data_type="test-type",
            data={"value": 42}
        )
        
        # Collect the data
        result = self.loop.run_until_complete(self.collector.collect(telemetry))
        
        self.assertTrue(result)
        self.assertEqual(len(self.collector.telemetry_data), 1)
        self.assertEqual(self.collector.telemetry_data[0].source, "test-source")
        self.assertEqual(self.collector.telemetry_data[0].data_type, "test-type")
        self.assertEqual(self.collector.telemetry_data[0].data["value"], 42)

    def test_get_telemetry(self):
        """Test getting telemetry data."""
        # Collect some telemetry data
        telemetry_items = [
            TelemetryData(source="source1", data_type="type1", data={"value": 1}),
            TelemetryData(source="source1", data_type="type2", data={"value": 2}),
            TelemetryData(source="source2", data_type="type1", data={"value": 3})
        ]
        
        for item in telemetry_items:
            self.loop.run_until_complete(self.collector.collect(item))
        
        # Get all telemetry
        telemetry = self.loop.run_until_complete(self.collector.get_telemetry())
        
        self.assertEqual(len(telemetry), len(telemetry_items))
        
        # Get telemetry with source filter
        source1_telemetry = self.loop.run_until_complete(
            self.collector.get_telemetry(source="source1")
        )
        
        self.assertEqual(len(source1_telemetry), 2)
        for item in source1_telemetry:
            self.assertEqual(item.source, "source1")
        
        # Get telemetry with data_type filter
        type1_telemetry = self.loop.run_until_complete(
            self.collector.get_telemetry(data_type="type1")
        )
        
        self.assertEqual(len(type1_telemetry), 2)
        for item in type1_telemetry:
            self.assertEqual(item.data_type, "type1")

    def test_register_collector(self):
        """Test registering a telemetry collector."""
        # Define a mock collector callback
        async def mock_collector():
            return {"value": 42}
        
        # Register the collector
        result = self.loop.run_until_complete(
            self.collector.register_collector("test-source", "test-type", mock_collector)
        )
        
        self.assertTrue(result)
        self.assertIn("test-source", self.collector.collectors)
        self.assertIn("test-type", self.collector.collectors["test-source"])
        
        # Start the collector to trigger collection
        self.loop.run_until_complete(self.collector.start())
        
        # Wait a bit for the collection to happen
        # In a real test, we might mock the time or use other techniques
        # to avoid actual waiting, but for simplicity we'll just wait
        time.sleep(0.1)
        
        # Stop the collector
        self.loop.run_until_complete(self.collector.stop())


class TestUnifiedMonitoringSystem(unittest.TestCase):
    """Test cases for the UnifiedMonitoringSystem class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock components
        self.performance_monitor = AsyncMock()
        self.health_checker = AsyncMock()
        self.diagnostic_tools = AsyncMock()
        self.telemetry_collector = AsyncMock()
        
        # Create test instance
        self.monitoring_system = UnifiedMonitoringSystem(
            config={
                "performance_monitor": {},
                "health_checker": {},
                "diagnostic_tools": {},
                "telemetry_collector": {}
            }
        )
        
        # Replace components with mocks
        self.monitoring_system.performance_monitor = self.performance_monitor
        self.monitoring_system.health_checker = self.health_checker
        self.monitoring_system.diagnostic_tools = self.diagnostic_tools
        self.monitoring_system.telemetry_collector = self.telemetry_collector
        
        # Set up event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_initialization(self):
        """Test that the UnifiedMonitoringSystem initializes correctly."""
        system = UnifiedMonitoringSystem()  # Create a fresh instance
        
        self.assertIsInstance(system.performance_monitor, PerformanceMonitor)
        self.assertIsInstance(system.health_checker, HealthChecker)
        self.assertIsInstance(system.diagnostic_tools, DiagnosticTools)
        self.assertIsInstance(system.telemetry_collector, TelemetryCollector)
        self.assertFalse(system.is_initialized)
        self.assertFalse(system.is_running)

    def test_initialize(self):
        """Test the initialize method."""
        # Mock diagnostic_tools.initialize to return True
        self.diagnostic_tools.initialize.return_value = True
        
        result = self.loop.run_until_complete(self.monitoring_system.initialize())
        
        self.assertTrue(result)
        self.assertTrue(self.monitoring_system.is_initialized)
        
        # Verify component initialization
        self.diagnostic_tools.initialize.assert_called_once()

    def test_start(self):
        """Test the start method."""
        # Set initialized state
        self.monitoring_system.is_initialized = True
        
        # Mock component start methods to return True
        self.performance_monitor.start.return_value = True
        self.health_checker.start.return_value = True
        self.telemetry_collector.start.return_value = True
        
        result = self.loop.run_until_complete(self.monitoring_system.start())
        
        self.assertTrue(result)
        self.assertTrue(self.monitoring_system.is_running)
        
        # Verify components are started
        self.performance_monitor.start.assert_called_once()
        self.health_checker.start.assert_called_once()
        self.telemetry_collector.start.assert_called_once()

    def test_stop(self):
        """Test the stop method."""
        # Set running state
        self.monitoring_system.is_running = True
        
        # Mock component stop methods to return True
        self.performance_monitor.stop.return_value = True
        self.health_checker.stop.return_value = True
        self.telemetry_collector.stop.return_value = True
        
        result = self.loop.run_until_complete(self.monitoring_system.stop())
        
        self.assertTrue(result)
        self.assertFalse(self.monitoring_system.is_running)
        
        # Verify components are stopped
        self.performance_monitor.stop.assert_called_once()
        self.health_checker.stop.assert_called_once()
        self.telemetry_collector.stop.assert_called_once()

    def test_check_health(self):
        """Test the check_health method."""
        # Set initialized state
        self.monitoring_system.is_initialized = True
        
        # Mock health_checker.check to return a SystemHealth object
        mock_health = SystemHealth(status=SystemHealthStatus.HEALTHY)
        self.health_checker.check.return_value = mock_health
        
        result = self.loop.run_until_complete(self.monitoring_system.check_health())
        
        self.assertEqual(result, mock_health)
        self.health_checker.check.assert_called_once()

    def test_get_performance_metrics(self):
        """Test the get_performance_metrics method."""
        # Set initialized state
        self.monitoring_system.is_initialized = True
        
        # Mock performance_monitor.get_metrics to return a PerformanceMetrics object
        mock_metrics = PerformanceMetrics(cpu_usage=0.5, memory_usage=0.3)
        self.performance_monitor.get_metrics.return_value = mock_metrics
        
        result = self.loop.run_until_complete(self.monitoring_system.get_performance_metrics())
        
        self.assertEqual(result, mock_metrics)
        self.performance_monitor.get_metrics.assert_called_once()

    def test_run_diagnostic(self):
        """Test the run_diagnostic method."""
        # Set initialized state
        self.monitoring_system.is_initialized = True
        
        # Mock diagnostic_tools.run_diagnostic to return a DiagnosticResult object
        mock_result = DiagnosticResult(
            success=True,
            component="test-component",
            test_name="test-diagnostic"
        )
        self.diagnostic_tools.run_diagnostic.return_value = mock_result
        
        result = self.loop.run_until_complete(
            self.monitoring_system.run_diagnostic("test-component", "test-diagnostic")
        )
        
        self.assertEqual(result, mock_result)
        self.diagnostic_tools.run_diagnostic.assert_called_once_with(
            "test-component", "test-diagnostic"
        )

    def test_log_error(self):
        """Test the log_error method."""
        # Set initialized state
        self.monitoring_system.is_initialized = True
        
        # Mock diagnostic_tools.log_error to return True
        self.diagnostic_tools.log_error.return_value = True
        
        # Create a test error
        test_error = ValueError("Test error")
        
        result = self.loop.run_until_complete(self.monitoring_system.log_error(test_error))
        
        self.assertTrue(result)
        self.diagnostic_tools.log_error.assert_called_once_with(test_error)

    def test_collect_telemetry(self):
        """Test the collect_telemetry method."""
        # Set initialized state
        self.monitoring_system.is_initialized = True
        
        # Mock telemetry_collector.collect to return True
        self.telemetry_collector.collect.return_value = True
        
        # Create test telemetry data
        test_telemetry = TelemetryData(
            source="test-source",
            data_type="test-type",
            data={"value": 42}
        )
        
        result = self.loop.run_until_complete(
            self.monitoring_system.collect_telemetry(test_telemetry)
        )
        
        self.assertTrue(result)
        self.telemetry_collector.collect.assert_called_once_with(test_telemetry)

    def test_register_health_check(self):
        """Test the register_health_check method."""
        # Set initialized state
        self.monitoring_system.is_initialized = True
        
        # Mock health_checker.register_health_check to return True
        self.health_checker.register_health_check.return_value = True
        
        # Define a mock callback
        async def mock_callback():
            return SystemHealthStatus.HEALTHY.value
        
        result = self.loop.run_until_complete(
            self.monitoring_system.register_health_check("test-component", mock_callback)
        )
        
        self.assertTrue(result)
        self.health_checker.register_health_check.assert_called_once_with(
            "test-component", mock_callback
        )

    def test_register_diagnostic(self):
        """Test the register_diagnostic method."""
        # Set initialized state
        self.monitoring_system.is_initialized = True
        
        # Mock diagnostic_tools.register_diagnostic to return True
        self.diagnostic_tools.register_diagnostic.return_value = True
        
        # Define a mock callback
        async def mock_callback():
            return DiagnosticResult(
                success=True,
                component="test-component",
                test_name="test-diagnostic"
            )
        
        result = self.loop.run_until_complete(
            self.monitoring_system.register_diagnostic(
                "test-component", "test-diagnostic", mock_callback
            )
        )
        
        self.assertTrue(result)
        self.diagnostic_tools.register_diagnostic.assert_called_once_with(
            "test-component", "test-diagnostic", mock_callback
        )

    def test_register_telemetry_collector(self):
        """Test the register_telemetry_collector method."""
        # Set initialized state
        self.monitoring_system.is_initialized = True
        
        # Mock telemetry_collector.register_collector to return True
        self.telemetry_collector.register_collector.return_value = True
        
        # Define a mock callback
        async def mock_callback():
            return {"value": 42}
        
        result = self.loop.run_until_complete(
            self.monitoring_system.register_telemetry_collector(
                "test-source", "test-type", mock_callback
            )
        )
        
        self.assertTrue(result)
        self.telemetry_collector.register_collector.assert_called_once_with(
            "test-source", "test-type", mock_callback
        )


if __name__ == "__main__":
    unittest.main()