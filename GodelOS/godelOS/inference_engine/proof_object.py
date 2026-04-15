"""
ProofObject data structure for representing the outcome of a reasoning process.

This module defines the ProofObject class, which is a standardized way to represent
the outcome of a reasoning process, including the proof steps if successful.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
import time

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode


@dataclass(frozen=True)
class ProofStepNode:
    """
    Represents a single step in a proof.
    
    A proof step consists of a formula derived at this step, the rule used to derive it,
    and references to the previous steps that were used in this derivation.
    """
    
    formula: AST_Node
    """The formula derived at this step."""
    
    rule_name: str
    """The name of the inference rule used (e.g., "Resolution", "Modus Ponens")."""
    
    premises: List[int]
    """References to the previous steps (by index) that were used in this derivation."""
    
    explanation: str = ""
    """Optional human-readable explanation of this step."""


@dataclass(frozen=True)
class ProofObject:
    """
    A standardized representation of the outcome of a reasoning process.
    
    This class encapsulates all relevant information about a proof attempt,
    including whether the goal was achieved, the bindings found, the proof steps,
    and performance metrics.
    """
    
    goal_achieved: bool
    """Whether the goal was successfully achieved."""
    
    conclusion_ast: Optional[AST_Node] = None
    """The proven goal or derived expression, if successful."""
    
    bindings: Optional[Dict[VariableNode, AST_Node]] = None
    """Variable bindings found during the proof, for 'find' type goals."""
    
    status_message: str = ""
    """Status message (e.g., "Proved", "Failed: Timeout", "Contradiction Found")."""
    
    proof_steps: List[ProofStepNode] = field(default_factory=list)
    """Detailed derivation steps of the proof."""
    
    used_axioms_rules: Set[AST_Node] = field(default_factory=set)
    """The initial facts/rules that were crucial for the proof."""
    
    inference_engine_used: str = ""
    """Name of the prover/engine module that produced this proof."""
    
    time_taken_ms: float = 0.0
    """Time taken to produce the proof, in milliseconds."""
    
    resources_consumed: Dict[str, float] = field(default_factory=dict)
    """Resources consumed during the proof (e.g., {"depth": 10, "nodes_explored": 1000})."""
    
    @classmethod
    def create_success(cls, conclusion_ast: AST_Node, bindings: Optional[Dict[VariableNode, AST_Node]] = None,
                      proof_steps: Optional[List[ProofStepNode]] = None, used_axioms_rules: Optional[Set[AST_Node]] = None,
                      inference_engine_used: str = "", time_taken_ms: float = 0.0,
                      resources_consumed: Optional[Dict[str, float]] = None) -> 'ProofObject':
        """
        Create a successful proof object.
        
        Args:
            conclusion_ast: The proven goal or derived expression
            bindings: Variable bindings found during the proof
            proof_steps: Detailed derivation steps of the proof
            used_axioms_rules: The initial facts/rules that were crucial for the proof
            inference_engine_used: Name of the prover/engine module that produced this proof
            time_taken_ms: Time taken to produce the proof, in milliseconds
            resources_consumed: Resources consumed during the proof
            
        Returns:
            A ProofObject representing a successful proof
        """
        return cls(
            goal_achieved=True,
            conclusion_ast=conclusion_ast,
            bindings=bindings,
            status_message="Proved",
            proof_steps=proof_steps or [],
            used_axioms_rules=used_axioms_rules or set(),
            inference_engine_used=inference_engine_used,
            time_taken_ms=time_taken_ms,
            resources_consumed=resources_consumed or {}
        )
    
    @classmethod
    def create_failure(cls, status_message: str, inference_engine_used: str = "",
                      time_taken_ms: float = 0.0, resources_consumed: Optional[Dict[str, float]] = None) -> 'ProofObject':
        """
        Create a failed proof object.
        
        Args:
            status_message: Reason for failure (e.g., "Failed: Timeout", "Contradiction Found")
            inference_engine_used: Name of the prover/engine module that attempted the proof
            time_taken_ms: Time taken until failure, in milliseconds
            resources_consumed: Resources consumed during the attempt
            
        Returns:
            A ProofObject representing a failed proof attempt
        """
        return cls(
            goal_achieved=False,
            status_message=status_message,
            inference_engine_used=inference_engine_used,
            time_taken_ms=time_taken_ms,
            resources_consumed=resources_consumed or {}
        )
    
    def with_time_and_resources(self, time_taken_ms: float, resources_consumed: Dict[str, float]) -> 'ProofObject':
        """
        Create a new ProofObject with updated time and resource information.
        
        Args:
            time_taken_ms: Time taken to produce the proof, in milliseconds
            resources_consumed: Resources consumed during the proof
            
        Returns:
            A new ProofObject with updated time and resource information
        """
        return ProofObject(
            goal_achieved=self.goal_achieved,
            conclusion_ast=self.conclusion_ast,
            bindings=self.bindings,
            status_message=self.status_message,
            proof_steps=self.proof_steps,
            used_axioms_rules=self.used_axioms_rules,
            inference_engine_used=self.inference_engine_used,
            time_taken_ms=time_taken_ms,
            resources_consumed=resources_consumed
        )