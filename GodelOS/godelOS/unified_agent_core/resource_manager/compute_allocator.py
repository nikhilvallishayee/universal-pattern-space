"""
Compute Resource Allocator Implementation for GodelOS

This module implements the ComputeResourceAllocator class, which is responsible for
allocating and managing compute resources for the UnifiedAgentCore.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any

from godelOS.unified_agent_core.resource_manager.interfaces import (
    ResourceRequirements, ResourceAllocation, ResourceUtilization,
    ResourcePriority, ComputeResourceAllocatorInterface
)

logger = logging.getLogger(__name__)


class ComputeResourceAllocator(ComputeResourceAllocatorInterface):
    """
    ComputeResourceAllocator implementation for GodelOS.
    
    The ComputeResourceAllocator is responsible for allocating and managing
    compute resources for the UnifiedAgentCore.
    
    Features:
    - Adaptive resource allocation based on task complexity
    - Load balancing across available compute resources
    - Task preemption for high-priority tasks
    - Resource usage prediction and proactive allocation
    - Performance monitoring and optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the compute resource allocator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize resource tracking
        self.total_compute_units = self.config.get("total_compute_units", 1.0)
        self.allocated_compute_units = 0.0
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.task_allocations: Dict[str, float] = {}  # task_id -> compute_units
        
        # Initialize utilization tracking
        self.utilization_history: List[ResourceUtilization] = []
        self.max_history_size = self.config.get("max_history_size", 100)
        
        # Initialize performance tracking
        self.task_performance: Dict[str, Dict[str, Any]] = {}  # task_id -> performance metrics
        self.resource_efficiency: Dict[str, float] = {}  # allocation_id -> efficiency score
        
        # Initialize load balancing
        self.compute_nodes: Dict[str, Dict[str, Any]] = self.config.get("compute_nodes", {
            "default": {"capacity": 1.0, "load": 0.0, "efficiency": 1.0}
        })
        
        # Initialize prediction model parameters
        self.prediction_window = self.config.get("prediction_window", 10)  # Number of samples to use for prediction
        self.prediction_horizon = self.config.get("prediction_horizon", 5)  # How far ahead to predict
        self.prediction_weights = [0.8, 0.6, 0.4, 0.2, 0.1]  # Weights for recent samples (most recent first)
        
        # Initialize lock
        self.lock = asyncio.Lock()
    
    async def allocate(self, requirements: ResourceRequirements) -> Optional[ResourceAllocation]:
        """
        Allocate resources based on requirements.
        
        Args:
            requirements: The resource requirements
            
        Returns:
            The resource allocation, or None if resources could not be allocated
        """
        async with self.lock:
            requested_compute = requirements.compute * self.total_compute_units
            
            # Check if we have enough resources
            if self.allocated_compute_units + requested_compute > self.total_compute_units:
                # If request is critical, try to preempt lower priority allocations
                if requirements.priority == ResourcePriority.CRITICAL:
                    freed_compute = await self._preempt_for_critical(requested_compute)
                    if self.allocated_compute_units - freed_compute + requested_compute > self.total_compute_units:
                        logger.warning(f"Cannot allocate {requested_compute} compute units even after preemption")
                        return None
                else:
                    logger.warning(f"Cannot allocate {requested_compute} compute units")
                    return None
            
            # Create allocation
            allocation = ResourceAllocation(
                compute=requested_compute,
                memory=requirements.memory,
                attention=requirements.attention,
                network=requirements.network,
                storage=requirements.storage,
                metadata={
                    "priority": requirements.priority.value,
                    "deadline": requirements.deadline
                }
            )
            
            # Set expiration time if deadline is specified
            if requirements.deadline:
                allocation.expires_at = requirements.deadline
            
            # Update tracking
            self.allocations[allocation.id] = allocation
            self.allocated_compute_units += requested_compute
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Allocated {requested_compute} compute units (ID: {allocation.id})")
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
            
            # Update tracking
            self.allocated_compute_units -= allocation.compute
            del self.allocations[allocation_id]
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Released {allocation.compute} compute units (ID: {allocation_id})")
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
            requested_compute = requirements.compute * self.total_compute_units
            compute_diff = requested_compute - old_allocation.compute
            
            # Check if we have enough resources for the update
            if compute_diff > 0 and self.allocated_compute_units + compute_diff > self.total_compute_units:
                logger.warning(f"Cannot update allocation {allocation_id}: not enough compute resources")
                return None
            
            # Update allocation
            new_allocation = ResourceAllocation(
                id=allocation_id,
                compute=requested_compute,
                memory=requirements.memory,
                attention=requirements.attention,
                network=requirements.network,
                storage=requirements.storage,
                allocated_at=old_allocation.allocated_at,
                metadata={
                    "priority": requirements.priority.value,
                    "deadline": requirements.deadline
                }
            )
            
            # Set expiration time if deadline is specified
            if requirements.deadline:
                new_allocation.expires_at = requirements.deadline
            
            # Update tracking
            self.allocations[allocation_id] = new_allocation
            self.allocated_compute_units += compute_diff
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Updated allocation {allocation_id}: compute {old_allocation.compute} -> {requested_compute}")
            return new_allocation
    
    async def get_utilization(self) -> ResourceUtilization:
        """
        Get current resource utilization.
        
        Returns:
            The current resource utilization
        """
        async with self.lock:
            return ResourceUtilization(
                compute=self.allocated_compute_units / self.total_compute_units,
                memory=0.0,  # Not tracked by this allocator
                attention=0.0,  # Not tracked by this allocator
                network=0.0,  # Not tracked by this allocator
                storage=0.0,  # Not tracked by this allocator
                metadata={
                    "total_compute_units": self.total_compute_units,
                    "allocated_compute_units": self.allocated_compute_units,
                    "active_allocations": len(self.allocations)
                }
            )
    
    async def allocate_compute_intensive_task(self, task_id: str, compute_units: float) -> bool:
        """
        Allocate resources for a compute-intensive task.
        
        Args:
            task_id: The ID of the task
            compute_units: The number of compute units required
            
        Returns:
            True if resources were allocated, False otherwise
        """
        async with self.lock:
            # Check if we have enough resources
            if self.allocated_compute_units + compute_units > self.total_compute_units:
                logger.warning(f"Cannot allocate {compute_units} compute units for task {task_id}")
                return False
            
            # Create requirements
            requirements = ResourceRequirements(
                compute=compute_units / self.total_compute_units,
                memory=0.1,  # Minimal memory requirement
                priority=ResourcePriority.HIGH
            )
            
            # Allocate resources
            allocation = await self.allocate(requirements)
            
            if allocation:
                # Track task allocation
                self.task_allocations[task_id] = compute_units
                return True
            
            return False
    
    async def optimize(self) -> Dict[str, Any]:
        """
        Optimize compute resource allocation.
        
        Features:
        - Dynamic resource scaling based on utilization patterns
        - Load balancing across compute nodes
        - Resource efficiency analysis and optimization
        - Predictive resource allocation
        - Task performance optimization
        
        Returns:
            Dictionary with optimization results
        """
        async with self.lock:
            start_time = time.time()
            
            # Check for expired allocations
            expired_allocations = [
                allocation_id for allocation_id, allocation in self.allocations.items()
                if allocation.expires_at and time.time() > allocation.expires_at
            ]
            
            # Release expired allocations
            for allocation_id in expired_allocations:
                await self.release(allocation_id)
            
            # Analyze utilization patterns
            utilization_stats = self._analyze_utilization_patterns()
            
            # Perform load balancing
            load_balancing_stats = await self._balance_compute_load()
            
            # Optimize resource efficiency
            efficiency_stats = self._optimize_resource_efficiency()
            
            # Predict future resource needs
            prediction_stats = self._predict_resource_needs()
            
            # Adjust resource allocation based on predictions
            if prediction_stats["predicted_increase"] > 0.2 and self.config.get("auto_scale", False):
                old_total = self.total_compute_units
                scale_factor = 1.0 + min(0.5, prediction_stats["predicted_increase"])
                self.total_compute_units *= scale_factor
                logger.info(f"Predictive auto-scaling compute units: {old_total} -> {self.total_compute_units}")
            
            execution_time = time.time() - start_time
            
            return {
                "expired_allocations_released": len(expired_allocations),
                "utilization_stats": utilization_stats,
                "load_balancing_stats": load_balancing_stats,
                "efficiency_stats": efficiency_stats,
                "prediction_stats": prediction_stats,
                "total_compute_units": self.total_compute_units,
                "execution_time": execution_time
            }
    
    def _update_utilization(self) -> None:
        """Update the utilization history."""
        utilization = ResourceUtilization(
            compute=self.allocated_compute_units / self.total_compute_units,
            memory=0.0,  # Not tracked by this allocator
            attention=0.0,  # Not tracked by this allocator
            network=0.0,  # Not tracked by this allocator
            storage=0.0  # Not tracked by this allocator
        )
        
        self.utilization_history.append(utilization)
        
        # Trim history if needed
        if len(self.utilization_history) > self.max_history_size:
            self.utilization_history = self.utilization_history[-self.max_history_size:]
    
    def _calculate_average_utilization(self) -> float:
        """Calculate the average utilization over the history."""
        if not self.utilization_history:
            return 0.0
        
        total = sum(u.compute for u in self.utilization_history)
        return total / len(self.utilization_history)
    
    def _analyze_utilization_patterns(self) -> Dict[str, Any]:
        """
        Analyze utilization patterns to identify trends and optimize allocation.
        
        Returns:
            Dictionary with utilization statistics
        """
        if len(self.utilization_history) < 2:
            return {
                "average_utilization": self._calculate_average_utilization(),
                "trend": "stable",
                "variability": 0.0,
                "peak_utilization": 0.0,
                "trough_utilization": 0.0
            }
        
        # Calculate statistics
        utilization_values = [u.compute for u in self.utilization_history]
        avg_utilization = sum(utilization_values) / len(utilization_values)
        peak_utilization = max(utilization_values)
        trough_utilization = min(utilization_values)
        variability = peak_utilization - trough_utilization
        
        # Calculate trend (using linear regression slope)
        n = len(utilization_values)
        if n > 5:  # Only calculate trend if we have enough data points
            x = list(range(n))
            x_mean = sum(x) / n
            y_mean = avg_utilization
            
            # Calculate slope
            numerator = sum((x[i] - x_mean) * (utilization_values[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            slope = numerator / denominator if denominator != 0 else 0
            
            # Determine trend
            if slope > 0.01:
                trend = "increasing"
            elif slope < -0.01:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "average_utilization": avg_utilization,
            "trend": trend,
            "variability": variability,
            "peak_utilization": peak_utilization,
            "trough_utilization": trough_utilization
        }
    
    async def _balance_compute_load(self) -> Dict[str, Any]:
        """
        Balance load across compute nodes.
        
        Returns:
            Dictionary with load balancing statistics
        """
        # Skip if only one compute node
        if len(self.compute_nodes) <= 1:
            return {"status": "skipped", "reason": "insufficient_nodes"}
        
        # Calculate current load distribution
        total_capacity = sum(node["capacity"] for node in self.compute_nodes.values())
        for node_id, node in self.compute_nodes.items():
            node["load_percentage"] = node["load"] / node["capacity"] if node["capacity"] > 0 else 0
        
        # Find overloaded and underloaded nodes
        avg_load_percentage = sum(node["load_percentage"] for node in self.compute_nodes.values()) / len(self.compute_nodes)
        overloaded_nodes = {node_id: node for node_id, node in self.compute_nodes.items()
                           if node["load_percentage"] > avg_load_percentage * 1.2}
        underloaded_nodes = {node_id: node for node_id, node in self.compute_nodes.items()
                            if node["load_percentage"] < avg_load_percentage * 0.8}
        
        # Balance load if needed
        migrations = []
        if overloaded_nodes and underloaded_nodes:
            # Sort allocations by size (largest first)
            sorted_allocations = sorted(
                [(alloc_id, alloc) for alloc_id, alloc in self.allocations.items()],
                key=lambda x: x[1].compute,
                reverse=True
            )
            
            # Migrate allocations from overloaded to underloaded nodes
            for alloc_id, alloc in sorted_allocations:
                # Skip if allocation doesn't specify a node
                if "compute_node" not in alloc.metadata:
                    continue
                
                source_node = alloc.metadata["compute_node"]
                if source_node in overloaded_nodes:
                    # Find best target node
                    target_node = min(underloaded_nodes.items(),
                                     key=lambda x: x[1]["load_percentage"])[0]
                    
                    # Update allocation metadata
                    self.allocations[alloc_id].metadata["compute_node"] = target_node
                    
                    # Update node loads
                    self.compute_nodes[source_node]["load"] -= alloc.compute
                    self.compute_nodes[target_node]["load"] += alloc.compute
                    
                    # Update load percentages
                    self.compute_nodes[source_node]["load_percentage"] = (
                        self.compute_nodes[source_node]["load"] /
                        self.compute_nodes[source_node]["capacity"]
                    )
                    self.compute_nodes[target_node]["load_percentage"] = (
                        self.compute_nodes[target_node]["load"] /
                        self.compute_nodes[target_node]["capacity"]
                    )
                    
                    # Record migration
                    migrations.append({
                        "allocation_id": alloc_id,
                        "from_node": source_node,
                        "to_node": target_node,
                        "compute_units": alloc.compute
                    })
                    
                    # Check if source node is no longer overloaded
                    if self.compute_nodes[source_node]["load_percentage"] <= avg_load_percentage * 1.2:
                        del overloaded_nodes[source_node]
                    
                    # Check if target node is no longer underloaded
                    if self.compute_nodes[target_node]["load_percentage"] >= avg_load_percentage * 0.8:
                        del underloaded_nodes[target_node]
                    
                    # Stop if no more overloaded or underloaded nodes
                    if not overloaded_nodes or not underloaded_nodes:
                        break
        
        # Calculate load distribution after balancing
        load_distribution = {
            node_id: {
                "capacity": node["capacity"],
                "load": node["load"],
                "load_percentage": node["load_percentage"]
            }
            for node_id, node in self.compute_nodes.items()
        }
        
        return {
            "migrations": migrations,
            "load_distribution": load_distribution,
            "average_load_percentage": avg_load_percentage
        }
    
    def _optimize_resource_efficiency(self) -> Dict[str, Any]:
        """
        Optimize resource efficiency by analyzing allocation performance.
        
        Returns:
            Dictionary with efficiency optimization statistics
        """
        if not self.task_performance:
            return {"status": "skipped", "reason": "no_performance_data"}
        
        # Calculate efficiency scores for each allocation
        for alloc_id, alloc in self.allocations.items():
            task_id = alloc.metadata.get("task_id")
            if task_id and task_id in self.task_performance:
                perf = self.task_performance[task_id]
                
                # Calculate efficiency score based on performance metrics
                throughput = perf.get("throughput", 0)
                latency = perf.get("latency", 1)
                error_rate = perf.get("error_rate", 0)
                
                # Higher throughput, lower latency, lower error rate = better efficiency
                efficiency_score = (throughput / (latency * (1 + error_rate))) if latency > 0 else 0
                
                # Store efficiency score
                self.resource_efficiency[alloc_id] = efficiency_score
        
        # Identify inefficient allocations
        avg_efficiency = (
            sum(self.resource_efficiency.values()) / len(self.resource_efficiency)
            if self.resource_efficiency else 0
        )
        
        inefficient_allocations = {
            alloc_id: efficiency
            for alloc_id, efficiency in self.resource_efficiency.items()
            if efficiency < avg_efficiency * 0.7  # 70% of average efficiency
        }
        
        return {
            "average_efficiency": avg_efficiency,
            "inefficient_allocations": len(inefficient_allocations),
            "efficiency_range": {
                "min": min(self.resource_efficiency.values()) if self.resource_efficiency else 0,
                "max": max(self.resource_efficiency.values()) if self.resource_efficiency else 0
            }
        }
    
    def _predict_resource_needs(self) -> Dict[str, Any]:
        """
        Predict future resource needs based on utilization history.
        
        Returns:
            Dictionary with prediction statistics
        """
        if len(self.utilization_history) < self.prediction_window:
            return {
                "status": "insufficient_data",
                "predicted_increase": 0.0,
                "confidence": 0.0
            }
        
        # Get recent utilization values
        recent_values = [u.compute for u in self.utilization_history[-self.prediction_window:]]
        
        # Calculate weighted average of recent changes
        changes = [recent_values[i] - recent_values[i-1] for i in range(1, len(recent_values))]
        
        # Use only available weights (in case we have fewer changes than weights)
        weights = self.prediction_weights[:len(changes)]
        
        # Normalize weights
        weight_sum = sum(weights)
        normalized_weights = [w / weight_sum for w in weights] if weight_sum > 0 else [1.0 / len(weights)] * len(weights)
        
        # Calculate weighted average change
        weighted_avg_change = sum(c * w for c, w in zip(changes, normalized_weights)) if changes else 0
        
        # Project future utilization
        current_utilization = recent_values[-1]
        predicted_utilization = current_utilization + (weighted_avg_change * self.prediction_horizon)
        
        # Calculate predicted increase as a percentage
        predicted_increase = (predicted_utilization - current_utilization) / current_utilization if current_utilization > 0 else 0
        
        # Calculate prediction confidence based on variability of changes
        if len(changes) > 1:
            mean_change = sum(changes) / len(changes)
            variance = sum((c - mean_change) ** 2 for c in changes) / len(changes)
            std_dev = variance ** 0.5
            
            # Lower variability = higher confidence
            confidence = 1.0 / (1.0 + std_dev * 5) if std_dev > 0 else 1.0
        else:
            confidence = 0.5  # Default confidence with limited data
        
        return {
            "current_utilization": current_utilization,
            "predicted_utilization": max(0.0, min(1.0, predicted_utilization)),  # Clamp to [0, 1]
            "predicted_increase": predicted_increase,
            "prediction_horizon": self.prediction_horizon,
            "confidence": confidence
        }
    
    async def _preempt_for_critical(self, required_compute: float) -> float:
        """
        Preempt lower priority allocations to make room for a critical allocation.
        
        Args:
            required_compute: The required compute units
            
        Returns:
            The amount of compute units freed
        """
        # Sort allocations by priority (lowest first)
        sorted_allocations = sorted(
            self.allocations.items(),
            key=lambda x: ResourcePriority(x[1].metadata.get("priority", "medium")).value
        )
        
        freed_compute = 0.0
        preempted_ids = []
        
        # Preempt allocations until we have enough resources
        for allocation_id, allocation in sorted_allocations:
            # Skip high priority and critical allocations
            if allocation.metadata.get("priority") in [ResourcePriority.HIGH.value, ResourcePriority.CRITICAL.value]:
                continue
            
            preempted_ids.append(allocation_id)
            freed_compute += allocation.compute
            
            if freed_compute >= required_compute:
                break
        
        # Release preempted allocations
        for allocation_id in preempted_ids:
            await self.release(allocation_id)
        
        logger.info(f"Preempted {len(preempted_ids)} allocations to free {freed_compute} compute units")
        return freed_compute
        
    async def allocate_adaptive(self, task_id: str, complexity: float, deadline: Optional[float] = None) -> Optional[ResourceAllocation]:
        """
        Adaptively allocate compute resources based on task complexity.
        
        Args:
            task_id: The ID of the task
            complexity: The complexity factor of the task (0.0 to 1.0)
            deadline: Optional deadline for the task
            
        Returns:
            The resource allocation, or None if resources could not be allocated
        """
        async with self.lock:
            # Calculate required compute based on complexity
            base_compute = 0.1  # Minimum compute allocation
            adaptive_compute = base_compute + (complexity * 0.5)  # Scale with complexity
            
            # Determine priority based on deadline
            if deadline:
                time_until_deadline = deadline - time.time()
                if time_until_deadline < 60:  # Less than a minute
                    priority = ResourcePriority.CRITICAL
                elif time_until_deadline < 300:  # Less than 5 minutes
                    priority = ResourcePriority.HIGH
                else:
                    priority = ResourcePriority.MEDIUM
            else:
                priority = ResourcePriority.MEDIUM
            
            # Create requirements
            requirements = ResourceRequirements(
                compute=adaptive_compute,
                memory=0.1,  # Default memory requirement
                attention=0.1,  # Default attention requirement
                priority=priority,
                deadline=deadline,
                metadata={"task_id": task_id, "complexity": complexity}
            )
            
            # Allocate resources
            allocation = await self.allocate(requirements)
            
            if allocation:
                # Track task allocation
                self.task_allocations[task_id] = adaptive_compute
                
                # Assign to least loaded compute node
                if len(self.compute_nodes) > 1:
                    least_loaded_node = min(
                        self.compute_nodes.items(),
                        key=lambda x: x[1]["load"] / x[1]["capacity"] if x[1]["capacity"] > 0 else float('inf')
                    )[0]
                    
                    allocation.metadata["compute_node"] = least_loaded_node
                    self.compute_nodes[least_loaded_node]["load"] += adaptive_compute
                
                logger.debug(f"Adaptive allocation for task {task_id}: {adaptive_compute} compute units (complexity: {complexity})")
                return allocation
            
            return None
    
    async def update_task_performance(self, task_id: str, performance_metrics: Dict[str, Any]) -> None:
        """
        Update performance metrics for a task.
        
        Args:
            task_id: The ID of the task
            performance_metrics: Dictionary with performance metrics
        """
        async with self.lock:
            self.task_performance[task_id] = performance_metrics
            
            # Use performance data to optimize future allocations
            if task_id in self.task_allocations:
                current_allocation = self.task_allocations[task_id]
                
                # Calculate efficiency
                throughput = performance_metrics.get("throughput", 0)
                latency = performance_metrics.get("latency", 1)
                
                efficiency = throughput / latency if latency > 0 else 0
                
                # Store for future reference
                if "efficiency_history" not in performance_metrics:
                    performance_metrics["efficiency_history"] = []
                
                performance_metrics["efficiency_history"].append(efficiency)
                performance_metrics["current_efficiency"] = efficiency