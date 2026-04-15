"""
Module 9.4: Default Reasoning Module (DRM)

This module implements default reasoning mechanisms (non-monotonic reasoning),
handles reasoning with incomplete information, implements defeasible inference,
provides methods for reasoning with defaults and exceptions, and integrates
with the Inference Engine for reasoning.
"""

import logging
from typing import Dict, List, Optional, Any, Set, Tuple, Union, Callable
import time
from enum import Enum, auto
from dataclasses import dataclass, field

from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.coordinator import InferenceCoordinator
from godelOS.common_sense.context_engine import ContextEngine, Context

# Configure logging
logger = logging.getLogger(__name__)


class DefaultType(Enum):
    """Enumeration of different types of defaults."""
    NORMAL = auto()        # Normal defaults (typically true)
    SUPERNORMAL = auto()   # Supernormal defaults (almost always true)
    CONDITIONAL = auto()   # Conditional defaults (true under certain conditions)
    STATISTICAL = auto()   # Statistical defaults (true with some probability)
    DEFEASIBLE = auto()    # Defeasible defaults (can be defeated by exceptions)


@dataclass
class Default:
    """Represents a default rule or assumption."""
    id: str
    prerequisite: str  # Condition that must be true for the default to apply
    justification: str  # Condition that must be consistent for the default to apply
    consequent: str  # What is concluded if the default applies
    type: DefaultType = DefaultType.NORMAL
    priority: int = 0  # Higher priority defaults take precedence
    confidence: float = 0.8  # Confidence in the default (0.0 to 1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "prerequisite": self.prerequisite,
            "justification": self.justification,
            "consequent": self.consequent,
            "type": self.type.name,
            "priority": self.priority,
            "confidence": self.confidence,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Default':
        """Create from dictionary representation."""
        return cls(
            id=data["id"],
            prerequisite=data["prerequisite"],
            justification=data["justification"],
            consequent=data["consequent"],
            type=DefaultType[data["type"]],
            priority=data.get("priority", 0),
            confidence=data.get("confidence", 0.8),
            metadata=data.get("metadata", {})
        )


@dataclass
class Exception:
    """Represents an exception to a default rule."""
    id: str
    default_id: str  # ID of the default this is an exception to
    condition: str  # Condition under which the exception applies
    priority: int = 0  # Higher priority exceptions take precedence
    confidence: float = 0.9  # Confidence in the exception (0.0 to 1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "default_id": self.default_id,
            "condition": self.condition,
            "priority": self.priority,
            "confidence": self.confidence,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Exception':
        """Create from dictionary representation."""
        return cls(
            id=data["id"],
            default_id=data["default_id"],
            condition=data["condition"],
            priority=data.get("priority", 0),
            confidence=data.get("confidence", 0.9),
            metadata=data.get("metadata", {})
        )


class DefaultReasoningModule:
    """Implements default reasoning mechanisms.
    
    This class is responsible for handling reasoning with incomplete information,
    implementing defeasible inference, and providing methods for reasoning with
    defaults and exceptions.
    """
    
    def __init__(self, 
                 knowledge_store: KnowledgeStoreInterface,
                 inference_coordinator: InferenceCoordinator,
                 context_engine: Optional[ContextEngine] = None):
        """Initialize the Default Reasoning Module.
        
        Args:
            knowledge_store: The knowledge store to use for reasoning
            inference_coordinator: The inference coordinator to use for reasoning
            context_engine: Optional context engine for context-aware reasoning
        """
        self.knowledge_store = knowledge_store
        self.inference_coordinator = inference_coordinator
        self.context_engine = context_engine
        self.defaults: Dict[str, Default] = {}
        self.exceptions: Dict[str, Exception] = {}
        self.exception_by_default: Dict[str, List[str]] = {}  # Maps default IDs to exception IDs
    
    def add_default(self, default: Default) -> None:
        """Add a default rule.
        
        Args:
            default: The default rule to add
        """
        self.defaults[default.id] = default
        
        # Initialize exceptions list for this default if not exists
        if default.id not in self.exception_by_default:
            self.exception_by_default[default.id] = []
        
        # Add to knowledge store
        self._add_default_to_knowledge_store(default)
    
    def add_exception(self, exception: Exception) -> None:
        """Add an exception to a default rule.
        
        Args:
            exception: The exception to add
        """
        self.exceptions[exception.id] = exception
        
        # Add to exceptions list for the default
        if exception.default_id not in self.exception_by_default:
            self.exception_by_default[exception.default_id] = []
        
        self.exception_by_default[exception.default_id].append(exception.id)
        
        # Add to knowledge store
        self._add_exception_to_knowledge_store(exception)
    
    def remove_default(self, default_id: str) -> bool:
        """Remove a default rule.
        
        Args:
            default_id: ID of the default rule to remove
            
        Returns:
            True if the default was removed, False otherwise
        """
        if default_id not in self.defaults:
            return False
        
        # Remove all exceptions to this default
        for exception_id in self.exception_by_default.get(default_id, []):
            self.exceptions.pop(exception_id, None)
        
        # Remove from exception mapping
        self.exception_by_default.pop(default_id, None)
        
        # Remove from defaults
        self.defaults.pop(default_id)
        
        # Remove from knowledge store
        self._remove_default_from_knowledge_store(default_id)
        
        return True
    
    def remove_exception(self, exception_id: str) -> bool:
        """Remove an exception.
        
        Args:
            exception_id: ID of the exception to remove
            
        Returns:
            True if the exception was removed, False otherwise
        """
        if exception_id not in self.exceptions:
            return False
        
        exception = self.exceptions[exception_id]
        
        # Remove from exception mapping
        if exception.default_id in self.exception_by_default:
            if exception_id in self.exception_by_default[exception.default_id]:
                self.exception_by_default[exception.default_id].remove(exception_id)
        
        # Remove from exceptions
        self.exceptions.pop(exception_id)
        
        # Remove from knowledge store
        self._remove_exception_from_knowledge_store(exception_id)
        
        return True
    
    def get_default(self, default_id: str) -> Optional[Default]:
        """Get a default rule by ID.
        
        Args:
            default_id: ID of the default rule
            
        Returns:
            The default rule if found, None otherwise
        """
        return self.defaults.get(default_id)
    
    def get_exception(self, exception_id: str) -> Optional[Exception]:
        """Get an exception by ID.
        
        Args:
            exception_id: ID of the exception
            
        Returns:
            The exception if found, None otherwise
        """
        return self.exceptions.get(exception_id)
    
    def get_exceptions_for_default(self, default_id: str) -> List[Exception]:
        """Get all exceptions for a default rule.
        
        Args:
            default_id: ID of the default rule
            
        Returns:
            List of exceptions for the default rule
        """
        exception_ids = self.exception_by_default.get(default_id, [])
        return [self.exceptions[eid] for eid in exception_ids if eid in self.exceptions]
    
    def apply_defaults(self, 
                      query: str, 
                      context_id: Optional[str] = None,
                      confidence_threshold: float = 0.0) -> Dict[str, Any]:
        """Apply default reasoning to answer a query.
        
        Args:
            query: The query to answer
            context_id: Optional ID of the context to use for reasoning
            confidence_threshold: Minimum confidence threshold for results
            
        Returns:
            Dictionary with reasoning results
        """
        # Get context if provided
        context = None
        if self.context_engine and context_id:
            context = self.context_engine.get_context(context_id)
        
        # First, try to answer the query using standard inference
        standard_result = self._try_standard_inference(query)
        
        if standard_result["success"]:
            return standard_result
        
        # If standard inference fails, apply default reasoning
        return self._apply_default_reasoning(query, context, confidence_threshold)
    
    def check_consistency(self, statement: str) -> bool:
        """Check if a statement is consistent with the knowledge base.
        
        Args:
            statement: The statement to check
            
        Returns:
            True if the statement is consistent, False otherwise
        """
        # This would use the inference engine to check consistency
        # For now, we'll use a simplified approach
        
        try:
            # Try to find a contradiction
            negated_statement = f"not ({statement})"
            result = self.inference_coordinator.prove(negated_statement)
            
            # If the negation can be proven, the statement is inconsistent
            return not result.success
            
        except Exception as e:
            logger.warning(f"Error checking consistency: {e}")
            return True  # Assume consistent if there's an error
    
    def _try_standard_inference(self, query: str) -> Dict[str, Any]:
        """Try to answer a query using standard inference.
        
        Args:
            query: The query to answer
            
        Returns:
            Dictionary with inference results
        """
        try:
            # Use the inference coordinator to prove the query
            proof_result = self.inference_coordinator.prove(query)
            
            return {
                "success": proof_result.success,
                "confidence": 1.0 if proof_result.success else 0.0,
                "explanation": proof_result.explanation if hasattr(proof_result, "explanation") else None,
                "method": "standard_inference",
                "defaults_used": [],
                "exceptions_applied": []
            }
            
        except Exception as e:
            logger.warning(f"Error in standard inference: {e}")
            return {
                "success": False,
                "confidence": 0.0,
                "explanation": f"Error in standard inference: {e}",
                "method": "standard_inference",
                "defaults_used": [],
                "exceptions_applied": []
            }
    
    def _apply_default_reasoning(self, 
                               query: str, 
                               context: Optional[Context] = None,
                               confidence_threshold: float = 0.0) -> Dict[str, Any]:
        """Apply default reasoning to answer a query.
        
        Args:
            query: The query to answer
            context: Optional context to use for reasoning
            confidence_threshold: Minimum confidence threshold for results
            
        Returns:
            Dictionary with reasoning results
        """
        # Get applicable defaults
        applicable_defaults = self._get_applicable_defaults(query, context)
        
        if not applicable_defaults:
            return {
                "success": False,
                "confidence": 0.0,
                "explanation": "No applicable defaults found",
                "method": "default_reasoning",
                "defaults_used": [],
                "exceptions_applied": []
            }
        
        # Filter out defeated defaults
        undefeated_defaults = self._filter_undefeated_defaults(applicable_defaults, context)
        
        if not undefeated_defaults:
            return {
                "success": False,
                "confidence": 0.0,
                "explanation": "All applicable defaults were defeated by exceptions",
                "method": "default_reasoning",
                "defaults_used": [d.id for d in applicable_defaults],
                "exceptions_applied": self._get_applied_exceptions(applicable_defaults)
            }
        
        # Apply the defaults to derive a conclusion
        conclusion, confidence, explanation, defaults_used, exceptions_applied = self._derive_conclusion(
            query, undefeated_defaults, context
        )
        
        # Check if confidence meets the threshold
        success = confidence >= confidence_threshold
        
        return {
            "success": success,
            "conclusion": conclusion,
            "confidence": confidence,
            "explanation": explanation,
            "method": "default_reasoning",
            "defaults_used": defaults_used,
            "exceptions_applied": exceptions_applied
        }
    
    def _get_applicable_defaults(self, 
                               query: str, 
                               context: Optional[Context] = None) -> List[Default]:
        """Get defaults that are applicable to a query.
        
        Args:
            query: The query
            context: Optional context
            
        Returns:
            List of applicable defaults
        """
        applicable_defaults = []
        
        for default in self.defaults.values():
            # Check if the default's consequent is relevant to the query
            if self._is_relevant_to_query(default.consequent, query):
                # Check if the prerequisite is satisfied
                if self._is_prerequisite_satisfied(default.prerequisite, context):
                    # Check if the justification is consistent
                    if self._is_justification_consistent(default.justification):
                        applicable_defaults.append(default)
        
        # Sort by priority (higher priority first)
        return sorted(applicable_defaults, key=lambda d: d.priority, reverse=True)
    
    def _filter_undefeated_defaults(self, 
                                  defaults: List[Default], 
                                  context: Optional[Context] = None) -> List[Default]:
        """Filter out defaults that are defeated by exceptions.
        
        Args:
            defaults: List of defaults to filter
            context: Optional context
            
        Returns:
            List of undefeated defaults
        """
        undefeated_defaults = []
        
        for default in defaults:
            # Get exceptions for this default
            exceptions = self.get_exceptions_for_default(default.id)
            
            # Check if any exception applies
            defeated = False
            for exception in exceptions:
                if self._is_exception_applicable(exception, context):
                    defeated = True
                    break
            
            if not defeated:
                undefeated_defaults.append(default)
        
        return undefeated_defaults
    
    def _derive_conclusion(self, 
                         query: str, 
                         defaults: List[Default], 
                         context: Optional[Context] = None) -> Tuple[str, float, str, List[str], List[str]]:
        """Derive a conclusion from defaults.
        
        Args:
            query: The query
            defaults: List of defaults to apply
            context: Optional context
            
        Returns:
            Tuple of (conclusion, confidence, explanation, defaults_used, exceptions_applied)
        """
        # For simplicity, we'll use the highest priority default that directly answers the query
        direct_defaults = []
        for default in defaults:
            if self._directly_answers_query(default.consequent, query):
                direct_defaults.append(default)
        
        if direct_defaults:
            # Use the highest priority direct default
            best_default = max(direct_defaults, key=lambda d: d.priority)
            
            return (
                best_default.consequent,
                best_default.confidence,
                f"Derived from default rule: {best_default.id}",
                [best_default.id],
                []
            )
        
        # If no direct default, try to combine defaults
        # This would be a more complex reasoning process in a real implementation
        # For now, we'll use a simplified approach
        combined_confidence = 0.0
        combined_explanation = "Combined from multiple defaults: "
        defaults_used = []
        
        for default in defaults:
            # Add to the combined reasoning
            combined_confidence = max(combined_confidence, default.confidence * 0.8)
            combined_explanation += f"{default.id}, "
            defaults_used.append(default.id)
        
        if defaults_used:
            combined_explanation = combined_explanation[:-2]  # Remove trailing comma and space
            return (
                "Partial answer derived from defaults",
                combined_confidence,
                combined_explanation,
                defaults_used,
                []
            )
        
        # If no defaults could be applied
        return (
            "Unknown",
            0.0,
            "No applicable defaults found",
            [],
            []
        )
    
    def _is_relevant_to_query(self, consequent: str, query: str) -> bool:
        """Check if a default's consequent is relevant to a query.
        
        Args:
            consequent: The default's consequent
            query: The query
            
        Returns:
            True if relevant, False otherwise
        """
        # This would use more sophisticated relevance checking in a real implementation
        # For now, we'll use a simplified approach
        
        # Convert to lowercase for case-insensitive comparison
        consequent_lower = consequent.lower()
        query_lower = query.lower()
        
        # Check for direct match
        if consequent_lower == query_lower:
            return True
        
        # Check if consequent contains the query
        if query_lower in consequent_lower:
            return True
        
        # Check if query contains the consequent
        if consequent_lower in query_lower:
            return True
        
        # Check for shared terms
        consequent_terms = set(consequent_lower.split())
        query_terms = set(query_lower.split())
        shared_terms = consequent_terms.intersection(query_terms)
        
        return len(shared_terms) > 0
    
    def _is_prerequisite_satisfied(self, prerequisite: str, context: Optional[Context] = None) -> bool:
        """Check if a default's prerequisite is satisfied.
        
        Args:
            prerequisite: The prerequisite to check
            context: Optional context
            
        Returns:
            True if satisfied, False otherwise
        """
        # If prerequisite is empty or "true", it's always satisfied
        if not prerequisite or prerequisite.lower() == "true":
            return True
        
        # Try to prove the prerequisite
        try:
            proof_result = self.inference_coordinator.prove(prerequisite)
            return proof_result.success
        except Exception as e:
            logger.warning(f"Error checking prerequisite: {e}")
            return False
    
    def _is_justification_consistent(self, justification: str) -> bool:
        """Check if a default's justification is consistent.
        
        Args:
            justification: The justification to check
            
        Returns:
            True if consistent, False otherwise
        """
        # If justification is empty or "true", it's always consistent
        if not justification or justification.lower() == "true":
            return True
        
        return self.check_consistency(justification)
    
    def _is_exception_applicable(self, exception: Exception, context: Optional[Context] = None) -> bool:
        """Check if an exception is applicable.
        
        Args:
            exception: The exception to check
            context: Optional context
            
        Returns:
            True if applicable, False otherwise
        """
        # If condition is empty or "true", it's always applicable
        if not exception.condition or exception.condition.lower() == "true":
            return True
        
        # Try to prove the condition
        try:
            proof_result = self.inference_coordinator.prove(exception.condition)
            return proof_result.success
        except Exception as e:
            logger.warning(f"Error checking exception condition: {e}")
            return False
    
    def _directly_answers_query(self, consequent: str, query: str) -> bool:
        """Check if a default's consequent directly answers a query.
        
        Args:
            consequent: The default's consequent
            query: The query
            
        Returns:
            True if it directly answers, False otherwise
        """
        # This would use more sophisticated matching in a real implementation
        # For now, we'll use a simplified approach
        
        # Convert to lowercase for case-insensitive comparison
        consequent_lower = consequent.lower()
        query_lower = query.lower()
        
        # Check for direct match
        if consequent_lower == query_lower:
            return True
        
        # Check if consequent is an answer to the query
        # This is a simplified check and would be more sophisticated in a real implementation
        if query_lower.startswith("what") or query_lower.startswith("who") or query_lower.startswith("where"):
            return True
        
        return False
    
    def _get_applied_exceptions(self, defaults: List[Default]) -> List[str]:
        """Get exceptions that were applied to defeat defaults.
        
        Args:
            defaults: List of defaults that were considered
            
        Returns:
            List of exception IDs that were applied
        """
        applied_exceptions = []
        
        for default in defaults:
            exceptions = self.get_exceptions_for_default(default.id)
            for exception in exceptions:
                if self._is_exception_applicable(exception, None):
                    applied_exceptions.append(exception.id)
        
        return applied_exceptions
    
    def _add_default_to_knowledge_store(self, default: Default) -> None:
        """Add a default rule to the knowledge store.
        
        Args:
            default: The default rule to add
        """
        try:
            # Add as an entity
            self.knowledge_store.add_entity(f"default:{default.id}")
            
            # Add properties
            self.knowledge_store.add_property(f"default:{default.id}", "prerequisite", default.prerequisite)
            self.knowledge_store.add_property(f"default:{default.id}", "justification", default.justification)
            self.knowledge_store.add_property(f"default:{default.id}", "consequent", default.consequent)
            self.knowledge_store.add_property(f"default:{default.id}", "type", default.type.name)
            self.knowledge_store.add_property(f"default:{default.id}", "priority", default.priority)
            self.knowledge_store.add_property(f"default:{default.id}", "confidence", default.confidence)
            
            # Add metadata
            for key, value in default.metadata.items():
                self.knowledge_store.add_property(f"default:{default.id}", f"metadata:{key}", value)
                
        except Exception as e:
            logger.warning(f"Error adding default to knowledge store: {e}")
    
    def _add_exception_to_knowledge_store(self, exception: Exception) -> None:
        """Add an exception to the knowledge store.
        
        Args:
            exception: The exception to add
        """
        try:
            # Add as an entity
            self.knowledge_store.add_entity(f"exception:{exception.id}")
            
            # Add properties
            self.knowledge_store.add_property(f"exception:{exception.id}", "default_id", exception.default_id)
            self.knowledge_store.add_property(f"exception:{exception.id}", "condition", exception.condition)
            self.knowledge_store.add_property(f"exception:{exception.id}", "priority", exception.priority)
            self.knowledge_store.add_property(f"exception:{exception.id}", "confidence", exception.confidence)
            
            # Add relation to default
            self.knowledge_store.add_relation(
                f"exception:{exception.id}", "excepts", f"default:{exception.default_id}"
            )
            
            # Add metadata
            for key, value in exception.metadata.items():
                self.knowledge_store.add_property(f"exception:{exception.id}", f"metadata:{key}", value)
                
        except Exception as e:
            logger.warning(f"Error adding exception to knowledge store: {e}")
    
    def _remove_default_from_knowledge_store(self, default_id: str) -> None:
        """Remove a default rule from the knowledge store.
        
        Args:
            default_id: ID of the default rule to remove
        """
        try:
            self.knowledge_store.remove_entity(f"default:{default_id}")
        except Exception as e:
            logger.warning(f"Error removing default from knowledge store: {e}")
    
    def _remove_exception_from_knowledge_store(self, exception_id: str) -> None:
        """Remove an exception from the knowledge store.
        
        Args:
            exception_id: ID of the exception to remove
        """
        try:
            self.knowledge_store.remove_entity(f"exception:{exception_id}")
        except Exception as e:
            logger.warning(f"Error removing exception from knowledge store: {e}")