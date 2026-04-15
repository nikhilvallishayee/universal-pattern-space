#!/usr/bin/env python3
"""
Enhanced Metrics System with Histograms and Build Information

This module provides comprehensive metrics collection including latency histograms,
build/version information, and detailed performance tracking for cognitive operations.
"""

import time
import json
import subprocess
import platform
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
import threading

@dataclass
class BuildInfo:
    """Build and version information."""
    git_sha: Optional[str] = None
    git_branch: Optional[str] = None
    git_tag: Optional[str] = None
    build_time: Optional[str] = None
    version: str = "unknown"
    python_version: str = platform.python_version()
    platform: str = platform.platform()

@dataclass
class LatencyHistogram:
    """Histogram for tracking latency distributions."""
    buckets: List[float] = field(default_factory=lambda: [
        0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')
    ])
    counts: Dict[float, int] = field(default_factory=dict)
    total_count: int = 0
    total_sum: float = 0.0
    
    def __post_init__(self):
        if not self.counts:
            self.counts = {bucket: 0 for bucket in self.buckets}
    
    def observe(self, value: float):
        """Add an observation to the histogram."""
        self.total_count += 1
        self.total_sum += value
        
        # Find the appropriate bucket
        for bucket in self.buckets:
            if value <= bucket:
                self.counts[bucket] += 1
                break
    
    def get_percentile(self, percentile: float) -> float:
        """Calculate percentile from histogram."""
        if self.total_count == 0:
            return 0.0
        
        target_count = self.total_count * (percentile / 100.0)
        current_count = 0
        
        for bucket in self.buckets:
            current_count += self.counts[bucket]
            if current_count >= target_count:
                return bucket
        
        return self.buckets[-1]
    
    def get_average(self) -> float:
        """Get average latency."""
        return self.total_sum / self.total_count if self.total_count > 0 else 0.0
    
    def to_prometheus(self, metric_name: str) -> str:
        """Export as Prometheus histogram format."""
        lines = []
        
        # Bucket counts
        for bucket in self.buckets:
            bucket_str = "+Inf" if bucket == float('inf') else str(bucket)
            lines.append(f'{metric_name}_bucket{{le="{bucket_str}"}} {self.counts[bucket]}')
        
        # Total count and sum
        lines.append(f'{metric_name}_count {self.total_count}')
        lines.append(f'{metric_name}_sum {self.total_sum}')
        
        return '\n'.join(lines)

class MetricsCollector:
    """Comprehensive metrics collector with histograms and counters."""
    
    def __init__(self):
        self.lock = Lock()
        
        # Counters
        self.counters: Dict[str, int] = defaultdict(int)
        
        # Gauges
        self.gauges: Dict[str, float] = {}
        
        # Histograms
        self.histograms: Dict[str, LatencyHistogram] = {}
        
        # Error counters by service and code
        self.error_counters: Dict[Tuple[str, str], int] = defaultdict(int)
        
        # Cognitive-specific metrics
        self.cognitive_metrics = {
            "query_processing_total": 0,
            "query_processing_success": 0,
            "coordination_decisions_total": 0,
            "consciousness_assessments_total": 0,
            "circuit_breaker_opens": 0,
            "adaptive_learning_predictions": 0,
            "knowledge_retrieval_requests": 0,
            "websocket_connections_active": 0,
            "websocket_messages_sent": 0,
            "reasoning_trace_depth_total": 0.0,
            "reasoning_trace_count": 0
        }
        
        # Performance tracking
        self.recent_operations: deque = deque(maxlen=1000)
        
        # Build info
        self.build_info = self._get_build_info()
        
        # System info cache
        self.system_info_cache = {}
        self.system_info_cache_time = 0
        
        # Initialize default histograms
        self._init_default_histograms()
    
    def _init_default_histograms(self):
        """Initialize default histograms for common operations."""
        operations = [
            "query_processing_duration_seconds",
            "llm_request_duration_seconds", 
            "vector_search_duration_seconds",
            "consciousness_assessment_duration_seconds",
            "coordination_decision_duration_seconds",
            "knowledge_retrieval_duration_seconds",
            "websocket_broadcast_duration_seconds",
            "circuit_breaker_call_duration_seconds"
        ]
        
        for op in operations:
            self.histograms[op] = LatencyHistogram()
    
    def _get_build_info(self) -> BuildInfo:
        """Extract build and version information."""
        build_info = BuildInfo()
        
        try:
            # Get git information
            git_sha = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], 
                stderr=subprocess.DEVNULL
            ).decode().strip()
            build_info.git_sha = git_sha[:12]  # Short SHA
            
            git_branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            build_info.git_branch = git_branch
            
            # Try to get tag
            try:
                git_tag = subprocess.check_output(
                    ['git', 'describe', '--tags', '--exact-match'],
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                build_info.git_tag = git_tag
                build_info.version = git_tag
            except subprocess.CalledProcessError:
                # No exact tag match
                build_info.version = f"{git_branch}-{build_info.git_sha}"
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Git not available or not in git repo
            pass
        
        # Build time (approximate)
        build_info.build_time = datetime.utcnow().isoformat() + "Z"
        
        return build_info
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        with self.lock:
            metric_key = name
            if labels:
                label_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
                metric_key = f"{name}{{{label_str}}}"
            
            self.counters[metric_key] += value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric."""
        with self.lock:
            metric_key = name
            if labels:
                label_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
                metric_key = f"{name}{{{label_str}}}"
            
            self.gauges[metric_key] = value
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observe a value in a histogram."""
        with self.lock:
            metric_key = name
            if labels:
                label_str = ','.join(f'{k}="{v}"' for k, v in sorted(labels.items()))
                metric_key = f"{name}{{{label_str}}}"
            
            if metric_key not in self.histograms:
                self.histograms[metric_key] = LatencyHistogram()
            
            self.histograms[metric_key].observe(value)
    
    def record_error(self, service: str, error_code: str, count: int = 1):
        """Record an error by service and error code."""
        with self.lock:
            self.error_counters[(service, error_code)] += count
    
    def record_cognitive_event(self, event_type: str, success: bool = True, **kwargs):
        """Record a cognitive processing event."""
        with self.lock:
            if event_type == "query_processing":
                self.cognitive_metrics["query_processing_total"] += 1
                if success:
                    self.cognitive_metrics["query_processing_success"] += 1
            
            elif event_type == "coordination_decision":
                self.cognitive_metrics["coordination_decisions_total"] += 1
            
            elif event_type == "consciousness_assessment":
                self.cognitive_metrics["consciousness_assessments_total"] += 1
            
            elif event_type == "circuit_breaker_open":
                self.cognitive_metrics["circuit_breaker_opens"] += 1
            
            elif event_type == "adaptive_learning_prediction":
                self.cognitive_metrics["adaptive_learning_predictions"] += 1
            
            elif event_type == "knowledge_retrieval":
                self.cognitive_metrics["knowledge_retrieval_requests"] += 1
            
            elif event_type == "reasoning_trace":
                depth = kwargs.get("depth", 0)
                self.cognitive_metrics["reasoning_trace_depth_total"] += depth
                self.cognitive_metrics["reasoning_trace_count"] += 1
    
    def record_websocket_event(self, event_type: str, count: int = 1):
        """Record WebSocket-related events."""
        with self.lock:
            if event_type == "connection_active":
                self.cognitive_metrics["websocket_connections_active"] = count
            elif event_type == "message_sent":
                self.cognitive_metrics["websocket_messages_sent"] += count
    
    def track_operation(self, operation: str, duration: float, success: bool, **metadata):
        """Track an operation's performance."""
        with self.lock:
            self.recent_operations.append({
                "operation": operation,
                "duration": duration,
                "success": success,
                "timestamp": time.time(),
                "metadata": metadata
            })
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics with caching."""
        current_time = time.time()
        
        # Cache system metrics for 5 seconds
        if current_time - self.system_info_cache_time > 5:
            process = psutil.Process()
            
            self.system_info_cache = {
                "cpu_usage_percent": psutil.cpu_percent(interval=None),
                "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
                "memory_usage_percent": process.memory_percent(),
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "open_files": len(process.open_files()),
                "num_threads": process.num_threads(),
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
                "uptime_seconds": time.time() - psutil.boot_time()
            }
            self.system_info_cache_time = current_time
        
        return self.system_info_cache
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from recent operations."""
        if not self.recent_operations:
            return {}
        
        operations_by_type = defaultdict(list)
        for op in self.recent_operations:
            operations_by_type[op["operation"]].append(op)
        
        summary = {}
        for op_type, ops in operations_by_type.items():
            durations = [op["duration"] for op in ops]
            successes = sum(1 for op in ops if op["success"])
            
            summary[op_type] = {
                "count": len(ops),
                "success_rate": successes / len(ops),
                "avg_duration_ms": sum(durations) / len(durations) * 1000,
                "p95_duration_ms": sorted(durations)[int(0.95 * len(durations))] * 1000,
                "p99_duration_ms": sorted(durations)[int(0.99 * len(durations))] * 1000
            }
        
        return summary
    
    def export_prometheus(self) -> str:
        """Export all metrics in Prometheus format."""
        lines = []
        
        # Build info
        lines.append('# HELP godelos_build_info Build and version information')
        lines.append('# TYPE godelos_build_info gauge')
        lines.append(f'godelos_build_info{{version="{self.build_info.version}",git_sha="{self.build_info.git_sha or "unknown"}",git_branch="{self.build_info.git_branch or "unknown"}",platform="{self.build_info.platform}"}} 1')
        lines.append('')
        
        # System metrics
        system_metrics = self.get_system_metrics()
        lines.append('# HELP godelos_cpu_usage_percent CPU usage percentage')
        lines.append('# TYPE godelos_cpu_usage_percent gauge')
        lines.append(f'godelos_cpu_usage_percent {system_metrics["cpu_usage_percent"]}')
        lines.append('')
        
        lines.append('# HELP godelos_memory_usage_mb Memory usage in megabytes')
        lines.append('# TYPE godelos_memory_usage_mb gauge')
        lines.append(f'godelos_memory_usage_mb {system_metrics["memory_usage_mb"]}')
        lines.append('')
        
        # Counters
        if self.counters:
            lines.append('# Counters')
            for name, value in self.counters.items():
                lines.append(f'# TYPE {name.split("{")[0]} counter')
                lines.append(f'{name} {value}')
            lines.append('')
        
        # Gauges  
        if self.gauges:
            lines.append('# Gauges')
            for name, value in self.gauges.items():
                lines.append(f'# TYPE {name.split("{")[0]} gauge')
                lines.append(f'{name} {value}')
            lines.append('')
        
        # Histograms
        for name, histogram in self.histograms.items():
            lines.append(f'# HELP {name} Latency histogram')
            lines.append(f'# TYPE {name} histogram')
            lines.append(histogram.to_prometheus(name))
            lines.append('')
        
        # Error counters
        if self.error_counters:
            lines.append('# HELP godelos_errors_total Error count by service and code')
            lines.append('# TYPE godelos_errors_total counter')
            for (service, code), count in self.error_counters.items():
                lines.append(f'godelos_errors_total{{service="{service}",code="{code}"}} {count}')
            lines.append('')
        
        # Cognitive metrics
        lines.append('# Cognitive Processing Metrics')
        for name, value in self.cognitive_metrics.items():
            lines.append(f'# TYPE godelos_{name} counter' if 'total' in name else f'# TYPE godelos_{name} gauge')
            lines.append(f'godelos_{name} {value}')
        lines.append('')
        
        # Derived metrics
        if self.cognitive_metrics["query_processing_total"] > 0:
            success_rate = self.cognitive_metrics["query_processing_success"] / self.cognitive_metrics["query_processing_total"]
            lines.append('# HELP godelos_query_success_rate Query processing success rate')
            lines.append('# TYPE godelos_query_success_rate gauge')
            lines.append(f'godelos_query_success_rate {success_rate}')
        
        if self.cognitive_metrics["reasoning_trace_count"] > 0:
            avg_depth = self.cognitive_metrics["reasoning_trace_depth_total"] / self.cognitive_metrics["reasoning_trace_count"]
            lines.append('# HELP godelos_reasoning_depth_average Average reasoning trace depth')
            lines.append('# TYPE godelos_reasoning_depth_average gauge')
            lines.append(f'godelos_reasoning_depth_average {avg_depth}')
        
        return '\n'.join(lines)
    
    def get_json_metrics(self) -> Dict[str, Any]:
        """Export metrics as JSON for API consumption."""
        return {
            "build_info": {
                "version": self.build_info.version,
                "git_sha": self.build_info.git_sha,
                "git_branch": self.build_info.git_branch,
                "git_tag": self.build_info.git_tag,
                "build_time": self.build_info.build_time,
                "python_version": self.build_info.python_version,
                "platform": self.build_info.platform
            },
            "system": self.get_system_metrics(),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                name: {
                    "count": hist.total_count,
                    "sum": hist.total_sum,
                    "average": hist.get_average(),
                    "p50": hist.get_percentile(50),
                    "p95": hist.get_percentile(95),
                    "p99": hist.get_percentile(99)
                }
                for name, hist in self.histograms.items()
            },
            "errors": {
                f"{service}:{code}": count 
                for (service, code), count in self.error_counters.items()
            },
            "cognitive": self.cognitive_metrics,
            "performance": self.get_performance_summary(),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Context manager for operation timing
class operation_timer:
    """Context manager for automatic operation timing."""
    
    def __init__(self, operation_name: str, histogram_name: str = None, 
                 record_cognitive: bool = False, cognitive_event: str = None):
        self.operation_name = operation_name
        self.histogram_name = histogram_name or f"{operation_name}_duration_seconds"
        self.record_cognitive = record_cognitive
        self.cognitive_event = cognitive_event or operation_name
        self.start_time = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.success = exc_type is None
        
        # Record in histogram
        metrics_collector.observe_histogram(self.histogram_name, duration)
        
        # Track operation
        metadata = {}
        if exc_type:
            metadata["error"] = str(exc_val)
        
        metrics_collector.track_operation(
            self.operation_name, duration, self.success, **metadata
        )
        
        # Record cognitive event if requested
        if self.record_cognitive:
            metrics_collector.record_cognitive_event(
                self.cognitive_event, self.success
            )


# Decorator for automatic metrics collection
def collect_metrics(operation_name: str = None, histogram_name: str = None, 
                   record_cognitive: bool = False, cognitive_event: str = None):
    """Decorator to automatically collect metrics for a function."""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with operation_timer(op_name, histogram_name, record_cognitive, cognitive_event):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with operation_timer(op_name, histogram_name, record_cognitive, cognitive_event):
                return func(*args, **kwargs)
        
        if hasattr(func, '__await__'):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
