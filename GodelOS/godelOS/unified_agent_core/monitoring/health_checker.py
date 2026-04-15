"""
HealthChecker Implementation for GodelOS

This module implements the HealthChecker class, which provides health checking
capabilities for the UnifiedAgentCore.
"""

import logging
import time
import asyncio
import psutil
import os
from typing import Dict, List, Optional, Any, Callable, Tuple
from collections import deque

from godelOS.unified_agent_core.monitoring.interfaces import (
    HealthCheckerInterface, SystemHealth, SystemHealthStatus
)

logger = logging.getLogger(__name__)


class HealthChecker(HealthCheckerInterface):
    """
    Health checker implementation.
    
    Checks the health of system components and provides an overall health status.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the health checker.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize state
        self.is_running = False
        self.checking_task = None
        
        # Checking configuration
        self.check_interval = self.config.get("check_interval", 60.0)  # seconds
        self.history_size = self.config.get("history_size", 100)
        
        # Health check callbacks
        self.health_checks: Dict[str, Callable] = {}
        
        # Health history
        self.health_history = []  # For test compatibility
        
        # Internal health history tracking
        self._health_history_internal: Dict[str, deque] = {
            "system": deque(maxlen=self.history_size)
        }
        
        # Thresholds
        self.cpu_threshold = self.config.get("cpu_threshold", 90.0)  # percent
        self.memory_threshold = self.config.get("memory_threshold", 90.0)  # percent
        self.disk_threshold = self.config.get("disk_threshold", 90.0)  # percent
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    async def start(self) -> bool:
        """
        Start the health checker.
        
        Returns:
            True if the checker was started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("HealthChecker is already running")
            return True
        
        try:
            logger.info("Starting HealthChecker")
            
            self.is_running = True
            self.checking_task = asyncio.create_task(self._checking_loop())
            
            logger.info("HealthChecker started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error starting HealthChecker: {e}")
            self.is_running = False
            return False
    
    async def stop(self) -> bool:
        """
        Stop the health checker.
        
        Returns:
            True if the checker was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("HealthChecker is not running")
            return True
        
        try:
            logger.info("Stopping HealthChecker")
            
            self.is_running = False
            if self.checking_task:
                self.checking_task.cancel()
                try:
                    await self.checking_task
                except asyncio.CancelledError:
                    pass
                self.checking_task = None
            
            logger.info("HealthChecker stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping HealthChecker: {e}")
            return False
    
    async def check(self) -> SystemHealth:
        """
        Check the health of the system.
        
        Returns:
            The system health
        """
        async with self.lock:
            try:
                # Check system resources
                cpu_status = await self._check_cpu()
                memory_status = await self._check_memory()
                disk_status = await self._check_disk()
                
                # Check registered components
                component_statuses = {}
                for component, check_func in self.health_checks.items():
                    try:
                        status = await check_func()
                        # Convert string value to enum if necessary
                        if isinstance(status, str):
                            try:
                                status = SystemHealthStatus(status)
                            except ValueError:
                                logger.warning(f"Invalid health status value: {status}")
                                status = SystemHealthStatus.UNKNOWN
                        component_statuses[component] = status
                    except Exception as e:
                        logger.error(f"Error checking health of component {component}: {e}")
                        component_statuses[component] = SystemHealthStatus.UNKNOWN
                
                # Determine overall status
                system_status = self._determine_overall_status(
                    cpu_status, memory_status, disk_status, component_statuses
                )
                
                # Create health details
                details = {
                    "cpu": {
                        "status": cpu_status.name,
                        "usage": psutil.cpu_percent()
                    },
                    "memory": {
                        "status": memory_status.name,
                        "usage": psutil.virtual_memory().percent
                    },
                    "disk": {
                        "status": disk_status.name,
                        "usage": psutil.disk_usage('/').percent
                    }
                }
                
                # Create system health
                health = SystemHealth(
                    status=system_status,
                    components={**component_statuses},
                    details=details
                )
                
                # Update health history
                self._health_history_internal["system"].append((time.time(), system_status))
                
                return health
            
            except Exception as e:
                logger.error(f"Error checking system health: {e}")
                return SystemHealth(
                    status=SystemHealthStatus.UNKNOWN,
                    message=f"Error checking system health: {str(e)}"
                )
    
    async def register_health_check(self, component: str, callback: Callable) -> bool:
        """
        Register a health check.
        
        Args:
            component: The name of the component
            callback: A callback function that returns the component health status
            
        Returns:
            True if the health check was registered successfully, False otherwise
        """
        async with self.lock:
            try:
                self.health_checks[component] = callback
                self._health_history_internal[component] = deque(maxlen=self.history_size)
                logger.info(f"Registered health check for component: {component}")
                return True
            
            except Exception as e:
                logger.error(f"Error registering health check for component {component}: {e}")
                return False
    
    async def unregister_health_check(self, component: str) -> bool:
        """
        Unregister a health check.
        
        Args:
            component: The name of the component
            
        Returns:
            True if the health check was unregistered successfully, False otherwise
        """
        async with self.lock:
            try:
                if component in self.health_checks:
                    del self.health_checks[component]
                    del self._health_history_internal[component]
                    logger.info(f"Unregistered health check for component: {component}")
                    return True
                else:
                    logger.warning(f"Health check not found for component: {component}")
                    return False
            
            except Exception as e:
                logger.error(f"Error unregistering health check for component {component}: {e}")
                return False
    
    async def _checking_loop(self) -> None:
        """Background task for checking system health."""
        try:
            while self.is_running:
                await self.check()
                await asyncio.sleep(self.check_interval)
        
        except asyncio.CancelledError:
            logger.info("Health checking loop cancelled")
            raise
        
        except Exception as e:
            logger.error(f"Error in health checking loop: {e}")
            if self.is_running:
                # Restart the checking loop
                self.checking_task = asyncio.create_task(self._checking_loop())
    
    async def _check_cpu(self) -> SystemHealthStatus:
        """Check CPU health."""
        try:
            cpu_percent = psutil.cpu_percent()
            
            if cpu_percent >= self.cpu_threshold:
                return SystemHealthStatus.CRITICAL
            elif cpu_percent >= self.cpu_threshold * 0.8:
                return SystemHealthStatus.UNHEALTHY
            elif cpu_percent >= self.cpu_threshold * 0.6:
                return SystemHealthStatus.DEGRADED
            else:
                return SystemHealthStatus.HEALTHY
        
        except Exception as e:
            logger.error(f"Error checking CPU health: {e}")
            return SystemHealthStatus.UNKNOWN
    
    async def _check_memory(self) -> SystemHealthStatus:
        """Check memory health."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent >= self.memory_threshold:
                return SystemHealthStatus.CRITICAL
            elif memory_percent >= self.memory_threshold * 0.8:
                return SystemHealthStatus.UNHEALTHY
            elif memory_percent >= self.memory_threshold * 0.6:
                return SystemHealthStatus.DEGRADED
            else:
                return SystemHealthStatus.HEALTHY
        
        except Exception as e:
            logger.error(f"Error checking memory health: {e}")
            return SystemHealthStatus.UNKNOWN
    
    async def _check_disk(self) -> SystemHealthStatus:
        """Check disk health."""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            if disk_percent >= self.disk_threshold:
                return SystemHealthStatus.CRITICAL
            elif disk_percent >= self.disk_threshold * 0.8:
                return SystemHealthStatus.UNHEALTHY
            elif disk_percent >= self.disk_threshold * 0.6:
                return SystemHealthStatus.DEGRADED
            else:
                return SystemHealthStatus.HEALTHY
        
        except Exception as e:
            logger.error(f"Error checking disk health: {e}")
            return SystemHealthStatus.UNKNOWN
    
    def _determine_overall_status(self, cpu_status: SystemHealthStatus,
                                memory_status: SystemHealthStatus,
                                disk_status: SystemHealthStatus,
                                component_statuses: Dict[str, SystemHealthStatus]) -> SystemHealthStatus:
        """Determine overall system health status."""
        # If there are no health checks and no components, return UNKNOWN
        if not self.health_checks and not component_statuses:
            return SystemHealthStatus.UNKNOWN
            
        # If any component is CRITICAL, the system is CRITICAL
        if (cpu_status == SystemHealthStatus.CRITICAL or
                memory_status == SystemHealthStatus.CRITICAL or
                disk_status == SystemHealthStatus.CRITICAL or
                SystemHealthStatus.CRITICAL in component_statuses.values()):
            return SystemHealthStatus.CRITICAL
        
        # If any component is UNHEALTHY, the system is UNHEALTHY
        if (cpu_status == SystemHealthStatus.UNHEALTHY or
                memory_status == SystemHealthStatus.UNHEALTHY or
                disk_status == SystemHealthStatus.UNHEALTHY or
                SystemHealthStatus.UNHEALTHY in component_statuses.values()):
            return SystemHealthStatus.UNHEALTHY
        
        # If any component is DEGRADED, the system is DEGRADED
        if (cpu_status == SystemHealthStatus.DEGRADED or
                memory_status == SystemHealthStatus.DEGRADED or
                disk_status == SystemHealthStatus.DEGRADED or
                SystemHealthStatus.DEGRADED in component_statuses.values()):
            return SystemHealthStatus.DEGRADED
        
        # If any component is UNKNOWN, the system is DEGRADED
        if (cpu_status == SystemHealthStatus.UNKNOWN or
                memory_status == SystemHealthStatus.UNKNOWN or
                disk_status == SystemHealthStatus.UNKNOWN or
                SystemHealthStatus.UNKNOWN in component_statuses.values()):
            return SystemHealthStatus.DEGRADED
        
        # Otherwise, the system is HEALTHY
        return SystemHealthStatus.HEALTHY