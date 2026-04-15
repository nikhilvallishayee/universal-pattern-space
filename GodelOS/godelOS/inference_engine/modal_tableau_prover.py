"""
Modal Tableau Prover for Modal Logics.

This module implements the ModalTableauProver class, which determines the validity
or satisfiability of formulae in various modal logics (e.g., K, T, D, B, S4, S5)
using the semantic tableau method.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, FrozenSet
import time
import logging
import copy
from dataclasses import dataclass, field
from enum import Enum

from godelOS.core_kr.ast.nodes import (
    AST_Node, VariableNode, ModalOpNode, ConnectiveNode, ConstantNode
)
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode

# Set up logging
logger = logging.getLogger(__name__)


class FormulaType(Enum):
    """Enumeration of formula types for tableau rules."""
    ALPHA = "alpha"  # Conjunctive formulas (AND)
    BETA = "beta"    # Disjunctive formulas (OR)
    PI = "pi"        # Box formulas (□)
    NU = "nu"        # Diamond formulas (◇)
    LITERAL = "literal"  # Atomic formulas or their negations
    COMPLEX = "complex"  # Other formulas that need preprocessing


class ModalSystem(Enum):
    """Enumeration of modal systems with their accessibility relation properties."""
    K = "K"      # No special properties
    T = "T"      # Reflexive
    D = "D"      # Serial
    B = "B"      # Reflexive and Symmetric
    S4 = "S4"    # Reflexive and Transitive
    S5 = "S5"    # Reflexive, Symmetric, and Transitive


@dataclass(frozen=True)
class SignedFormula:
    """
    Represents a signed formula in a tableau.
    
    A signed formula consists of a formula and a truth value sign (True/False).
    """
    formula: AST_Node
    sign: bool = True  # True for T (true), False for F (false)
    
    def __str__(self) -> str:
        sign_str = "T" if self.sign else "F"
        return f"{sign_str}: {self.formula}"
    
    def negate(self) -> 'SignedFormula':
        """Return a new signed formula with the opposite sign."""
        return SignedFormula(self.formula, not self.sign)


@dataclass
class World:
    """
    Represents a possible world in a Kripke model.
    
    Each world has a unique ID and a set of formulas that hold in that world.
    """
    world_id: int
    formulas: Set[SignedFormula] = field(default_factory=set)
    
    def __str__(self) -> str:
        return f"World {self.world_id}: {{{', '.join(str(f) for f in self.formulas)}}}"
    
    def add_formula(self, formula: SignedFormula) -> None:
        """Add a formula to this world."""
        self.formulas.add(formula)
    
    def contains_formula(self, formula: SignedFormula) -> bool:
        """Check if this world contains the given formula."""
        return formula in self.formulas
    
    def contains_contradiction(self) -> bool:
        """
        Check if this world contains a contradiction.
        
        A contradiction occurs when a formula and its negation both hold in the same world.
        This handles both sign-based contradictions (T:P and F:P) and explicit negation
        contradictions (T:P and T:NOT(P), or F:P and F:NOT(P)).
        """
        for formula in self.formulas:
            # Check for sign-based contradiction: T:X vs F:X
            if formula.negate() in self.formulas:
                return True
            # Check for explicit NOT contradiction: T:P vs T:NOT(P)
            if formula.sign:
                # If we have T:X, check for T:NOT(X)
                not_formula = ConnectiveNode("NOT", [formula.formula], formula.formula.type)
                if SignedFormula(not_formula, True) in self.formulas:
                    return True
                # If we have T:NOT(X), check for T:X
                if isinstance(formula.formula, ConnectiveNode) and formula.formula.connective_type == "NOT":
                    inner = formula.formula.operands[0]
                    if SignedFormula(inner, True) in self.formulas:
                        return True
        return False


@dataclass(frozen=True)
class AccessibilityRelation:
    """
    Represents an accessibility relation between worlds in a Kripke model.
    
    An accessibility relation is a directed edge from one world to another.
    """
    from_world_id: int
    to_world_id: int
    
    def __str__(self) -> str:
        return f"{self.from_world_id} → {self.to_world_id}"


@dataclass
class Branch:
    """
    Represents a branch in a tableau.
    
    A branch consists of a set of worlds and accessibility relations between them.
    """
    worlds: Dict[int, World] = field(default_factory=dict)
    accessibility_relations: Set[AccessibilityRelation] = field(default_factory=set)
    closed: bool = False
    expanded_formulas: Set[tuple] = field(default_factory=set)  # Track (world_id, SignedFormula) already expanded
    
    def __str__(self) -> str:
        worlds_str = "\n  ".join(str(w) for w in self.worlds.values())
        relations_str = ", ".join(str(r) for r in self.accessibility_relations)
        status = "CLOSED" if self.closed else "OPEN"
        return f"Branch ({status}):\n  {worlds_str}\n  Relations: {relations_str}"
    
    def add_world(self, world: World) -> None:
        """Add a world to this branch."""
        self.worlds[world.world_id] = world
    
    def add_accessibility_relation(self, relation: AccessibilityRelation) -> None:
        """Add an accessibility relation to this branch."""
        self.accessibility_relations.add(relation)
    
    def get_accessible_worlds(self, from_world_id: int) -> List[World]:
        """Get all worlds accessible from the given world."""
        accessible_world_ids = [
            rel.to_world_id for rel in self.accessibility_relations
            if rel.from_world_id == from_world_id
        ]
        return [self.worlds[world_id] for world_id in accessible_world_ids]
    
    def is_closed(self) -> bool:
        """
        Check if this branch is closed.
        
        A branch is closed if any of its worlds contains a contradiction.
        """
        if self.closed:
            return True
        
        for world in self.worlds.values():
            if world.contains_contradiction():
                self.closed = True
                return True
        
        return False
    
    def is_fully_expanded(self) -> bool:
        """
        Check if this branch is fully expanded.
        
        A branch is fully expanded if all applicable tableau rules have been applied.
        This is a simplified check and would be more complex in a full implementation.
        """
        # For now, just return False to ensure rules continue to be applied
        return False


@dataclass
class Tableau:
    """
    Represents a tableau for modal logic.
    
    A tableau consists of a set of branches, each representing a possible model.
    """
    branches: List[Branch] = field(default_factory=list)
    next_world_id: int = 0
    
    def __str__(self) -> str:
        return "\n".join(str(b) for b in self.branches)
    
    def add_branch(self, branch: Branch) -> None:
        """Add a branch to this tableau."""
        self.branches.append(branch)
    
    def create_new_world(self) -> int:
        """Create a new world and return its ID."""
        world_id = self.next_world_id
        self.next_world_id += 1
        return world_id
    
    def is_closed(self) -> bool:
        """
        Check if this tableau is closed.
        
        A tableau is closed if all of its branches are closed.
        """
        return all(branch.is_closed() for branch in self.branches)
    
    def has_open_branch(self) -> bool:
        """
        Check if this tableau has an open branch.
        
        A tableau has an open branch if at least one of its branches is not closed.
        """
        return any(not branch.is_closed() for branch in self.branches)


class TableauRuleApplicator:
    """
    Applies tableau rules to expand a tableau.
    
    This class encapsulates the logic for applying tableau rules to expand a tableau
    based on the formulas in its branches and the modal system being used.
    """
    
    def __init__(self, modal_system: ModalSystem):
        """
        Initialize the tableau rule applicator.
        
        Args:
            modal_system: The modal system to use (K, T, D, B, S4, S5)
        """
        self.modal_system = modal_system

    def get_formula_type(self, signed_formula: SignedFormula) -> FormulaType:
        """
        Determine the type of a formula for tableau rule application.
        
        Args:
            signed_formula: The signed formula to classify
            
        Returns:
            The formula type (ALPHA, BETA, PI, NU, LITERAL, or COMPLEX)
        """
        formula = signed_formula.formula
        sign = signed_formula.sign
        
        # Check if the formula is a modal operator
        if isinstance(formula, ModalOpNode):
            if formula.modal_operator == "NECESSARY":  # Box (□)
                return FormulaType.PI if sign else FormulaType.NU
            elif formula.modal_operator == "POSSIBLE":  # Diamond (◇)
                return FormulaType.NU if sign else FormulaType.PI
        
        # Check if the formula is a connective
        if isinstance(formula, ConnectiveNode):
            if formula.connective_type == "AND":
                return FormulaType.ALPHA if sign else FormulaType.BETA
            elif formula.connective_type == "OR":
                return FormulaType.BETA if sign else FormulaType.ALPHA
            elif formula.connective_type == "IMPLIES":
                return FormulaType.BETA if sign else FormulaType.ALPHA
            elif formula.connective_type == "NOT":
                # NOT is always an alpha rule (deterministic single-branch)
                return FormulaType.ALPHA
        
        # If it's not a complex formula, it's a literal
        return FormulaType.LITERAL
    
    def apply_alpha_rule(self, signed_formula: SignedFormula, branch: Branch, world_id: int) -> None:
        """
        Apply the alpha rule to a conjunctive formula.
        
        The alpha rule adds both conjuncts to the current world.
        
        Args:
            signed_formula: The signed formula to expand
            branch: The branch to apply the rule to
            world_id: The ID of the world in which to apply the rule
        """
        formula = signed_formula.formula
        sign = signed_formula.sign
        
        if isinstance(formula, ConnectiveNode):
            if formula.connective_type == "NOT":
                # T: NOT(A) -> F: A  ;  F: NOT(A) -> T: A
                branch.worlds[world_id].add_formula(SignedFormula(formula.operands[0], not sign))
            elif formula.connective_type == "AND":
                if sign:  # T: A ∧ B -> T: A, T: B
                    branch.worlds[world_id].add_formula(SignedFormula(formula.operands[0], True))
                    branch.worlds[world_id].add_formula(SignedFormula(formula.operands[1], True))
                else:  # F: A ∧ B -> F: A | F: B (handled by beta rule)
                    pass
            elif formula.connective_type == "OR":
                if not sign:  # F: A ∨ B -> F: A, F: B
                    branch.worlds[world_id].add_formula(SignedFormula(formula.operands[0], False))
                    branch.worlds[world_id].add_formula(SignedFormula(formula.operands[1], False))
                else:  # T: A ∨ B -> T: A | T: B (handled by beta rule)
                    pass
            elif formula.connective_type == "IMPLIES":
                if not sign:  # F: A → B -> T: A, F: B
                    branch.worlds[world_id].add_formula(SignedFormula(formula.operands[0], True))
                    branch.worlds[world_id].add_formula(SignedFormula(formula.operands[1], False))
                else:  # T: A → B -> F: A | T: B (handled by beta rule)
                    pass
    
    def apply_beta_rule(self, signed_formula: SignedFormula, branch: Branch, world_id: int) -> List[Branch]:
        """
        Apply the beta rule to a disjunctive formula.
        
        The beta rule splits the branch into two, one for each disjunct.
        
        Args:
            signed_formula: The signed formula to expand
            branch: The branch to apply the rule to
            world_id: The ID of the world in which to apply the rule
            
        Returns:
            A list of new branches created by the rule application
        """
        formula = signed_formula.formula
        sign = signed_formula.sign
        
        new_branches = []
        
        if isinstance(formula, ConnectiveNode):
            if formula.connective_type == "AND":
                if not sign:  # F: A ∧ B -> F: A | F: B
                    # Create first branch: F: A
                    branch1 = copy.deepcopy(branch)
                    branch1.worlds[world_id].add_formula(SignedFormula(formula.operands[0], False))
                    new_branches.append(branch1)
                    
                    # Create second branch: F: B
                    branch2 = copy.deepcopy(branch)
                    branch2.worlds[world_id].add_formula(SignedFormula(formula.operands[1], False))
                    new_branches.append(branch2)
            elif formula.connective_type == "OR":
                if sign:  # T: A ∨ B -> T: A | T: B
                    # Create first branch: T: A
                    branch1 = copy.deepcopy(branch)
                    branch1.worlds[world_id].add_formula(SignedFormula(formula.operands[0], True))
                    new_branches.append(branch1)
                    
                    # Create second branch: T: B
                    branch2 = copy.deepcopy(branch)
                    branch2.worlds[world_id].add_formula(SignedFormula(formula.operands[1], True))
                    new_branches.append(branch2)
            elif formula.connective_type == "IMPLIES":
                if sign:  # T: A → B -> F: A | T: B
                    # Create first branch: F: A
                    branch1 = copy.deepcopy(branch)
                    branch1.worlds[world_id].add_formula(SignedFormula(formula.operands[0], False))
                    new_branches.append(branch1)
                    
                    # Create second branch: T: B
                    branch2 = copy.deepcopy(branch)
                    branch2.worlds[world_id].add_formula(SignedFormula(formula.operands[1], True))
                    new_branches.append(branch2)
        
        return new_branches
    
    def apply_pi_rule(self, signed_formula: SignedFormula, branch: Branch, world_id: int) -> None:
        """
        Apply the pi rule to a universal modal formula.
        
        PI formulas propagate to ALL accessible worlds.
        T: □A -> add T: A to all accessible worlds
        F: ◇A -> add F: A to all accessible worlds
        
        Args:
            signed_formula: The signed formula to expand
            branch: The branch to apply the rule to
            world_id: The ID of the world in which to apply the rule
        """
        formula = signed_formula.formula
        sign = signed_formula.sign
        
        if isinstance(formula, ModalOpNode):
            if formula.modal_operator == "NECESSARY" and sign:
                # T: □A -> add T: A to all accessible worlds
                for accessible_world in branch.get_accessible_worlds(world_id):
                    accessible_world.add_formula(SignedFormula(formula.proposition, True))
            elif formula.modal_operator == "POSSIBLE" and not sign:
                # F: ◇A -> add F: A to all accessible worlds
                for accessible_world in branch.get_accessible_worlds(world_id):
                    accessible_world.add_formula(SignedFormula(formula.proposition, False))
    
    def apply_nu_rule(self, signed_formula: SignedFormula, branch: Branch, world_id: int, tableau: Tableau) -> None:
        """
        Apply the nu rule to an existential modal formula.
        
        NU formulas create a NEW accessible world.
        T: ◇A -> create new world with T: A
        F: □A -> create new world with F: A
        
        Args:
            signed_formula: The signed formula to expand
            branch: The branch to apply the rule to
            world_id: The ID of the world in which to apply the rule
            tableau: The tableau being expanded
        """
        formula = signed_formula.formula
        sign = signed_formula.sign
        
        if isinstance(formula, ModalOpNode):
            if formula.modal_operator == "POSSIBLE" and sign:
                # T: ◇A -> create new world with T: A
                new_world_id = tableau.create_new_world()
                new_world = World(new_world_id)
                new_world.add_formula(SignedFormula(formula.proposition, True))
                branch.add_world(new_world)
                branch.add_accessibility_relation(AccessibilityRelation(world_id, new_world_id))
                self.apply_accessibility_properties(branch, new_world_id)
            elif formula.modal_operator == "NECESSARY" and not sign:
                # F: □A -> create new world with F: A
                new_world_id = tableau.create_new_world()
                new_world = World(new_world_id)
                new_world.add_formula(SignedFormula(formula.proposition, False))
                branch.add_world(new_world)
                branch.add_accessibility_relation(AccessibilityRelation(world_id, new_world_id))
                self.apply_accessibility_properties(branch, new_world_id)
    
    def apply_accessibility_properties(self, branch: Branch, world_id: int) -> None:
        """
        Apply accessibility relation properties based on the modal system.
        
        Args:
            branch: The branch to apply the properties to
            world_id: The ID of the world to consider for new relations
        """
        # Reflexivity (T, B, S4, S5)
        if self.modal_system in [ModalSystem.T, ModalSystem.B, ModalSystem.S4, ModalSystem.S5]:
            branch.add_accessibility_relation(AccessibilityRelation(world_id, world_id))
        
        # Symmetry (B, S5)
        if self.modal_system in [ModalSystem.B, ModalSystem.S5]:
            for relation in list(branch.accessibility_relations):
                if relation.to_world_id == world_id:
                    branch.add_accessibility_relation(AccessibilityRelation(world_id, relation.from_world_id))
        
        # Transitivity (S4, S5)
        if self.modal_system in [ModalSystem.S4, ModalSystem.S5]:
            for relation1 in list(branch.accessibility_relations):
                if relation1.from_world_id == world_id:
                    for relation2 in list(branch.accessibility_relations):
                        if relation2.from_world_id == relation1.to_world_id:
                            branch.add_accessibility_relation(AccessibilityRelation(world_id, relation2.to_world_id))
        
        # Seriality (D)
        if self.modal_system == ModalSystem.D:
            has_successor = False
            for relation in branch.accessibility_relations:
                if relation.from_world_id == world_id:
                    has_successor = True
                    break
            
            if not has_successor:
                # Create a new world and make it accessible from this world
                new_world_id = max(branch.worlds.keys()) + 1 if branch.worlds else 0
                branch.add_world(World(new_world_id))
                branch.add_accessibility_relation(AccessibilityRelation(world_id, new_world_id))
    
    def expand_branch(self, branch: Branch, tableau: Tableau) -> List[Branch]:
        """
        Expand a branch by applying tableau rules.
        
        Args:
            branch: The branch to expand
            tableau: The tableau being expanded
            
        Returns:
            A list of branches resulting from the expansion
        """
        if branch.is_closed():
            return [branch]
        
        # Apply accessibility properties for the modal system first
        for world_id in list(branch.worlds.keys()):
            self.apply_accessibility_properties(branch, world_id)
        
        # Find an unexpanded formula in any world
        for world_id, world in branch.worlds.items():
            for signed_formula in list(world.formulas):
                # Skip if already expanded in this world
                expansion_key = (world_id, signed_formula)
                if expansion_key in branch.expanded_formulas:
                    continue
                
                formula_type = self.get_formula_type(signed_formula)
                
                if formula_type == FormulaType.ALPHA:
                    branch.expanded_formulas.add(expansion_key)
                    self.apply_alpha_rule(signed_formula, branch, world_id)
                    return [branch]  # Continue with the same branch
                
                elif formula_type == FormulaType.BETA:
                    branch.expanded_formulas.add(expansion_key)
                    new_branches = self.apply_beta_rule(signed_formula, branch, world_id)
                    # Copy expanded_formulas to new branches
                    for b in new_branches:
                        b.expanded_formulas = set(branch.expanded_formulas)
                    return new_branches  # Return the new branches
                
                elif formula_type == FormulaType.PI:
                    branch.expanded_formulas.add(expansion_key)
                    self.apply_pi_rule(signed_formula, branch, world_id)
                    return [branch]  # Continue with the same branch
                
                elif formula_type == FormulaType.NU:
                    branch.expanded_formulas.add(expansion_key)
                    self.apply_nu_rule(signed_formula, branch, world_id, tableau)
                    return [branch]  # Continue with the same branch
        
        # If no rules were applied, the branch is fully expanded - mark it
        branch.closed = False  # It stays open
        return []  # Return empty to signal no more work


class ModalTableauProver(BaseProver):
    """
    Prover for modal logics using the tableau method.
    
    This prover determines the validity or satisfiability of formulae in various
    modal logics (e.g., K, T, D, B, S4, S5) using the semantic tableau method.
    It constructs a semantic tableau (a proof tree) for the input modal formula
    and checks if all branches close.
    """
    
    def __init__(self, kr_system_interface: KnowledgeStoreInterface,
                type_system: TypeSystemManager):
        """
        Initialize the modal tableau prover.
        
        Args:
            kr_system_interface: Interface to the Knowledge Representation system
            type_system: The type system manager for type checking and inference
        """
        self.kr_system_interface = kr_system_interface
        self.type_system = type_system
    
    @property
    def name(self) -> str:
        """Get the name of this prover."""
        return "ModalTableauProver"
    
    @property
    def capabilities(self) -> Dict[str, bool]:
        """Get the capabilities of this prover."""
        capabilities = super().capabilities.copy()
        capabilities.update({
            "modal_logic": True,
            "propositional_logic": True,
            "first_order_logic": True  # Limited support for FOL within modal contexts
        })
        return capabilities
    
    def can_handle(self, goal_ast: AST_Node, context_asts: Set[AST_Node]) -> bool:
        """
        Determine if this prover can handle the given goal and context.
        
        The modal tableau prover can handle goals and contexts that involve modal operators.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            
        Returns:
            True if this prover can handle the given goal and context, False otherwise
        """
        # Check if the goal or any context assertion contains a modal operator
        from godelOS.inference_engine.coordinator import InferenceCoordinator
        coordinator = InferenceCoordinator(self.kr_system_interface, {})
        
        if coordinator._contains_modal_operator(goal_ast):
            return True
        
        for ast in context_asts:
            if coordinator._contains_modal_operator(ast):
                return True
        
        return False
    
    def _negate_formula(self, formula: AST_Node) -> AST_Node:
        """
        Negate a formula, with double-negation elimination.
        
        Args:
            formula: The formula to negate
            
        Returns:
            The negated formula
        """
        # If the formula is already a negation, return its operand (double-negation elimination)
        if isinstance(formula, ConnectiveNode) and formula.connective_type == "NOT":
            inner = formula.operands[0]
            # Recursively simplify if the inner formula is also a negation
            if isinstance(inner, ConnectiveNode) and inner.connective_type == "NOT":
                return self._negate_formula(inner)
            return inner
        
        # Otherwise, wrap it in a negation
        return ConnectiveNode("NOT", [formula], formula.type)
    
    def _create_initial_tableau(self, formula: AST_Node, context_formulas: Set[AST_Node], check_validity: bool) -> Tableau:
        """
        Create the initial tableau for a formula.
        
        Args:
            formula: The formula to prove
            context_formulas: The set of context formulas to include
            check_validity: If True, negate the formula to check validity
            
        Returns:
            The initial tableau
        """
        tableau = Tableau()
        
        # Create the initial world
        world_id = tableau.create_new_world()
        world = World(world_id)
        
        # Add the formula to the world
        if check_validity:
            # To check validity, we try to find a model for the negation
            negated_formula = self._negate_formula(formula)
            world.add_formula(SignedFormula(negated_formula, True))
        else:
            # To check satisfiability, we try to find a model for the formula
            world.add_formula(SignedFormula(formula, True))
        
        # Add context formulas to the world
        for context_formula in context_formulas:
            world.add_formula(SignedFormula(context_formula, True))
        
        # Create the initial branch
        branch = Branch()
        branch.add_world(world)
        tableau.add_branch(branch)
        
        return tableau
    
    def _expand_tableau(self, tableau: Tableau, modal_system: ModalSystem, resources: ResourceLimits) -> Tuple[Tableau, Dict[str, Any]]:
        """
        Expand a tableau by applying tableau rules.
        
        Args:
            tableau: The tableau to expand
            modal_system: The modal system to use
            resources: Resource limits for the proof attempt
            
        Returns:
            A tuple of the expanded tableau and a dictionary of resources consumed
        """
        rule_applicator = TableauRuleApplicator(modal_system)
        
        # Track resources
        start_time = time.time()
        nodes_explored = 0
        max_depth = 0
        
        # Continue expanding until all branches are closed or a resource limit is reached
        while not tableau.is_closed() and tableau.branches:
            # Check resource limits
            if resources:
                current_time = time.time()
                time_taken_ms = (current_time - start_time) * 1000
                
                if resources.time_limit_ms and time_taken_ms > resources.time_limit_ms:
                    logger.info("Time limit exceeded")
                    break
                
                if resources.nodes_limit and nodes_explored >= resources.nodes_limit:
                    logger.info("Nodes limit exceeded")
                    break
                
                if resources.depth_limit and max_depth >= resources.depth_limit:
                    logger.info("Depth limit exceeded")
                    break
            
            # Get the next branch to expand
            branch = next((b for b in tableau.branches if not b.is_closed()), None)
            if not branch:
                break
            
            # Expand the branch
            new_branches = rule_applicator.expand_branch(branch, tableau)
            
            # Update the tableau with the new branches
            if new_branches:
                tableau.branches.remove(branch)
                tableau.branches.extend(new_branches)
            else:
                # Branch is fully expanded with no more work - stop trying to expand it
                break
            
            nodes_explored += 1
            max_depth = max(max_depth, len(tableau.branches))
        
        # Calculate resources consumed
        end_time = time.time()
        time_taken_ms = (end_time - start_time) * 1000
        
        resources_consumed = {
            "nodes_explored": nodes_explored,
            "max_depth": max_depth,
            "branches_created": len(tableau.branches),
            "time_taken_ms": time_taken_ms
        }
        
        return tableau, resources_consumed
    
    def _create_proof_steps(self, tableau: Tableau, goal_ast: AST_Node, check_validity: bool) -> List[ProofStepNode]:
        """
        Create proof steps from a tableau.
        
        Args:
            tableau: The completed tableau
            goal_ast: The original goal
            check_validity: Whether we were checking validity or satisfiability
            
        Returns:
            A list of proof steps
        """
        proof_steps = []
        
        # Add the initial goal as the first step
        if check_validity:
            proof_steps.append(ProofStepNode(
                formula=goal_ast,
                rule_name="goal",
                premises=[],
                explanation="Original goal to prove"
            ))
            
            # Add the negation of the goal as the second step
            negated_goal = self._negate_formula(goal_ast)
            proof_steps.append(ProofStepNode(
                formula=negated_goal,
                rule_name="negation",
                premises=[0],
                explanation="Negation of the goal (for proof by contradiction)"
            ))
        else:
            proof_steps.append(ProofStepNode(
                formula=goal_ast,
                rule_name="goal",
                premises=[],
                explanation="Original formula to check for satisfiability"
            ))
        
        # Add steps for each branch closure
        step_idx = len(proof_steps)
        for i, branch in enumerate(tableau.branches):
            if branch.is_closed():
                for world in branch.worlds.values():
                    for formula in world.formulas:
                        if formula.negate() in world.formulas:
                            proof_steps.append(ProofStepNode(
                                formula=formula.formula,
                                rule_name="contradiction",
                                premises=[step_idx - 1],
                                explanation=f"Contradiction found in branch {i}, world {world.world_id}: "
                                           f"{formula} and {formula.negate()}"
                            ))
                            step_idx += 1
                            break
                    else:
                        continue
                    break
        
        # Add the final conclusion
        if tableau.is_closed():
            if check_validity:
                proof_steps.append(ProofStepNode(
                    formula=goal_ast,
                    rule_name="conclusion",
                    premises=list(range(step_idx)),
                    explanation="All branches closed, proving the goal is valid"
                ))
            else:
                proof_steps.append(ProofStepNode(
                    formula=self._negate_formula(goal_ast),
                    rule_name="conclusion",
                    premises=list(range(step_idx)),
                    explanation="All branches closed, proving the formula is unsatisfiable"
                ))
        else:
            # Find an open branch
            open_branch = next((b for b in tableau.branches if not b.is_closed()), None)
            if open_branch:
                if check_validity:
                    proof_steps.append(ProofStepNode(
                        formula=self._negate_formula(goal_ast),
                        rule_name="countermodel",
                        premises=list(range(step_idx)),
                        explanation="Found an open branch, providing a countermodel to the goal"
                    ))
                else:
                    proof_steps.append(ProofStepNode(
                        formula=goal_ast,
                        rule_name="model",
                        premises=list(range(step_idx)),
                        explanation="Found an open branch, providing a model for the formula"
                    ))
        
        return proof_steps
    
    def _check_tableau_provable(self, goal_ast: AST_Node, context_asts: Set[AST_Node] = None,
                               modal_system_name: str = "K", check_validity: bool = True,
                               resources: Optional[ResourceLimits] = None) -> Tuple[bool, Any]:
        """
        Check if a formula is provable using the tableau method.
        
        Args:
            goal_ast: The goal formula
            context_asts: Context assertions
            modal_system_name: Modal system name
            check_validity: Whether to check validity
            resources: Optional resource limits
            
        Returns:
            Tuple of (is_provable, proof_steps_or_reason)
        """
        if context_asts is None:
            context_asts = set()
        if resources is None:
            resources = ResourceLimits(time_limit_ms=10000, depth_limit=100, nodes_limit=10000)
        
        try:
            modal_system = ModalSystem[modal_system_name]
        except KeyError:
            return (False, f"Unknown modal system: {modal_system_name}")
        
        # Create and expand the tableau
        tableau = self._create_initial_tableau(goal_ast, context_asts, check_validity)
        expanded_tableau, resources_consumed = self._expand_tableau(tableau, modal_system, resources)
        
        # Check if resource limits were exceeded
        if resources.time_limit_ms and resources_consumed.get("time_taken_ms", 0) > resources.time_limit_ms:
            return (False, "Timeout")
        
        is_closed = expanded_tableau.is_closed()
        proof_steps = self._create_proof_steps(expanded_tableau, goal_ast, check_validity)
        
        if (is_closed and check_validity) or (not is_closed and not check_validity):
            return (True, proof_steps)
        else:
            return (False, proof_steps)
    
    def _apply_tableau_rule(self, formula: AST_Node, sign: bool) -> List[List[AST_Node]]:
        """
        Apply a tableau rule to a formula.
        
        Args:
            formula: The formula to apply the rule to
            sign: The sign of the formula (True/False)
            
        Returns:
            A list of branches, where each branch is a list of formulas
        """
        signed = SignedFormula(formula, sign)
        rule_applicator = TableauRuleApplicator(ModalSystem.K)
        formula_type = rule_applicator.get_formula_type(signed)
        
        if isinstance(formula, ConnectiveNode):
            if formula.connective_type == "NOT":
                return [[formula.operands[0]]]
            elif formula.connective_type == "AND":
                if sign:
                    return [list(formula.operands)]
                else:
                    return [[op] for op in formula.operands]
            elif formula.connective_type == "OR":
                if sign:
                    return [[op] for op in formula.operands]
                else:
                    return [list(formula.operands)]
            elif formula.connective_type == "IMPLIES":
                if sign:
                    return [[formula.operands[1]]]
                else:
                    return [[formula.operands[0], self._negate_formula(formula.operands[1])]]
        
        if isinstance(formula, ModalOpNode):
            return [[formula.proposition]]
        
        return [[formula]]

    def prove(self, goal_ast: AST_Node, context_asts: Set[AST_Node],
             resources: Optional[ResourceLimits] = None,
             modal_system_name: str = "K",
             check_validity: bool = True) -> ProofObject:
        """
        Attempt to prove a modal goal using the tableau method.
        
        This method implements the full modal tableau algorithm, including:
        1. Initializing a tableau with the goal (or its negation if checking validity)
        2. Applying tableau expansion rules based on the modal system
        3. Checking if all branches close
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            resources: Optional resource limits for the proof attempt
            modal_system_name: The modal system to use (e.g., "K", "T", "S4", "S5")
            check_validity: If True, check validity by negating the goal first
            
        Returns:
            A ProofObject representing the result of the proof attempt
        """
        start_time = time.time()
        
        # Set default resource limits if none provided
        if resources is None:
            resources = ResourceLimits(time_limit_ms=10000, depth_limit=100, nodes_limit=10000)
        
        logger.info(f"ModalTableauProver attempting to prove: {goal_ast}")
        logger.info(f"Modal system: {modal_system_name}")
        logger.info(f"Check validity: {check_validity}")
        
        try:
            # Delegate to _check_tableau_provable
            is_provable, result = self._check_tableau_provable(
                goal_ast, context_asts, modal_system_name, check_validity,
                resources=resources
            )
            
            end_time = time.time()
            time_taken_ms = (end_time - start_time) * 1000
            
            if isinstance(result, str):
                # Error or reason string
                if result == "Timeout":
                    return ProofObject.create_failure(
                        status_message="Failed: Resource limits exceeded",
                        inference_engine_used=self.name,
                        time_taken_ms=time_taken_ms,
                        resources_consumed={"timeout": True}
                    )
                return ProofObject.create_failure(
                    status_message=result,
                    inference_engine_used=self.name,
                    time_taken_ms=time_taken_ms,
                    resources_consumed={}
                )
            
            proof_steps = result if isinstance(result, list) else []
            
            if is_provable:
                return ProofObject.create_success(
                    conclusion_ast=goal_ast,
                    proof_steps=proof_steps,
                    used_axioms_rules=context_asts,
                    inference_engine_used=self.name,
                    time_taken_ms=time_taken_ms,
                    resources_consumed={}
                )
            else:
                status_message = "Formula is invalid" if check_validity else "Formula is unsatisfiable"
                return ProofObject.create_failure(
                    status_message=status_message,
                    inference_engine_used=self.name,
                    time_taken_ms=time_taken_ms,
                    resources_consumed={}
                )
                
        except Exception as e:
            logger.error(f"Error during tableau proof: {str(e)}", exc_info=True)
            
            end_time = time.time()
            time_taken_ms = (end_time - start_time) * 1000
            
            return ProofObject.create_failure(
                status_message=f"Error: {str(e)}",
                inference_engine_used=self.name,
                time_taken_ms=time_taken_ms,
                resources_consumed={"error": 1}
            )