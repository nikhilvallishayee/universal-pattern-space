"""
Interfaces for the monitoring module.

This module defines the interfaces for the monitoring components of the UnifiedAgentCore.
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class SystemHealthStatus(Enum):
    """Health status of the system."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SystemHealth:
    """
    Represents the health of the system.
    """
    status: SystemHealthStatus
    components: Dict[str, SystemHealthStatus] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())
    message: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """
    Represents performance metrics for the system.
    """
    cpu_usage: float
    memory_usage: float
    response_times: Dict[str, float] = field(default_factory=dict)
    throughput: Dict[str, float] = field(default_factory=dict)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())


@dataclass
class DiagnosticResult:
    """
    Represents the result of a diagnostic operation.
    """
    success: bool
    component: str
    test_name: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())
    message: Optional[str] = None


@dataclass
class TelemetryData:
    """
    Represents telemetry data collected from the system.
    """
    source: str
    data_type: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=lambda: time.time())
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitorInterface(ABC):
    """Interface for the performance monitor."""
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the performance monitor.
        
        Returns:
            True if the monitor was started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the performance monitor.
        
        Returns:
            True if the monitor was stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_metrics(self) -> PerformanceMetrics:
        """
        Get performance metrics.
        
        Returns:
            The performance metrics
        """
        pass
    
    @abstractmethod
    async def register_custom_metric(self, name: str, callback: callable) -> bool:
        """
        Register a custom metric.
        
        Args:
            name: The name of the metric
            callback: A callback function that returns the metric value
            
        Returns:
            True if the metric was registered successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def unregister_custom_metric(self, name: str) -> bool:
        """
        Unregister a custom metric.
        
        Args:
            name: The name of the metric
            
        Returns:
            True if the metric was unregistered successfully, False otherwise
        """
        pass


class HealthCheckerInterface(ABC):
    """Interface for the health checker."""
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the health checker.
        
        Returns:
            True if the checker was started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the health checker.
        
        Returns:
            True if the checker was stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def check(self) -> SystemHealth:
        """
        Check the health of the system.
        
        Returns:
            The system health
        """
        pass
    
    @abstractmethod
    async def register_health_check(self, component: str, callback: callable) -> bool:
        """
        Register a health check.
        
        Args:
            component: The name of the component
            callback: A callback function that returns the component health status
            
        Returns:
            True if the health check was registered successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def unregister_health_check(self, component: str) -> bool:
        """
        Unregister a health check.
        
        Args:
            component: The name of the component
            
        Returns:
            True if the health check was unregistered successfully, False otherwise
        """
        pass


class DiagnosticToolsInterface(ABC):
    """Interface for the diagnostic tools."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the diagnostic tools.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def run_diagnostic(self, component: str, test_name: str) -> DiagnosticResult:
        """
        Run a diagnostic test.
        
        Args:
            component: The name of the component
            test_name: The name of the test
            
        Returns:
            The diagnostic result
        """
        pass
    
    @abstractmethod
    async def log_error(self, error: Exception) -> bool:
        """
        Log an error.
        
        Args:
            error: The error to log
            
        Returns:
            True if the error was logged successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_error_logs(self, component: Optional[str] = None, 
                            start_time: Optional[float] = None,
                            end_time: Optional[float] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get error logs.
        
        Args:
            component: Optional component filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of logs to return
            
        Returns:
            The error logs
        """
        pass
    
    @abstractmethod
    async def register_diagnostic(self, component: str, test_name: str, callback: callable) -> bool:
        """
        Register a diagnostic test.
        
        Args:
            component: The name of the component
            test_name: The name of the test
            callback: A callback function that performs the diagnostic test
            
        Returns:
            True if the diagnostic was registered successfully, False otherwise
        """
        pass


class TelemetryCollectorInterface(ABC):
    """Interface for the telemetry collector."""
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the telemetry collector.
        
        Returns:
            True if the collector was started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the telemetry collector.
        
        Returns:
            True if the collector was stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def collect(self, telemetry: TelemetryData) -> bool:
        """
        Collect telemetry data.
        
        Args:
            telemetry: The telemetry data to collect
            
        Returns:
            True if the data was collected successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_telemetry(self, source: Optional[str] = None,
                           data_type: Optional[str] = None,
                           start_time: Optional[float] = None,
                           end_time: Optional[float] = None,
                           limit: int = 100) -> List[TelemetryData]:
        """
        Get telemetry data.
        
        Args:
            source: Optional source filter
            data_type: Optional data type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of data points to return
            
        Returns:
            The telemetry data
        """
        pass
    
    @abstractmethod
    async def register_collector(self, source: str, data_type: str, callback: callable) -> bool:
        """
        Register a telemetry collector.
        
        Args:
            source: The source of the telemetry
            data_type: The type of data to collect
            callback: A callback function that returns the telemetry data
            
        Returns:
            True if the collector was registered successfully, False otherwise
        """
        pass


class AbstractUnifiedMonitoringSystem(ABC):
    """Abstract base class for the UnifiedMonitoringSystem."""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the monitoring system.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def start(self) -> bool:
        """
        Start the monitoring system.
        
        Returns:
            True if the system was started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the monitoring system.
        
        Returns:
            True if the system was stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def check_health(self) -> SystemHealth:
        """
        Check the health of the system.
        
        Returns:
            The system health
        """
        pass
    
    @abstractmethod
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Get performance metrics.
        
        Returns:
            The performance metrics
        """
        pass
    
    @abstractmethod
    async def run_diagnostic(self, component: str, test_name: str) -> DiagnosticResult:
        """
        Run a diagnostic test.
        
        Args:
            component: The name of the component
            test_name: The name of the test
            
        Returns:
            The diagnostic result
        """
        pass
    
    @abstractmethod
    async def log_error(self, error: Exception) -> bool:
        """
        Log an error.
        
        Args:
            error: The error to log
            
        Returns:
            True if the error was logged successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def collect_telemetry(self, telemetry: TelemetryData) -> bool:
        """
        Collect telemetry data.
        
        Args:
            telemetry: The telemetry data to collect
            
        Returns:
            True if the data was collected successfully, False otherwise
        """
        pass