"""
Self-Monitoring Module (SMM) for GödelOS.

This module implements the SelfMonitoringModule component (Module 7.1) of the Metacognition & 
Self-Improvement System, which is responsible for monitoring system performance, resource usage, 
and cognitive operations to support metacognitive processes.

The SelfMonitoringModule:
1. Monitors system performance, resource usage, and cognitive operations
2. Tracks success/failure rates of different reasoning strategies
3. Detects anomalies and potential issues
4. Integrates with InternalStateMonitor from Module 4.5
5. Provides an API for other metacognition components to access monitoring data
"""

import logging
import time
import threading
import statistics
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import deque, defaultdict

from godelOS.symbol_grounding.internal_state_monitor import (
    InternalStateMonitor, 
    SystemMetric, 
    ModuleState, 
    ResourceStatus,
    ModuleStatus
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.manager import TypeSystemManager

logger = logging.getLogger(__name__)


@dataclass
class ReasoningEvent:
    """Represents a reasoning event with its outcome and metadata."""
    strategy_name: str
    successful: bool
    duration_ms: float
    goal_id: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAnomaly:
    """Represents a detected anomaly in system or cognitive performance."""
    anomaly_type: str
    severity: float  # 0.0 to 1.0
    affected_component: str
    description: str
    timestamp: float = field(default_factory=time.time)
    metrics: Dict[str, Any] = field(default_factory=dict)


class AnomalyType(Enum):
    """Enum representing types of performance anomalies."""
    RESOURCE_SATURATION = "resource_saturation"
    REASONING_TIMEOUT = "reasoning_timeout"
    HIGH_FAILURE_RATE = "high_failure_rate"
    MEMORY_LEAK = "memory_leak"
    DEADLOCK = "deadlock"
    THRASHING = "thrashing"
    PERFORMANCE_DEGRADATION = "performance_degradation"


class SelfMonitoringModule:
    """
    Self-Monitoring Module (SMM) for GödelOS.
    
    The SelfMonitoringModule monitors system performance, resource usage, and cognitive operations
    to support metacognitive processes. It builds on the InternalStateMonitor to provide higher-level
    monitoring capabilities focused on metacognition.
    """
    
    def __init__(
        self, 
        internal_state_monitor: InternalStateMonitor,
        kr_system_interface: KnowledgeStoreInterface,
        type_system: TypeSystemManager,
        metacognition_context_id: str = "METACOGNITION_CONTEXT",
        history_window_size: int = 100,
        anomaly_detection_interval_sec: float = 10.0,
        performance_metrics_interval_sec: float = 5.0
    ):
        """Initialize the self-monitoring module."""
        self.internal_state_monitor = internal_state_monitor
        self.kr_interface = kr_system_interface
        self.type_system = type_system
        self.metacognition_context_id = metacognition_context_id
        self.history_window_size = history_window_size
        self.anomaly_detection_interval_sec = anomaly_detection_interval_sec
        self.performance_metrics_interval_sec = performance_metrics_interval_sec
        
        # Create metacognition context if it doesn't exist
        if metacognition_context_id not in kr_system_interface.list_contexts():
            kr_system_interface.create_context(metacognition_context_id, None, "metacognition")
        
        # Initialize history tracking
        self.reasoning_history = deque(maxlen=history_window_size)
        self.anomaly_history = deque(maxlen=history_window_size)
        self.resource_history = defaultdict(lambda: deque(maxlen=history_window_size))
        self.module_state_history = defaultdict(lambda: deque(maxlen=history_window_size))
        
        # Strategy performance tracking
        self.strategy_success_counts = defaultdict(int)
        self.strategy_failure_counts = defaultdict(int)
        self.strategy_durations = defaultdict(list)
        
        # Performance metrics
        self.current_performance_metrics = {}
        
        # Anomaly detection thresholds
        self.anomaly_thresholds = {
            "cpu_saturation": 95.0,  # CPU usage percentage
            "memory_saturation": 90.0,  # Memory usage percentage
            "reasoning_timeout_ms": 5000.0,  # Reasoning timeout in milliseconds
            "strategy_failure_rate": 0.3,  # Strategy failure rate (0.0 to 1.0)
            "performance_degradation_factor": 1.5,  # Performance degradation factor
        }
        
        # Initialize monitoring threads
        self.anomaly_detection_thread = None
        self.performance_metrics_thread = None
        self.stop_threads = threading.Event()
        
        # Callbacks for anomaly notifications
        self.anomaly_callbacks = []
    
    def start_monitoring(self) -> None:
        """Start the monitoring threads."""
        # Make sure the internal state monitor is running
        logger.debug(f"Internal state monitor: {self.internal_state_monitor}")
        try:
            if not hasattr(self.internal_state_monitor, 'monitoring_thread') or not self.internal_state_monitor.monitoring_thread or not self.internal_state_monitor.monitoring_thread.is_alive():
                logger.debug("Starting internal state monitor")
                self.internal_state_monitor.start_monitoring()
        except AttributeError as e:
            logger.error(f"AttributeError accessing monitoring_thread: {e}")
        
        if (self.anomaly_detection_thread and self.anomaly_detection_thread.is_alive() and
            self.performance_metrics_thread and self.performance_metrics_thread.is_alive()):
            logger.warning("Monitoring threads are already running")
            return
        
        self.stop_threads.clear()
        
        # Start anomaly detection thread
        self.anomaly_detection_thread = threading.Thread(
            target=self._anomaly_detection_loop,
            daemon=True
        )
        self.anomaly_detection_thread.start()
        
        # Start performance metrics thread
        self.performance_metrics_thread = threading.Thread(
            target=self._performance_metrics_loop,
            daemon=True
        )
        self.performance_metrics_thread.start()
        
        logger.info("Started self-monitoring threads")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring threads."""
        if (not self.anomaly_detection_thread or not self.anomaly_detection_thread.is_alive() or
            not self.performance_metrics_thread or not self.performance_metrics_thread.is_alive()):
            logger.warning("Monitoring threads are not running")
            return
        
        self.stop_threads.set()
        self.anomaly_detection_thread.join(timeout=2.0)
        self.performance_metrics_thread.join(timeout=2.0)
        logger.info("Stopped self-monitoring threads")
    
    def record_reasoning_event(
        self, 
        strategy_name: str, 
        successful: bool, 
        duration_ms: float, 
        goal_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a reasoning event."""
        event = ReasoningEvent(
            strategy_name=strategy_name,
            successful=successful,
            duration_ms=duration_ms,
            goal_id=goal_id,
            metadata=metadata or {}
        )
        
        # Add to history
        self.reasoning_history.append(event)
        
        # Update strategy performance tracking
        if successful:
            self.strategy_success_counts[strategy_name] += 1
        else:
            self.strategy_failure_counts[strategy_name] += 1
        
        self.strategy_durations[strategy_name].append(duration_ms)
        
        # Check for immediate anomalies
        if duration_ms > self.anomaly_thresholds["reasoning_timeout_ms"]:
            self._record_anomaly(
                AnomalyType.REASONING_TIMEOUT,
                0.7,  # Severity
                f"Reasoning strategy {strategy_name}",
                f"Reasoning timeout: {duration_ms}ms > {self.anomaly_thresholds['reasoning_timeout_ms']}ms",
                {"duration_ms": duration_ms, "goal_id": goal_id, "strategy_name": strategy_name}
            )
    
    def get_strategy_success_rate(self, strategy_name: str) -> float:
        """Get the success rate for a reasoning strategy."""
        successes = self.strategy_success_counts[strategy_name]
        failures = self.strategy_failure_counts[strategy_name]
        total = successes + failures
        
        if total == 0:
            return 0.0
        
        return successes / total
    
    def get_strategy_average_duration(self, strategy_name: str) -> float:
        """Get the average duration for a reasoning strategy."""
        durations = self.strategy_durations[strategy_name]
        
        if not durations:
            return 0.0
        
        return statistics.mean(durations)
    
    def get_recent_anomalies(self, limit: Optional[int] = None) -> List[PerformanceAnomaly]:
        """Get recent performance anomalies."""
        if limit is None:
            return list(self.anomaly_history)
        
        return list(self.anomaly_history)[-limit:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.current_performance_metrics.copy()
    
    def register_anomaly_callback(self, callback: Callable[[PerformanceAnomaly], None]) -> None:
        """Register a callback function to be called when an anomaly is detected."""
        self.anomaly_callbacks.append(callback)
    
    def _anomaly_detection_loop(self) -> None:
        """Main loop for anomaly detection."""
        while not self.stop_threads.is_set():
            try:
                self._detect_anomalies()
            except Exception as e:
                logger.error(f"Error in anomaly detection: {e}")
            
            # Sleep until next cycle
            self.stop_threads.wait(self.anomaly_detection_interval_sec)
    
    def _performance_metrics_loop(self) -> None:
        """Main loop for calculating performance metrics."""
        while not self.stop_threads.is_set():
            try:
                self._calculate_performance_metrics()
            except Exception as e:
                logger.error(f"Error in performance metrics calculation: {e}")
            
            # Sleep until next cycle
            self.stop_threads.wait(self.performance_metrics_interval_sec)
    
    def _detect_anomalies(self) -> None:
        """Detect anomalies in system and cognitive performance."""
        # Get current system state
        system_state = self.internal_state_monitor.get_current_state_summary()
        logger.debug(f"Detecting anomalies with system state: {system_state}")
        
        # Check for resource saturation
        for resource_name, metrics in system_state.get("system_resources", {}).items():
            logger.debug(f"Checking resource {resource_name} with metrics {metrics}")
            
            # Debug comparison values
            if resource_name == "CPU":
                logger.debug(f"CPU value: {metrics.get('value', 0)}, threshold: {self.anomaly_thresholds['cpu_saturation']}, comparison result: {metrics.get('value', 0) >= self.anomaly_thresholds['cpu_saturation']}")
            
            if resource_name == "CPU" and metrics.get("value", 0) >= self.anomaly_thresholds["cpu_saturation"]:
                logger.debug(f"CPU saturation detected: {metrics.get('value')}% >= {self.anomaly_thresholds['cpu_saturation']}%")
                self._record_anomaly(
                    AnomalyType.RESOURCE_SATURATION,
                    0.8,  # Severity
                    "CPU",
                    f"CPU saturation: {metrics.get('value')}% >= {self.anomaly_thresholds['cpu_saturation']}%",
                    {"resource": resource_name, "value": metrics.get("value")}
                )
            
            if resource_name == "Memory" and metrics.get("value", 0) >= self.anomaly_thresholds["memory_saturation"]:
                self._record_anomaly(
                    AnomalyType.RESOURCE_SATURATION,
                    0.8,  # Severity
                    "Memory",
                    f"Memory saturation: {metrics.get('value')}% >= {self.anomaly_thresholds['memory_saturation']}%",
                    {"resource": resource_name, "value": metrics.get("value")}
                )
            
            # Track resource history
            if "value" in metrics:
                self.resource_history[resource_name].append(metrics["value"])
        
        # Check for strategy failure rates
        for strategy_name in self.strategy_success_counts.keys():
            success_rate = self.get_strategy_success_rate(strategy_name)
            failure_rate = 1.0 - success_rate
            
            if failure_rate > self.anomaly_thresholds["strategy_failure_rate"]:
                self._record_anomaly(
                    AnomalyType.HIGH_FAILURE_RATE,
                    0.6,  # Severity
                    f"Reasoning strategy {strategy_name}",
                    f"High failure rate: {failure_rate:.2f} > {self.anomaly_thresholds['strategy_failure_rate']}",
                    {"strategy_name": strategy_name, "failure_rate": failure_rate}
                )
        
        # Check for performance degradation
        for module_id, states in self.module_state_history.items():
            if len(states) < 2:
                continue
            
            # Simple performance degradation detection based on module-specific metrics
            if module_id == "InferenceEngine":
                # Check inference steps per second
                if "metrics" in states[-1] and "metrics" in states[0]:
                    current_rate = states[-1]["metrics"].get("inference_steps_per_second", 0)
                    previous_rate = states[0]["metrics"].get("inference_steps_per_second", 0)
                    
                    if (previous_rate > 0 and current_rate > 0 and 
                        previous_rate / current_rate > self.anomaly_thresholds["performance_degradation_factor"]):
                        self._record_anomaly(
                            AnomalyType.PERFORMANCE_DEGRADATION,
                            0.5,  # Severity
                            "InferenceEngine",
                            f"Performance degradation: {previous_rate:.2f} -> {current_rate:.2f} steps/s",
                            {"module_id": module_id, "previous_rate": previous_rate, "current_rate": current_rate}
                        )
    
    def _calculate_performance_metrics(self) -> None:
        """Calculate current performance metrics."""
        metrics = {}
        
        # System resource metrics
        system_state = self.internal_state_monitor.get_current_state_summary()
        metrics["system_resources"] = system_state.get("system_resources", {})
        
        # Module state metrics
        metrics["module_states"] = system_state.get("module_states", {})
        
        # Strategy performance metrics
        strategy_metrics = {}
        for strategy_name in set(self.strategy_success_counts.keys()) | set(self.strategy_failure_counts.keys()):
            strategy_metrics[strategy_name] = {
                "success_rate": self.get_strategy_success_rate(strategy_name),
                "average_duration_ms": self.get_strategy_average_duration(strategy_name),
                "total_executions": (self.strategy_success_counts[strategy_name] + 
                                    self.strategy_failure_counts[strategy_name])
            }
        
        metrics["reasoning_strategies"] = strategy_metrics
        
        # Anomaly metrics
        metrics["anomalies"] = {
            "recent_count": len(self.anomaly_history),
            "by_type": defaultdict(int)
        }
        
        for anomaly in self.anomaly_history:
            metrics["anomalies"]["by_type"][anomaly.anomaly_type] += 1
        
        # Update current metrics
        self.current_performance_metrics = metrics
    
    def _record_anomaly(
        self,
        anomaly_type: Union[AnomalyType, str],
        severity: float,
        affected_component: str,
        description: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a performance anomaly."""
        # Handle both enum and string values for anomaly_type
        anomaly_type_value = anomaly_type.value if isinstance(anomaly_type, AnomalyType) else anomaly_type
        
        logger.debug(f"Recording anomaly: type={anomaly_type_value}, component={affected_component}, description={description}")
        
        anomaly = PerformanceAnomaly(
            anomaly_type=anomaly_type_value,
            severity=severity,
            affected_component=affected_component,
            description=description,
            metrics=metrics or {}
        )
        
        # Add to history
        self.anomaly_history.append(anomaly)
        
        # Log the anomaly
        logger.warning(f"Performance anomaly detected: {description}")
        
        # Notify callbacks
        for callback in self.anomaly_callbacks:
            try:
                callback(anomaly)
            except Exception as e:
                logger.error(f"Error in anomaly callback: {e}")