"""
Unified Resource Manager Implementation for GodelOS

This module implements the UnifiedResourceManager class, which integrates the
compute allocator, memory manager, attention manager, and priority scheduler
to provide comprehensive resource management for the UnifiedAgentCore.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any

from godelOS.unified_agent_core.resource_manager.interfaces import (
    ResourceRequirements, ResourceAllocation, ResourceUtilization,
    ResourcePriority, AbstractUnifiedResourceManager
)
from godelOS.unified_agent_core.resource_manager.compute_allocator import ComputeResourceAllocator
from godelOS.unified_agent_core.resource_manager.memory_manager import MemoryManager
from godelOS.unified_agent_core.resource_manager.attention_manager import AttentionManager
from godelOS.unified_agent_core.resource_manager.priority_scheduler import PriorityScheduler

logger = logging.getLogger(__name__)


class UnifiedResourceManager(AbstractUnifiedResourceManager):
    """
    UnifiedResourceManager implementation for GodelOS.
    
    The UnifiedResourceManager integrates the compute allocator, memory manager,
    attention manager, and priority scheduler to provide comprehensive resource
    management for the UnifiedAgentCore.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the unified resource manager.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__()
        
        self.config = config or {}
        
        # Initialize components
        self.compute_allocator = ComputeResourceAllocator(self.config.get("compute_allocator"))
        self.memory_manager = MemoryManager(self.config.get("memory_manager"))
        self.attention_manager = AttentionManager(self.config.get("attention_manager"))
        self.priority_scheduler = PriorityScheduler(self.config.get("priority_scheduler"))
        
        # Initialize allocation tracking
        self.allocations: Dict[str, ResourceAllocation] = {}
        
        # Initialize optimization parameters
        self.optimization_interval = self.config.get("optimization_interval", 300)  # 5 minutes
        self.last_optimization = 0
        
        # Initialize lock
        self.lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """
        Initialize the resource manager.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        if self.is_initialized:
            logger.warning("UnifiedResourceManager is already initialized")
            return True
        
        try:
            logger.info("Initializing UnifiedResourceManager")
            
            # Initialize state
            self.is_initialized = True
            logger.info("UnifiedResourceManager initialized successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error initializing UnifiedResourceManager: {e}")
            return False
    
    async def start(self) -> bool:
        """
        Start the resource manager.
        
        Returns:
            True if the manager was started successfully, False otherwise
        """
        if not self.is_initialized:
            success = await self.initialize()
            if not success:
                return False
        
        if self.is_running:
            logger.warning("UnifiedResourceManager is already running")
            return True
        
        try:
            logger.info("Starting UnifiedResourceManager")
            
            # Reset last optimization time
            self.last_optimization = time.time()
            
            # Start state
            self.is_running = True
            logger.info("UnifiedResourceManager started successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error starting UnifiedResourceManager: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop the resource manager.
        
        Returns:
            True if the manager was stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("UnifiedResourceManager is not running")
            return True
        
        try:
            logger.info("Stopping UnifiedResourceManager")
            
            # Release all allocations
            for allocation_id in list(self.allocations.keys()):
                await self.release_resources(self.allocations[allocation_id])
            
            # Update state
            self.is_running = False
            logger.info("UnifiedResourceManager stopped successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error stopping UnifiedResourceManager: {e}")
            return False
    
    async def allocate_resources(self, requirements: ResourceRequirements) -> Optional[ResourceAllocation]:
        """
        Allocate resources based on requirements.
        
        Args:
            requirements: The resource requirements
            
        Returns:
            The resource allocation, or None if resources could not be allocated
        """
        if not self.is_running:
            raise RuntimeError("UnifiedResourceManager is not running")
        
        async with self.lock:
            # Check if optimization is needed
            await self._check_optimization()
            
            logger.debug(f"Allocating resources: compute={requirements.compute}, memory={requirements.memory}, attention={requirements.attention}")
            
            try:
                # Allocate compute resources
                compute_allocation = await self.compute_allocator.allocate(requirements)
                if not compute_allocation:
                    logger.warning("Failed to allocate compute resources")
                    return None
                
                # Allocate memory resources
                memory_allocation = await self.memory_manager.allocate(requirements)
                if not memory_allocation:
                    # Release compute allocation
                    await self.compute_allocator.release(compute_allocation.id)
                    logger.warning("Failed to allocate memory resources")
                    return None
                
                # Allocate attention resources
                attention_allocation = await self.attention_manager.allocate(requirements)
                if not attention_allocation:
                    # Release previous allocations
                    await self.compute_allocator.release(compute_allocation.id)
                    await self.memory_manager.release(memory_allocation.id)
                    logger.warning("Failed to allocate attention resources")
                    return None
                
                # Create unified allocation
                allocation = ResourceAllocation(
                    compute=compute_allocation.compute,
                    memory=memory_allocation.memory,
                    attention=attention_allocation.attention,
                    network=requirements.network,
                    storage=requirements.storage,
                    metadata={
                        "priority": requirements.priority.value,
                        "deadline": requirements.deadline,
                        "compute_allocation_id": compute_allocation.id,
                        "memory_allocation_id": memory_allocation.id,
                        "attention_allocation_id": attention_allocation.id
                    }
                )
                
                # Set expiration time if deadline is specified
                if requirements.deadline:
                    allocation.expires_at = requirements.deadline
                
                # Store allocation
                self.allocations[allocation.id] = allocation
                
                logger.debug(f"Resource allocation successful (ID: {allocation.id})")
                return allocation
            
            except Exception as e:
                logger.error(f"Error allocating resources: {e}")
                return None
    
    async def release_resources(self, allocation: ResourceAllocation) -> bool:
        """
        Release allocated resources.
        
        Args:
            allocation: The resource allocation to release
            
        Returns:
            True if the resources were released, False otherwise
        """
        if not self.is_running:
            raise RuntimeError("UnifiedResourceManager is not running")
        
        async with self.lock:
            logger.debug(f"Releasing resources (ID: {allocation.id})")
            
            try:
                # Get component allocation IDs
                compute_id = allocation.metadata.get("compute_allocation_id")
                memory_id = allocation.metadata.get("memory_allocation_id")
                attention_id = allocation.metadata.get("attention_allocation_id")
                
                # Release compute resources
                if compute_id:
                    await self.compute_allocator.release(compute_id)
                
                # Release memory resources
                if memory_id:
                    await self.memory_manager.release(memory_id)
                
                # Release attention resources
                if attention_id:
                    await self.attention_manager.release(attention_id)
                
                # Remove from allocations
                if allocation.id in self.allocations:
                    del self.allocations[allocation.id]
                
                logger.debug(f"Resources released successfully (ID: {allocation.id})")
                return True
            
            except Exception as e:
                logger.error(f"Error releasing resources: {e}")
                return False
    
    async def allocate_resources_for_interaction(self, interaction: Dict[str, Any]) -> ResourceAllocation:
        """
        Allocate resources for an interaction.
        
        Args:
            interaction: The interaction data
            
        Returns:
            The resource allocation
        """
        if not self.is_running:
            raise RuntimeError("UnifiedResourceManager is not running")
        
        # Determine resource requirements based on interaction type
        interaction_type = interaction.get("type", "general")
        
        # Default requirements
        requirements = ResourceRequirements(
            compute=0.1,
            memory=0.1,
            attention=0.1,
            priority=ResourcePriority.MEDIUM
        )
        
        # Adjust based on interaction type
        if interaction_type == "query":
            requirements.compute = 0.2
            requirements.memory = 0.3
            requirements.attention = 0.4
            requirements.priority = ResourcePriority.HIGH
        
        elif interaction_type == "command":
            requirements.compute = 0.3
            requirements.memory = 0.2
            requirements.attention = 0.3
            requirements.priority = ResourcePriority.HIGH
        
        elif interaction_type == "background":
            requirements.compute = 0.1
            requirements.memory = 0.1
            requirements.attention = 0.1
            requirements.priority = ResourcePriority.BACKGROUND
        
        # Allocate resources
        allocation = await self.allocate_resources(requirements)
        
        if not allocation:
            # Fallback to minimal allocation
            minimal_requirements = ResourceRequirements(
                compute=0.05,
                memory=0.05,
                attention=0.05,
                priority=ResourcePriority.MEDIUM
            )
            
            allocation = await self.allocate_resources(minimal_requirements)
            
            if not allocation:
                # Create a dummy allocation as a last resort
                allocation = ResourceAllocation(
                    compute=0.01,
                    memory=0.01,
                    attention=0.01,
                    metadata={"dummy": True}
                )
                
                logger.warning(f"Using dummy allocation for interaction type {interaction_type}")
        
        # Focus attention on the interaction
        if interaction.get("content"):
            await self.attention_manager.focus_attention(
                f"interaction:{interaction.get('id', 'unknown')}",
                requirements.priority
            )
        
        return allocation
    
    async def allocate_resources_for_thought(self, thought: Dict[str, Any]) -> ResourceAllocation:
        """
        Allocate resources for a thought.
        
        Args:
            thought: The thought data
            
        Returns:
            The resource allocation
        """
        if not self.is_running:
            raise RuntimeError("UnifiedResourceManager is not running")
        
        # Determine resource requirements based on thought type
        thought_type = thought.get("type", "general")
        
        # Default requirements
        requirements = ResourceRequirements(
            compute=0.1,
            memory=0.2,
            attention=0.3,
            priority=ResourcePriority.MEDIUM
        )
        
        # Adjust based on thought type
        if thought_type == "insight":
            requirements.compute = 0.3
            requirements.memory = 0.3
            requirements.attention = 0.4
            requirements.priority = ResourcePriority.HIGH
        
        elif thought_type == "hypothesis":
            requirements.compute = 0.4
            requirements.memory = 0.3
            requirements.attention = 0.3
            requirements.priority = ResourcePriority.HIGH
        
        elif thought_type == "reflection":
            requirements.compute = 0.2
            requirements.memory = 0.4
            requirements.attention = 0.5
            requirements.priority = ResourcePriority.HIGH
        
        # Allocate resources
        allocation = await self.allocate_resources(requirements)
        
        if not allocation:
            # Fallback to minimal allocation
            minimal_requirements = ResourceRequirements(
                compute=0.05,
                memory=0.05,
                attention=0.05,
                priority=ResourcePriority.MEDIUM
            )
            
            allocation = await self.allocate_resources(minimal_requirements)
            
            if not allocation:
                # Create a dummy allocation as a last resort
                allocation = ResourceAllocation(
                    compute=0.01,
                    memory=0.01,
                    attention=0.01,
                    metadata={"dummy": True}
                )
                
                logger.warning(f"Using dummy allocation for thought type {thought_type}")
        
        # Focus attention on the thought
        if thought.get("content"):
            await self.attention_manager.focus_attention(
                f"thought:{thought.get('id', 'unknown')}",
                requirements.priority
            )
        
        return allocation
    
    async def get_resource_utilization(self) -> Dict[str, ResourceUtilization]:
        """
        Get current resource utilization for all resource types.
        
        Returns:
            Dictionary mapping resource types to utilization
        """
        compute_utilization = await self.compute_allocator.get_utilization()
        memory_utilization = await self.memory_manager.get_utilization()
        attention_utilization = await self.attention_manager.get_utilization()
        
        return {
            "compute": compute_utilization,
            "memory": memory_utilization,
            "attention": attention_utilization
        }
    
    async def _check_optimization(self) -> None:
        """Check if optimization is needed and perform it if necessary."""
        current_time = time.time()
        
        if current_time - self.last_optimization >= self.optimization_interval:
            # Perform optimization
            await self._optimize_resources()
            
            # Update last optimization time
            self.last_optimization = current_time
    
    async def _optimize_resources(self) -> Dict[str, Any]:
        """
        Optimize resource allocation.
        
        Returns:
            Dictionary with optimization results
        """
        logger.debug("Optimizing resource allocation")
        
        try:
            # Optimize each component
            compute_result = await self.compute_allocator.optimize()
            memory_result = await self.memory_manager.optimize()
            attention_result = await self.attention_manager.optimize()
            
            # Clean up orphaned allocations
            cleaned_allocations = await self._clean_orphaned_allocations()
            
            return {
                "compute": compute_result,
                "memory": memory_result,
                "attention": attention_result,
                "cleaned_allocations": cleaned_allocations
            }
        
        except Exception as e:
            logger.error(f"Error optimizing resources: {e}")
            return {"error": str(e)}
    
    async def _clean_orphaned_allocations(self) -> int:
        """
        Clean up orphaned allocations.
        
        Returns:
            Number of allocations cleaned up
        """
        # Find allocations that are expired
        current_time = time.time()
        expired_allocations = [
            allocation_id for allocation_id, allocation in self.allocations.items()
            if allocation.expires_at and current_time > allocation.expires_at
        ]
        
        # Release expired allocations
        for allocation_id in expired_allocations:
            if allocation_id in self.allocations:
                await self.release_resources(self.allocations[allocation_id])
        
        return len(expired_allocations)
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report for the resource manager.
        
        Returns:
            Dictionary with performance metrics and statistics
        """
        # Get current resource utilization
        utilization = await self.get_resource_utilization()
        
        # Get resource analytics
        analytics = await self.get_resource_analytics()
        
        # Get scheduler statistics
        scheduler_stats = await self.priority_scheduler.get_scheduler_statistics()
        
        # Calculate average response times
        avg_allocation_time = sum(self.performance_metrics["allocation_time"]) / len(self.performance_metrics["allocation_time"]) if self.performance_metrics["allocation_time"] else 0
        avg_optimization_time = sum(self.performance_metrics["optimization_time"]) / len(self.performance_metrics["optimization_time"]) if self.performance_metrics["optimization_time"] else 0
        
        # Build comprehensive report
        report = {
            "timestamp": time.time(),
            "uptime": time.time() - self.last_optimization if self.is_running else 0,
            "resource_utilization": {
                "compute": utilization["compute"].memory,
                "memory": utilization["memory"].memory,
                "attention": utilization["attention"].memory,
                "overall": (utilization["compute"].memory + utilization["memory"].memory + utilization["attention"].memory) / 3
            },
            "performance_metrics": {
                "avg_allocation_time": avg_allocation_time,
                "avg_optimization_time": avg_optimization_time,
                "resource_efficiency": analytics.get("resource_efficiency", 1.0),
                "allocation_success_rate": analytics.get("allocation_success_rate", 1.0)
            },
            "resource_analytics": analytics,
            "scheduler_statistics": scheduler_stats,
            "active_allocations": len(self.allocations),
            "allocation_strategies": {
                "default_strategy": self.default_strategy,
                "enabled_strategies": [name for name, strategy in self.strategies.items() if strategy.enabled]
            }
        }
        
        return report
    
    async def allocate_resources_with_strategy(self, requirements: ResourceRequirements, strategy_name: str) -> Optional[ResourceAllocation]:
        """
        Allocate resources using a specific allocation strategy.
        
        Args:
            requirements: The resource requirements
            strategy_name: The name of the strategy to use
            
        Returns:
            The resource allocation, or None if resources could not be allocated
        """
        if strategy_name not in self.strategies:
            logger.warning(f"Strategy '{strategy_name}' not found, using default strategy")
            strategy_name = self.default_strategy
        
        return await self.allocate_resources(requirements, strategy_name)
    
    async def suggest_optimal_requirements(self, initial_requirements: ResourceRequirements) -> ResourceRequirements:
        """
        Suggest optimal resource requirements based on system state and historical patterns.
        
        Args:
            initial_requirements: The initial resource requirements
            
        Returns:
            Optimized resource requirements
        """
        # Get current utilization
        utilization = await self.get_resource_utilization()
        
        # Create a copy of the initial requirements
        optimized = ResourceRequirements(
            compute=initial_requirements.compute,
            memory=initial_requirements.memory,
            attention=initial_requirements.attention,
            network=initial_requirements.network,
            storage=initial_requirements.storage,
            priority=initial_requirements.priority,
            deadline=initial_requirements.deadline,
            metadata=initial_requirements.metadata.copy() if initial_requirements.metadata else {}
        )
        
        # Check resource availability and adjust requirements
        compute_available = 1.0 - utilization["compute"].memory
        memory_available = 1.0 - utilization["memory"].memory
        attention_available = 1.0 - utilization["attention"].memory
        
        # Adjust based on availability (don't request more than available)
        if optimized.compute > compute_available * 0.9:
            optimized.compute = compute_available * 0.9
        
        if optimized.memory > memory_available * 0.9:
            optimized.memory = memory_available * 0.9
        
        if optimized.attention > attention_available * 0.9:
            optimized.attention = attention_available * 0.9
        
        # Adjust based on historical efficiency
        if self.resource_analytics.get("historical_trends"):
            trends = self.resource_analytics["historical_trends"]
            
            # If compute usage is trending down, reduce compute request
            if trends.get("compute", 0) < -0.1:
                optimized.compute *= 0.9
            
            # If memory usage is trending up, increase memory request
            if trends.get("memory", 0) > 0.1:
                optimized.memory *= 1.1
                if optimized.memory > memory_available * 0.9:
                    optimized.memory = memory_available * 0.9
        
        # Add metadata about optimization
        optimized.metadata["optimized"] = True
        optimized.metadata["original_requirements"] = {
            "compute": initial_requirements.compute,
            "memory": initial_requirements.memory,
            "attention": initial_requirements.attention
        }
        
        return optimized