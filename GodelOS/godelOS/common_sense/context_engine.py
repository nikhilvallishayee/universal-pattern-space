"""
Module 9.2: Context Engine (CE)

This module manages the current context of reasoning and interaction,
tracks and updates contextual variables, implements context switching mechanisms,
provides methods for context-aware operations, and integrates with the KR System
for context representation.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union
import time
import json
import uuid
import copy
from dataclasses import dataclass, field
from enum import Enum, auto

from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface

# Configure logging
logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Enumeration of different context types."""
    TEMPORAL = auto()  # Time-based context
    SPATIAL = auto()   # Location-based context
    THEMATIC = auto()  # Topic or theme-based context
    TASK = auto()      # Task or goal-oriented context
    DIALOGUE = auto()  # Conversation or dialogue context
    USER = auto()      # User-specific context
    SYSTEM = auto()    # System state context
    CUSTOM = auto()    # User-defined context type


@dataclass
class ContextVariable:
    """Represents a variable within a context."""
    name: str
    value: Any
    type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.type,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextVariable':
        """Create from dictionary representation."""
        return cls(
            name=data["name"],
            value=data["value"],
            type=data["type"],
            metadata=data.get("metadata", {}),
            timestamp=data.get("timestamp", time.time())
        )


@dataclass
class Context:
    """Represents a context with a set of variables and metadata."""
    id: str
    name: str
    type: ContextType
    variables: Dict[str, ContextVariable] = field(default_factory=dict)
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def add_variable(self, variable: ContextVariable) -> None:
        """Add a variable to the context."""
        self.variables[variable.name] = variable
        self.updated_at = time.time()
    
    def get_variable(self, name: str) -> Optional[ContextVariable]:
        """Get a variable by name."""
        return self.variables.get(name)
    
    def update_variable(self, name: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update a variable's value and metadata."""
        if name in self.variables:
            var = self.variables[name]
            var.value = value
            var.timestamp = time.time()
            if metadata:
                var.metadata.update(metadata)
            self.updated_at = time.time()
            return True
        return False
    
    def remove_variable(self, name: str) -> bool:
        """Remove a variable by name."""
        if name in self.variables:
            del self.variables[name]
            self.updated_at = time.time()
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.name,
            "variables": {k: v.to_dict() for k, v in self.variables.items()},
            "parent_id": self.parent_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Context':
        """Create from dictionary representation."""
        context = cls(
            id=data["id"],
            name=data["name"],
            type=ContextType[data["type"]],
            parent_id=data.get("parent_id"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time())
        )
        
        for var_name, var_data in data.get("variables", {}).items():
            context.variables[var_name] = ContextVariable.from_dict(var_data)
        
        return context


class ContextEngine:
    """Manages contexts for reasoning and interaction.
    
    This class is responsible for tracking and updating the current context,
    implementing context switching, and providing methods for context-aware operations.
    """
    
    def __init__(self, knowledge_store: Optional[KnowledgeStoreInterface] = None):
        """Initialize the Context Engine.
        
        Args:
            knowledge_store: Optional knowledge store for context representation
        """
        self.knowledge_store = knowledge_store
        self.contexts: Dict[str, Context] = {}
        self.active_context_id: Optional[str] = None
        self.context_history: List[str] = []  # History of active context IDs
        self.max_history_length: int = 100
    
    def create_context(self, name: str, context_type: ContextType, 
                      parent_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None,
                      variables: Optional[Dict[str, Any]] = None) -> Context:
        """Create a new context.
        
        Args:
            name: Name of the context
            context_type: Type of the context
            parent_id: Optional ID of the parent context
            metadata: Optional metadata for the context
            variables: Optional initial variables for the context
            
        Returns:
            The newly created context
        """
        context_id = str(uuid.uuid4())
        context = Context(
            id=context_id,
            name=name,
            type=context_type,
            parent_id=parent_id,
            metadata=metadata or {}
        )
        
        # Add initial variables if provided
        if variables:
            for var_name, var_value in variables.items():
                if isinstance(var_value, dict) and "type" in var_value:
                    # If a complete variable specification is provided
                    var_type = var_value.get("type", "unknown")
                    var_metadata = var_value.get("metadata", {})
                    actual_value = var_value.get("value")
                    
                    context.add_variable(ContextVariable(
                        name=var_name,
                        value=actual_value,
                        type=var_type,
                        metadata=var_metadata
                    ))
                else:
                    # If only a value is provided, infer the type
                    var_type = type(var_value).__name__
                    context.add_variable(ContextVariable(
                        name=var_name,
                        value=var_value,
                        type=var_type
                    ))
        
        self.contexts[context_id] = context
        
        # Integrate with knowledge store if available
        if self.knowledge_store:
            self._integrate_context_with_kr(context)
        
        return context
    
    def get_context(self, context_id: str) -> Optional[Context]:
        """Get a context by ID.
        
        Args:
            context_id: ID of the context to retrieve
            
        Returns:
            The context if found, None otherwise
        """
        return self.contexts.get(context_id)
    
    def update_context(self, context_id: str, 
                      metadata: Optional[Dict[str, Any]] = None,
                      variables: Optional[Dict[str, Any]] = None) -> bool:
        """Update a context's metadata and variables.
        
        Args:
            context_id: ID of the context to update
            metadata: Optional metadata to update
            variables: Optional variables to update
            
        Returns:
            True if the context was updated, False otherwise
        """
        context = self.get_context(context_id)
        if not context:
            return False
        
        # Update metadata if provided
        if metadata:
            context.metadata.update(metadata)
        
        # Update variables if provided
        if variables:
            for var_name, var_value in variables.items():
                if isinstance(var_value, dict) and "type" in var_value:
                    # If a complete variable specification is provided
                    var_type = var_value.get("type", "unknown")
                    var_metadata = var_value.get("metadata", {})
                    actual_value = var_value.get("value")
                    
                    if var_name in context.variables:
                        context.update_variable(var_name, actual_value, var_metadata)
                    else:
                        context.add_variable(ContextVariable(
                            name=var_name,
                            value=actual_value,
                            type=var_type,
                            metadata=var_metadata
                        ))
                else:
                    # If only a value is provided
                    if var_name in context.variables:
                        context.update_variable(var_name, var_value)
                    else:
                        var_type = type(var_value).__name__
                        context.add_variable(ContextVariable(
                            name=var_name,
                            value=var_value,
                            type=var_type
                        ))
        
        context.updated_at = time.time()
        
        # Update in knowledge store if available
        if self.knowledge_store:
            self._update_context_in_kr(context)
        
        return True
    
    def delete_context(self, context_id: str) -> bool:
        """Delete a context by ID.
        
        Args:
            context_id: ID of the context to delete
            
        Returns:
            True if the context was deleted, False otherwise
        """
        if context_id not in self.contexts:
            return False
        
        # If this is the active context, deactivate it
        if self.active_context_id == context_id:
            self.active_context_id = None
        
        # Remove from history
        while context_id in self.context_history:
            self.context_history.remove(context_id)
        
        # Remove from knowledge store if available
        if self.knowledge_store:
            self._remove_context_from_kr(context_id)
        
        # Delete the context
        del self.contexts[context_id]
        
        return True
    
    def set_active_context(self, context_id: str) -> bool:
        """Set the active context.
        
        Args:
            context_id: ID of the context to set as active
            
        Returns:
            True if the context was set as active, False otherwise
        """
        if context_id not in self.contexts:
            return False
        
        # Add the previous active context to history if it exists
        if self.active_context_id:
            self.context_history.append(self.active_context_id)
            # Trim history if needed
            if len(self.context_history) > self.max_history_length:
                self.context_history = self.context_history[-self.max_history_length:]
        
        self.active_context_id = context_id
        return True
    
    def get_active_context(self) -> Optional[Context]:
        """Get the currently active context.
        
        Returns:
            The active context if one is set, None otherwise
        """
        if self.active_context_id:
            return self.get_context(self.active_context_id)
        return None
    
    def get_variable(self, name: str, context_id: Optional[str] = None) -> Optional[Any]:
        """Get a variable's value from a context.
        
        Args:
            name: Name of the variable
            context_id: Optional ID of the context to get the variable from.
                        If None, use the active context.
            
        Returns:
            The variable's value if found, None otherwise
        """
        # Determine which context to use
        ctx_id = context_id or self.active_context_id
        if not ctx_id:
            return None
        
        context = self.get_context(ctx_id)
        if not context:
            return None
        
        # Get the variable
        var = context.get_variable(name)
        if var:
            return var.value
        
        # If not found and the context has a parent, try the parent
        if context.parent_id:
            return self.get_variable(name, context.parent_id)
        
        return None
    
    def set_variable(self, name: str, value: Any, 
                    var_type: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None,
                    context_id: Optional[str] = None) -> bool:
        """Set a variable in a context.
        
        Args:
            name: Name of the variable
            value: Value to set
            var_type: Optional type of the variable. If None, infer from value.
            metadata: Optional metadata for the variable
            context_id: Optional ID of the context to set the variable in.
                        If None, use the active context.
            
        Returns:
            True if the variable was set, False otherwise
        """
        # Determine which context to use
        ctx_id = context_id or self.active_context_id
        if not ctx_id:
            return False
        
        context = self.get_context(ctx_id)
        if not context:
            return False
        
        # Determine the variable type if not provided
        if var_type is None:
            var_type = type(value).__name__
        
        # Set or update the variable
        if name in context.variables:
            return context.update_variable(name, value, metadata)
        else:
            context.add_variable(ContextVariable(
                name=name,
                value=value,
                type=var_type,
                metadata=metadata or {}
            ))
            return True
    
    def remove_variable(self, name: str, context_id: Optional[str] = None) -> bool:
        """Remove a variable from a context.
        
        Args:
            name: Name of the variable
            context_id: Optional ID of the context to remove the variable from.
                        If None, use the active context.
            
        Returns:
            True if the variable was removed, False otherwise
        """
        # Determine which context to use
        ctx_id = context_id or self.active_context_id
        if not ctx_id:
            return False
        
        context = self.get_context(ctx_id)
        if not context:
            return False
        
        return context.remove_variable(name)
    
    def get_context_hierarchy(self, context_id: Optional[str] = None) -> List[Context]:
        """Get a context and its ancestors in order from child to parent.
        
        Args:
            context_id: Optional ID of the context to start from.
                        If None, use the active context.
            
        Returns:
            List of contexts in the hierarchy, from child to parent
        """
        # Determine which context to start from
        ctx_id = context_id or self.active_context_id
        if not ctx_id:
            return []
        
        hierarchy = []
        current_id = ctx_id
        
        # Traverse the hierarchy
        while current_id:
            context = self.get_context(current_id)
            if not context:
                break
            
            hierarchy.append(context)
            current_id = context.parent_id
        
        return hierarchy
    
    def merge_contexts(self, source_id: str, target_id: str, 
                      override: bool = False) -> bool:
        """Merge variables from a source context into a target context.
        
        Args:
            source_id: ID of the source context
            target_id: ID of the target context
            override: If True, override existing variables in the target
            
        Returns:
            True if the merge was successful, False otherwise
        """
        source = self.get_context(source_id)
        target = self.get_context(target_id)
        
        if not source or not target:
            return False
        
        # Merge variables
        for var_name, var in source.variables.items():
            if var_name not in target.variables or override:
                target.add_variable(copy.deepcopy(var))
        
        # Update target context
        target.updated_at = time.time()
        
        # Update in knowledge store if available
        if self.knowledge_store:
            self._update_context_in_kr(target)
        
        return True
    
    def derive_context(self, parent_id: str, name: str, 
                      context_type: Optional[ContextType] = None,
                      metadata: Optional[Dict[str, Any]] = None,
                      inherit_variables: bool = True) -> Optional[Context]:
        """Create a new context derived from a parent context.
        
        Args:
            parent_id: ID of the parent context
            name: Name of the new context
            context_type: Optional type of the new context. If None, use parent's type.
            metadata: Optional metadata for the new context
            inherit_variables: If True, inherit variables from the parent
            
        Returns:
            The newly created context, or None if the parent doesn't exist
        """
        parent = self.get_context(parent_id)
        if not parent:
            return None
        
        # Use parent's type if not specified
        if context_type is None:
            context_type = parent.type
        
        # Create the new context
        new_context = self.create_context(
            name=name,
            context_type=context_type,
            parent_id=parent_id,
            metadata=metadata
        )
        
        # Inherit variables if requested
        if inherit_variables:
            for var_name, var in parent.variables.items():
                new_context.add_variable(copy.deepcopy(var))
        
        return new_context
    
    def save_contexts(self, file_path: str) -> bool:
        """Save all contexts to a file.
        
        Args:
            file_path: Path to save the contexts to
            
        Returns:
            True if the contexts were saved, False otherwise
        """
        try:
            data = {
                "contexts": {ctx_id: ctx.to_dict() for ctx_id, ctx in self.contexts.items()},
                "active_context_id": self.active_context_id,
                "context_history": self.context_history
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving contexts: {e}")
            return False
    
    def load_contexts(self, file_path: str) -> bool:
        """Load contexts from a file.
        
        Args:
            file_path: Path to load the contexts from
            
        Returns:
            True if the contexts were loaded, False otherwise
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Clear existing contexts
            self.contexts = {}
            
            # Load contexts
            for ctx_id, ctx_data in data.get("contexts", {}).items():
                self.contexts[ctx_id] = Context.from_dict(ctx_data)
            
            # Set active context and history
            self.active_context_id = data.get("active_context_id")
            self.context_history = data.get("context_history", [])
            
            return True
        except Exception as e:
            logger.error(f"Error loading contexts: {e}")
            return False
    
    def _integrate_context_with_kr(self, context: Context) -> None:
        """Integrate a context with the knowledge representation system.
        
        Args:
            context: The context to integrate
        """
        if not self.knowledge_store:
            return
        
        try:
            # Add the context as an entity
            self.knowledge_store.add_entity(f"context:{context.id}")
            
            # Add context properties
            self.knowledge_store.add_property(f"context:{context.id}", "name", context.name)
            self.knowledge_store.add_property(f"context:{context.id}", "type", context.type.name)
            
            if context.parent_id:
                self.knowledge_store.add_relation(
                    f"context:{context.id}", "has_parent", f"context:{context.parent_id}"
                )
            
            # Add context variables
            for var_name, var in context.variables.items():
                var_id = f"context_var:{context.id}:{var_name}"
                self.knowledge_store.add_entity(var_id)
                self.knowledge_store.add_relation(f"context:{context.id}", "has_variable", var_id)
                self.knowledge_store.add_property(var_id, "name", var_name)
                self.knowledge_store.add_property(var_id, "type", var.type)
                
                # Store the value as a property if it's a primitive type
                if isinstance(var.value, (str, int, float, bool)) or var.value is None:
                    self.knowledge_store.add_property(var_id, "value", var.value)
        
        except Exception as e:
            logger.warning(f"Error integrating context with knowledge store: {e}")
    
    def _update_context_in_kr(self, context: Context) -> None:
        """Update a context in the knowledge representation system.
        
        Args:
            context: The context to update
        """
        if not self.knowledge_store:
            return
        
        # For simplicity, we'll just remove and re-add the context
        self._remove_context_from_kr(context.id)
        self._integrate_context_with_kr(context)
    
    def _remove_context_from_kr(self, context_id: str) -> None:
        """Remove a context from the knowledge representation system.
        
        Args:
            context_id: ID of the context to remove
        """
        if not self.knowledge_store:
            return
        
        try:
            # Remove the context entity and all its related entities
            self.knowledge_store.remove_entity(f"context:{context_id}")
            
            # Find and remove all variable entities for this context
            # This would depend on the specific implementation of the knowledge store
            # For now, we'll assume there's a way to query and remove entities by pattern
            var_pattern = f"context_var:{context_id}:"
            # This is a placeholder for a method that would remove entities by pattern
            # self.knowledge_store.remove_entities_by_pattern(var_pattern)
        
        except Exception as e:
            logger.warning(f"Error removing context from knowledge store: {e}")
    
    def get_contexts_by_type(self, context_type: ContextType) -> List[Context]:
        """Get all contexts of a specific type.
        
        Args:
            context_type: Type of contexts to retrieve
            
        Returns:
            List of contexts of the specified type
        """
        return [ctx for ctx in self.contexts.values() if ctx.type == context_type]
    
    def get_contexts_by_variable(self, var_name: str, var_value: Optional[Any] = None) -> List[Context]:
        """Get all contexts that have a specific variable.
        
        Args:
            var_name: Name of the variable to look for
            var_value: Optional value to match. If None, match any value.
            
        Returns:
            List of contexts that have the specified variable
        """
        result = []
        
        for context in self.contexts.values():
            var = context.get_variable(var_name)
            if var:
                if var_value is None or var.value == var_value:
                    result.append(context)
        
        return result
    
    def switch_context(self, context_id: str) -> bool:
        """Switch the active context to a different context.
        
        Args:
            context_id: ID of the context to switch to
            
        Returns:
            True if the switch was successful, False otherwise
        """
        return self.set_active_context(context_id)
    
    def revert_context(self) -> bool:
        """Revert to the previous active context.
        
        Returns:
            True if the revert was successful, False otherwise
        """
        if not self.context_history:
            return False
        
        prev_context_id = self.context_history.pop()
        return self.set_active_context(prev_context_id)
    
    def get_context_snapshot(self, context_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a snapshot of all variables in a context and its parents.
        
        Args:
            context_id: Optional ID of the context to get a snapshot of.
                        If None, use the active context.
            
        Returns:
            Dictionary mapping variable names to their values
        """
        # Get the context hierarchy
        hierarchy = self.get_context_hierarchy(context_id)
        
        # Build the snapshot from parent to child (so child values override parent values)
        snapshot = {}
        for context in reversed(hierarchy):
            for var_name, var in context.variables.items():
                snapshot[var_name] = var.value
        
        return snapshot
    
    def clear(self) -> None:
        """Clear all contexts and reset the engine."""
        self.contexts = {}
        self.active_context_id = None
        self.context_history = []