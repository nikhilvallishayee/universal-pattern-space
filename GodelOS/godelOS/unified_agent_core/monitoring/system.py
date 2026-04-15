"""
UnifiedMonitoringSystem Implementation for GodelOS

This module implements the UnifiedMonitoringSystem class, which provides monitoring
capabilities including performance monitoring, health checking, diagnostics, and
telemetry collection for the UnifiedAgentCore.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable

from godelOS.unified_agent_core.monitoring.interfaces import (
    AbstractUnifiedMonitoringSystem, SystemHealth, PerformanceMetrics,
    DiagnosticResult, TelemetryData
)
from godelOS.unified_agent_core.monitoring.performance_monitor import PerformanceMonitor
from godelOS.unified_agent_core.monitoring.health_checker import HealthChecker
from godelOS.unified_agent_core.monitoring.diagnostic_tools import DiagnosticTools
from godelOS.unified_agent_core.monitoring.telemetry_collector import TelemetryCollector

logger = logging.getLogger(__name__)


class UnifiedMonitoringSystem(AbstractUnifiedMonitoringSystem):
    """
    UnifiedMonitoringSystem implementation for GodelOS.
    
    The UnifiedMonitoringSystem provides monitoring capabilities including
    performance monitoring, health checking, diagnostics, and telemetry collection
    for the UnifiedAgentCore.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the unified monitoring system.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        self.performance_monitor = PerformanceMonitor(self.config.get("performance_monitor"))
        self.health_checker = HealthChecker(self.config.get("health_checker"))
        self.diagnostic_tools = DiagnosticTools(self.config.get("diagnostic_tools"))
        self.telemetry_collector = TelemetryCollector(self.config.get("telemetry_collector"))
        
        # Initialize state
        self.is_initialized = False
        self.is_running = False
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """
        Initialize the monitoring system.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self.is_initialized:
            logger.warning("UnifiedMonitoringSystem is already initialized")
            return True
        
        try:
            logger.info("Initializing UnifiedMonitoringSystem")
            
            # Initialize components
            await self.diagnostic_tools.initialize()
            
            # Register health checks
            await self._register_health_checks()
            
            # Register telemetry collectors
            await self._register_telemetry_collectors()
            
            self.is_initialized = True
            logger.info("UnifiedMonitoringSystem initialized successfully")
            
            return True
        
        except Exception as e:
            logger.error(f"Error initializing UnifiedMonitoringSystem: {e}")
            return False
    
    async def start(self) -> bool:
        """
        Start the monitoring system.
        
        Returns:
            True if the system was started successfully, False otherwise
        """
        if not self.is_initialized:
            success = await self.initialize()
            if not success:
                return False
        
        if self.is_running:
            logger.warning("UnifiedMonitoringSystem is already running")
            return True
        
        try:
            logger.info("Starting UnifiedMonitoringSystem")
            
            # Start components
            await self.performance_monitor.start()
            await self.health_checker.start()
            await self.telemetry_collector.start()
            
            self.is_running = True
            logger.info("UnifiedMonitoringSystem started successfully")
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting UnifiedMonitoringSystem: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the monitoring system.
        
        Returns:
            True if the system was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("UnifiedMonitoringSystem is not running")
            return True
        
        try:
            logger.info("Stopping UnifiedMonitoringSystem")
            
            # Stop components
            await self.performance_monitor.stop()
            await self.health_checker.stop()
            await self.telemetry_collector.stop()
            
            self.is_running = False
            logger.info("UnifiedMonitoringSystem stopped successfully")
            
            return True
        
        except Exception as e:
            logger.error(f"Error stopping UnifiedMonitoringSystem: {e}")
            return False
    
    async def check_health(self) -> SystemHealth:
        """
        Check the health of the system.
        
        Returns:
            The system health
        """
        if not self.is_initialized:
            raise RuntimeError("UnifiedMonitoringSystem is not initialized")
        
        try:
            return await self.health_checker.check()
        
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            await self.log_error(e)
            
            return SystemHealth(
                status="unknown",
                message=f"Error checking system health: {str(e)}"
            )
    
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Get performance metrics.
        
        Returns:
            The performance metrics
        """
        if not self.is_initialized:
            raise RuntimeError("UnifiedMonitoringSystem is not initialized")
        
        try:
            return await self.performance_monitor.get_metrics()
        
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            await self.log_error(e)
            
            # Return empty metrics
            return PerformanceMetrics(
                cpu_usage=0.0,
                memory_usage=0.0
            )
    
    async def run_diagnostic(self, component: str, test_name: str) -> DiagnosticResult:
        """
        Run a diagnostic test.
        
        Args:
            component: The name of the component
            test_name: The name of the test
            
        Returns:
            The diagnostic result
        """
        if not self.is_initialized:
            raise RuntimeError("UnifiedMonitoringSystem is not initialized")
        
        try:
            return await self.diagnostic_tools.run_diagnostic(component, test_name)
        
        except Exception as e:
            logger.error(f"Error running diagnostic {component}.{test_name}: {e}")
            await self.log_error(e)
            
            return DiagnosticResult(
                success=False,
                component=component,
                test_name=test_name,
                message=f"Error running diagnostic: {str(e)}"
            )
    
    async def log_error(self, error: Exception) -> bool:
        """
        Log an error.
        
        Args:
            error: The error to log
            
        Returns:
            True if the error was logged successfully, False otherwise
        """
        if not self.is_initialized:
            logger.error(f"UnifiedMonitoringSystem is not initialized, error will be logged to system logger only: {error}")
            return False
        
        try:
            return await self.diagnostic_tools.log_error(error)
        
        except Exception as e:
            logger.error(f"Error logging error: {e}")
            return False
    
    async def collect_telemetry(self, telemetry: TelemetryData) -> bool:
        """
        Collect telemetry data.
        
        Args:
            telemetry: The telemetry data to collect
            
        Returns:
            True if the data was collected successfully, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("UnifiedMonitoringSystem is not initialized")
        
        try:
            return await self.telemetry_collector.collect(telemetry)
        
        except Exception as e:
            logger.error(f"Error collecting telemetry data: {e}")
            await self.log_error(e)
            
            return False
    
    async def register_health_check(self, component: str, callback: Callable) -> bool:
        """
        Register a health check.
        
        Args:
            component: The name of the component
            callback: A callback function that returns the component health status
            
        Returns:
            True if the health check was registered successfully, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("UnifiedMonitoringSystem is not initialized")
        
        try:
            return await self.health_checker.register_health_check(component, callback)
        
        except Exception as e:
            logger.error(f"Error registering health check for component {component}: {e}")
            await self.log_error(e)
            
            return False
    
    async def register_diagnostic(self, component: str, test_name: str, callback: Callable) -> bool:
        """
        Register a diagnostic test.
        
        Args:
            component: The name of the component
            test_name: The name of the test
            callback: A callback function that performs the diagnostic test
            
        Returns:
            True if the diagnostic was registered successfully, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("UnifiedMonitoringSystem is not initialized")
        
        try:
            return await self.diagnostic_tools.register_diagnostic(component, test_name, callback)
        
        except Exception as e:
            logger.error(f"Error registering diagnostic {component}.{test_name}: {e}")
            await self.log_error(e)
            
            return False
    
    async def register_telemetry_collector(self, source: str, data_type: str, callback: Callable) -> bool:
        """
        Register a telemetry collector.
        
        Args:
            source: The source of the telemetry
            data_type: The type of data to collect
            callback: A callback function that returns the telemetry data
            
        Returns:
            True if the collector was registered successfully, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("UnifiedMonitoringSystem is not initialized")
        
        try:
            return await self.telemetry_collector.register_collector(source, data_type, callback)
        
        except Exception as e:
            logger.error(f"Error registering telemetry collector {source}.{data_type}: {e}")
            await self.log_error(e)
            
            return False
    
    async def _register_health_checks(self) -> None:
        """Register built-in health checks."""
        # Register component health checks
        await self.health_checker.register_health_check("performance_monitor", self._check_performance_monitor_health)
        await self.health_checker.register_health_check("health_checker", self._check_health_checker_health)
        await self.health_checker.register_health_check("diagnostic_tools", self._check_diagnostic_tools_health)
        await self.health_checker.register_health_check("telemetry_collector", self._check_telemetry_collector_health)
    
    async def _register_telemetry_collectors(self) -> None:
        """Register built-in telemetry collectors."""
        # Register component telemetry collectors
        await self.telemetry_collector.register_collector("system", "performance", self._collect_performance_telemetry)
        await self.telemetry_collector.register_collector("system", "health", self._collect_health_telemetry)
    
    async def _check_performance_monitor_health(self) -> str:
        """Check performance monitor health."""
        try:
            if not hasattr(self.performance_monitor, "is_running"):
                return "unknown"
            
            return "healthy" if self.performance_monitor.is_running else "degraded"
        
        except Exception as e:
            logger.error(f"Error checking performance monitor health: {e}")
            return "unhealthy"
    
    async def _check_health_checker_health(self) -> str:
        """Check health checker health."""
        try:
            if not hasattr(self.health_checker, "is_running"):
                return "unknown"
            
            return "healthy" if self.health_checker.is_running else "degraded"
        
        except Exception as e:
            logger.error(f"Error checking health checker health: {e}")
            return "unhealthy"
    
    async def _check_diagnostic_tools_health(self) -> str:
        """Check diagnostic tools health."""
        try:
            if not hasattr(self.diagnostic_tools, "is_initialized"):
                return "unknown"
            
            return "healthy" if self.diagnostic_tools.is_initialized else "degraded"
        
        except Exception as e:
            logger.error(f"Error checking diagnostic tools health: {e}")
            return "unhealthy"
    
    async def _check_telemetry_collector_health(self) -> str:
        """Check telemetry collector health."""
        try:
            if not hasattr(self.telemetry_collector, "is_running"):
                return "unknown"
            
            return "healthy" if self.telemetry_collector.is_running else "degraded"
        
        except Exception as e:
            logger.error(f"Error checking telemetry collector health: {e}")
            return "unhealthy"
    
    async def _collect_performance_telemetry(self) -> Dict[str, Any]:
        """Collect performance telemetry."""
        try:
            metrics = await self.performance_monitor.get_metrics()
            
            return {
                "cpu_usage": metrics.cpu_usage,
                "memory_usage": metrics.memory_usage,
                "response_times": metrics.response_times,
                "throughput": metrics.throughput
            }
        
        except Exception as e:
            logger.error(f"Error collecting performance telemetry: {e}")
            return {
                "error": str(e)
            }
    
    async def _collect_health_telemetry(self) -> Dict[str, Any]:
        """Collect health telemetry."""
        try:
            health = await self.health_checker.check()
            
            return {
                "status": health.status.value if hasattr(health.status, "value") else str(health.status),
                "components": {
                    component: status.value if hasattr(status, "value") else str(status)
                    for component, status in health.components.items()
                }
            }
        
        except Exception as e:
            logger.error(f"Error collecting health telemetry: {e}")
            return {
                "error": str(e)
            }