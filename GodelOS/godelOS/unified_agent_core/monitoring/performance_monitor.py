"""
PerformanceMonitor Implementation for GodelOS

This module implements the PerformanceMonitor class, which provides performance
monitoring capabilities for the UnifiedAgentCore.
"""

import logging
import time
import asyncio
import psutil
import os
from typing import Dict, List, Optional, Any, Callable, Tuple
from collections import deque

from godelOS.unified_agent_core.monitoring.interfaces import (
    PerformanceMonitorInterface, PerformanceMetrics
)

logger = logging.getLogger(__name__)


class PerformanceMonitor(PerformanceMonitorInterface):
    """
    Performance monitor implementation.
    
    Monitors system performance metrics such as CPU usage, memory usage,
    response times, and throughput.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the performance monitor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize state
        self.is_running = False
        self.monitoring_task = None
        
        # Sampling configuration
        self.sampling_interval = self.config.get("sampling_interval", 1.0)  # seconds
        self.history_size = self.config.get("history_size", 100)
        self.monitoring_interval = self.config.get("monitoring_interval", 60)  # Default 60 seconds
        
        # Initialize metrics
        self.process = psutil.Process(os.getpid())
        self.cpu_usage_history = deque(maxlen=self.history_size)
        self.memory_usage_history = deque(maxlen=self.history_size)
        self.response_times: Dict[str, deque] = {}
        self.throughput_counters: Dict[str, int] = {}
        self.throughput_history: Dict[str, deque] = {}
        self.last_throughput_time = time.time()
        
        # Custom metrics
        self.custom_metrics: Dict[str, Callable] = {}
        self.custom_metrics_history: Dict[str, deque] = {}
        
        # Metrics history for test compatibility
        self.metrics_history = []
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    async def start(self) -> bool:
        """
        Start the performance monitor.
        
        Returns:
            True if the monitor was started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("PerformanceMonitor is already running")
            return True
        
        try:
            logger.info("Starting PerformanceMonitor")
            
            self.is_running = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            logger.info("PerformanceMonitor started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error starting PerformanceMonitor: {e}")
            self.is_running = False
            return False
    
    async def stop(self) -> bool:
        """
        Stop the performance monitor.
        
        Returns:
            True if the monitor was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("PerformanceMonitor is not running")
            return True
        
        try:
            logger.info("Stopping PerformanceMonitor")
            
            self.is_running = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
                self.monitoring_task = None
            
            logger.info("PerformanceMonitor stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping PerformanceMonitor: {e}")
            return False
    
    async def get_metrics(self) -> PerformanceMetrics:
        """
        Get performance metrics.
        
        Returns:
            The performance metrics
        """
        async with self.lock:
            # Calculate CPU usage (average of recent samples)
            cpu_usage = 0.0
            if self.cpu_usage_history:
                cpu_usage = sum(self.cpu_usage_history) / len(self.cpu_usage_history)
            
            # Calculate memory usage (latest sample)
            memory_usage = 0.0
            if self.memory_usage_history:
                memory_usage = self.memory_usage_history[-1]
            
            # Calculate response times (average of recent samples)
            response_times = {}
            for endpoint, times in self.response_times.items():
                if times:
                    response_times[endpoint] = sum(times) / len(times)
            
            # Calculate throughput (requests per second)
            throughput = {}
            for endpoint, history in self.throughput_history.items():
                if history:
                    throughput[endpoint] = sum(history) / len(history)
            
            # Get custom metrics (latest values)
            custom_metrics = {}
            for name, history in self.custom_metrics_history.items():
                if history:
                    custom_metrics[name] = history[-1]
            
            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                response_times=response_times,
                throughput=throughput,
                custom_metrics=custom_metrics
            )
    
    async def register_custom_metric(self, name: str, callback: Callable) -> bool:
        """
        Register a custom metric.
        
        Args:
            name: The name of the metric
            callback: A callback function that returns the metric value
            
        Returns:
            True if the metric was registered successfully, False otherwise
        """
        async with self.lock:
            try:
                self.custom_metrics[name] = callback
                self.custom_metrics_history[name] = deque(maxlen=self.history_size)
                logger.info(f"Registered custom metric: {name}")
                return True
            
            except Exception as e:
                logger.error(f"Error registering custom metric {name}: {e}")
                return False
    
    async def unregister_custom_metric(self, name: str) -> bool:
        """
        Unregister a custom metric.
        
        Args:
            name: The name of the metric
            
        Returns:
            True if the metric was unregistered successfully, False otherwise
        """
        async with self.lock:
            try:
                if name in self.custom_metrics:
                    del self.custom_metrics[name]
                    del self.custom_metrics_history[name]
                    logger.info(f"Unregistered custom metric: {name}")
                    return True
                else:
                    logger.warning(f"Custom metric not found: {name}")
                    return False
            
            except Exception as e:
                logger.error(f"Error unregistering custom metric {name}: {e}")
                return False
    
    async def record_response_time(self, endpoint: str, response_time: float) -> None:
        """
        Record a response time for an endpoint.
        
        Args:
            endpoint: The endpoint
            response_time: The response time in seconds
        """
        async with self.lock:
            if endpoint not in self.response_times:
                self.response_times[endpoint] = deque(maxlen=self.history_size)
            
            self.response_times[endpoint].append(response_time)
    
    async def increment_throughput(self, endpoint: str) -> None:
        """
        Increment the throughput counter for an endpoint.
        
        Args:
            endpoint: The endpoint
        """
        async with self.lock:
            if endpoint not in self.throughput_counters:
                self.throughput_counters[endpoint] = 0
                self.throughput_history[endpoint] = deque(maxlen=self.history_size)
            
            self.throughput_counters[endpoint] += 1
    
    async def _monitoring_loop(self) -> None:
        """Background task for collecting performance metrics."""
        try:
            while self.is_running:
                await self._collect_metrics()
                await asyncio.sleep(self.sampling_interval)
        
        except asyncio.CancelledError:
            logger.info("Performance monitoring loop cancelled")
            raise
        
        except Exception as e:
            logger.error(f"Error in performance monitoring loop: {e}")
            if self.is_running:
                # Restart the monitoring loop
                self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def _collect_metrics(self) -> None:
        """Collect performance metrics."""
        async with self.lock:
            try:
                # Collect CPU usage
                cpu_percent = self.process.cpu_percent() / psutil.cpu_count()
                self.cpu_usage_history.append(cpu_percent)
                
                # Collect memory usage
                memory_info = self.process.memory_info()
                memory_percent = memory_info.rss / psutil.virtual_memory().total * 100
                self.memory_usage_history.append(memory_percent)
                
                # Calculate throughput
                current_time = time.time()
                elapsed = current_time - self.last_throughput_time
                
                if elapsed >= 1.0:  # Calculate throughput at least every second
                    for endpoint, count in self.throughput_counters.items():
                        throughput = count / elapsed
                        self.throughput_history[endpoint].append(throughput)
                        self.throughput_counters[endpoint] = 0
                    
                    self.last_throughput_time = current_time
                
                # Collect custom metrics
                for name, callback in self.custom_metrics.items():
                    try:
                        value = callback()
                        self.custom_metrics_history[name].append(value)
                    except Exception as e:
                        logger.error(f"Error collecting custom metric {name}: {e}")
            
            except Exception as e:
                logger.error(f"Error collecting performance metrics: {e}")