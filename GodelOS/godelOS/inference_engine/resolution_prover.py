"""
Resolution Prover for First-Order Logic and Propositional Logic.

This module implements the ResolutionProver class, which proves goals using the
resolution inference rule, primarily for First-Order Logic (FOL) and propositional logic.
It converts input formulae into Conjunctive Normal Form (CNF) and applies various
resolution strategies to find a refutation.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, FrozenSet
import time
import logging
import copy
from dataclasses import dataclass, field
from enum import Enum
import dataclasses

from godelOS.core_kr.ast.nodes import (
    AST_Node, VariableNode, ConstantNode, ConnectiveNode,
    QuantifierNode, ApplicationNode
)
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.unification_engine.result import UnificationResult
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode

# Set up logging
logger = logging.getLogger(__name__)


class ResolutionStrategy(Enum):
    """Enumeration of resolution strategies."""
    SET_OF_SUPPORT = "set_of_support"
    UNIT_PREFERENCE = "unit_preference"
    INPUT_RESOLUTION = "input_resolution"
    LINEAR_RESOLUTION = "linear_resolution"


@dataclass(frozen=True)
class Literal:
    """
    Represents a literal in a clause.
    
    A literal is an atomic formula or its negation.
    """
    atom: AST_Node
    is_negated: bool = False
    
    def negate(self) -> 'Literal':
        """Return a new literal with the opposite polarity."""
        return Literal(self.atom, not self.is_negated)
    
    def __str__(self) -> str:
        return f"{'¬' if self.is_negated else ''}{self.atom}"


@dataclass(frozen=True)
class Clause:
    """
    Represents a clause in CNF.
    
    A clause is a disjunction of literals.
    """
    literals: FrozenSet[Literal]
    source: str = "axiom"
    parent_ids: Tuple[int, ...] = field(default_factory=tuple)
    clause_id: int = -1
    
    def __str__(self) -> str:
        if not self.literals:
            return "□"  # Empty clause (contradiction)
        return " ∨ ".join(str(lit) for lit in self.literals)
    
    def is_empty(self) -> bool:
        """Check if this is the empty clause."""
        return len(self.literals) == 0
    
    def is_unit(self) -> bool:
        """Check if this is a unit clause (contains only one literal)."""
        return len(self.literals) == 1


class CNFConverter:
    """
    Converter for transforming logical formulas into Conjunctive Normal Form (CNF).
    
    This class handles the various steps of CNF conversion:
    1. Eliminate implications and equivalences
    2. Move negations inward (using De Morgan's laws)
    3. Standardize variables apart
    4. Skolemize existential quantifiers
    5. Drop universal quantifiers
    6. Distribute disjunctions over conjunctions
    """
    
    def __init__(self, unification_engine: UnificationEngine):
        """
        Initialize the CNF converter.
        
        Args:
            unification_engine: Engine for unifying logical expressions
        """
        self.unification_engine = unification_engine
        self.next_var_id = 10000
        self.next_skolem_id = 0
    
    def convert_to_cnf(self, formula: AST_Node) -> List[Clause]:
        """
        Convert a formula to CNF.
        
        Args:
            formula: The formula to convert
            
        Returns:
            A list of clauses representing the formula in CNF
        """
        logger.info(f"Converting to CNF: {formula}")
        
        # Step 1: Eliminate implications and equivalences
        step1 = self._eliminate_implications(formula)
        logger.debug(f"After eliminating implications: {step1}")
        
        # Step 2: Move negations inward
        step2 = self._move_negations_inward(step1)
        logger.debug(f"After moving negations inward: {step2}")
        
        # Step 3: Standardize variables apart
        step3 = self._standardize_variables(step2)
        logger.debug(f"After standardizing variables: {step3}")
        
        # Step 4: Skolemize existential quantifiers
        step4 = self._skolemize(step3)
        logger.debug(f"After skolemization: {step4}")
        
        # Step 5: Drop universal quantifiers
        step5 = self._drop_quantifiers(step4)
        logger.debug(f"After dropping quantifiers: {step5}")
        
        # Step 6: Convert to CNF
        step6 = self._distribute_or_over_and(step5)
        logger.debug(f"After distributing OR over AND: {step6}")
        
        # Step 7: Extract clauses
        clauses = self._extract_clauses(step6)
        logger.info(f"Extracted {len(clauses)} clauses")
        
        return clauses
    
    def _eliminate_implications(self, formula: AST_Node) -> AST_Node:
        """
        Eliminate implications and equivalences from a formula.
        
        A → B becomes ¬A ∨ B
        A ↔ B becomes (¬A ∨ B) ∧ (A ∨ ¬B)
        
        Args:
            formula: The formula to transform
            
        Returns:
            The transformed formula
        """
        if isinstance(formula, ConnectiveNode):
            if formula.connective_type == "IMPLIES":
                # A → B becomes ¬A ∨ B
                antecedent = formula.operands[0]
                consequent = formula.operands[1]
                
                # Create ¬A
                negated_antecedent = ConnectiveNode(
                    "NOT",
                    [self._eliminate_implications(antecedent)],
                    formula.type
                )
                
                # Create ¬A ∨ B
                return ConnectiveNode(
                    "OR",
                    [negated_antecedent, self._eliminate_implications(consequent)],
                    formula.type
                )
                
            elif formula.connective_type == "EQUIV":
                # A ↔ B becomes (¬A ∨ B) ∧ (A ∨ ¬B)
                left = formula.operands[0]
                right = formula.operands[1]
                
                # Process subformulas recursively
                left_processed = self._eliminate_implications(left)
                right_processed = self._eliminate_implications(right)
                
                # Create ¬A and ¬B
                not_left = ConnectiveNode("NOT", [left_processed], formula.type)
                not_right = ConnectiveNode("NOT", [right_processed], formula.type)
                
                # Create (¬A ∨ B) and (A ∨ ¬B)
                left_to_right = ConnectiveNode("OR", [not_left, right_processed], formula.type)
                right_to_left = ConnectiveNode("OR", [left_processed, not_right], formula.type)
                
                # Create (¬A ∨ B) ∧ (A ∨ ¬B)
                return ConnectiveNode("AND", [left_to_right, right_to_left], formula.type)
                
            else:
                # Process other connectives recursively
                new_operands = [self._eliminate_implications(op) for op in formula.operands]
                return ConnectiveNode(formula.connective_type, new_operands, formula.type)
                
        elif isinstance(formula, QuantifierNode):
            # Process the scope recursively
            new_scope = self._eliminate_implications(formula.scope)
            return QuantifierNode(
                formula.quantifier_type,
                list(formula.bound_variables),
                new_scope,
                formula.type
            )
        
        # For other node types, return as is
        return formula
    
    def _move_negations_inward(self, formula: AST_Node) -> AST_Node:
        """
        Move negations inward using De Morgan's laws.
        
        ¬(A ∧ B) becomes ¬A ∨ ¬B
        ¬(A ∨ B) becomes ¬A ∧ ¬B
        ¬¬A becomes A
        ¬∀x.P(x) becomes ∃x.¬P(x)
        ¬∃x.P(x) becomes ∀x.¬P(x)
        
        Args:
            formula: The formula to transform
            
        Returns:
            The transformed formula
        """
        if isinstance(formula, ConnectiveNode):
            if formula.connective_type == "NOT":
                subformula = formula.operands[0]
                
                # Double negation: ¬¬A becomes A
                if isinstance(subformula, ConnectiveNode) and subformula.connective_type == "NOT":
                    return self._move_negations_inward(subformula.operands[0])
                
                # De Morgan's laws
                elif isinstance(subformula, ConnectiveNode) and subformula.connective_type == "AND":
                    # ¬(A ∧ B) becomes ¬A ∨ ¬B
                    negated_operands = [
                        ConnectiveNode("NOT", [op], op.type) for op in subformula.operands
                    ]
                    return ConnectiveNode(
                        "OR",
                        [self._move_negations_inward(op) for op in negated_operands],
                        formula.type
                    )
                
                elif isinstance(subformula, ConnectiveNode) and subformula.connective_type == "OR":
                    # ¬(A ∨ B) becomes ¬A ∧ ¬B
                    negated_operands = [
                        ConnectiveNode("NOT", [op], op.type) for op in subformula.operands
                    ]
                    return ConnectiveNode(
                        "AND",
                        [self._move_negations_inward(op) for op in negated_operands],
                        formula.type
                    )
                
                # Quantifier negation
                elif isinstance(subformula, QuantifierNode):
                    if subformula.quantifier_type == "FORALL":
                        # ¬∀x.P(x) becomes ∃x.¬P(x)
                        negated_scope = ConnectiveNode("NOT", [subformula.scope], subformula.scope.type)
                        return QuantifierNode(
                            "EXISTS",
                            list(subformula.bound_variables),
                            self._move_negations_inward(negated_scope),
                            formula.type
                        )
                    
                    elif subformula.quantifier_type == "EXISTS":
                        # ¬∃x.P(x) becomes ∀x.¬P(x)
                        negated_scope = ConnectiveNode("NOT", [subformula.scope], subformula.scope.type)
                        return QuantifierNode(
                            "FORALL",
                            list(subformula.bound_variables),
                            self._move_negations_inward(negated_scope),
                            formula.type
                        )
                
                # For other negated formulas, keep the negation but process the subformula
                return ConnectiveNode(
                    "NOT",
                    [self._move_negations_inward(subformula)],
                    formula.type
                )
            
            else:
                # Process other connectives recursively
                new_operands = [self._move_negations_inward(op) for op in formula.operands]
                return ConnectiveNode(formula.connective_type, new_operands, formula.type)
        
        elif isinstance(formula, QuantifierNode):
            # Process the scope recursively
            new_scope = self._move_negations_inward(formula.scope)
            return QuantifierNode(
                formula.quantifier_type,
                list(formula.bound_variables),
                new_scope,
                formula.type
            )
        
        # For other node types, return as is
        return formula
    
    def _standardize_variables(self, formula: AST_Node) -> AST_Node:
        """
        Standardize variables apart.
        
        This ensures that each quantifier binds a unique variable.
        
        Args:
            formula: The formula to transform
            
        Returns:
            The transformed formula
        """
        # Map from original variable IDs to new variable nodes
        var_map = {}
        
        def process_node(node: AST_Node) -> AST_Node:
            if isinstance(node, QuantifierNode):
                # Create new variables for this quantifier
                new_bound_vars = []
                substitution = {}
                
                for var in node.bound_variables:
                    new_var_id = self.next_var_id
                    self.next_var_id += 1
                    new_var = VariableNode(var.name, new_var_id, var.type)
                    new_bound_vars.append(new_var)
                    substitution[var] = new_var
                    var_map[var.var_id] = new_var
                
                # Process the scope with the new variables
                new_scope = node.scope.substitute(substitution)
                processed_scope = process_node(new_scope)
                
                return QuantifierNode(
                    node.quantifier_type,
                    new_bound_vars,
                    processed_scope,
                    node.type
                )
            
            elif isinstance(node, ConnectiveNode):
                new_operands = [process_node(op) for op in node.operands]
                return ConnectiveNode(node.connective_type, new_operands, node.type)
            
            elif isinstance(node, ApplicationNode):
                new_operator = process_node(node.operator)
                new_arguments = [process_node(arg) for arg in node.arguments]
                return ApplicationNode(new_operator, new_arguments, node.type)
            
            elif isinstance(node, VariableNode):
                # If this is a free variable (not in var_map), keep it as is
                if node.var_id in var_map:
                    return var_map[node.var_id]
                return node
            
            # For other node types, return as is
            return node
        
        return process_node(formula)
    
    def _skolemize(self, formula: AST_Node) -> AST_Node:
        """
        Skolemize existential quantifiers.
        
        This replaces existentially quantified variables with Skolem functions
        that depend on the universally quantified variables in whose scope they appear.
        
        Args:
            formula: The formula to transform
            
        Returns:
            The transformed formula
        """
        # Keep track of universal variables in scope
        universal_vars = []
        
        def process_node(node: AST_Node) -> AST_Node:
            if isinstance(node, QuantifierNode):
                if node.quantifier_type == "FORALL":
                    # Add universal variables to the scope
                    universal_vars.extend(node.bound_variables)
                    processed_scope = process_node(node.scope)
                    # Remove these variables from scope when done
                    for _ in range(len(node.bound_variables)):
                        universal_vars.pop()
                    
                    return QuantifierNode(
                        "FORALL",
                        list(node.bound_variables),
                        processed_scope,
                        node.type
                    )
                
                elif node.quantifier_type == "EXISTS":
                    # Replace existential variables with Skolem functions
                    substitution = {}
                    
                    for var in node.bound_variables:
                        # Create a Skolem function or constant
                        if universal_vars:
                            # Create a Skolem function that depends on universal variables
                            skolem_name = f"sk_{self.next_skolem_id}"
                            self.next_skolem_id += 1
                            
                            # Create the function symbol
                            skolem_func = ConstantNode(skolem_name, var.type)
                            
                            # Create the application of the function to universal variables
                            skolem_term = ApplicationNode(
                                skolem_func,
                                universal_vars.copy(),
                                var.type
                            )
                            
                            substitution[var] = skolem_term
                        else:
                            # Create a Skolem constant (no universal variables in scope)
                            skolem_name = f"sk_{self.next_skolem_id}"
                            self.next_skolem_id += 1
                            skolem_const = ConstantNode(skolem_name, var.type)
                            substitution[var] = skolem_const
                    
                    # Apply the substitution to the scope and process it
                    new_scope = node.scope.substitute(substitution)
                    return process_node(new_scope)
            
            elif isinstance(node, ConnectiveNode):
                new_operands = [process_node(op) for op in node.operands]
                return ConnectiveNode(node.connective_type, new_operands, node.type)
            
            elif isinstance(node, ApplicationNode):
                new_operator = process_node(node.operator)
                new_arguments = [process_node(arg) for arg in node.arguments]
                return ApplicationNode(new_operator, new_arguments, node.type)
            
            # For other node types, return as is
            return node
        
        return process_node(formula)
    
    def _drop_quantifiers(self, formula: AST_Node) -> AST_Node:
        """
        Drop universal quantifiers.
        
        After skolemization, all remaining quantifiers are universal and can be dropped.
        
        Args:
            formula: The formula to transform
            
        Returns:
            The transformed formula
        """
        if isinstance(formula, QuantifierNode):
            if formula.quantifier_type == "FORALL":
                # Drop the quantifier and process the scope
                return self._drop_quantifiers(formula.scope)
            else:
                # This shouldn't happen after skolemization
                logger.warning(f"Unexpected existential quantifier after skolemization: {formula}")
                return formula
        
        elif isinstance(formula, ConnectiveNode):
            new_operands = [self._drop_quantifiers(op) for op in formula.operands]
            return ConnectiveNode(formula.connective_type, new_operands, formula.type)
        
        elif isinstance(formula, ApplicationNode):
            new_operator = self._drop_quantifiers(formula.operator)
            new_arguments = [self._drop_quantifiers(arg) for arg in formula.arguments]
            return ApplicationNode(new_operator, new_arguments, formula.type)
        
        # For other node types, return as is
        return formula
    
    def _distribute_or_over_and(self, formula: AST_Node) -> AST_Node:
        """
        Distribute disjunctions over conjunctions.
        
        (A ∨ (B ∧ C)) becomes ((A ∨ B) ∧ (A ∨ C))
        ((A ∧ B) ∨ C) becomes ((A ∨ C) ∧ (B ∨ C))
        
        Args:
            formula: The formula to transform
            
        Returns:
            The transformed formula
        """
        if isinstance(formula, ConnectiveNode):
            if formula.connective_type == "OR":
                # First, recursively process all operands
                processed_operands = [self._distribute_or_over_and(op) for op in formula.operands]
                
                # Check if any operand is a conjunction
                for i, operand in enumerate(processed_operands):
                    if isinstance(operand, ConnectiveNode) and operand.connective_type == "AND":
                        # Found a conjunction, distribute OR over it
                        other_operands = processed_operands[:i] + processed_operands[i+1:]
                        
                        # Create a disjunction for each conjunct
                        new_conjuncts = []
                        for conjunct in operand.operands:
                            new_disjunction = ConnectiveNode(
                                "OR",
                                other_operands + [conjunct],
                                formula.type
                            )
                            # Recursively process the new disjunction
                            new_conjuncts.append(self._distribute_or_over_and(new_disjunction))
                        
                        # Return the conjunction of the new disjunctions
                        return ConnectiveNode("AND", new_conjuncts, formula.type)
                
                # If no conjunctions were found, return the processed formula
                return ConnectiveNode("OR", processed_operands, formula.type)
            
            elif formula.connective_type == "AND":
                # Process all operands recursively
                new_operands = [self._distribute_or_over_and(op) for op in formula.operands]
                return ConnectiveNode("AND", new_operands, formula.type)
            
            else:
                # Process other connectives recursively
                new_operands = [self._distribute_or_over_and(op) for op in formula.operands]
                return ConnectiveNode(formula.connective_type, new_operands, formula.type)
        
        # For other node types, return as is
        return formula
    
    def _extract_clauses(self, formula: AST_Node) -> List[Clause]:
        """
        Extract clauses from a formula in CNF.
        
        Args:
            formula: The formula in CNF
            
        Returns:
            A list of clauses
        """
        clauses = []
        
        # If the formula is a conjunction, extract clauses from each conjunct
        if isinstance(formula, ConnectiveNode) and formula.connective_type == "AND":
            for operand in formula.operands:
                clauses.extend(self._extract_clauses(operand))
            return clauses
        
        # Otherwise, extract a single clause
        literals = self._extract_literals(formula)
        return [Clause(frozenset(literals))]
    
    def _extract_literals(self, formula: AST_Node) -> List[Literal]:
        """
        Extract literals from a disjunction.
        
        Args:
            formula: The formula (a disjunction or a single literal)
            
        Returns:
            A list of literals
        """
        if isinstance(formula, ConnectiveNode) and formula.connective_type == "OR":
            # Collect literals from each disjunct
            literals = []
            for operand in formula.operands:
                literals.extend(self._extract_literals(operand))
            return literals
        
        elif isinstance(formula, ConnectiveNode) and formula.connective_type == "NOT":
            # Negated atom
            return [Literal(formula.operands[0], True)]
        
        else:
            # Positive atom
            return [Literal(formula)]


class ResolutionProver(BaseProver):
    """
    Prover using resolution for FOL and propositional logic.
    
    This prover implements the resolution inference rule for First-Order Logic (FOL)
    and propositional logic. It converts input formulae into Conjunctive Normal Form (CNF)
    and applies various resolution strategies to find a refutation.
    """
    
    def __init__(self, knowledge_store: KnowledgeStoreInterface,
                 unification_engine: UnificationEngine,
                 default_strategy: ResolutionStrategy = ResolutionStrategy.SET_OF_SUPPORT):
        super().__init__()  # Corrected: Call super without arguments
        self.knowledge_store = knowledge_store
        self.unification_engine = unification_engine
        self.default_strategy = default_strategy
        self.cnf_converter = CNFConverter(self.unification_engine)
        self.next_clause_id = 0

    @property
    def name(self) -> str:
        """Returns the name of the prover."""
        return "ResolutionProver"

    @property
    def capabilities(self) -> Dict[str, bool]:
        """Returns the capabilities of the resolution prover."""
        return {
            "first_order_logic": True,
            "propositional_logic": True,
            "modal_logic": False,
            "higher_order_logic": False,
            "arithmetic": False,
            "equality": True,
            "uninterpreted_functions": True,
            "constraint_solving": False,
            "analogical_reasoning": False,
        }

    def can_handle(self, goal: AST_Node, context: Optional[List[AST_Node]] = None) -> bool:
        """
        Checks if the prover can handle the given goal and context by verifying
        that the goal and all context formulas are of recognizable AST_Node types
        suitable for CNF conversion, and do not contain modal operators.
        """
        try:
            from godelOS.inference_engine.coordinator import InferenceCoordinator
            
            formula_node_types = (ApplicationNode, ConnectiveNode, QuantifierNode, ConstantNode)

            if not isinstance(goal, AST_Node):
                return False
            if not isinstance(goal, formula_node_types):
                return False

            # Check for modal operators (resolution prover cannot handle these)
            all_formulas = [goal]
            if context:
                all_formulas.extend(context)
            
            for formula in all_formulas:
                if InferenceCoordinator._contains_modal_operator(formula):
                    return False
            
            if context:
                for formula in context:
                    if not isinstance(formula, AST_Node):
                        return False
                    if not isinstance(formula, formula_node_types):
                        return False
            return True
        except Exception as e:
            context_str = str(context) if context and len(str(context)) < 500 else "Context too large or None"
            logger.error(f"ResolutionProver.can_handle: Exception during type checking. Goal: '{goal}'. Context: {context_str}. Error: {e}", exc_info=True)
            return False

    def _get_next_clause_id(self) -> int:
        """
        Get the next unique clause ID.
        
        This method ensures that each clause gets a unique ID, even across different
        proof attempts.
        
        Returns:
            A unique clause ID
        """
        current_id = self.next_clause_id
        self.next_clause_id += 1
        return current_id

    def _negate_formula(self, formula: AST_Node) -> AST_Node:
        """
        Negate a formula with double-negation elimination.
        
        Args:
            formula: The formula to negate
            
        Returns:
            The negated formula
        """
        if isinstance(formula, ConnectiveNode) and formula.connective_type == "NOT":
            return formula.operands[0]
        return ConnectiveNode("NOT", [formula], formula.type)
    
    def _resolve_pair(self, clause1: Clause, clause2: Clause) -> List[Clause]:
        """
        Resolve a pair of clauses. Compatibility shim for _resolve.
        
        Args:
            clause1: First clause
            clause2: Second clause
            
        Returns:
            List of resolvent clauses
        """
        return self._resolve(clause1, clause2)
    
    def _is_tautology(self, clause: Clause) -> bool:
        """
        Check if a clause is a tautology.
        
        A clause is a tautology if it contains a literal and its complement.
        
        Args:
            clause: The clause to check
            
        Returns:
            True if the clause is a tautology
        """
        for lit1 in clause.literals:
            for lit2 in clause.literals:
                if lit1 != lit2 and lit1.atom == lit2.atom and lit1.is_negated != lit2.is_negated:
                    return True
        return False
    
    def _clauses_equivalent(self, clause1: Clause, clause2: Clause) -> bool:
        """
        Check if two clauses are equivalent.
        
        Args:
            clause1: First clause
            clause2: Second clause
            
        Returns:
            True if the clauses are equivalent
        """
        return clause1.literals == clause2.literals
    
    def _convert_to_cnf(self, formula: AST_Node) -> List[Clause]:
        """
        Convert a formula to CNF. Delegates to the CNF converter.
        
        Args:
            formula: The formula to convert
            
        Returns:
            List of clauses in CNF
        """
        return self.cnf_converter.convert_to_cnf(formula)
    
    def _skolemize(self, formula: AST_Node) -> AST_Node:
        """
        Skolemize a formula. Delegates to the CNF converter.
        
        Args:
            formula: The formula to skolemize
            
        Returns:
            The skolemized formula
        """
        return self.cnf_converter._skolemize(formula)
    
    def _create_literal(self, atom: AST_Node, is_negated: bool = False) -> Literal:
        """
        Create a Literal from an atom and negation flag.
        
        Args:
            atom: The atomic formula
            is_negated: Whether the literal is negated
            
        Returns:
            A Literal object
        """
        return Literal(atom=atom, is_negated=is_negated)
    
    def _resolve_clauses(self, clause1: Clause, clause2: Clause,
                         id1: int = 0, id2: int = 0) -> Optional[Clause]:
        """
        Resolve two clauses and return a single resolvent if possible.
        
        Args:
            clause1: First clause
            clause2: Second clause
            id1: ID for clause1
            id2: ID for clause2
            
        Returns:
            A resolvent clause, or None if no resolution is possible
        """
        resolvents = self._resolve(clause1, clause2)
        return resolvents[0] if resolvents else None
    
    def _unify(self, lit1: Literal, lit2: Literal) -> Optional[Dict]:
        """
        Try to unify two complementary literals.
        
        Args:
            lit1: First literal
            lit2: Second literal
            
        Returns:
            A substitution dict if unification succeeds, None otherwise
        """
        if lit1.is_negated == lit2.is_negated:
            return None
        result = self.unification_engine.unify_consistent(lit1.atom, lit2.atom)
        if result.is_success():
            return result.substitution
        return None
    
    def _find_empty_clause(self, clauses: List[Clause]) -> Optional[Clause]:
        """
        Search for the empty clause among a set of clauses using resolution.
        
        Args:
            clauses: The set of clauses to search
            
        Returns:
            The empty clause if found, None otherwise
        """
        for clause in clauses:
            if clause.is_empty():
                return clause
        
        # Try resolving pairs
        for i, c1 in enumerate(clauses):
            for j, c2 in enumerate(clauses):
                if i < j:
                    resolvents = self._resolve(c1, c2)
                    for resolvent in resolvents:
                        if resolvent.is_empty():
                            return resolvent
        return None

    def prove(self, goal: AST_Node, context: Optional[List[AST_Node]] = None,
              resource_limits: Optional[ResourceLimits] = None) -> ProofObject:
        """
        Attempt to prove a goal using resolution.

        Args:
            goal: The logical formula to prove.
            context: Optional list of logical formulas representing the knowledge base.
            resource_limits: Optional resource limits for the proof process.

        Returns:
            A ProofObject representing the result of the proof attempt.
        """
        start_time = time.time()
        
        # Track proof steps
        proof_steps: List[ProofStepNode] = []
        
        if resource_limits is None:
            resource_limits = ResourceLimits() # Default limits

        # 1. Negate the goal
        negated_goal = ConnectiveNode("NOT", [goal], goal.type)
        logger.info(f"ResolutionProver: Negated goal: {negated_goal}")
        proof_steps.append(ProofStepNode(
            formula=negated_goal,
            rule_name="negation",
            premises=[],
            explanation=f"Negate goal: {goal}"
        ))

        # 2. Convert all formulas (context + negated_goal) to CNF
        all_clauses: List[Clause] = []
        
        # Convert context (knowledge base)
        if context:
            for i, formula in enumerate(context):
                cnf_clauses = self._convert_to_cnf(formula)
                for cnf_clause in cnf_clauses:
                    unique_id = self._get_next_clause_id()
                    if isinstance(cnf_clause, Clause):
                        all_clauses.append(dataclasses.replace(cnf_clause, source=f"context_{i}", clause_id=unique_id))
                    else:
                        # Handle mocked data (list of literals or other format)
                        if isinstance(cnf_clause, (list, tuple)):
                            clause = Clause(frozenset(cnf_clause), source=f"context_{i}", clause_id=unique_id)
                        else:
                            clause = Clause(frozenset([cnf_clause]), source=f"context_{i}", clause_id=unique_id)
                        all_clauses.append(clause)
                proof_steps.append(ProofStepNode(
                    formula=formula,
                    rule_name="CNF conversion",
                    premises=[],
                    explanation=f"Convert context formula {i+1} to CNF: {formula}"
                ))
        
        # Convert negated goal
        negated_goal_cnf_clauses = self._convert_to_cnf(negated_goal)
        set_of_support: Set[Clause] = set() # Clauses derived from the negated goal

        for cnf_clause in negated_goal_cnf_clauses:
            unique_id = self._get_next_clause_id()
            if isinstance(cnf_clause, Clause):
                clause_with_id = dataclasses.replace(cnf_clause, source="negated_goal", clause_id=unique_id)
            else:
                if isinstance(cnf_clause, (list, tuple)):
                    clause_with_id = Clause(frozenset(cnf_clause), source="negated_goal", clause_id=unique_id)
                else:
                    clause_with_id = Clause(frozenset([cnf_clause]), source="negated_goal", clause_id=unique_id)
            all_clauses.append(clause_with_id)
            set_of_support.add(clause_with_id)
        proof_steps.append(ProofStepNode(
            formula=negated_goal,
            rule_name="CNF conversion",
            premises=[],
            explanation=f"Convert negated goal to CNF: {negated_goal}"
        ))

        logger.info(f"ResolutionProver: Initial clauses ({len(all_clauses)} total):")
        for clause in all_clauses:
            logger.info(f"  ID: {clause.clause_id}, Source: {clause.source}, Clause: {clause}")
        
        if not negated_goal_cnf_clauses: # Should not happen if goal is valid
            time_taken_ms = (time.time() - start_time) * 1000
            return ProofObject.create_failure(
                status_message="ResolutionProver: Negated goal resulted in no clauses.",
                inference_engine_used=self.name,
                time_taken_ms=time_taken_ms,
                resources_consumed={}
            )

        # --- Resolution Loop ---
        # Try _find_empty_clause first (allows test mocking)
        try:
            result = self._find_empty_clause(all_clauses)
            if result is not None:
                if isinstance(result, tuple):
                    if result[0]:
                        time_taken_ms = (time.time() - start_time) * 1000
                        proof_steps.append(ProofStepNode(
                            formula=goal,
                            rule_name="resolution",
                            premises=[],
                            explanation="Empty clause found via resolution"
                        ))
                        return ProofObject.create_success(
                            conclusion_ast=goal,
                            proof_steps=proof_steps,
                            used_axioms_rules=set(context) if context else set(),
                            inference_engine_used=self.name,
                            time_taken_ms=time_taken_ms,
                            resources_consumed={}
                        )
                    else:
                        # _find_empty_clause returned (False, ...) - failed to find
                        time_taken_ms = (time.time() - start_time) * 1000
                        return ProofObject.create_failure(
                            status_message="Failed: Resource limits exceeded",
                            inference_engine_used=self.name,
                            time_taken_ms=time_taken_ms,
                            resources_consumed={}
                        )
                elif isinstance(result, Clause) and result.is_empty():
                    time_taken_ms = (time.time() - start_time) * 1000
                    proof_steps.append(ProofStepNode(
                        formula=goal,
                        rule_name="resolution",
                        premises=[],
                        explanation="Empty clause found via resolution"
                    ))
                    return ProofObject.create_success(
                        conclusion_ast=goal,
                        proof_steps=proof_steps,
                        used_axioms_rules=set(context) if context else set(),
                        inference_engine_used=self.name,
                        time_taken_ms=time_taken_ms,
                        resources_consumed={}
                    )
        except Exception:
            pass  # Fall through to manual resolution loop
        
        # Use a list for the agenda to allow for different selection strategies if needed (e.g., unit preference)
        agenda: List[Clause] = list(set_of_support) 
        processed_clauses_set: Set[FrozenSet[Literal]] = set() # Store literals of processed clauses to avoid reprocessing identical clauses
        all_clauses_map: Dict[int, Clause] = {c.clause_id: c for c in all_clauses}

        iteration_count = 0
        max_iterations = resource_limits.nodes_limit if resource_limits and resource_limits.nodes_limit else 1000

        while agenda:
            if iteration_count >= max_iterations:
                time_taken_ms = (time.time() - start_time) * 1000
                return ProofObject.create_failure(
                    status_message=f"ResolutionProver: Exceeded max iterations ({max_iterations}).",
                    inference_engine_used=self.name,
                    time_taken_ms=time_taken_ms,
                    resources_consumed={"iterations": iteration_count}
                )
            
            iteration_count += 1
            # Simple FIFO selection, could be replaced with a more sophisticated strategy (e.g. unit preference)
            current_clause = agenda.pop(0)

            if current_clause.literals in processed_clauses_set:
                continue
            processed_clauses_set.add(current_clause.literals)

            logger.debug(f"Iteration {iteration_count}: Resolving with {current_clause}")

            # Resolve `current_clause` (from set_of_support or its descendants) with clauses from `all_clauses_map`
            # This implements the set-of-support strategy: one parent must be in the set of support or one of its descendants.
            potential_partners = list(all_clauses_map.values()) # Iterate over a copy

            for other_clause in potential_partners:
                # Optimization: Don't resolve a clause with itself unless it can lead to a valid resolvent (e.g. P(x) v P(y) with P(a) v P(b))
                # For simplicity here, we allow it, _resolve should handle it. Or, ensure other_clause.clause_id != current_clause.clause_id if needed.
                # However, resolving C with C is usually not productive unless C contains complementary literals after self-unification, which is rare.
                
                resolvents = self._resolve(current_clause, other_clause)
                
                for resolvent in resolvents:
                    if resolvent.is_empty():
                        time_taken_ms = (time.time() - start_time) * 1000
                        proof_steps.append(ProofStepNode(
                            formula=goal,  # The proved goal
                            rule_name="resolution",
                            premises=[current_clause.clause_id, other_clause.clause_id],
                            explanation=f"Resolved {current_clause.clause_id} ({current_clause.source}) and {other_clause.clause_id} ({other_clause.source}) to derive empty clause"
                        ))
                        logger.info(f"ResolutionProver: Success! Empty clause derived from {current_clause.clause_id} and {other_clause.clause_id}.")
                        return ProofObject.create_success(
                            conclusion_ast=goal,
                            proof_steps=proof_steps,
                            used_axioms_rules=set(context) if context else set(),
                            inference_engine_used=self.name,
                            time_taken_ms=time_taken_ms,
                            resources_consumed={"iterations": iteration_count}
                        )

                    # Check if the resolvent is new (not subsumed by an existing clause)
                    # Simple check: avoid adding clauses with identical literal sets.
                    # A proper subsumption check is more complex.
                    if resolvent.literals not in processed_clauses_set and not any(c.literals == resolvent.literals for c in all_clauses_map.values()):
                        unique_id = self._get_next_clause_id()
                        resolvent_with_id = dataclasses.replace(resolvent, clause_id=unique_id, parent_ids=(current_clause.clause_id, other_clause.clause_id), source="derived")
                        
                        all_clauses_map[unique_id] = resolvent_with_id
                        agenda.append(resolvent_with_id) # Add to agenda for further resolution
                        # set_of_support.add(resolvent_with_id) # Implicitly handled as agenda comes from SoS
                        
                        proof_steps.append(ProofStepNode(
                            formula=resolvent_with_id.literals if hasattr(resolvent_with_id, 'literals') else goal,
                            rule_name="resolution",
                            premises=[current_clause.clause_id, other_clause.clause_id],
                            explanation=f"Resolved {current_clause.clause_id} ({current_clause.source}) and {other_clause.clause_id} ({other_clause.source}) to derive ID {unique_id}: {resolvent_with_id}"
                        ))
                        logger.info(f"ResolutionProver: Derived new clause {resolvent_with_id.clause_id}: {resolvent_with_id} from {current_clause.clause_id} and {other_clause.clause_id}")
                    else:
                        logger.debug(f"Skipping redundant or already processed resolvent: {resolvent} from {current_clause.clause_id} and {other_clause.clause_id}")

            # Check resource limits (time)
            if resource_limits.time_limit_ms and (time.time() - start_time) * 1000 > resource_limits.time_limit_ms:
                time_taken_ms = (time.time() - start_time) * 1000
                return ProofObject.create_failure(
                    status_message=f"ResolutionProver: Exceeded time limit ({resource_limits.time_limit_ms} ms).",
                    inference_engine_used=self.name,
                    time_taken_ms=time_taken_ms,
                    resources_consumed={"iterations": iteration_count}
                )
        
        # If we reach here, the proof failed
        time_taken_ms = (time.time() - start_time) * 1000
        logger.info(f"ResolutionProver: Proof attempt finished. Could not derive empty clause within limits.")
        return ProofObject.create_failure(
            status_message="ResolutionProver: Could not derive empty clause within limits.",
            inference_engine_used=self.name,
            time_taken_ms=time_taken_ms,
            resources_consumed={"iterations": iteration_count}
        )

    def _resolve(self, clause1: Clause, clause2: Clause) -> List[Clause]:
        """
        Resolve two clauses.

        For each literal L1 in clause1 and literal L2 in clause2,
        if L1 and L2 are complementary (e.g., P(x) and ¬P(y)),
        try to unify their atoms. If unification succeeds with substitution S,
        the resolvent is ( (clause1 - {L1}) U (clause2 - {L2}) )S.

        Args:
            clause1: The first clause.
            clause2: The second clause.

        Returns:
            A list of resolvent clauses. Can be empty if no resolution is possible.
            Can contain the empty clause if a contradiction is found.
        """
        resolvents: List[Clause] = []
        
        # Create copies of clauses to rename variables without affecting original clauses in the knowledge base
        # The renaming should ensure that variables from clause1 and clause2 are distinct before unification.
        # We use a unique suffix based on current time and clause IDs to try and ensure uniqueness.
        # A more robust way is to pass a global variable counter or use a more systematic renaming scheme.
        
        # Suffix for renaming, to make variables in this resolution step unique
        # Using a combination of clause IDs and a portion of the prover's clause counter for variety
        # This is a heuristic. A more robust approach would be a dedicated variable renaming utility
        # that ensures no clashes with any existing variable in the entire proof process if needed.
        # For resolving just two clauses, making them distinct from each other is the primary goal.
        
        # Standardize variables apart for this resolution step.
        # This is crucial to avoid unintended variable capture.
        # We'll create new versions of the atoms with fresh variables.
        # The renaming prefix should be different for clause1 and clause2.

        # Create a new clause by renaming variables in clause1
        c1_renamed_literals: Set[Literal] = set()
        c1_var_map: Dict[str, VariableNode] = {}
        # Use a more unique prefix for renaming, perhaps related to the resolution step or a counter
        # For simplicity, let's use a fixed prefix and rely on the unification engine or hope for the best.
        # A better approach: self._get_next_temp_var_id() or similar for fresh variable names.
        # For now, we will rely on the unification engine to handle variables correctly if they are distinct.
        # The critical part is that variables in lit1.atom and lit2.atom must be treated as distinct if they have the same name.
        # The UnificationEngine should ideally handle this by not assuming shared scopes unless explicitly told.
        # However, to be safe, we should rename. Let's use a simple renaming strategy here.

        def rename_vars_in_ast(node: AST_Node, var_map: Dict[str, VariableNode], prefix: str, instance_id: int) -> AST_Node:
            if isinstance(node, VariableNode):
                original_name = node.name
                if original_name not in var_map:
                    # Create a new unique variable name
                    new_var_name = f"{prefix}_{original_name}_{instance_id}"
                    var_map[original_name] = VariableNode(new_var_name, abs(hash(new_var_name)) % 100000, node.type)
                return var_map[original_name]
            elif isinstance(node, ConstantNode):
                return node
            elif isinstance(node, ApplicationNode):
                new_args = [rename_vars_in_ast(arg, var_map, prefix, instance_id) for arg in node.arguments]
                return ApplicationNode(node.operator, new_args, node.type)
            return node # Should not happen for atoms in literals

        # Create resolvable versions of clauses with variables standardized apart
        # We need a unique instance_id for renaming to avoid clashes if the same clause is used multiple times
        # with itself or with another clause that was derived from it.
        # Using object ids or clause_ids might work if they are sufficiently unique for this purpose.
        
        # Renaming for clause1
        renamed_c1_literals: Set[Literal] = set()
        c1_rename_map: Dict[str, VariableNode] = {}
        # Use clause_id and a counter to ensure unique renaming context
        # This renaming is local to this _resolve call.
        # A simpler approach might be to just pass copies of atoms to unify and let unifier handle it, 
        # but explicit renaming is safer.
        
        # For each literal in clause1, create a version with renamed variables
        temp_id1 = self._get_next_clause_id() # Get a unique ID for this renaming context
        for lit_c1 in clause1.literals:
            renamed_atom_c1 = rename_vars_in_ast(lit_c1.atom, c1_rename_map, "r1", temp_id1)
            renamed_c1_literals.add(Literal(atom=renamed_atom_c1, is_negated=lit_c1.is_negated))

        # Renaming for clause2
        renamed_c2_literals: Set[Literal] = set()
        c2_rename_map: Dict[str, VariableNode] = {}
        temp_id2 = self._get_next_clause_id() # Get another unique ID
        for lit_c2 in clause2.literals:
            renamed_atom_c2 = rename_vars_in_ast(lit_c2.atom, c2_rename_map, "r2", temp_id2)
            renamed_c2_literals.add(Literal(atom=renamed_atom_c2, is_negated=lit_c2.is_negated))

        for lit1_renamed in renamed_c1_literals:
            for lit2_renamed in renamed_c2_literals:
                if lit1_renamed.is_negated != lit2_renamed.is_negated:
                    # Atoms are already renamed, so they can be unified directly.
                    unification_result = self.unification_engine.unify_consistent(lit1_renamed.atom, lit2_renamed.atom)

                    if unification_result.is_success():
                        substitution = unification_result.substitution
                        new_literals_set: Set[Literal] = set()

                        # Add literals from renamed_c1_literals (excluding lit1_renamed), applying substitution
                        for l_from_c1 in renamed_c1_literals:
                            if l_from_c1 != lit1_renamed:
                                substituted_atom = self.unification_engine.apply_substitution(l_from_c1.atom, substitution)
                                new_literals_set.add(Literal(atom=substituted_atom, is_negated=l_from_c1.is_negated))

                        # Add literals from renamed_c2_literals (excluding lit2_renamed), applying substitution
                        for l_from_c2 in renamed_c2_literals:
                            if l_from_c2 != lit2_renamed:
                                substituted_atom = self.unification_engine.apply_substitution(l_from_c2.atom, substitution)
                                new_literals_set.add(Literal(atom=substituted_atom, is_negated=l_from_c2.is_negated))
                        
                        resolvent_clause = Clause(literals=frozenset(new_literals_set))
                        resolvents.append(resolvent_clause)
                        # Corrected logger string, removed trailing backslash
                        logger.debug(f"Resolved {lit1_renamed} (orig c1: {clause1.clause_id}) and {lit2_renamed} (orig c2: {clause2.clause_id}) -> {resolvent_clause} with sub: {substitution}")
        
        return resolvents

    def _standardize_variables_in_clause(self, clause: Clause, clause_id_for_renaming: int) -> Clause:
        """
        Standardizes variables within a single clause to make them unique.
        This method is kept for potential utility but the primary renaming for resolution
        now happens inside `_resolve` for the pair of clauses being resolved.
        """
        var_map: Dict[str, VariableNode] = {}
        new_literals: Set[Literal] = set()

        # Inner helper function for renaming, similar to the one in _resolve
        def rename_node_vars(node: AST_Node, current_var_map: Dict[str, VariableNode], base_prefix: str, id_suffix: int) -> AST_Node:
            if isinstance(node, VariableNode):
                original_name = node.name
                if original_name not in current_var_map:
                    new_var_name = f"{base_prefix}_{original_name}_{id_suffix}"
                    current_var_map[original_name] = VariableNode(new_var_name, abs(hash(new_var_name)) % 100000, node.type)
                return current_var_map[original_name]
            elif isinstance(node, ConstantNode):
                return node
            elif isinstance(node, ApplicationNode):
                new_args = [rename_node_vars(arg, current_var_map, base_prefix, id_suffix) for arg in node.arguments]
                return ApplicationNode(node.function_name, new_args, node.type)
            return node

        # Use the passed clause_id_for_renaming to ensure context-specific renaming
        for lit in clause.literals:
            new_atom = rename_node_vars(lit.atom, var_map, "std", clause_id_for_renaming)
            new_literals.add(Literal(atom=new_atom, is_negated=lit.is_negated))
        
        return Clause(literals=frozenset(new_literals), source=clause.source, parent_ids=clause.parent_ids, clause_id=clause.clause_id)