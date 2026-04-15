"""
Unified Resource Manager Interfaces for GodelOS

This module defines the interfaces for the UnifiedResourceManager component of the
UnifiedAgentCore architecture, which is responsible for managing system resources
such as compute, memory, and attention.
"""

import abc
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable
from dataclasses import dataclass, field
import time
import uuid
from enum import Enum


class ResourceType(Enum):
    """Enum representing different types of resources."""
    COMPUTE = "compute"
    MEMORY = "memory"
    ATTENTION = "attention"
    NETWORK = "network"
    STORAGE = "storage"


class ResourcePriority(Enum):
    """Enum representing resource allocation priorities."""
    CRITICAL = "critical"  # Highest priority, must be allocated
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"  # Lowest priority, allocated only if available


@dataclass
class ResourceRequirements:
    """Class representing resource requirements for a task."""
    compute: float = 0.1  # 0.0 to 1.0
    memory: float = 0.1  # 0.0 to 1.0
    attention: float = 0.1  # 0.0 to 1.0
    network: float = 0.0  # 0.0 to 1.0
    storage: float = 0.0  # 0.0 to 1.0
    priority: ResourcePriority = ResourcePriority.MEDIUM
    deadline: Optional[float] = None  # Deadline in seconds since epoch
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceAllocation:
    """Class representing allocated resources for a task."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    compute: float = 0.0  # 0.0 to 1.0
    memory: float = 0.0  # 0.0 to 1.0
    attention: float = 0.0  # 0.0 to 1.0
    network: float = 0.0  # 0.0 to 1.0
    storage: float = 0.0  # 0.0 to 1.0
    allocated_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceUtilization:
    """Class representing resource utilization in the system."""
    compute: float = 0.0  # 0.0 to 1.0
    memory: float = 0.0  # 0.0 to 1.0
    attention: float = 0.0  # 0.0 to 1.0
    network: float = 0.0  # 0.0 to 1.0
    storage: float = 0.0  # 0.0 to 1.0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ResourceAllocatorInterface(Protocol):
    """Protocol for resource allocation operations."""
    
    async def allocate(self, requirements: ResourceRequirements) -> Optional[ResourceAllocation]:
        """
        Allocate resources based on requirements.
        
        Args:
            requirements: The resource requirements
            
        Returns:
            The resource allocation, or None if resources could not be allocated
        """
        ...
    
    async def release(self, allocation_id: str) -> bool:
        """
        Release allocated resources.
        
        Args:
            allocation_id: The ID of the resource allocation to release
            
        Returns:
            True if the resources were released, False otherwise
        """
        ...
    
    async def update_allocation(self, allocation_id: str, requirements: ResourceRequirements) -> Optional[ResourceAllocation]:
        """
        Update an existing resource allocation.
        
        Args:
            allocation_id: The ID of the resource allocation to update
            requirements: The new resource requirements
            
        Returns:
            The updated resource allocation, or None if the update failed
        """
        ...
    
    async def get_utilization(self) -> ResourceUtilization:
        """
        Get current resource utilization.
        
        Returns:
            The current resource utilization
        """
        ...


@runtime_checkable
class ComputeResourceAllocatorInterface(ResourceAllocatorInterface, Protocol):
    """Protocol for compute resource allocation operations."""
    
    async def allocate_compute_intensive_task(self, task_id: str, compute_units: float) -> bool:
        """
        Allocate resources for a compute-intensive task.
        
        Args:
            task_id: The ID of the task
            compute_units: The number of compute units required
            
        Returns:
            True if resources were allocated, False otherwise
        """
        ...
    
    async def optimize(self) -> Dict[str, Any]:
        """
        Optimize compute resource allocation.
        
        Returns:
            Dictionary with optimization results
        """
        ...


@runtime_checkable
class MemoryManagerInterface(ResourceAllocatorInterface, Protocol):
    """Protocol for memory management operations."""
    
    async def allocate_memory_block(self, size: int, purpose: str) -> Optional[str]:
        """
        Allocate a block of memory.
        
        Args:
            size: The size of the memory block in bytes
            purpose: The purpose of the memory block
            
        Returns:
            The ID of the allocated memory block, or None if allocation failed
        """
        ...
    
    async def release_memory_block(self, block_id: str) -> bool:
        """
        Release a block of memory.
        
        Args:
            block_id: The ID of the memory block to release
            
        Returns:
            True if the memory block was released, False otherwise
        """
        ...
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Returns:
            Dictionary with memory usage statistics
        """
        ...
    
    async def optimize(self) -> Dict[str, Any]:
        """
        Optimize memory usage.
        
        Returns:
            Dictionary with optimization results
        """
        ...


@runtime_checkable
class AttentionManagerInterface(ResourceAllocatorInterface, Protocol):
    """Protocol for attention management operations."""
    
    async def focus_attention(self, focus_target: str, priority: ResourcePriority) -> bool:
        """
        Focus attention on a target.
        
        Args:
            focus_target: The target to focus on
            priority: The priority of the focus
            
        Returns:
            True if attention was focused, False otherwise
        """
        ...
    
    async def get_current_focus(self) -> Dict[str, float]:
        """
        Get the current attention focus.
        
        Returns:
            Dictionary mapping focus targets to attention values
        """
        ...
    
    async def optimize(self) -> Dict[str, Any]:
        """
        Optimize attention allocation.
        
        Returns:
            Dictionary with optimization results
        """
        ...


@runtime_checkable
class PrioritySchedulerInterface(Protocol):
    """Protocol for priority scheduling operations."""
    
    async def schedule(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Schedule tasks based on priority.
        
        Args:
            tasks: List of tasks to schedule
            
        Returns:
            List of scheduled tasks with resource allocations
        """
        ...
    
    async def preempt(self, high_priority_task: Dict[str, Any]) -> bool:
        """
        Preempt lower priority tasks for a high priority task.
        
        Args:
            high_priority_task: The high priority task
            
        Returns:
            True if preemption was successful, False otherwise
        """
        ...
    
    async def get_schedule(self) -> List[Dict[str, Any]]:
        """
        Get the current task schedule.
        
        Returns:
            List of scheduled tasks
        """
        ...


class UnifiedResourceManagerInterface(abc.ABC):
    """Abstract base class for unified resource manager implementations."""
    
    @abc.abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the resource manager.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def start(self) -> bool:
        """
        Start the resource manager.
        
        Returns:
            True if the manager was started successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def stop(self) -> bool:
        """
        Stop the resource manager.
        
        Returns:
            True if the manager was stopped successfully, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def allocate_resources(self, requirements: ResourceRequirements) -> Optional[ResourceAllocation]:
        """
        Allocate resources based on requirements.
        
        Args:
            requirements: The resource requirements
            
        Returns:
            The resource allocation, or None if resources could not be allocated
        """
        pass
    
    @abc.abstractmethod
    async def release_resources(self, allocation: ResourceAllocation) -> bool:
        """
        Release allocated resources.
        
        Args:
            allocation: The resource allocation to release
            
        Returns:
            True if the resources were released, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def allocate_resources_for_interaction(self, interaction: Dict[str, Any]) -> ResourceAllocation:
        """
        Allocate resources for an interaction.
        
        Args:
            interaction: The interaction data
            
        Returns:
            The resource allocation
        """
        pass
    
    @abc.abstractmethod
    async def allocate_resources_for_thought(self, thought: Dict[str, Any]) -> ResourceAllocation:
        """
        Allocate resources for a thought.
        
        Args:
            thought: The thought data
            
        Returns:
            The resource allocation
        """
        pass
    
    @abc.abstractmethod
    def set_state(self, state: Any) -> None:
        """
        Set the unified state reference.
        
        Args:
            state: The unified state
        """
        pass
    
    @abc.abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the resource manager.
        
        Returns:
            Dictionary with status information
        """
        pass


class AbstractUnifiedResourceManager(UnifiedResourceManagerInterface):
    """
    Abstract implementation of the UnifiedResourceManagerInterface.
    
    This class provides a base implementation of the UnifiedResourceManagerInterface
    with common functionality that concrete implementations can build upon.
    """
    
    def __init__(self):
        """Initialize the abstract unified resource manager."""
        self.compute_allocator = None
        self.memory_manager = None
        self.attention_manager = None
        self.priority_scheduler = None
        self.state = None
        self.is_initialized = False
        self.is_running = False
    
    def set_state(self, state: Any) -> None:
        """
        Set the unified state reference.
        
        Args:
            state: The unified state
        """
        self.state = state
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the resource manager.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_initialized": self.is_initialized,
            "is_running": self.is_running,
            "components": {
                "compute_allocator": bool(self.compute_allocator),
                "memory_manager": bool(self.memory_manager),
                "attention_manager": bool(self.attention_manager),
                "priority_scheduler": bool(self.priority_scheduler)
            }
        }