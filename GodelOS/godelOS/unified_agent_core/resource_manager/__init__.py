"""
GodelOS Unified Resource Manager Package

This package implements the UnifiedResourceManager component of the UnifiedAgentCore
architecture, which is responsible for managing system resources such as compute,
memory, and attention.

Key components:
- ComputeResourceAllocator: Manages computational resources
- MemoryManager: Manages memory resources
- AttentionManager: Manages attention resources
- PriorityScheduler: Schedules tasks based on priority
"""

from godelOS.unified_agent_core.resource_manager.interfaces import (
    UnifiedResourceManagerInterface,
    ResourceAllocatorInterface,
    ComputeResourceAllocatorInterface,
    MemoryManagerInterface,
    AttentionManagerInterface,
    PrioritySchedulerInterface,
    ResourceType,
    ResourcePriority,
    ResourceRequirements,
    ResourceAllocation,
    ResourceUtilization
)