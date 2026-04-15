"""
Attention Manager Implementation for GodelOS

This module implements the AttentionManager class, which is responsible for
allocating and managing attention resources for the UnifiedAgentCore.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Set

from godelOS.unified_agent_core.resource_manager.interfaces import (
    ResourceRequirements, ResourceAllocation, ResourceUtilization,
    ResourcePriority, AttentionManagerInterface
)

logger = logging.getLogger(__name__)


class AttentionContext:
    """Class representing a context for attention management."""
    
    def __init__(self, name: str, priority: float = 1.0):
        """
        Initialize an attention context.
        
        Args:
            name: The name of the context
            priority: The priority of the context (higher values have higher priority)
        """
        self.name = name
        self.priority = priority
        self.created_at = time.time()
        self.last_updated = time.time()
        self.active = True
        self.focus_targets: Dict[str, "AttentionFocus"] = {}
        self.total_allocation = 0.0
        self.max_allocation = 0.8  # Maximum attention allocation for this context
        self.switch_cost = 0.2  # Cost of switching to this context (0.0 to 1.0)
    
    def update(self) -> None:
        """Update the context's last updated time."""
        self.last_updated = time.time()
    
    def add_focus(self, focus: "AttentionFocus") -> None:
        """
        Add a focus target to this context.
        
        Args:
            focus: The attention focus to add
        """
        self.focus_targets[focus.target] = focus
        self.total_allocation += focus.allocation
        self.update()
    
    def remove_focus(self, target: str) -> Optional["AttentionFocus"]:
        """
        Remove a focus target from this context.
        
        Args:
            target: The target to remove
            
        Returns:
            The removed attention focus, or None if not found
        """
        if target in self.focus_targets:
            focus = self.focus_targets[target]
            self.total_allocation -= focus.allocation
            self.update()
            return self.focus_targets.pop(target)
        return None
    
    def get_active_foci(self) -> List["AttentionFocus"]:
        """
        Get all active focus targets in this context.
        
        Returns:
            List of active attention foci
        """
        return [focus for focus in self.focus_targets.values() if focus.active]
    
    def get_context_score(self) -> float:
        """
        Calculate the context score based on priority, recency, and focus allocation.
        
        Returns:
            The context score (higher is more important)
        """
        recency_factor = 1.0 / (1.0 + (time.time() - self.last_updated) / 3600)  # Decay over time
        allocation_factor = min(1.0, self.total_allocation / self.max_allocation)
        
        return self.priority * (0.6 * recency_factor + 0.4 * allocation_factor)


class AttentionFocus:
    """Class representing a focus of attention."""
    
    def __init__(self, target: str, priority: ResourcePriority, allocation: float, context_name: Optional[str] = None):
        """
        Initialize an attention focus.
        
        Args:
            target: The target of attention
            priority: The priority of the focus
            allocation: The attention allocation (0.0 to 1.0)
            context_name: Optional name of the context this focus belongs to
        """
        self.target = target
        self.priority = priority
        self.allocation = allocation
        self.created_at = time.time()
        self.last_updated = time.time()
        self.active = True
        self.context_name = context_name
        self.importance = 0.5  # Importance score (0.0 to 1.0)
        self.urgency = 0.5  # Urgency score (0.0 to 1.0)
        self.access_history: List[float] = []  # History of access timestamps
        self.max_history_size = 20
        self.distraction_resistance = 0.5  # Resistance to distractions (0.0 to 1.0)
        self.refresh_count = 0  # Number of times this focus has been refreshed
    
    def update(self, allocation: float) -> None:
        """
        Update the attention allocation.
        
        Args:
            allocation: The new attention allocation
        """
        self.allocation = allocation
        self.last_updated = time.time()
        self.access_history.append(self.last_updated)
        
        # Trim history if needed
        if len(self.access_history) > self.max_history_size:
            self.access_history = self.access_history[-self.max_history_size:]
        
        # Update active status
        self.active = True
        
        # Increment refresh count
        self.refresh_count += 1
    
    def get_effective_priority(self) -> float:
        """
        Calculate effective priority based on priority, importance, and urgency.
        
        Returns:
            Effective priority score (higher is more important)
        """
        # Map enum to numeric priority
        priority_values = {
            ResourcePriority.CRITICAL: 1.0,
            ResourcePriority.HIGH: 0.8,
            ResourcePriority.MEDIUM: 0.6,
            ResourcePriority.LOW: 0.4,
            ResourcePriority.BACKGROUND: 0.2
        }
        
        base_priority = priority_values.get(self.priority, 0.5)
        
        # Calculate recency factor (higher for more recent updates)
        recency_factor = 1.0 / (1.0 + (time.time() - self.last_updated) / 300)  # 5 minutes decay
        
        # Calculate effective priority
        return (0.4 * base_priority + 0.3 * self.importance + 0.2 * self.urgency + 0.1 * recency_factor)
    
    def calculate_switch_cost(self, current_focus: Optional["AttentionFocus"]) -> float:
        """
        Calculate the cost of switching to this focus from the current focus.
        
        Args:
            current_focus: The current focus of attention, or None
            
        Returns:
            Switch cost (0.0 to 1.0, higher means more expensive)
        """
        if current_focus is None:
            return 0.2  # Base cost for initializing focus
            
        # Same focus has no switch cost
        if self.target == current_focus.target:
            return 0.0
            
        # Same context has lower switch cost
        if self.context_name and self.context_name == current_focus.context_name:
            return 0.3
            
        # Different context has higher switch cost
        return 0.7


class AttentionManager(AttentionManagerInterface):
    """
    AttentionManager implementation for GodelOS.
    
    The AttentionManager is responsible for allocating and managing attention
    resources for the UnifiedAgentCore.
    
    Features:
    - Attention allocation based on task importance and urgency
    - Context switching optimization
    - Attention decay and refreshing mechanisms
    - Focus area prioritization
    - Distraction management and filtering
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the attention manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize resource tracking
        self.total_attention = 1.0
        self.allocated_attention = 0.0
        self.allocations: Dict[str, ResourceAllocation] = {}
        
        # Initialize attention focus tracking
        self.focus_targets: Dict[str, AttentionFocus] = {}
        self.primary_focus: Optional[str] = None
        self.secondary_foci: Set[str] = set()
        
        # Initialize context tracking
        self.contexts: Dict[str, AttentionContext] = {}
        self.active_context: Optional[str] = None
        self.context_history: List[str] = []
        self.max_context_history = self.config.get("max_context_history", 10)
        
        # Initialize decay parameters
        self.decay_rate = self.config.get("decay_rate", 0.1)
        self.decay_interval = self.config.get("decay_interval", 5.0)
        self.last_decay = time.time()
        
        # Initialize refresh parameters
        self.refresh_interval = self.config.get("refresh_interval", 60.0)  # 1 minute
        self.last_refresh = time.time()
        self.refresh_threshold = self.config.get("refresh_threshold", 0.3)
        
        # Initialize distraction management
        self.distraction_threshold = self.config.get("distraction_threshold", 0.7)
        self.max_distractions_per_cycle = self.config.get("max_distractions_per_cycle", 3)
        self.distraction_filter_strength = self.config.get("distraction_filter_strength", 0.6)
        
        # Initialize context switching parameters
        self.context_switch_threshold = self.config.get("context_switch_threshold", 0.8)
        self.min_context_duration = self.config.get("min_context_duration", 30.0)  # 30 seconds
        self.last_context_switch = time.time()
        
        # Initialize importance/urgency parameters
        self.importance_decay_rate = self.config.get("importance_decay_rate", 0.05)
        self.urgency_growth_rate = self.config.get("urgency_growth_rate", 0.1)
        
        # Initialize utilization tracking
        self.utilization_history: List[ResourceUtilization] = []
        self.max_history_size = self.config.get("max_history_size", 100)
        
        # Initialize lock
        self.lock = asyncio.Lock()
        
        # Create default context
        self._create_default_context()
    
    def _create_default_context(self) -> None:
        """Create the default attention context."""
        default_context = AttentionContext("default", priority=0.5)
        self.contexts["default"] = default_context
        self.active_context = "default"
        self.context_history.append("default")
    
    async def allocate(self, requirements: ResourceRequirements) -> Optional[ResourceAllocation]:
        """
        Allocate resources based on requirements.
        
        Args:
            requirements: The resource requirements
            
        Returns:
            The resource allocation, or None if resources could not be allocated
        """
        async with self.lock:
            # Apply attention decay if needed
            await self._apply_attention_decay()
            
            requested_attention = requirements.attention
            
            # Check if we have enough resources
            if self.allocated_attention + requested_attention > self.total_attention:
                # If request is critical, try to preempt lower priority allocations
                if requirements.priority == ResourcePriority.CRITICAL:
                    freed_attention = await self._preempt_for_critical(requested_attention)
                    if self.allocated_attention - freed_attention + requested_attention > self.total_attention:
                        logger.warning(f"Cannot allocate {requested_attention} attention units even after preemption")
                        return None
                else:
                    logger.warning(f"Cannot allocate {requested_attention} attention units")
                    return None
            
            # Create allocation
            allocation = ResourceAllocation(
                compute=requirements.compute,
                memory=requirements.memory,
                attention=requested_attention,
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
            self.allocated_attention += requested_attention
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Allocated {requested_attention} attention units (ID: {allocation.id})")
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
            self.allocated_attention -= allocation.attention
            del self.allocations[allocation_id]
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Released {allocation.attention} attention units (ID: {allocation_id})")
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
            attention_diff = requirements.attention - old_allocation.attention
            
            # Check if we have enough resources for the update
            if attention_diff > 0 and self.allocated_attention + attention_diff > self.total_attention:
                logger.warning(f"Cannot update allocation {allocation_id}: not enough attention resources")
                return None
            
            # Update allocation
            new_allocation = ResourceAllocation(
                id=allocation_id,
                compute=requirements.compute,
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
            self.allocated_attention += attention_diff
            
            # Update utilization history
            self._update_utilization()
            
            logger.debug(f"Updated allocation {allocation_id}: attention {old_allocation.attention} -> {requirements.attention}")
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
                memory=0.0,  # Not tracked by this manager
                attention=self.allocated_attention / self.total_attention,
                network=0.0,  # Not tracked by this manager
                storage=0.0,  # Not tracked by this manager
                metadata={
                    "total_attention": self.total_attention,
                    "allocated_attention": self.allocated_attention,
                    "active_allocations": len(self.allocations),
                    "primary_focus": self.primary_focus,
                    "secondary_foci": list(self.secondary_foci)
                }
            )
    
    async def focus_attention(self, focus_target: str, priority: ResourcePriority) -> bool:
        """
        Focus attention on a target.
        
        Args:
            focus_target: The target to focus on
            priority: The priority of the focus
            
        Returns:
            True if attention was focused, False otherwise
        """
        async with self.lock:
            # Apply attention decay if needed
            await self._apply_attention_decay()
            
            # Determine allocation based on priority
            allocation_map = {
                ResourcePriority.CRITICAL: 0.8,
                ResourcePriority.HIGH: 0.6,
                ResourcePriority.MEDIUM: 0.4,
                ResourcePriority.LOW: 0.2,
                ResourcePriority.BACKGROUND: 0.1
            }
            
            allocation = allocation_map.get(priority, 0.3)
            
            # Check if target is already in focus
            if focus_target in self.focus_targets:
                focus = self.focus_targets[focus_target]
                
                # Update existing focus
                old_allocation = focus.allocation
                focus.update(allocation)
                focus.priority = priority
                focus.active = True
                
                # Update primary/secondary focus lists
                self._update_focus_lists()
                
                logger.debug(f"Updated attention focus on {focus_target}: {old_allocation} -> {allocation}")
                return True
            
            # Create new focus
            focus = AttentionFocus(focus_target, priority, allocation)
            self.focus_targets[focus_target] = focus
            
            # Update primary/secondary focus lists
            self._update_focus_lists()
            
            logger.debug(f"Created new attention focus on {focus_target} with allocation {allocation}")
            return True
    
    async def get_current_focus(self) -> Dict[str, float]:
        """
        Get the current attention focus.
        
        Returns:
            Dictionary mapping focus targets to attention values
        """
        async with self.lock:
            # Apply attention decay if needed
            await self._apply_attention_decay()
            
            # Build focus map
            focus_map = {
                focus.target: focus.allocation
                for focus in self.focus_targets.values()
                if focus.active
            }
            
            return focus_map
    
    async def optimize(self) -> Dict[str, Any]:
        """
        Optimize attention allocation.
        
        Features:
        - Attention decay and refreshing
        - Context switching optimization
        - Importance and urgency updates
        - Distraction filtering
        - Focus area prioritization
        
        Returns:
            Dictionary with optimization results
        """
        async with self.lock:
            start_time = time.time()
            results = {}
            
            # Apply attention decay
            decay_results = await self._apply_attention_decay()
            results["decay"] = decay_results
            
            # Apply attention refreshing
            refresh_results = await self._refresh_attention()
            results["refresh"] = refresh_results
            
            # Check for expired allocations
            expired_allocations = [
                allocation_id for allocation_id, allocation in self.allocations.items()
                if allocation.expires_at and time.time() > allocation.expires_at
            ]
            
            # Release expired allocations
            for allocation_id in expired_allocations:
                await self.release(allocation_id)
            
            # Remove inactive focus targets
            inactive_targets = [
                target for target, focus in self.focus_targets.items()
                if not focus.active
            ]
            
            for target in inactive_targets:
                # Remove from context if assigned
                focus = self.focus_targets[target]
                if focus.context_name and focus.context_name in self.contexts:
                    self.contexts[focus.context_name].remove_focus(target)
                
                # Remove from focus targets
                del self.focus_targets[target]
            
            # Update importance and urgency
            importance_results = self._update_importance_urgency()
            results["importance_urgency"] = importance_results
            
            # Optimize context switching
            context_results = await self._optimize_context_switching()
            results["context_switching"] = context_results
            
            # Filter distractions
            distraction_results = self._filter_distractions()
            results["distraction_filtering"] = distraction_results
            
            # Update primary/secondary focus lists
            self._update_focus_lists()
            
            # Clean up empty contexts
            empty_contexts = [
                context_name for context_name, context in self.contexts.items()
                if not context.focus_targets and context_name != "default"
            ]
            
            for context_name in empty_contexts:
                del self.contexts[context_name]
            
            results["empty_contexts_removed"] = len(empty_contexts)
            results["expired_allocations_released"] = len(expired_allocations)
            results["inactive_targets_removed"] = len(inactive_targets)
            results["current_utilization"] = self.allocated_attention / self.total_attention
            results["active_context"] = self.active_context
            results["execution_time"] = time.time() - start_time
            
            return results
    
    def _update_utilization(self) -> None:
        """Update the utilization history."""
        utilization = ResourceUtilization(
            compute=0.0,  # Not tracked by this manager
            memory=0.0,  # Not tracked by this manager
            attention=self.allocated_attention / self.total_attention,
            network=0.0,  # Not tracked by this manager
            storage=0.0  # Not tracked by this manager
        )
        
        self.utilization_history.append(utilization)
        
        # Trim history if needed
        if len(self.utilization_history) > self.max_history_size:
            self.utilization_history = self.utilization_history[-self.max_history_size:]
    
    def _update_focus_lists(self) -> None:
        """Update the primary and secondary focus lists."""
        # Sort focus targets by allocation (highest first)
        sorted_targets = sorted(
            self.focus_targets.values(),
            key=lambda x: (x.allocation, x.priority.value),
            reverse=True
        )
        
        # Filter out inactive targets
        active_targets = [focus for focus in sorted_targets if focus.active]
        
        # Update primary focus
        self.primary_focus = active_targets[0].target if active_targets else None
        
        # Update secondary foci (next 2-5 targets)
        secondary_count = min(5, len(active_targets) - 1)
        self.secondary_foci = {
            focus.target for focus in active_targets[1:1+secondary_count]
        }
    
    async def _apply_attention_decay(self) -> int:
        """
        Apply decay to attention focus targets.
        
        Returns:
            Number of targets that were decayed
        """
        current_time = time.time()
        
        # Check if decay should be applied
        if current_time - self.last_decay < self.decay_interval:
            return 0
        
        decayed_count = 0
        
        # Apply decay to all focus targets
        for focus in self.focus_targets.values():
            # Skip recently updated targets
            if current_time - focus.last_updated < self.decay_interval:
                continue
            
            # Apply decay
            old_allocation = focus.allocation
            focus.allocation *= (1.0 - self.decay_rate)
            
            # Mark as inactive if allocation is too low
            if focus.allocation < 0.05:
                focus.active = False
                decayed_count += 1
        
        # Update primary/secondary focus lists
        self._update_focus_lists()
        
        # Update last decay time
        self.last_decay = current_time
        
        return decayed_count
    
    async def _preempt_for_critical(self, required_attention: float) -> float:
        """
        Preempt lower priority allocations to make room for a critical allocation.
        
        Args:
            required_attention: The required attention units
            
        Returns:
            The amount of attention units freed
        """
        # Sort allocations by priority (lowest first)
        sorted_allocations = sorted(
            self.allocations.items(),
            key=lambda x: ResourcePriority(x[1].metadata.get("priority", "medium")).value
        )
        
        freed_attention = 0.0
        preempted_ids = []
        
        # Preempt allocations until we have enough resources
        for allocation_id, allocation in sorted_allocations:
            # Skip high priority and critical allocations
            if allocation.metadata.get("priority") in [ResourcePriority.HIGH.value, ResourcePriority.CRITICAL.value]:
                continue
            
            preempted_ids.append(allocation_id)
            freed_attention += allocation.attention
            
            if freed_attention >= required_attention:
                break
        
        # Release preempted allocations
        for allocation_id in preempted_ids:
            await self.release(allocation_id)
        
        logger.info(f"Preempted {len(preempted_ids)} allocations to free {freed_attention} attention units")
        return freed_attention
    
    async def create_context(self, name: str, priority: float = 1.0) -> bool:
        """
        Create a new attention context.
        
        Args:
            name: The name of the context
            priority: The priority of the context
            
        Returns:
            True if the context was created, False if it already exists
        """
        async with self.lock:
            if name in self.contexts:
                logger.warning(f"Context {name} already exists")
                return False
            
            self.contexts[name] = AttentionContext(name, priority)
            logger.debug(f"Created attention context {name} with priority {priority}")
            return True
    
    async def switch_context(self, context_name: str) -> bool:
        """
        Switch to a different attention context.
        
        Args:
            context_name: The name of the context to switch to
            
        Returns:
            True if the context was switched, False otherwise
        """
        async with self.lock:
            if context_name not in self.contexts:
                logger.warning(f"Context {context_name} not found")
                return False
            
            # Skip if already in this context
            if self.active_context == context_name:
                return True
            
            # Check if enough time has passed since last switch
            current_time = time.time()
            if current_time - self.last_context_switch < self.min_context_duration:
                logger.debug(f"Not switching context: minimum duration not reached")
                return False
            
            # Update context history
            if self.active_context:
                self.context_history.append(self.active_context)
                if len(self.context_history) > self.max_context_history:
                    self.context_history = self.context_history[-self.max_context_history:]
            
            # Switch context
            old_context = self.active_context
            self.active_context = context_name
            self.last_context_switch = current_time
            
            # Update context
            self.contexts[context_name].update()
            
            logger.info(f"Switched attention context: {old_context} -> {context_name}")
            return True
    
    async def focus_attention_in_context(self, context_name: str, focus_target: str,
                                        priority: ResourcePriority, importance: float = 0.5,
                                        urgency: float = 0.5) -> bool:
        """
        Focus attention on a target within a specific context.
        
        Args:
            context_name: The name of the context
            focus_target: The target to focus on
            priority: The priority of the focus
            importance: The importance of the target (0.0 to 1.0)
            urgency: The urgency of the target (0.0 to 1.0)
            
        Returns:
            True if attention was focused, False otherwise
        """
        async with self.lock:
            # Create context if it doesn't exist
            if context_name not in self.contexts:
                await self.create_context(context_name)
            
            # Get context
            context = self.contexts[context_name]
            
            # Determine allocation based on priority
            allocation_map = {
                ResourcePriority.CRITICAL: 0.8,
                ResourcePriority.HIGH: 0.6,
                ResourcePriority.MEDIUM: 0.4,
                ResourcePriority.LOW: 0.2,
                ResourcePriority.BACKGROUND: 0.1
            }
            
            base_allocation = allocation_map.get(priority, 0.3)
            
            # Adjust allocation based on importance and urgency
            adjusted_allocation = base_allocation * (0.5 + 0.25 * importance + 0.25 * urgency)
            
            # Check if target is already in focus
            if focus_target in self.focus_targets:
                focus = self.focus_targets[focus_target]
                
                # Update existing focus
                old_allocation = focus.allocation
                focus.update(adjusted_allocation)
                focus.priority = priority
                focus.importance = importance
                focus.urgency = urgency
                focus.active = True
                
                # Update context assignment if needed
                if focus.context_name != context_name:
                    # Remove from old context if assigned
                    if focus.context_name and focus.context_name in self.contexts:
                        self.contexts[focus.context_name].remove_focus(focus_target)
                    
                    # Add to new context
                    focus.context_name = context_name
                    context.add_focus(focus)
                
                # Update primary/secondary focus lists
                self._update_focus_lists()
                
                logger.debug(f"Updated attention focus on {focus_target} in context {context_name}: {old_allocation} -> {adjusted_allocation}")
                return True
            
            # Create new focus
            focus = AttentionFocus(focus_target, priority, adjusted_allocation, context_name)
            focus.importance = importance
            focus.urgency = urgency
            
            # Add to focus targets
            self.focus_targets[focus_target] = focus
            
            # Add to context
            context.add_focus(focus)
            
            # Update primary/secondary focus lists
            self._update_focus_lists()
            
            logger.debug(f"Created new attention focus on {focus_target} in context {context_name} with allocation {adjusted_allocation}")
            return True
    
    async def get_context_foci(self, context_name: str) -> Dict[str, float]:
        """
        Get the attention foci in a specific context.
        
        Args:
            context_name: The name of the context
            
        Returns:
            Dictionary mapping focus targets to attention values
        """
        async with self.lock:
            if context_name not in self.contexts:
                return {}
            
            context = self.contexts[context_name]
            
            # Build focus map
            focus_map = {
                focus.target: focus.allocation
                for focus in context.get_active_foci()
            }
            
            return focus_map
    
    async def _refresh_attention(self) -> Dict[str, Any]:
        """
        Refresh attention for important focus targets.
        
        Returns:
            Dictionary with refresh statistics
        """
        current_time = time.time()
        
        # Check if refresh should be applied
        if current_time - self.last_refresh < self.refresh_interval:
            return {"status": "skipped", "reason": "interval_not_reached"}
        
        # Get focus targets sorted by effective priority
        sorted_foci = sorted(
            self.focus_targets.values(),
            key=lambda f: f.get_effective_priority(),
            reverse=True
        )
        
        # Limit to active foci
        active_foci = [focus for focus in sorted_foci if focus.active]
        
        # Refresh top foci
        refreshed_count = 0
        for focus in active_foci[:3]:  # Refresh top 3 foci
            # Skip recently updated foci
            if current_time - focus.last_updated < self.refresh_interval / 2:
                continue
                
            # Check if focus needs refreshing
            if focus.allocation < self.refresh_threshold:
                # Calculate refresh amount
                refresh_amount = min(0.2, 1.0 - focus.allocation)
                
                # Apply refresh
                old_allocation = focus.allocation
                focus.allocation += refresh_amount
                focus.update(focus.allocation)  # This will update last_updated
                
                refreshed_count += 1
                
                logger.debug(f"Refreshed attention for {focus.target}: {old_allocation} -> {focus.allocation}")
        
        # Update last refresh time
        self.last_refresh = current_time
        
        return {
            "refreshed_foci": refreshed_count,
            "total_active_foci": len(active_foci)
        }
    
    def _update_importance_urgency(self) -> Dict[str, Any]:
        """
        Update importance and urgency values for all focus targets.
        
        Returns:
            Dictionary with update statistics
        """
        current_time = time.time()
        
        # Track statistics
        importance_decreased = 0
        urgency_increased = 0
        
        for focus in self.focus_targets.values():
            if not focus.active:
                continue
                
            # Decrease importance over time
            old_importance = focus.importance
            focus.importance = max(0.1, focus.importance * (1.0 - self.importance_decay_rate))
            
            if focus.importance < old_importance:
                importance_decreased += 1
            
            # Increase urgency over time for high priority targets
            if focus.priority in [ResourcePriority.HIGH, ResourcePriority.CRITICAL]:
                old_urgency = focus.urgency
                focus.urgency = min(1.0, focus.urgency + self.urgency_growth_rate * (current_time - focus.last_updated) / 3600)
                
                if focus.urgency > old_urgency:
                    urgency_increased += 1
        
        return {
            "importance_decreased": importance_decreased,
            "urgency_increased": urgency_increased
        }
    
    async def _optimize_context_switching(self) -> Dict[str, Any]:
        """
        Optimize context switching based on context scores.
        
        Returns:
            Dictionary with context switching statistics
        """
        # Skip if no contexts
        if not self.contexts:
            return {"status": "skipped", "reason": "no_contexts"}
        
        current_time = time.time()
        
        # Check if enough time has passed since last switch
        if current_time - self.last_context_switch < self.min_context_duration:
            return {
                "status": "skipped",
                "reason": "min_duration_not_reached",
                "time_since_last_switch": current_time - self.last_context_switch
            }
        
        # Calculate context scores
        context_scores = {
            name: context.get_context_score()
            for name, context in self.contexts.items()
        }
        
        # Get current context score
        current_context_score = context_scores.get(self.active_context, 0.0)
        
        # Find highest scoring context
        best_context = max(context_scores.items(), key=lambda x: x[1])
        best_context_name, best_context_score = best_context
        
        # Check if switch is worthwhile
        if (best_context_name != self.active_context and
            best_context_score > current_context_score * self.context_switch_threshold):
            # Switch context
            await self.switch_context(best_context_name)
            
            return {
                "status": "switched",
                "from_context": self.active_context,
                "to_context": best_context_name,
                "from_score": current_context_score,
                "to_score": best_context_score
            }
        
        return {
            "status": "maintained",
            "current_context": self.active_context,
            "current_score": current_context_score,
            "best_alternative": best_context_name,
            "best_score": best_context_score
        }
    
    def _filter_distractions(self) -> Dict[str, Any]:
        """
        Filter out distractions from attention focus.
        
        Returns:
            Dictionary with distraction filtering statistics
        """
        # Skip if no focus targets
        if not self.focus_targets:
            return {"status": "skipped", "reason": "no_focus_targets"}
        
        # Get primary focus
        if not self.primary_focus or self.primary_focus not in self.focus_targets:
            return {"status": "skipped", "reason": "no_primary_focus"}
        
        primary = self.focus_targets[self.primary_focus]
        
        # Calculate distraction threshold based on primary focus
        threshold = self.distraction_threshold * primary.distraction_resistance
        
        # Identify potential distractions
        distractions = []
        
        for target, focus in self.focus_targets.items():
            # Skip primary focus and inactive foci
            if target == self.primary_focus or not focus.active:
                continue
                
            # Skip foci in the same context as primary
            if primary.context_name and primary.context_name == focus.context_name:
                continue
                
            # Calculate distraction score
            effective_priority = focus.get_effective_priority()
            distraction_score = effective_priority / primary.get_effective_priority()
            
            # Check if it's a distraction
            if distraction_score < threshold:
                distractions.append((target, focus, distraction_score))
        
        # Sort distractions by score (lowest first)
        distractions.sort(key=lambda x: x[2])
        
        # Filter out distractions (reduce their allocation)
        filtered_count = 0
        for target, focus, score in distractions[:self.max_distractions_per_cycle]:
            # Calculate reduction factor
            reduction = self.distraction_filter_strength * (1.0 - score / threshold)
            
            # Apply reduction
            old_allocation = focus.allocation
            focus.allocation *= (1.0 - reduction)
            
            filtered_count += 1
            
            logger.debug(f"Filtered distraction {target}: {old_allocation} -> {focus.allocation}")
        
        return {
            "distractions_identified": len(distractions),
            "distractions_filtered": filtered_count
        }