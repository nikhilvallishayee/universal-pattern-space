"""
Base Prover abstract class for the Inference Engine Architecture.

This module defines the BaseProver abstract class, which serves as the common interface
for all provers in the Inference Engine Architecture. All concrete provers should
inherit from this class and implement its abstract methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Set, Any

from godelOS.core_kr.ast.nodes import AST_Node
from godelOS.inference_engine.proof_object import ProofObject


class ResourceLimits:
    """
    Represents resource limits for a proof attempt.
    
    This class encapsulates various resource limits that can be imposed on a proof attempt,
    such as time limit, depth limit, and memory limit.
    """
    
    def __init__(self, time_limit_ms: Optional[float] = None, 
                depth_limit: Optional[int] = None,
                memory_limit_mb: Optional[float] = None,
                nodes_limit: Optional[int] = None,
                **kwargs: Any):
        """
        Initialize resource limits.
        
        Args:
            time_limit_ms: Maximum time allowed for the proof, in milliseconds
            depth_limit: Maximum depth of the proof search tree
            memory_limit_mb: Maximum memory usage allowed, in megabytes
            nodes_limit: Maximum number of nodes to explore in the search space
            **kwargs: Additional resource limits specific to particular provers
        """
        self.time_limit_ms = time_limit_ms
        self.depth_limit = depth_limit
        self.memory_limit_mb = memory_limit_mb
        self.nodes_limit = nodes_limit
        self.additional_limits = kwargs
    
    def get_limit(self, limit_name: str, default: Any = None) -> Any:
        """
        Get a specific resource limit.
        
        Args:
            limit_name: The name of the limit to get
            default: Default value to return if the limit is not set
            
        Returns:
            The value of the specified limit, or the default if not set
        """
        if hasattr(self, limit_name):
            return getattr(self, limit_name)
        return self.additional_limits.get(limit_name, default)
    
    def __str__(self) -> str:
        """String representation of the resource limits."""
        limits = []
        if self.time_limit_ms is not None:
            limits.append(f"time_limit_ms={self.time_limit_ms}")
        if self.depth_limit is not None:
            limits.append(f"depth_limit={self.depth_limit}")
        if self.memory_limit_mb is not None:
            limits.append(f"memory_limit_mb={self.memory_limit_mb}")
        if self.nodes_limit is not None:
            limits.append(f"nodes_limit={self.nodes_limit}")
        for k, v in self.additional_limits.items():
            limits.append(f"{k}={v}")
        return f"ResourceLimits({', '.join(limits)})"


class BaseProver(ABC):
    """
    Abstract base class for all provers in the Inference Engine Architecture.
    
    This class defines the common interface that all provers must implement.
    The InferenceCoordinator uses this interface to interact with the provers.
    """
    
    @abstractmethod
    def prove(self, goal_ast: AST_Node, context_asts: Set[AST_Node], 
             resources: Optional[ResourceLimits] = None) -> ProofObject:
        """
        Attempt to prove a goal given a set of context assertions.
        
        This is the main method that all provers must implement. It attempts to prove
        the given goal using the provided context assertions and resource limits.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions (axioms, facts, rules)
            resources: Optional resource limits for the proof attempt
            
        Returns:
            A ProofObject representing the result of the proof attempt
        """
        pass
    
    @abstractmethod
    def can_handle(self, goal_ast: AST_Node, context_asts: Set[AST_Node]) -> bool:
        """
        Determine if this prover can handle the given goal and context.
        
        This method is used by the InferenceCoordinator to select an appropriate
        prover for a given goal and context.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions (axioms, facts, rules)
            
        Returns:
            True if this prover can handle the given goal and context, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of this prover.
        
        Returns:
            The name of this prover
        """
        pass
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """
        Get the capabilities of this prover.
        
        This method returns a dictionary of capabilities that this prover supports.
        Subclasses can override this method to provide more specific capabilities.
        
        Returns:
            A dictionary of capability names to boolean values indicating support
        """
        return {
            "first_order_logic": False,
            "propositional_logic": False,
            "modal_logic": False,
            "higher_order_logic": False,
            "arithmetic": False,
            "equality": False,
            "uninterpreted_functions": False,
            "constraint_solving": False,
            "analogical_reasoning": False
        }