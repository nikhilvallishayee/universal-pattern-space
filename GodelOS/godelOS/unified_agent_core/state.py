"""
UnifiedState Implementation for GodelOS

This module implements the UnifiedState class, which maintains the global state
of the UnifiedAgentCore system, including interaction context, cognitive context,
and resource state.
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class StateType(Enum):
    """Enum representing different types of state data."""
    INTERACTION = "interaction"
    COGNITIVE = "cognitive"
    RESOURCE = "resource"
    GLOBAL = "global"


@dataclass
class AttentionFocus:
    """Class representing the current focus of attention in the system."""
    primary_focus: str
    secondary_foci: List[str] = field(default_factory=list)
    focus_strength: float = 1.0  # 0.0 to 1.0
    last_updated: float = field(default_factory=time.time)


@dataclass
class Goal:
    """Class representing a goal in the system."""
    id: str
    description: str
    priority: float  # 0.0 to 1.0
    status: str  # "active", "completed", "failed", etc.
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    parent_goal_id: Optional[str] = None
    subgoal_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractionContext:
    """Class representing the context of interactions in the system."""
    current_interaction_id: Optional[str] = None
    interaction_history: List[str] = field(default_factory=list)
    active_protocols: Dict[str, Any] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)


@dataclass
class CognitiveContext:
    """Class representing the cognitive context of the system."""
    active_thoughts: List[str] = field(default_factory=list)
    current_reflection_id: Optional[str] = None
    cognitive_load: float = 0.0  # 0.0 to 1.0
    last_updated: float = field(default_factory=time.time)


@dataclass
class ResourceState:
    """Class representing the state of system resources."""
    compute_utilization: float = 0.0  # 0.0 to 1.0
    memory_utilization: float = 0.0  # 0.0 to 1.0
    attention_allocation: Dict[str, float] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)


@dataclass
class GlobalState:
    """Class representing the global state of the system."""
    system_mode: str = "normal"  # "normal", "maintenance", "emergency", etc.
    startup_time: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    metrics: Dict[str, Any] = field(default_factory=dict)


class UnifiedState:
    """
    UnifiedState for GodelOS.
    
    The UnifiedState maintains the global state of the UnifiedAgentCore system,
    including interaction context, cognitive context, and resource state.
    """
    
    def __init__(self):
        """Initialize the unified state."""
        self._lock = threading.RLock()
        
        # Initialize state components
        self.interaction_context = InteractionContext()
        self.cognitive_context = CognitiveContext()
        self.resource_state = ResourceState()
        self.global_state = GlobalState()
        self.attention_focus = AttentionFocus(primary_focus="idle")
        self.active_goals: Dict[str, Goal] = {}
        
        # State change subscribers
        self.state_change_subscribers: Dict[StateType, List[callable]] = {
            StateType.INTERACTION: [],
            StateType.COGNITIVE: [],
            StateType.RESOURCE: [],
            StateType.GLOBAL: []
        }
    
    async def initialize(self) -> bool:
        """
        Initialize the unified state.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            with self._lock:
                # Reset state components to initial values
                self.interaction_context = InteractionContext()
                self.cognitive_context = CognitiveContext()
                self.resource_state = ResourceState()
                self.global_state = GlobalState()
                self.attention_focus = AttentionFocus(primary_focus="idle")
                self.active_goals = {}
            
            logger.info("UnifiedState initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing UnifiedState: {e}")
            return False
    
    def update_interaction_context(self, updates: Dict[str, Any]) -> None:
        """
        Update the interaction context.
        
        Args:
            updates: Dictionary of updates to apply to the interaction context
        """
        with self._lock:
            for key, value in updates.items():
                if hasattr(self.interaction_context, key):
                    setattr(self.interaction_context, key, value)
            
            self.interaction_context.last_updated = time.time()
            self._notify_state_change(StateType.INTERACTION)
    
    def update_cognitive_context(self, updates: Dict[str, Any]) -> None:
        """
        Update the cognitive context.
        
        Args:
            updates: Dictionary of updates to apply to the cognitive context
        """
        with self._lock:
            for key, value in updates.items():
                if hasattr(self.cognitive_context, key):
                    setattr(self.cognitive_context, key, value)
            
            self.cognitive_context.last_updated = time.time()
            self._notify_state_change(StateType.COGNITIVE)
    
    def update_resource_state(self, updates: Dict[str, Any]) -> None:
        """
        Update the resource state.
        
        Args:
            updates: Dictionary of updates to apply to the resource state
        """
        with self._lock:
            for key, value in updates.items():
                if hasattr(self.resource_state, key):
                    setattr(self.resource_state, key, value)
            
            self.resource_state.last_updated = time.time()
            self._notify_state_change(StateType.RESOURCE)
    
    def update_global_state(self, updates: Dict[str, Any]) -> None:
        """
        Update the global state.
        
        Args:
            updates: Dictionary of updates to apply to the global state
        """
        with self._lock:
            for key, value in updates.items():
                if hasattr(self.global_state, key):
                    setattr(self.global_state, key, value)
            
            self.global_state.last_updated = time.time()
            self._notify_state_change(StateType.GLOBAL)
    
    def update_attention_focus(self, primary_focus: str, secondary_foci: Optional[List[str]] = None, focus_strength: float = 1.0) -> None:
        """
        Update the attention focus.
        
        Args:
            primary_focus: The primary focus of attention
            secondary_foci: Optional list of secondary foci
            focus_strength: The strength of the focus (0.0 to 1.0)
        """
        with self._lock:
            self.attention_focus = AttentionFocus(
                primary_focus=primary_focus,
                secondary_foci=secondary_foci or [],
                focus_strength=focus_strength
            )
            self._notify_state_change(StateType.COGNITIVE)
    
    def add_goal(self, goal: Goal) -> None:
        """
        Add a goal to the active goals.
        
        Args:
            goal: The goal to add
        """
        with self._lock:
            self.active_goals[goal.id] = goal
            
            # If this is a subgoal, update the parent goal
            if goal.parent_goal_id and goal.parent_goal_id in self.active_goals:
                parent_goal = self.active_goals[goal.parent_goal_id]
                if goal.id not in parent_goal.subgoal_ids:
                    parent_goal.subgoal_ids.append(goal.id)
            
            self._notify_state_change(StateType.GLOBAL)
    
    def update_goal(self, goal_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a goal.
        
        Args:
            goal_id: The ID of the goal to update
            updates: Dictionary of updates to apply to the goal
            
        Returns:
            True if the goal was updated, False if the goal was not found
        """
        with self._lock:
            if goal_id not in self.active_goals:
                return False
            
            goal = self.active_goals[goal_id]
            
            for key, value in updates.items():
                if hasattr(goal, key):
                    setattr(goal, key, value)
            
            self._notify_state_change(StateType.GLOBAL)
            return True
    
    def complete_goal(self, goal_id: str) -> bool:
        """
        Mark a goal as completed.
        
        Args:
            goal_id: The ID of the goal to complete
            
        Returns:
            True if the goal was completed, False if the goal was not found
        """
        with self._lock:
            if goal_id not in self.active_goals:
                return False
            
            goal = self.active_goals[goal_id]
            goal.status = "completed"
            goal.completed_at = time.time()
            
            self._notify_state_change(StateType.GLOBAL)
            return True
    
    def get_active_goals(self) -> List[Goal]:
        """
        Get the active goals.
        
        Returns:
            List of active goals
        """
        with self._lock:
            return [goal for goal in self.active_goals.values() if goal.status == "active"]
    
    def get_goal_hierarchy(self) -> Dict[str, Any]:
        """
        Get the goal hierarchy.
        
        Returns:
            Dictionary representing the goal hierarchy
        """
        with self._lock:
            # Find root goals (those without a parent)
            root_goals = [goal for goal in self.active_goals.values() if not goal.parent_goal_id]
            
            # Build hierarchy
            hierarchy = {}
            for root_goal in root_goals:
                hierarchy[root_goal.id] = self._build_goal_subtree(root_goal.id)
            
            return hierarchy
    
    def _build_goal_subtree(self, goal_id: str) -> Dict[str, Any]:
        """
        Build a subtree of the goal hierarchy.
        
        Args:
            goal_id: The ID of the root of the subtree
            
        Returns:
            Dictionary representing the subtree
        """
        goal = self.active_goals[goal_id]
        subtree = {
            "id": goal.id,
            "description": goal.description,
            "status": goal.status,
            "priority": goal.priority
        }
        
        if goal.subgoal_ids:
            subtree["subgoals"] = {}
            for subgoal_id in goal.subgoal_ids:
                if subgoal_id in self.active_goals:
                    subtree["subgoals"][subgoal_id] = self._build_goal_subtree(subgoal_id)
        
        return subtree
    
    def subscribe_to_state_change(self, state_type: StateType, callback: callable) -> None:
        """
        Subscribe to state changes.
        
        Args:
            state_type: The type of state to subscribe to
            callback: Function to call when the state changes
        """
        with self._lock:
            self.state_change_subscribers[state_type].append(callback)
    
    def unsubscribe_from_state_change(self, state_type: StateType, callback: callable) -> bool:
        """
        Unsubscribe from state changes.
        
        Args:
            state_type: The type of state to unsubscribe from
            callback: Function to remove from subscribers
            
        Returns:
            True if the callback was removed, False otherwise
        """
        with self._lock:
            try:
                self.state_change_subscribers[state_type].remove(callback)
                return True
            except ValueError:
                return False
    
    def _notify_state_change(self, state_type: StateType) -> None:
        """
        Notify subscribers of a state change.
        
        Args:
            state_type: The type of state that changed
        """
        # Make a copy of the subscribers to avoid issues if the callback modifies the list
        subscribers = list(self.state_change_subscribers[state_type])
        
        for callback in subscribers:
            try:
                callback(state_type)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the unified state.
        
        Returns:
            Dictionary with status information
        """
        with self._lock:
            return {
                "interaction_context": {
                    "current_interaction_id": self.interaction_context.current_interaction_id,
                    "interaction_history_length": len(self.interaction_context.interaction_history),
                    "active_protocols": list(self.interaction_context.active_protocols.keys()),
                    "last_updated": self.interaction_context.last_updated
                },
                "cognitive_context": {
                    "active_thoughts_count": len(self.cognitive_context.active_thoughts),
                    "current_reflection_id": self.cognitive_context.current_reflection_id,
                    "cognitive_load": self.cognitive_context.cognitive_load,
                    "last_updated": self.cognitive_context.last_updated
                },
                "resource_state": {
                    "compute_utilization": self.resource_state.compute_utilization,
                    "memory_utilization": self.resource_state.memory_utilization,
                    "attention_allocation_count": len(self.resource_state.attention_allocation),
                    "last_updated": self.resource_state.last_updated
                },
                "global_state": {
                    "system_mode": self.global_state.system_mode,
                    "startup_time": self.global_state.startup_time,
                    "uptime": time.time() - self.global_state.startup_time,
                    "last_updated": self.global_state.last_updated
                },
                "attention_focus": {
                    "primary_focus": self.attention_focus.primary_focus,
                    "secondary_foci_count": len(self.attention_focus.secondary_foci),
                    "focus_strength": self.attention_focus.focus_strength,
                    "last_updated": self.attention_focus.last_updated
                },
                "goals": {
                    "active_count": len(self.get_active_goals()),
                    "total_count": len(self.active_goals)
                }
            }