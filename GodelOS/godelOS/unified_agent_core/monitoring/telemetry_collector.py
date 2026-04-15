"""
TelemetryCollector Implementation for GodelOS

This module implements the TelemetryCollector class, which provides telemetry
collection capabilities for the UnifiedAgentCore.
"""

import logging
import time
import asyncio
import os
import json
from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from collections import deque

from godelOS.unified_agent_core.monitoring.interfaces import (
    TelemetryCollectorInterface, TelemetryData
)

logger = logging.getLogger(__name__)


class TelemetryCollector(TelemetryCollectorInterface):
    """
    Telemetry collector implementation.
    
    Collects telemetry data from system components and provides access to
    collected data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the telemetry collector.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize state
        self.is_running = False
        self.collection_task = None
        
        # Collection configuration
        self.collection_interval = self.config.get("collection_interval", 60.0)  # seconds
        self.max_data_points = self.config.get("max_data_points", 10000)
        self.max_data_age = self.config.get("max_data_age", 86400)  # 1 day
        
        # Telemetry data
        self.telemetry_data: List[TelemetryData] = []
        
        # Collectors registry
        self.collectors: Dict[str, Dict[str, Callable]] = {}
        
        # Telemetry storage configuration
        self.storage_enabled = self.config.get("storage_enabled", False)
        self.storage_dir = self.config.get("storage_dir", "telemetry")
        self.storage_file = self.config.get("storage_file", "telemetry.json")
        self.max_storage_size = self.config.get("max_storage_size", 100 * 1024 * 1024)  # 100 MB
        self.max_storage_files = self.config.get("max_storage_files", 10)
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    async def start(self) -> bool:
        """
        Start the telemetry collector.
        
        Returns:
            True if the collector was started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("TelemetryCollector is already running")
            return True
        
        try:
            logger.info("Starting TelemetryCollector")
            
            # Create storage directory if needed
            if self.storage_enabled:
                os.makedirs(self.storage_dir, exist_ok=True)
            
            self.is_running = True
            self.collection_task = asyncio.create_task(self._collection_loop())
            
            logger.info("TelemetryCollector started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error starting TelemetryCollector: {e}")
            self.is_running = False
            return False
    
    async def stop(self) -> bool:
        """
        Stop the telemetry collector.
        
        Returns:
            True if the collector was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("TelemetryCollector is not running")
            return True
        
        try:
            logger.info("Stopping TelemetryCollector")
            
            self.is_running = False
            if self.collection_task:
                self.collection_task.cancel()
                try:
                    await self.collection_task
                except asyncio.CancelledError:
                    pass
                self.collection_task = None
            
            logger.info("TelemetryCollector stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping TelemetryCollector: {e}")
            return False
    
    async def collect(self, telemetry: TelemetryData) -> bool:
        """
        Collect telemetry data.
        
        Args:
            telemetry: The telemetry data to collect
            
        Returns:
            True if the data was collected successfully, False otherwise
        """
        async with self.lock:
            try:
                # Add telemetry data
                self.telemetry_data.append(telemetry)
                
                # Prune old data if needed
                await self._prune_data()
                
                # Store telemetry data if enabled
                if self.storage_enabled:
                    await self._store_telemetry(telemetry)
                
                return True
            
            except Exception as e:
                logger.error(f"Error collecting telemetry data: {e}")
                return False
    
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
        async with self.lock:
            try:
                # Filter telemetry data
                filtered_data = self.telemetry_data.copy()
                
                # Apply filters
                if source is not None:
                    filtered_data = [data for data in filtered_data if data.source == source]
                
                if data_type is not None:
                    filtered_data = [data for data in filtered_data if data.data_type == data_type]
                
                if start_time is not None:
                    filtered_data = [data for data in filtered_data if data.timestamp >= start_time]
                
                if end_time is not None:
                    filtered_data = [data for data in filtered_data if data.timestamp <= end_time]
                
                # Sort by timestamp (newest first)
                filtered_data.sort(key=lambda x: x.timestamp, reverse=True)
                
                # Apply limit
                filtered_data = filtered_data[:limit]
                
                return filtered_data
            
            except Exception as e:
                logger.error(f"Error getting telemetry data: {e}")
                return []
    
    async def register_collector(self, source: str, data_type: str, callback: Callable) -> bool:
        """
        Register a telemetry collector.
        
        Args:
            source: The source of the telemetry
            data_type: The type of data to collect
            callback: A callback function that returns the telemetry data
            
        Returns:
            True if the collector was registered successfully, False otherwise
        """
        async with self.lock:
            try:
                # Create source dictionary if it doesn't exist
                if source not in self.collectors:
                    self.collectors[source] = {}
                
                # Register collector
                self.collectors[source][data_type] = callback
                
                logger.info(f"Registered telemetry collector: {source}.{data_type}")
                return True
            
            except Exception as e:
                logger.error(f"Error registering telemetry collector {source}.{data_type}: {e}")
                return False
    
    async def unregister_collector(self, source: str, data_type: str) -> bool:
        """
        Unregister a telemetry collector.
        
        Args:
            source: The source of the telemetry
            data_type: The type of data to collect
            
        Returns:
            True if the collector was unregistered successfully, False otherwise
        """
        async with self.lock:
            try:
                # Check if collector exists
                if source not in self.collectors or data_type not in self.collectors[source]:
                    logger.warning(f"Telemetry collector not found: {source}.{data_type}")
                    return False
                
                # Unregister collector
                del self.collectors[source][data_type]
                
                # Remove source dictionary if empty
                if not self.collectors[source]:
                    del self.collectors[source]
                
                logger.info(f"Unregistered telemetry collector: {source}.{data_type}")
                return True
            
            except Exception as e:
                logger.error(f"Error unregistering telemetry collector {source}.{data_type}: {e}")
                return False
    
    async def _collection_loop(self) -> None:
        """Background task for collecting telemetry data."""
        try:
            while self.is_running:
                await self._collect_from_registered_collectors()
                await asyncio.sleep(self.collection_interval)
        
        except asyncio.CancelledError:
            logger.info("Telemetry collection loop cancelled")
            raise
        
        except Exception as e:
            logger.error(f"Error in telemetry collection loop: {e}")
            if self.is_running:
                # Restart the collection loop
                self.collection_task = asyncio.create_task(self._collection_loop())
    
    async def _collect_from_registered_collectors(self) -> None:
        """Collect telemetry data from registered collectors."""
        async with self.lock:
            try:
                for source, collectors in self.collectors.items():
                    for data_type, collector in collectors.items():
                        try:
                            # Call collector function
                            data = await collector()
                            
                            # Create telemetry data
                            if isinstance(data, TelemetryData):
                                telemetry = data
                            elif isinstance(data, dict):
                                telemetry = TelemetryData(
                                    source=source,
                                    data_type=data_type,
                                    data=data
                                )
                            else:
                                logger.warning(f"Invalid telemetry data from {source}.{data_type}: {data}")
                                continue
                            
                            # Collect telemetry data
                            await self.collect(telemetry)
                        
                        except Exception as e:
                            logger.error(f"Error collecting telemetry from {source}.{data_type}: {e}")
            
            except Exception as e:
                logger.error(f"Error collecting telemetry from registered collectors: {e}")
    
    async def _prune_data(self) -> None:
        """Prune old telemetry data."""
        try:
            # Check if pruning is needed
            if len(self.telemetry_data) <= self.max_data_points:
                return
            
            # Calculate cutoff time
            current_time = time.time()
            cutoff_time = current_time - self.max_data_age
            
            # Remove old data
            self.telemetry_data = [
                data for data in self.telemetry_data
                if data.timestamp >= cutoff_time
            ]
            
            # If still too many data points, remove oldest
            if len(self.telemetry_data) > self.max_data_points:
                # Sort by timestamp (oldest first)
                self.telemetry_data.sort(key=lambda x: x.timestamp)
                
                # Keep only the newest max_data_points
                self.telemetry_data = self.telemetry_data[-self.max_data_points:]
        
        except Exception as e:
            logger.error(f"Error pruning telemetry data: {e}")
    
    async def _store_telemetry(self, telemetry: TelemetryData) -> None:
        """Store telemetry data."""
        if not self.storage_enabled:
            return
        
        try:
            # Convert telemetry data to dictionary
            telemetry_dict = {
                "source": telemetry.source,
                "data_type": telemetry.data_type,
                "data": telemetry.data,
                "timestamp": telemetry.timestamp,
                "metadata": telemetry.metadata
            }
            
            # Get storage file path
            storage_path = os.path.join(self.storage_dir, self.storage_file)
            
            # Check if storage file exists and is too large
            if os.path.exists(storage_path) and os.path.getsize(storage_path) >= self.max_storage_size:
                await self._rotate_storage_files()
            
            # Append to storage file
            with open(storage_path, "a") as f:
                f.write(json.dumps(telemetry_dict) + "\n")
        
        except Exception as e:
            logger.error(f"Error storing telemetry data: {e}")
    
    async def _rotate_storage_files(self) -> None:
        """Rotate storage files."""
        try:
            # Get storage file path
            storage_path = os.path.join(self.storage_dir, self.storage_file)
            
            # Shift existing rotated files
            for i in range(self.max_storage_files - 1, 0, -1):
                old_path = f"{storage_path}.{i}"
                new_path = f"{storage_path}.{i + 1}"
                
                if os.path.exists(old_path):
                    if i + 1 >= self.max_storage_files:
                        os.remove(old_path)
                    else:
                        os.rename(old_path, new_path)
            
            # Rotate current storage file
            if os.path.exists(storage_path):
                os.rename(storage_path, f"{storage_path}.1")
        
        except Exception as e:
            logger.error(f"Error rotating storage files: {e}")