"""
Memory Manager Implementation for GodelOS

This module implements the MemoryManager class, which is responsible for
allocating and managing memory resources for the UnifiedAgentCore.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any

from godelOS.unified_agent_core.resource_manager.interfaces import (
    ResourceRequirements, ResourceAllocation, ResourceUtilization,
    ResourcePriority, MemoryManagerInterface
)

logger = logging.getLogger(__name__)


class MemoryTier:
    """Class representing a memory tier with specific characteristics."""
    
    def __init__(self, name: str, capacity: int, access_speed: float, cost_factor: float):
        """
        Initialize a memory tier.
        
        Args:
            name: The name of the tier (e.g., "fast", "standard", "slow")
            capacity: The capacity of the tier in bytes
            access_speed: Relative access speed (higher is faster)
            cost_factor: Relative cost factor (higher is more expensive)
        """
        self.name = name
        self.capacity = capacity
        self.access_speed = access_speed
        self.cost_factor = cost_factor
        self.used_capacity = 0
        self.blocks: Dict[str, "MemoryBlock"] = {}
    
    @property
    def available_capacity(self) -> int:
        """Get the available capacity in this tier."""
        return self.capacity - self.used_capacity
    
    @property
    def utilization(self) -> float:
        """Get the utilization of this tier (0.0 to 1.0)."""
        return self.used_capacity / self.capacity if self.capacity > 0 else 1.0


class MemoryBlock:
    """Class representing a block of memory."""
    
    def __init__(self, id: str, size: int, purpose: str, tier_name: str = "standard"):
        """
        Initialize a memory block.
        
        Args:
            id: The ID of the memory block
            size: The size of the memory block in bytes
            purpose: The purpose of the memory block
            tier_name: The name of the memory tier this block belongs to
        """
        self.id = id
        self.size = size
        self.purpose = purpose
        self.tier_name = tier_name
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
        self.fragmented = False
        self.cached = False
        self.cache_priority = 0
        self.access_pattern = []  # Store recent access timestamps
        self.max_access_history = 20
    
    def access(self) -> None:
        """Record an access to this memory block."""
        current_time = time.time()
        self.last_accessed = current_time
        self.access_count += 1
        
        # Record access pattern
        self.access_pattern.append(current_time)
        if len(self.access_pattern) > self.max_access_history:
            self.access_pattern = self.access_pattern[-self.max_access_history:]
        
        # Update cache priority based on access frequency and recency
        time_factor = 1.0 / (1.0 + (current_time - self.created_at) / 3600)  # Newer blocks get higher priority
        frequency_factor = min(1.0, self.access_count / 100)  # More frequently accessed blocks get higher priority
        recency_factor = 1.0  # Recently accessed blocks get higher priority
        
        self.cache_priority = (0.2 * time_factor + 0.5 * frequency_factor + 0.3 * recency_factor)
    
    def get_access_frequency(self, time_window: float = 3600) -> float:
        """
        Calculate access frequency within a time window.
        
        Args:
            time_window: Time window in seconds
            
        Returns:
            Access frequency (accesses per second)
        """
        current_time = time.time()
        recent_accesses = [t for t in self.access_pattern if current_time - t <= time_window]
        
        if not recent_accesses:
            return 0.0
            
        return len(recent_accesses) / min(time_window, current_time - self.created_at)


class MemoryManager(MemoryManagerInterface):
    """
    MemoryManager implementation for GodelOS.
    
    The MemoryManager is responsible for allocating and managing memory resources
    for the UnifiedAgentCore.
    
    Features:
    - Memory pool management with different tiers
    - Garbage collection and memory reclamation
    - Memory defragmentation
    - Cache optimization for frequently accessed data
    - Memory usage prediction and proactive allocation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the memory manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize resource tracking
        self.total_memory = self.config.get("total_memory", 1024 * 1024 * 1024)  # 1 GB default
        self.allocated_memory = 0
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.memory_blocks: Dict[str, MemoryBlock] = {}
        
        # Initialize memory tiers
        self.memory_tiers: Dict[str, MemoryTier] = self._initialize_memory_tiers()
        
        # Initialize memory pools
        self.memory_pools: Dict[str, int] = {
            "working_memory": int(self.total_memory * 0.4),  # 40% for working memory
            "long_term_memory": int(self.total_memory * 0.3),  # 30% for long-term memory
            "system": int(self.total_memory * 0.2),  # 20% for system
            "reserve": int(self.total_memory * 0.1)   # 10% reserve
        }
        self.pool_usage: Dict[str, int] = {pool: 0 for pool in self.memory_pools}
        
        # Initialize cache
        self.cache_size = self.config.get("cache_size", int(self.total_memory * 0.1))  # 10% for cache
        self.cached_blocks: Dict[str, MemoryBlock] = {}
        self.cache_usage = 0
        
        # Initialize defragmentation parameters
        self.fragmentation_threshold = self.config.get("fragmentation_threshold", 0.3)  # 30% fragmentation triggers defrag
        self.defrag_interval = self.config.get("defrag_interval", 3600)  # 1 hour between defrag operations
        self.last_defrag_time = time.time()
        self.fragmentation_level = 0.0
        
        # Initialize garbage collection parameters
        self.gc_interval = self.config.get("gc_interval", 300)  # 5 minutes between GC operations
        self.last_gc_time = time.time()
        self.gc_age_threshold = self.config.get("gc_age_threshold", 3600)  # 1 hour of inactivity
        
        # Initialize prediction model parameters
        self.prediction_window = self.config.get("prediction_window", 10)  # Number of samples for prediction
        self.prediction_horizon = self.config.get("prediction_horizon", 5)  # How far ahead to predict
        self.memory_usage_predictions: List[float] = []
        
        # Initialize utilization tracking
        self.utilization_history: List[ResourceUtilization] = []
        self.max_history_size = self.config.get("max_history_size", 100)
        
        # Initialize lock
        self.lock = asyncio.Lock()
    
    def _initialize_memory_tiers(self) -> Dict[str, MemoryTier]:
        """
        Initialize memory tiers with different characteristics.
        
        Returns:
            Dictionary mapping tier names to MemoryTier objects
        """
        tier_config = self.config.get("memory_tiers", {
            "fast": {
                "capacity_fraction": 0.2,  # 20% of total memory
                "access_speed": 5.0,
                "cost_factor": 3.0
            },
            "standard": {
                "capacity_fraction": 0.5,  # 50% of total memory
                "access_speed": 1.0,
                "cost_factor": 1.0
            },
            "slow": {
                "capacity_fraction": 0.3,  # 30% of total memory
                "access_speed": 0.2,
                "cost_factor": 0.5
            }
        })
        
        tiers = {}
        for tier_name, tier_specs in tier_config.items():
            capacity = int(self.total_memory * tier_specs.get("capacity_fraction", 0.3))
            tiers[tier_name] = MemoryTier(
                tier_name,
                capacity,
                tier_specs.get("access_speed", 1.0),
                tier_specs.get("cost_factor", 1.0)
            )
        
        return tiers
    
    async def allocate(self, requirements: ResourceRequirements) -> Optional[ResourceAllocation]:
        """
        Allocate resources based on requirements.
        
        Args:
            requirements: The resource requirements
            
        Returns:
            The resource allocation, or None if resources could not be allocated
        """
        async with self.lock:
            requested_memory = int(requirements.memory * self.total_memory)
            
            # Check if we have enough resources
            if self.allocated_memory + requested_memory > self.total_memory:
                # If request is critical, try to preempt lower priority allocations
                if requirements.priority == ResourcePriority.CRITICAL:
                    freed_memory = await self._preempt_for_critical(requested_memory)
                    if self.allocated_memory - freed_memory + requested_memory > self.total_memory:
                        logger.warning(f"Cannot allocate {requested_memory} bytes even after preemption")
                        return None
                else:
                    logger.warning(f"Cannot allocate {requested_memory} bytes")
                    return None
            
            # Create allocation
            allocation = ResourceAllocation(
                compute=requirements.compute,
                memory=requested_memory / self.total_memory,  # Normalize to 0.0-1.0
                attention=requirements.attention,
                network=requirements.network,
                storage=requirements.storage,
                metadata={
                    "priority": requirements.priority.value,
                    "deadline": requirements.deadline,
                    "memory_bytes": requested_memory
                }
            )
            
            # Set expiration time if deadline is specified
            if requirements.deadline:
                allocation.expires_at = requirements.deadline
            
            # Update tracking
            self.allocations[allocation.id] = allocation
            self.allocated_memory += requested_memory
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Allocated {requested_memory} bytes (ID: {allocation.id})")
            return allocation
    
    async def release(self, allocation_id: str) -> bool:
        """
        Release allocated resources.
        
        Args:
            allocation_id: The ID of the resource allocation to release
            
        Returns:
            True if the resources were released, False otherwise
        """
        async with self.lock:
            if allocation_id not in self.allocations:
                logger.warning(f"Allocation {allocation_id} not found")
                return False
            
            allocation = self.allocations[allocation_id]
            memory_bytes = allocation.metadata.get("memory_bytes", 0)
            
            # Update tracking
            self.allocated_memory -= memory_bytes
            del self.allocations[allocation_id]
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Released {memory_bytes} bytes (ID: {allocation_id})")
            return True
    
    async def update_allocation(self, allocation_id: str, requirements: ResourceRequirements) -> Optional[ResourceAllocation]:
        """
        Update an existing resource allocation.
        
        Args:
            allocation_id: The ID of the resource allocation to update
            requirements: The new resource requirements
            
        Returns:
            The updated resource allocation, or None if the update failed
        """
        async with self.lock:
            if allocation_id not in self.allocations:
                logger.warning(f"Allocation {allocation_id} not found")
                return None
            
            old_allocation = self.allocations[allocation_id]
            old_memory_bytes = old_allocation.metadata.get("memory_bytes", 0)
            requested_memory = int(requirements.memory * self.total_memory)
            memory_diff = requested_memory - old_memory_bytes
            
            # Check if we have enough resources for the update
            if memory_diff > 0 and self.allocated_memory + memory_diff > self.total_memory:
                logger.warning(f"Cannot update allocation {allocation_id}: not enough memory")
                return None
            
            # Update allocation
            new_allocation = ResourceAllocation(
                id=allocation_id,
                compute=requirements.compute,
                memory=requested_memory / self.total_memory,  # Normalize to 0.0-1.0
                attention=requirements.attention,
                network=requirements.network,
                storage=requirements.storage,
                allocated_at=old_allocation.allocated_at,
                metadata={
                    "priority": requirements.priority.value,
                    "deadline": requirements.deadline,
                    "memory_bytes": requested_memory
                }
            )
            
            # Set expiration time if deadline is specified
            if requirements.deadline:
                new_allocation.expires_at = requirements.deadline
            
            # Update tracking
            self.allocations[allocation_id] = new_allocation
            self.allocated_memory += memory_diff
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Updated allocation {allocation_id}: memory {old_memory_bytes} -> {requested_memory} bytes")
            return new_allocation
    
    async def get_utilization(self) -> ResourceUtilization:
        """
        Get current resource utilization.
        
        Returns:
            The current resource utilization
        """
        async with self.lock:
            return ResourceUtilization(
                compute=0.0,  # Not tracked by this manager
                memory=self.allocated_memory / self.total_memory,
                attention=0.0,  # Not tracked by this manager
                network=0.0,  # Not tracked by this manager
                storage=0.0,  # Not tracked by this manager
                metadata={
                    "total_memory": self.total_memory,
                    "allocated_memory": self.allocated_memory,
                    "active_allocations": len(self.allocations),
                    "memory_blocks": len(self.memory_blocks),
                    "pool_usage": self.pool_usage
                }
            )
    
    async def allocate_memory_block(self, size: int, purpose: str) -> Optional[str]:
        """
        Allocate a block of memory.
        
        Args:
            size: The size of the memory block in bytes
            purpose: The purpose of the memory block
            
        Returns:
            The ID of the allocated memory block, or None if allocation failed
        """
        async with self.lock:
            # Determine which pool to use
            pool = self._determine_pool_for_purpose(purpose)
            
            # Check if pool has enough space
            if self.pool_usage[pool] + size > self.memory_pools[pool]:
                # Try to free up space in the pool
                if not await self._optimize_pool(pool, size):
                    logger.warning(f"Cannot allocate {size} bytes in {pool} pool")
                    return None
            
            # Create memory block
            block_id = f"mem_{int(time.time())}_{len(self.memory_blocks)}"
            block = MemoryBlock(block_id, size, purpose)
            
            # Update tracking
            self.memory_blocks[block_id] = block
            self.pool_usage[pool] += size
            self.allocated_memory += size
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Allocated memory block {block_id}: {size} bytes for {purpose}")
            return block_id
    
    async def release_memory_block(self, block_id: str) -> bool:
        """
        Release a block of memory.
        
        Args:
            block_id: The ID of the memory block to release
            
        Returns:
            True if the memory block was released, False otherwise
        """
        async with self.lock:
            if block_id not in self.memory_blocks:
                logger.warning(f"Memory block {block_id} not found")
                return False
            
            block = self.memory_blocks[block_id]
            pool = self._determine_pool_for_purpose(block.purpose)
            
            # Update tracking
            self.pool_usage[pool] -= block.size
            self.allocated_memory -= block.size
            del self.memory_blocks[block_id]
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Released memory block {block_id}: {block.size} bytes")
            return True
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Returns:
            Dictionary with memory usage statistics
        """
        async with self.lock:
            # Calculate statistics
            total_blocks = len(self.memory_blocks)
            total_allocated = self.allocated_memory
            
            # Group blocks by purpose
            purpose_usage = {}
            for block in self.memory_blocks.values():
                if block.purpose not in purpose_usage:
                    purpose_usage[block.purpose] = 0
                purpose_usage[block.purpose] += block.size
            
            # Get pool usage
            pool_usage = {
                pool: {
                    "total": size,
                    "used": self.pool_usage[pool],
                    "free": size - self.pool_usage[pool],
                    "utilization": self.pool_usage[pool] / size if size > 0 else 0
                }
                for pool, size in self.memory_pools.items()
            }
            
            return {
                "total_memory": self.total_memory,
                "total_allocated": total_allocated,
                "utilization": total_allocated / self.total_memory,
                "total_blocks": total_blocks,
                "purpose_usage": purpose_usage,
                "pool_usage": pool_usage
            }
    
    async def optimize(self) -> Dict[str, Any]:
        """
        Optimize memory usage.
        
        Features:
        - Garbage collection of unused memory blocks
        - Memory defragmentation
        - Cache optimization for frequently accessed data
        - Tier migration for optimal performance
        - Memory pool rebalancing
        - Predictive memory allocation
        
        Returns:
            Dictionary with optimization results
        """
        async with self.lock:
            start_time = time.time()
            results = {}
            
            # Check for expired allocations
            expired_allocations = [
                allocation_id for allocation_id, allocation in self.allocations.items()
                if allocation.expires_at and time.time() > allocation.expires_at
            ]
            
            # Release expired allocations
            for allocation_id in expired_allocations:
                await self.release(allocation_id)
            
            results["expired_allocations_released"] = len(expired_allocations)
            
            # Run garbage collection if needed
            if time.time() - self.last_gc_time >= self.gc_interval:
                gc_results = await self._garbage_collect()
                results["garbage_collection"] = gc_results
                self.last_gc_time = time.time()
            
            # Run defragmentation if needed
            if (time.time() - self.last_defrag_time >= self.defrag_interval and
                self.fragmentation_level >= self.fragmentation_threshold):
                defrag_results = await self._defragment_memory()
                results["defragmentation"] = defrag_results
                self.last_defrag_time = time.time()
            
            # Optimize cache
            cache_results = self._optimize_cache()
            results["cache_optimization"] = cache_results
            
            # Optimize tier allocations
            tier_results = await self._optimize_tier_allocations()
            results["tier_optimization"] = tier_results
            
            # Rebalance memory pools if needed
            pool_results = await self._rebalance_pools()
            results["pool_rebalancing"] = pool_results
            
            # Predict future memory needs
            prediction_results = self._predict_memory_needs()
            results["memory_prediction"] = prediction_results
            
            # Proactively allocate memory if predicted usage is high
            if prediction_results["predicted_increase"] > 0.2:
                proactive_results = await self._proactive_allocation(prediction_results)
                results["proactive_allocation"] = proactive_results
            
            execution_time = time.time() - start_time
            results["execution_time"] = execution_time
            results["current_utilization"] = self.allocated_memory / self.total_memory
            
            return results
    
    def _update_utilization(self) -> None:
        """Update the utilization history."""
        utilization = ResourceUtilization(
            compute=0.0,  # Not tracked by this manager
            memory=self.allocated_memory / self.total_memory,
            attention=0.0,  # Not tracked by this manager
            network=0.0,  # Not tracked by this manager
            storage=0.0  # Not tracked by this manager
        )
        
        self.utilization_history.append(utilization)
        
        # Trim history if needed
        if len(self.utilization_history) > self.max_history_size:
            self.utilization_history = self.utilization_history[-self.max_history_size:]
    
    def _determine_pool_for_purpose(self, purpose: str) -> str:
        """
        Determine which memory pool to use for a given purpose.
        
        Args:
            purpose: The purpose of the memory block
            
        Returns:
            The name of the memory pool to use
        """
        purpose_lower = purpose.lower()
        
        if "working" in purpose_lower or "short_term" in purpose_lower:
            return "working_memory"
        elif "long_term" in purpose_lower or "permanent" in purpose_lower:
            return "long_term_memory"
        elif "system" in purpose_lower or "core" in purpose_lower:
            return "system"
        else:
            return "working_memory"  # Default to working memory
    
    async def _optimize_pool(self, pool: str, required_size: int) -> bool:
        """
        Optimize a memory pool to free up space.
        
        Args:
            pool: The name of the pool to optimize
            required_size: The required size in bytes
            
        Returns:
            True if enough space was freed, False otherwise
        """
        # Identify blocks in this pool
        pool_blocks = [
            (block_id, block) for block_id, block in self.memory_blocks.items()
            if self._determine_pool_for_purpose(block.purpose) == pool
        ]
        
        # Sort by last accessed time (oldest first)
        pool_blocks.sort(key=lambda x: x[1].last_accessed)
        
        # Calculate how much space we need to free
        to_free = required_size - (self.memory_pools[pool] - self.pool_usage[pool])
        if to_free <= 0:
            return True  # Already have enough space
        
        # Release blocks until we have enough space
        freed = 0
        for block_id, block in pool_blocks:
            await self.release_memory_block(block_id)
            freed += block.size
            
            if freed >= to_free:
                return True
        
        return False  # Couldn't free enough space
    
    async def _rebalance_pools(self) -> Dict[str, Any]:
        """
        Rebalance memory pools based on usage patterns and predictions.
        
        Returns:
            Dictionary with rebalancing statistics
        """
        # Calculate utilization of each pool
        pool_utilization = {
            pool: self.pool_usage[pool] / size
            for pool, size in self.memory_pools.items()
        }
        
        # Identify over-utilized and under-utilized pools
        over_utilized = [pool for pool, util in pool_utilization.items() if util > 0.9]
        under_utilized = [pool for pool, util in pool_utilization.items() if util < 0.5]
        
        transfers = []
        
        if not over_utilized or not under_utilized:
            return {"status": "no_rebalancing_needed", "transfers": transfers}
        
        # Calculate how much to transfer
        for over_pool in over_utilized:
            for under_pool in under_utilized:
                # Calculate transfer amount (10% of over-utilized pool)
                transfer = int(self.memory_pools[over_pool] * 0.1)
                
                # Ensure we don't transfer too much
                available = self.memory_pools[over_pool] - self.pool_usage[over_pool]
                transfer = min(transfer, available)
                
                if transfer > 0:
                    # Update pool sizes
                    self.memory_pools[over_pool] -= transfer
                    self.memory_pools[under_pool] += transfer
                    
                    transfers.append({
                        "from_pool": over_pool,
                        "to_pool": under_pool,
                        "amount": transfer,
                        "from_utilization_before": pool_utilization[over_pool],
                        "to_utilization_before": pool_utilization[under_pool]
                    })
                    
                    # Update utilization
                    pool_utilization[over_pool] = self.pool_usage[over_pool] / self.memory_pools[over_pool]
                    pool_utilization[under_pool] = self.pool_usage[under_pool] / self.memory_pools[under_pool]
                    
                    logger.info(f"Rebalanced memory pools: {transfer} bytes from {over_pool} to {under_pool}")
        
        return {
            "status": "rebalanced",
            "transfers": transfers,
            "pool_utilization_after": pool_utilization
        }
    
    async def _preempt_for_critical(self, required_memory: int) -> int:
        """
        Preempt lower priority allocations to make room for a critical allocation.
        
        Args:
            required_memory: The required memory in bytes
            
        Returns:
            The amount of memory freed in bytes
        """
        # Sort allocations by priority (lowest first)
        sorted_allocations = sorted(
            self.allocations.items(),
            key=lambda x: ResourcePriority(x[1].metadata.get("priority", "medium")).value
        )
        
        freed_memory = 0
        preempted_ids = []
        
        # Preempt allocations until we have enough memory
        for allocation_id, allocation in sorted_allocations:
            # Skip high priority and critical allocations
            if allocation.metadata.get("priority") in [ResourcePriority.HIGH.value, ResourcePriority.CRITICAL.value]:
                continue
            
            memory_bytes = allocation.metadata.get("memory_bytes", 0)
            preempted_ids.append(allocation_id)
            freed_memory += memory_bytes
            
            if freed_memory >= required_memory:
                break
        
        # Release preempted allocations
        for allocation_id in preempted_ids:
            await self.release(allocation_id)
        
        logger.info(f"Preempted {len(preempted_ids)} allocations to free {freed_memory} bytes")
        return freed_memory
    
    async def _garbage_collect(self) -> Dict[str, Any]:
        """
        Perform garbage collection to reclaim unused memory.
        
        Returns:
            Dictionary with garbage collection statistics
        """
        # Identify unused memory blocks
        current_time = time.time()
        unused_blocks = []
        
        # Different thresholds for different purposes
        thresholds = {
            "working_memory": self.gc_age_threshold * 0.5,  # Shorter threshold for working memory
            "long_term_memory": self.gc_age_threshold * 3.0,  # Longer threshold for long-term memory
            "system": self.gc_age_threshold * 2.0,  # Medium threshold for system
            "default": self.gc_age_threshold
        }
        
        # Find unused blocks based on purpose-specific thresholds
        for block_id, block in self.memory_blocks.items():
            purpose = block.purpose.lower()
            
            # Determine threshold based on purpose
            threshold = next(
                (thresholds[key] for key in thresholds if key in purpose),
                thresholds["default"]
            )
            
            # Check if block is unused
            if current_time - block.last_accessed > threshold:
                unused_blocks.append(block_id)
        
        # Sort by least recently accessed
        unused_blocks.sort(
            key=lambda block_id: self.memory_blocks[block_id].last_accessed
        )
        
        # Release unused blocks
        memory_freed = 0
        released_blocks = []
        
        for block_id in unused_blocks:
            if block_id in self.memory_blocks:  # Check again in case it was released during iteration
                block = self.memory_blocks[block_id]
                memory_freed += block.size
                released_blocks.append({
                    "id": block_id,
                    "size": block.size,
                    "purpose": block.purpose,
                    "tier": block.tier_name,
                    "last_accessed": current_time - block.last_accessed
                })
                await self.release_memory_block(block_id)
        
        return {
            "blocks_released": len(released_blocks),
            "memory_freed": memory_freed,
            "released_blocks": released_blocks[:10]  # Return details of up to 10 released blocks
        }
    
    async def _defragment_memory(self) -> Dict[str, Any]:
        """
        Defragment memory to reduce fragmentation.
        
        Returns:
            Dictionary with defragmentation statistics
        """
        start_time = time.time()
        
        # Calculate current fragmentation level
        self._calculate_fragmentation_level()
        
        if self.fragmentation_level < self.fragmentation_threshold:
            return {
                "status": "skipped",
                "reason": "fragmentation_below_threshold",
                "current_fragmentation": self.fragmentation_level
            }
        
        # Track statistics
        defragmented_blocks = 0
        memory_moved = 0
        
        # Defragment each tier separately
        tier_stats = {}
        
        for tier_name, tier in self.memory_tiers.items():
            # Skip if tier has no blocks
            if not tier.blocks:
                continue
            
            # Identify fragmented blocks
            fragmented_blocks = [
                block_id for block_id, block in tier.blocks.items()
                if block.fragmented
            ]
            
            # Skip if no fragmented blocks
            if not fragmented_blocks:
                continue
            
            # Defragment blocks
            tier_defragmented = 0
            tier_memory_moved = 0
            
            for block_id in fragmented_blocks:
                if block_id not in tier.blocks:  # Check in case it was released
                    continue
                    
                block = tier.blocks[block_id]
                
                # Create a new block with the same properties
                new_block_id = f"defrag_{block_id}_{int(time.time())}"
                new_block = MemoryBlock(
                    new_block_id,
                    block.size,
                    block.purpose,
                    tier_name
                )
                
                # Copy properties
                new_block.access_count = block.access_count
                new_block.last_accessed = block.last_accessed
                new_block.created_at = time.time()  # New creation time
                new_block.cached = block.cached
                new_block.cache_priority = block.cache_priority
                new_block.access_pattern = block.access_pattern.copy()
                
                # Add new block to tier
                tier.blocks[new_block_id] = new_block
                self.memory_blocks[new_block_id] = new_block
                
                # Remove old block
                del tier.blocks[block_id]
                del self.memory_blocks[block_id]
                
                # Update statistics
                tier_defragmented += 1
                tier_memory_moved += block.size
                defragmented_blocks += 1
                memory_moved += block.size
            
            # Store tier statistics
            tier_stats[tier_name] = {
                "blocks_defragmented": tier_defragmented,
                "memory_moved": tier_memory_moved
            }
        
        # Recalculate fragmentation level
        old_fragmentation = self.fragmentation_level
        self._calculate_fragmentation_level()
        
        return {
            "status": "completed",
            "blocks_defragmented": defragmented_blocks,
            "memory_moved": memory_moved,
            "fragmentation_before": old_fragmentation,
            "fragmentation_after": self.fragmentation_level,
            "tier_statistics": tier_stats,
            "execution_time": time.time() - start_time
        }
    
    def _calculate_fragmentation_level(self) -> float:
        """
        Calculate the current memory fragmentation level.
        
        Returns:
            Fragmentation level (0.0 to 1.0)
        """
        if not self.memory_blocks:
            self.fragmentation_level = 0.0
            return self.fragmentation_level
        
        # Count fragmented blocks
        fragmented_blocks = sum(1 for block in self.memory_blocks.values() if block.fragmented)
        
        # Calculate fragmentation level
        self.fragmentation_level = fragmented_blocks / len(self.memory_blocks)
        
        return self.fragmentation_level
    
    def _optimize_cache(self) -> Dict[str, Any]:
        """
        Optimize the memory cache for frequently accessed data.
        
        Returns:
            Dictionary with cache optimization statistics
        """
        # Skip if cache is disabled
        if self.cache_size <= 0:
            return {"status": "disabled"}
        
        start_time = time.time()
        
        # Track statistics
        added_to_cache = 0
        removed_from_cache = 0
        cache_hits = 0
        cache_misses = 0
        
        # Calculate cache efficiency
        for block in self.memory_blocks.values():
            if block.cached:
                cache_hits += block.access_count
            else:
                cache_misses += block.access_count
        
        cache_efficiency = cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
        
        # Update cache status for all blocks
        for block in self.memory_blocks.values():
            # Skip blocks that are too large for cache
            if block.size > self.cache_size * 0.1:  # Don't cache blocks larger than 10% of cache
                if block.cached:
                    block.cached = False
                    self.cache_usage -= block.size
                    removed_from_cache += 1
                continue
            
            # Calculate cache score based on access pattern
            access_frequency = block.get_access_frequency(300)  # Last 5 minutes
            recency_score = 1.0 / (1.0 + (time.time() - block.last_accessed) / 60)  # Higher for recent access
            
            cache_score = (0.7 * access_frequency + 0.3 * recency_score) * block.cache_priority
            
            # Decide whether to cache
            if cache_score > 0.7 and not block.cached:
                # Check if we have space
                if self.cache_usage + block.size <= self.cache_size:
                    block.cached = True
                    self.cache_usage += block.size
                    added_to_cache += 1
                else:
                    # Find lowest priority cached block to evict
                    cached_blocks = [(b_id, b) for b_id, b in self.memory_blocks.items() if b.cached]
                    if cached_blocks:
                        cached_blocks.sort(key=lambda x: x[1].cache_priority)
                        
                        # Evict blocks until we have space
                        space_needed = block.size
                        evicted = []
                        
                        for evict_id, evict_block in cached_blocks:
                            if evict_block.cache_priority >= block.cache_priority:
                                break  # Don't evict higher priority blocks
                                
                            evict_block.cached = False
                            self.cache_usage -= evict_block.size
                            removed_from_cache += 1
                            evicted.append(evict_id)
                            
                            space_needed -= evict_block.size
                            if space_needed <= 0:
                                break
                        
                        # Add block to cache if we freed enough space
                        if space_needed <= 0:
                            block.cached = True
                            self.cache_usage += block.size
                            added_to_cache += 1
            
            # Remove from cache if score is low
            elif cache_score < 0.3 and block.cached:
                block.cached = False
                self.cache_usage -= block.size
                removed_from_cache += 1
        
        return {
            "status": "completed",
            "added_to_cache": added_to_cache,
            "removed_from_cache": removed_from_cache,
            "cache_usage": self.cache_usage,
            "cache_capacity": self.cache_size,
            "cache_utilization": self.cache_usage / self.cache_size if self.cache_size > 0 else 0,
            "cache_efficiency": cache_efficiency,
            "execution_time": time.time() - start_time
        }
    
    async def _optimize_tier_allocations(self) -> Dict[str, Any]:
        """
        Optimize memory tier allocations for optimal performance.
        
        Returns:
            Dictionary with tier optimization statistics
        """
        # Skip if only one tier
        if len(self.memory_tiers) <= 1:
            return {"status": "skipped", "reason": "single_tier"}
        
        start_time = time.time()
        
        # Track statistics
        promotions = 0
        demotions = 0
        
        # Get tiers sorted by access speed (fastest first)
        sorted_tiers = sorted(
            self.memory_tiers.values(),
            key=lambda t: t.access_speed,
            reverse=True
        )
        
        # Identify blocks for promotion (move to faster tier)
        promotion_candidates = []
        
        for block_id, block in self.memory_blocks.items():
            # Skip if in fastest tier already
            if block.tier_name == sorted_tiers[0].name:
                continue
                
            # Calculate promotion score based on access pattern
            access_frequency = block.get_access_frequency(300)  # Last 5 minutes
            recency_score = 1.0 / (1.0 + (time.time() - block.last_accessed) / 60)
            
            promotion_score = 0.5 * access_frequency + 0.3 * recency_score + 0.2 * block.cache_priority
            
            if promotion_score > 0.7:
                promotion_candidates.append((block_id, block, promotion_score))
        
        # Sort candidates by score (highest first)
        promotion_candidates.sort(key=lambda x: x[2], reverse=True)
        
        # Identify blocks for demotion (move to slower tier)
        demotion_candidates = []
        
        for block_id, block in self.memory_blocks.items():
            # Skip if in slowest tier already
            if block.tier_name == sorted_tiers[-1].name:
                continue
                
            # Calculate demotion score based on access pattern
            access_frequency = block.get_access_frequency(3600)  # Last hour
            recency_score = 1.0 / (1.0 + (time.time() - block.last_accessed) / 3600)
            
            demotion_score = 1.0 - (0.5 * access_frequency + 0.3 * recency_score + 0.2 * block.cache_priority)
            
            if demotion_score > 0.7:
                demotion_candidates.append((block_id, block, demotion_score))
        
        # Sort candidates by score (highest first)
        demotion_candidates.sort(key=lambda x: x[2], reverse=True)
        
        # Process promotions
        for block_id, block, score in promotion_candidates:
            # Find current tier index
            current_tier_index = next(
                (i for i, tier in enumerate(sorted_tiers) if tier.name == block.tier_name),
                -1
            )
            
            if current_tier_index <= 0:
                continue  # Skip if already in fastest tier or tier not found
                
            # Target tier is one faster
            target_tier = sorted_tiers[current_tier_index - 1]
            
            # Check if target tier has space
            if target_tier.available_capacity >= block.size:
                # Move block to faster tier
                current_tier_name = block.tier_name
                
                # Remove from current tier
                if current_tier_name in self.memory_tiers and block_id in self.memory_tiers[current_tier_name].blocks:
                    del self.memory_tiers[current_tier_name].blocks[block_id]
                    self.memory_tiers[current_tier_name].used_capacity -= block.size
                
                # Add to target tier
                block.tier_name = target_tier.name
                target_tier.blocks[block_id] = block
                target_tier.used_capacity += block.size
                
                promotions += 1
                
                logger.debug(f"Promoted memory block {block_id} from {current_tier_name} to {target_tier.name}")
                
                # Limit the number of promotions per optimization cycle
                if promotions >= 10:
                    break
        
        # Process demotions
        for block_id, block, score in demotion_candidates:
            # Find current tier index
            current_tier_index = next(
                (i for i, tier in enumerate(sorted_tiers) if tier.name == block.tier_name),
                -1
            )
            
            if current_tier_index >= len(sorted_tiers) - 1 or current_tier_index < 0:
                continue  # Skip if already in slowest tier or tier not found
                
            # Target tier is one slower
            target_tier = sorted_tiers[current_tier_index + 1]
            
            # Move block to slower tier
            current_tier_name = block.tier_name
            
            # Remove from current tier
            if current_tier_name in self.memory_tiers and block_id in self.memory_tiers[current_tier_name].blocks:
                del self.memory_tiers[current_tier_name].blocks[block_id]
                self.memory_tiers[current_tier_name].used_capacity -= block.size
            
            # Add to target tier
            block.tier_name = target_tier.name
            target_tier.blocks[block_id] = block
            target_tier.used_capacity += block.size
            
            demotions += 1
            
            logger.debug(f"Demoted memory block {block_id} from {current_tier_name} to {target_tier.name}")
            
            # Limit the number of demotions per optimization cycle
            if demotions >= 20:
                break
        
        # Calculate tier utilization after optimization
        tier_utilization = {
            tier_name: tier.utilization
            for tier_name, tier in self.memory_tiers.items()
        }
        
        return {
            "status": "completed",
            "promotions": promotions,
            "demotions": demotions,
            "tier_utilization": tier_utilization,
            "execution_time": time.time() - start_time
        }
    
    def _predict_memory_needs(self) -> Dict[str, Any]:
        """
        Predict future memory needs based on usage patterns.
        
        Returns:
            Dictionary with prediction statistics
        """
        # Get recent utilization values
        if len(self.utilization_history) < self.prediction_window:
            return {
                "status": "insufficient_data",
                "predicted_increase": 0.0,
                "confidence": 0.0
            }
        
        # Extract memory utilization values
        recent_values = [u.memory for u in self.utilization_history[-self.prediction_window:]]
        
        # Calculate trend using linear regression
        n = len(recent_values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(recent_values) / n
        
        # Calculate slope
        numerator = sum((x[i] - x_mean) * (recent_values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0
        
        # Project future utilization
        current_utilization = recent_values[-1]
        predicted_utilization = current_utilization + (slope * self.prediction_horizon)
        
        # Calculate predicted increase as a percentage
        predicted_increase = (predicted_utilization - current_utilization) / current_utilization if current_utilization > 0 else 0
        
        # Calculate prediction confidence based on R-squared
        if n > 2:
            # Calculate predicted values using the model
            y_pred = [x_mean + slope * (x[i] - x_mean) for i in range(n)]
            
            # Calculate R-squared
            ss_total = sum((recent_values[i] - y_mean) ** 2 for i in range(n))
            ss_residual = sum((recent_values[i] - y_pred[i]) ** 2 for i in range(n))
            r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
            
            # Confidence is based on R-squared
            confidence = max(0.0, min(1.0, r_squared))
        else:
            confidence = 0.5  # Default with limited data
        
        # Store prediction for future reference
        self.memory_usage_predictions.append(predicted_utilization)
        if len(self.memory_usage_predictions) > self.max_history_size:
            self.memory_usage_predictions = self.memory_usage_predictions[-self.max_history_size:]
        
        return {
            "current_utilization": current_utilization,
            "predicted_utilization": max(0.0, min(1.0, predicted_utilization)),  # Clamp to [0, 1]
            "predicted_increase": predicted_increase,
            "prediction_horizon": self.prediction_horizon,
            "confidence": confidence,
            "trend_slope": slope
        }
    
    async def _proactive_allocation(self, prediction_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Proactively allocate memory based on predictions.
        
        Args:
            prediction_results: Results from _predict_memory_needs
            
        Returns:
            Dictionary with proactive allocation statistics
        """
        # Skip if confidence is too low
        if prediction_results["confidence"] < 0.6:
            return {
                "status": "skipped",
                "reason": "low_confidence",
                "confidence": prediction_results["confidence"]
            }
        
        start_time = time.time()
        
        # Calculate how much memory to reserve
        predicted_increase = prediction_results["predicted_increase"]
        current_utilization = prediction_results["current_utilization"]
        
        # Reserve memory proportional to predicted increase
        reserve_fraction = min(0.5, predicted_increase)  # Cap at 50%
        reserve_size = int(self.total_memory * reserve_fraction)
        
        # Check if we already have enough reserved
        current_reserve = self.memory_pools["reserve"]
        reserve_usage = self.pool_usage["reserve"]
        available_reserve = current_reserve - reserve_usage
        
        if available_reserve >= reserve_size:
            return {
                "status": "sufficient_reserve",
                "available_reserve": available_reserve,
                "needed_reserve": reserve_size
            }
        
        # Try to increase reserve pool
        additional_reserve_needed = reserve_size - available_reserve
        
        # Find pools to take from (prefer working_memory, then long_term_memory)
        pool_priorities = ["working_memory", "long_term_memory", "system"]
        reallocated = 0
        
        for pool in pool_priorities:
            # Skip reserve pool
            if pool == "reserve":
                continue
                
            # Calculate how much we can take from this pool
            pool_size = self.memory_pools[pool]
            pool_usage = self.pool_usage[pool]
            available = pool_size - pool_usage
            
            # Don't take more than 20% of the pool's size
            max_take = int(pool_size * 0.2)
            take_amount = min(additional_reserve_needed - reallocated, available, max_take)
            
            if take_amount > 0:
                # Update pool sizes
                self.memory_pools[pool] -= take_amount
                self.memory_pools["reserve"] += take_amount
                
                reallocated += take_amount
                
                logger.info(f"Proactively reallocated {take_amount} bytes from {pool} to reserve")
                
                # Check if we've reallocated enough
                if reallocated >= additional_reserve_needed:
                    break
        
        return {
            "status": "reallocated",
            "additional_reserve_needed": additional_reserve_needed,
            "reallocated": reallocated,
            "new_reserve_size": self.memory_pools["reserve"],
            "execution_time": time.time() - start_time
        }