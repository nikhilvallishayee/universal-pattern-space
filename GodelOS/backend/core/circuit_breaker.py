#!/usr/bin/env python3
"""
Circuit Breaker and Timeout Policies for Cognitive Components

This module provides circuit breaker patterns and timeout policies to prevent
cascading failures and ensure system resilience.
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any, List
from enum import Enum
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures to open circuit
    recovery_timeout: float = 60.0  # Seconds before trying half-open
    success_threshold: int = 2  # Successes needed to close from half-open
    timeout: float = 30.0  # Operation timeout in seconds
    slow_call_threshold: float = 10.0  # Threshold for slow calls
    slow_call_rate_threshold: float = 0.5  # Rate of slow calls to trip
    minimum_calls: int = 3  # Minimum calls before evaluating
    reset_timeout: float = 300.0  # Time to reset failure count when closed


@dataclass
class CallResult:
    """Result of a circuit breaker protected call."""
    success: bool
    duration: float
    error: Optional[Exception] = None
    timestamp: float = field(default_factory=time.time)


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting external service calls.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.last_success_time = 0.0
        self.state_change_time = time.time()
        
        # Call history for analysis
        self.call_history: deque = deque(maxlen=100)
        
        # Metrics
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "timeouts": 0,
            "circuit_opened": 0,
            "circuit_half_opened": 0,
            "circuit_closed": 0
        }
        
        logger.info(f"🔒 Circuit breaker '{name}' initialized")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenException: When circuit is open
            TimeoutError: When call times out
        """
        self.metrics["total_calls"] += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._move_to_half_open()
            else:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN"
                )
        
        # Execute call with timeout
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            duration = time.time() - start_time
            self._on_success(duration)
            
            return result
            
        except asyncio.TimeoutError as e:
            duration = time.time() - start_time
            self.metrics["timeouts"] += 1
            self._on_failure(e, duration)
            raise TimeoutError(f"Call to '{self.name}' timed out after {self.config.timeout}s")
            
        except Exception as e:
            duration = time.time() - start_time
            self._on_failure(e, duration)
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset to half-open."""
        time_since_open = time.time() - self.state_change_time
        return time_since_open >= self.config.recovery_timeout
    
    def _move_to_half_open(self):
        """Move circuit to half-open state."""
        self.state = CircuitState.HALF_OPEN
        self.state_change_time = time.time()
        self.success_count = 0
        self.metrics["circuit_half_opened"] += 1
        logger.info(f"🔓 Circuit breaker '{self.name}' moved to HALF_OPEN")
    
    def _on_success(self, duration: float):
        """Handle successful call."""
        self.metrics["successful_calls"] += 1
        self.last_success_time = time.time()
        
        call_result = CallResult(success=True, duration=duration)
        self.call_history.append(call_result)
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._move_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _on_failure(self, error: Exception, duration: float):
        """Handle failed call."""
        self.metrics["failed_calls"] += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        call_result = CallResult(success=False, duration=duration, error=error)
        self.call_history.append(call_result)
        
        if self.state == CircuitState.HALF_OPEN:
            self._move_to_open()
        elif self.state == CircuitState.CLOSED:
            if self._should_open_circuit():
                self._move_to_open()
    
    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened based on failure patterns."""
        # Simple failure count threshold
        if self.failure_count >= self.config.failure_threshold:
            return True
        
        # Check for slow call rate if we have enough calls
        recent_calls = [c for c in self.call_history if time.time() - c.timestamp < 60.0]
        if len(recent_calls) >= self.config.minimum_calls:
            slow_calls = [c for c in recent_calls if c.duration > self.config.slow_call_threshold]
            slow_call_rate = len(slow_calls) / len(recent_calls)
            
            if slow_call_rate > self.config.slow_call_rate_threshold:
                logger.warning(f"High slow call rate detected: {slow_call_rate:.2f}")
                return True
        
        return False
    
    def _move_to_open(self):
        """Move circuit to open state."""
        self.state = CircuitState.OPEN
        self.state_change_time = time.time()
        self.metrics["circuit_opened"] += 1
        logger.warning(f"🚫 Circuit breaker '{self.name}' OPENED after {self.failure_count} failures")
    
    def _move_to_closed(self):
        """Move circuit to closed state."""
        self.state = CircuitState.CLOSED
        self.state_change_time = time.time()
        self.failure_count = 0
        self.success_count = 0
        self.metrics["circuit_closed"] += 1
        logger.info(f"✅ Circuit breaker '{self.name}' CLOSED - service recovered")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        recent_calls = [c for c in self.call_history if time.time() - c.timestamp < 60.0]
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "metrics": self.metrics.copy(),
            "recent_calls": len(recent_calls),
            "recent_success_rate": (
                len([c for c in recent_calls if c.success]) / len(recent_calls)
                if recent_calls else 0.0
            ),
            "average_response_time": (
                sum(c.duration for c in recent_calls) / len(recent_calls)
                if recent_calls else 0.0
            ),
            "state_duration": time.time() - self.state_change_time
        }


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class TimeoutPolicy:
    """Configurable timeout policy for different operation types."""
    
    def __init__(self):
        self.timeouts = {
            "llm_call": 30.0,
            "knowledge_retrieval": 10.0,
            "consciousness_assessment": 15.0,
            "vector_search": 5.0,
            "graph_operation": 8.0,
            "reflection": 20.0,
            "learning": 25.0,
            "coordination": 3.0,
            "default": 10.0
        }
        
        # Adaptive timeouts based on historical performance
        self.adaptive_timeouts = {}
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
    
    def get_timeout(self, operation_type: str) -> float:
        """Get timeout for an operation type."""
        # Use adaptive timeout if available and reliable
        if operation_type in self.adaptive_timeouts:
            return self.adaptive_timeouts[operation_type]
        
        return self.timeouts.get(operation_type, self.timeouts["default"])
    
    def record_performance(self, operation_type: str, duration: float, success: bool):
        """Record performance data for adaptive timeout calculation."""
        self.performance_history[operation_type].append({
            "duration": duration,
            "success": success,
            "timestamp": time.time()
        })
        
        # Update adaptive timeout
        self._update_adaptive_timeout(operation_type)
    
    def _update_adaptive_timeout(self, operation_type: str):
        """Update adaptive timeout based on performance history."""
        history = self.performance_history[operation_type]
        
        if len(history) < 10:  # Need enough samples
            return
        
        # Use successful calls for timeout calculation
        successful_calls = [h for h in history if h["success"]]
        
        if not successful_calls:
            return
        
        durations = [h["duration"] for h in successful_calls]
        
        # Calculate 95th percentile with some buffer
        durations.sort()
        p95_index = int(0.95 * len(durations))
        p95_duration = durations[p95_index]
        
        # Add 50% buffer
        adaptive_timeout = p95_duration * 1.5
        
        # Don't go below base timeout or above 2x base timeout
        base_timeout = self.timeouts.get(operation_type, self.timeouts["default"])
        adaptive_timeout = max(base_timeout, min(adaptive_timeout, base_timeout * 2))
        
        self.adaptive_timeouts[operation_type] = adaptive_timeout
        
        logger.info(f"⏱️ Updated adaptive timeout for {operation_type}: {adaptive_timeout:.1f}s")


class CircuitBreakerManager:
    """Manages circuit breakers for different services."""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.timeout_policy = TimeoutPolicy()
        
        # Default circuit breaker configs for different service types
        self.default_configs = {
            "llm": CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=60.0,
                timeout=30.0,
                slow_call_threshold=15.0
            ),
            "knowledge": CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=30.0,
                timeout=10.0,
                slow_call_threshold=5.0
            ),
            "vector": CircuitBreakerConfig(
                failure_threshold=4,
                recovery_timeout=20.0,
                timeout=5.0,
                slow_call_threshold=3.0
            ),
            "default": CircuitBreakerConfig()
        }
    
    def get_circuit_breaker(self, service_name: str, service_type: str = "default") -> CircuitBreaker:
        """Get or create a circuit breaker for a service."""
        if service_name not in self.circuit_breakers:
            config = self.default_configs.get(service_type, self.default_configs["default"])
            self.circuit_breakers[service_name] = CircuitBreaker(service_name, config)
        
        return self.circuit_breakers[service_name]
    
    async def protected_call(self, service_name: str, service_type: str, 
                           operation_type: str, func: Callable, *args, **kwargs) -> Any:
        """Make a protected call with circuit breaker and timeout."""
        circuit_breaker = self.get_circuit_breaker(service_name, service_type)
        
        # Override timeout with adaptive timeout
        adaptive_timeout = self.timeout_policy.get_timeout(operation_type)
        circuit_breaker.config.timeout = adaptive_timeout
        
        start_time = time.time()
        success = False
        
        try:
            result = await circuit_breaker.call(func, *args, **kwargs)
            success = True
            return result
            
        finally:
            duration = time.time() - start_time
            self.timeout_policy.record_performance(operation_type, duration, success)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all circuit breakers."""
        return {
            "circuit_breakers": {
                name: cb.get_metrics() 
                for name, cb in self.circuit_breakers.items()
            },
            "timeout_policy": {
                "base_timeouts": self.timeout_policy.timeouts,
                "adaptive_timeouts": self.timeout_policy.adaptive_timeouts
            }
        }


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()
