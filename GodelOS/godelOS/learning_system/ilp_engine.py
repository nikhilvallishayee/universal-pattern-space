"""
Inductive Logic Programming Engine (ILPEngine) for GödelOS.

This module implements the ILPEngine component (Module 3.1) of the Learning System,
which is responsible for inducing new logical rules from positive and negative examples,
given background knowledge from the KR system.

The ILPEngine uses a top-down sequential covering algorithm similar to FOIL/Progol
to generate rule hypotheses that are consistent with positive examples and
inconsistent with negative examples.
"""

import math
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, DefaultDict
from collections import defaultdict
from dataclasses import dataclass, field

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode, ConnectiveNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.coordinator import InferenceCoordinator
from godelOS.inference_engine.proof_object import ProofObject

logger = logging.getLogger(__name__)


@dataclass
class ModeDeclaration:
    """
    Represents a mode declaration for a predicate in the language bias.
    
    Mode declarations specify how predicates can be used in rule hypotheses,
    including input/output modes for arguments.
    
    Example: modeh(1, parent(+person, -person)) specifies that the first argument
    of parent must be an input variable (already bound) and the second must be an
    output variable (to be bound).
    """
    predicate_name: str
    arg_modes: List[str]  # '+' for input, '-' for output, '#' for constant
    arg_types: List[str]
    recall: int = 1  # Maximum number of alternative solutions to consider
    
    def __post_init__(self):
        """Validate the mode declaration after initialization."""
        if len(self.arg_modes) != len(self.arg_types):
            raise ValueError(f"Number of argument modes ({len(self.arg_modes)}) must match number of argument types ({len(self.arg_types)})")
        
        for mode in self.arg_modes:
            if mode not in ['+', '-', '#']:
                raise ValueError(f"Invalid argument mode: {mode}. Must be '+', '-', or '#'")


@dataclass
class LanguageBias:
    """
    Represents the language bias for the ILP engine.
    
    Language bias constrains the form of learnable rules, which is crucial for
    controlling the size of the hypothesis space.
    """
    mode_declarations: List[ModeDeclaration] = field(default_factory=list)
    type_restrictions: Dict[str, str] = field(default_factory=dict)  # PredicateName -> AllowedArgumentTypes
    max_clause_length: int = 5
    max_variables: int = 10
    allow_recursion: bool = False
    
    def add_mode_declaration(self, mode_declaration: ModeDeclaration) -> None:
        """
        Add a mode declaration to the language bias.
        
        Args:
            mode_declaration: The mode declaration to add
        """
        self.mode_declarations.append(mode_declaration)
    
    def add_type_restriction(self, predicate_name: str, allowed_types: str) -> None:
        """
        Add a type restriction to the language bias.
        
        Args:
            predicate_name: The name of the predicate
            allowed_types: The allowed argument types for the predicate
        """
        self.type_restrictions[predicate_name] = allowed_types


@dataclass
class Clause:
    """
    Represents a clause (rule) in the hypothesis space.
    
    A clause consists of a head (the conclusion) and a body (the premises).
    The body is a list of literals (AST_Nodes) that must all be true for the head to be true.
    """
    head: AST_Node
    body: List[AST_Node] = field(default_factory=list)
    
    @property
    def length(self) -> int:
        """Get the length of the clause (number of literals in the body)."""
        return len(self.body)
    
    def to_ast(self) -> AST_Node:
        """
        Convert the clause to an AST_Node.
        
        If the body is empty, returns just the head.
        Otherwise, returns an implication: body -> head.
        
        Returns:
            An AST_Node representing the clause
        """
        if not self.body:
            return self.head
        
        # Create a conjunction of the body literals
        if len(self.body) == 1:
            body_ast = self.body[0]
        else:
            # Create a conjunction of all body literals
            body_ast = ConnectiveNode(
                connective_type="AND",
                operands=self.body,
                type_ref=self.body[0].type  # Assuming all literals have the same type
            )
        
        # Create an implication: body -> head
        return ConnectiveNode(
            connective_type="IMPLIES",
            operands=[body_ast, self.head],
            type_ref=self.head.type
        )
    
    def __str__(self) -> str:
        """String representation of the clause."""
        head_str = str(self.head)
        if not self.body:
            return f"{head_str} ← true"
        body_str = ", ".join(str(lit) for lit in self.body)
        return f"{head_str} ← {body_str}"


class CoverageCache:
    """
    Cache for clause coverage results to speed up evaluation.
    
    This class caches the results of coverage checks to avoid redundant
    computation when evaluating similar clauses.
    """
    
    def __init__(self):
        """Initialize the coverage cache."""
        self._cache: Dict[int, Tuple[Set[AST_Node], Set[AST_Node]]] = {}
    
    def get(self, clause: Clause) -> Optional[Tuple[Set[AST_Node], Set[AST_Node]]]:
        """
        Get the cached coverage for a clause.
        
        Args:
            clause: The clause to get coverage for
            
        Returns:
            A tuple of (positive_covered, negative_covered) if cached, None otherwise
        """
        clause_hash = hash(str(clause))
        return self._cache.get(clause_hash)
    
    def put(self, clause: Clause, positive_covered: Set[AST_Node], negative_covered: Set[AST_Node]) -> None:
        """
        Cache the coverage for a clause.
        
        Args:
            clause: The clause to cache coverage for
            positive_covered: The set of positive examples covered by the clause
            negative_covered: The set of negative examples covered by the clause
        """
        clause_hash = hash(str(clause))
        self._cache[clause_hash] = (positive_covered, negative_covered)
    
    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()


class ILPEngine:
    """
    Inductive Logic Programming Engine for GödelOS.
    
    This class implements the ILPEngine component (Module 3.1) of the Learning System,
    which is responsible for inducing new logical rules from positive and negative examples,
    given background knowledge from the KR system.
    """
    
    def __init__(self, kr_system_interface: KnowledgeStoreInterface, 
                 inference_engine: InferenceCoordinator,
                 language_bias: Optional[LanguageBias] = None):
        """
        Initialize the ILP engine.
        
        Args:
            kr_system_interface: Interface to the Knowledge Representation system
            inference_engine: The inference engine for coverage checking
            language_bias: Optional language bias configuration
        """
        self.ksi = kr_system_interface
        self.inference_engine = inference_engine
        self.language_bias = language_bias or LanguageBias()
        self.coverage_cache = CoverageCache()
    
    def induce_rules(self, target_predicate_signature: AST_Node, 
                    positive_examples: Set[AST_Node], 
                    negative_examples: Set[AST_Node],
                    background_context_id: str = "TRUTHS") -> List[AST_Node]:
        """
        Induce rules from positive and negative examples.
        
        This method implements a top-down sequential covering algorithm similar to FOIL/Progol.
        It iteratively learns clauses that cover positive examples and exclude negative examples,
        adding each learned clause to the theory and removing the covered positive examples.
        
        Args:
            target_predicate_signature: The signature of the target predicate to learn
            positive_examples: Set of positive examples
            negative_examples: Set of negative examples
            background_context_id: The context ID for background knowledge
            
        Returns:
            A list of induced rules as AST_Nodes
        """
        logger.info(f"Inducing rules for {target_predicate_signature}")
        logger.info(f"Positive examples: {len(positive_examples)}")
        logger.info(f"Negative examples: {len(negative_examples)}")
        
        # Get background knowledge from the knowledge store
        background_knowledge = self._get_background_knowledge(background_context_id)
        
        # Initialize the current positive examples and learned theory
        current_positive_examples = positive_examples.copy()
        learned_theory = []
        
        # Sequential covering: learn clauses until all positive examples are covered
        while current_positive_examples:
            logger.info(f"Remaining positive examples: {len(current_positive_examples)}")
            
            # Find the best clause
            best_clause = self._find_best_clause(
                target_predicate_signature,
                current_positive_examples,
                negative_examples,
                background_knowledge
            )
            
            # If no good clause found, break
            if best_clause is None:
                logger.warning("No good clause found, stopping induction")
                break
            
            # Convert the clause to an AST_Node and add it to the learned theory
            clause_ast = best_clause.to_ast()
            learned_theory.append(clause_ast)
            
            logger.info(f"Learned clause: {best_clause}")
            
            # Remove positive examples covered by the new clause
            positive_covered, _ = self._get_coverage(best_clause, current_positive_examples, negative_examples, background_knowledge)
            current_positive_examples = current_positive_examples - positive_covered
        
        return learned_theory
    
    def _find_best_clause(self, target_predicate_signature: AST_Node,
                         positive_examples: Set[AST_Node],
                         negative_examples: Set[AST_Node],
                         background_knowledge: Set[AST_Node]) -> Optional[Clause]:
        """
        Find the best clause for the given examples.
        
        This method implements a general-to-specific search to find the best clause
        that covers positive examples and excludes negative examples.
        
        Args:
            target_predicate_signature: The signature of the target predicate to learn
            positive_examples: Set of positive examples
            negative_examples: Set of negative examples
            background_knowledge: Set of background knowledge
            
        Returns:
            The best clause found, or None if no good clause was found
        """
        # Start with the most general clause (head ← true)
        start_clause = Clause(head=target_predicate_signature)
        
        # Initialize search queue with the starting clause
        search_queue = [start_clause]
        
        # Initialize best clause and score
        best_clause = None
        best_score = float('-inf')
        
        # Set search limits
        max_iterations = 1000
        max_clause_length = self.language_bias.max_clause_length
        
        # General-to-specific search
        iterations = 0
        while search_queue and iterations < max_iterations:
            iterations += 1
            
            # Get the next clause to refine
            current_clause = search_queue.pop(0)
            
            # Skip if the clause is already too long
            if current_clause.length >= max_clause_length:
                continue
            
            # Generate refinements of the current clause
            refinements = self._refine_clause(current_clause, background_knowledge)
            
            for refined_clause in refinements:
                # Check for redundancy and cycles
                if self._is_redundant(refined_clause) or (not self.language_bias.allow_recursion and self._contains_recursion(refined_clause)):
                    continue
                
                # Evaluate the refined clause
                score, pos_covered, neg_covered = self._evaluate_clause(
                    refined_clause, positive_examples, negative_examples, background_knowledge
                )
                
                # Update best clause if this one is better
                if score > best_score:
                    best_score = score
                    best_clause = refined_clause
                    logger.debug(f"New best clause: {best_clause}, score: {best_score}")
                
                # Add promising refinements to the search queue
                if len(pos_covered) > 0 and score > float('-inf'):
                    search_queue.append(refined_clause)
            
            # Sort the search queue by score (beam search)
            search_queue = sorted(
                search_queue,
                key=lambda c: self._evaluate_clause(c, positive_examples, negative_examples, background_knowledge)[0],
                reverse=True
            )[:10]  # Keep only the top 10 clauses (beam width)
        
        # Return the best clause if it meets minimum criteria
        if best_clause is not None and best_score > float('-inf'):
            return best_clause
        
        return None
    
    def _refine_clause(self, clause: Clause, background_knowledge: Set[AST_Node]) -> List[Clause]:
        """
        Refine a clause by adding literals according to the language bias.
        
        Args:
            clause: The clause to refine
            background_knowledge: Set of background knowledge
            
        Returns:
            A list of refined clauses
        """
        refinements = []
        
        # Get the variables already in the clause
        existing_vars = self._get_variables_in_clause(clause)
        
        # For each mode declaration
        for mode_decl in self.language_bias.mode_declarations:
            # Skip if this is a head mode declaration and we're refining the body
            if mode_decl.predicate_name == self._get_predicate_name(clause.head) and clause.length > 0:
                continue
            
            # Skip if adding this literal would exceed the maximum clause length
            if clause.length >= self.language_bias.max_clause_length:
                continue
            
            # Generate literals based on the mode declaration
            new_literals = self._generate_literals_from_mode(
                mode_decl, existing_vars, background_knowledge
            )
            
            # Add each new literal to the clause to create refinements
            for literal in new_literals:
                # Create a new clause with the literal added to the body
                new_body = clause.body.copy()
                new_body.append(literal)
                refined_clause = Clause(head=clause.head, body=new_body)
                
                refinements.append(refined_clause)
        
        return refinements
    
    def _generate_literals_from_mode(self, mode_decl: ModeDeclaration, 
                                    existing_vars: Dict[str, VariableNode],
                                    background_knowledge: Set[AST_Node]) -> List[AST_Node]:
        """
        Generate literals based on a mode declaration.
        
        Args:
            mode_decl: The mode declaration to use
            existing_vars: Dictionary of existing variables in the clause
            background_knowledge: Set of background knowledge
            
        Returns:
            A list of literals (AST_Nodes)
        """
        literals = []
        
        # Get constants of each type from background knowledge
        constants_by_type = self._get_constants_by_type(background_knowledge)
        
        # Generate arguments based on mode declaration
        possible_args_by_position = []
        
        for i, (mode, type_name) in enumerate(zip(mode_decl.arg_modes, mode_decl.arg_types)):
            if mode == '+':
                # Input variables must already exist with the correct type
                possible_args = [
                    var for var_name, var in existing_vars.items()
                    if var.type.name == type_name or self._is_subtype(var.type.name, type_name)
                ]
                if not possible_args:
                    # If no suitable variables exist, we can't create this literal
                    return []
                possible_args_by_position.append(possible_args)
            
            elif mode == '-':
                # Output variables can be new or existing
                # For simplicity, we'll just create a new variable
                var_id = len(existing_vars) + i + 1
                var_name = f"?V{var_id}"
                var_type = self.ksi.type_system.get_type(type_name)
                if var_type is None:
                    logger.warning(f"Type {type_name} not found in type system")
                    continue
                new_var = VariableNode(var_name, var_id, var_type)
                possible_args_by_position.append([new_var])
            
            elif mode == '#':
                # Constants must be of the correct type
                possible_args = constants_by_type.get(type_name, [])
                if not possible_args:
                    logger.warning(f"No constants of type {type_name} found in background knowledge")
                    continue
                possible_args_by_position.append(possible_args)
        
        # Generate all combinations of arguments (up to a limit)
        import itertools
        max_combinations = 10  # Limit the number of combinations to avoid explosion
        
        for args_combo in itertools.product(*possible_args_by_position):
            if len(literals) >= max_combinations:
                break
            
            # Create a predicate application with these arguments
            predicate_type = self.ksi.type_system.get_type("Predicate")
            if predicate_type is None:
                logger.warning("Predicate type not found in type system")
                continue
            
            predicate = ConstantNode(mode_decl.predicate_name, predicate_type)
            literal = ApplicationNode(predicate, list(args_combo), self.ksi.type_system.get_type("Boolean"))
            literals.append(literal)
        
        return literals
    
    def _evaluate_clause(self, clause: Clause, 
                        positive_examples: Set[AST_Node], 
                        negative_examples: Set[AST_Node],
                        background_knowledge: Set[AST_Node]) -> Tuple[float, Set[AST_Node], Set[AST_Node]]:
        """
        Evaluate a clause based on its coverage of positive and negative examples.
        
        Args:
            clause: The clause to evaluate
            positive_examples: Set of positive examples
            negative_examples: Set of negative examples
            background_knowledge: Set of background knowledge
            
        Returns:
            A tuple of (score, positive_covered, negative_covered)
        """
        # Get the coverage of the clause
        positive_covered, negative_covered = self._get_coverage(
            clause, positive_examples, negative_examples, background_knowledge
        )
        
        # Calculate the score using a heuristic
        p = len(positive_covered)
        n = len(negative_covered)
        P = len(positive_examples)
        N = len(negative_examples)
        
        # If the clause doesn't cover any positive examples, it's useless
        if p == 0:
            return float('-inf'), positive_covered, negative_covered
        
        # If the clause covers negative examples, penalize it
        if n > 0:
            return float('-inf'), positive_covered, negative_covered
        
        # Calculate FOIL gain: p * (log(p/(p+n)) - log(P/(P+N)))
        try:
            gain = p * (math.log2(p / (p + n + 1e-10)) - math.log2(P / (P + N + 1e-10)))
        except (ValueError, ZeroDivisionError):
            gain = 0
        
        # Penalize longer clauses to prefer simpler ones
        length_penalty = 0.1 * clause.length
        
        # Final score is gain minus length penalty
        score = gain - length_penalty
        
        return score, positive_covered, negative_covered
    
    def _get_coverage(self, clause: Clause, 
                     positive_examples: Set[AST_Node], 
                     negative_examples: Set[AST_Node],
                     background_knowledge: Set[AST_Node]) -> Tuple[Set[AST_Node], Set[AST_Node]]:
        """
        Get the coverage of a clause on positive and negative examples.
        
        Args:
            clause: The clause to evaluate
            positive_examples: Set of positive examples
            negative_examples: Set of negative examples
            background_knowledge: Set of background knowledge
            
        Returns:
            A tuple of (positive_covered, negative_covered)
        """
        # Check if the coverage is cached
        cached_coverage = self.coverage_cache.get(clause)
        if cached_coverage is not None:
            return cached_coverage
        
        # Convert the clause to an AST_Node
        clause_ast = clause.to_ast()
        
        # Check coverage of positive examples
        positive_covered = set()
        for example in positive_examples:
            if self._check_coverage(clause_ast, example, background_knowledge):
                positive_covered.add(example)
        
        # Check coverage of negative examples
        negative_covered = set()
        for example in negative_examples:
            if self._check_coverage(clause_ast, example, background_knowledge):
                negative_covered.add(example)
        
        # Cache the coverage
        self.coverage_cache.put(clause, positive_covered, negative_covered)
        
        return positive_covered, negative_covered
    
    def _check_coverage(self, clause_ast: AST_Node, example_ast: AST_Node, 
                       background_knowledge: Set[AST_Node]) -> bool:
        """
        Check if a clause covers an example.
        
        A clause covers an example if the example can be derived from the clause
        and the background knowledge.
        
        Args:
            clause_ast: The clause to check
            example_ast: The example to check
            background_knowledge: Set of background knowledge
            
        Returns:
            True if the clause covers the example, False otherwise
        """
        # Combine background knowledge and the clause
        knowledge = background_knowledge.copy()
        knowledge.add(clause_ast)
        
        # Use the inference engine to check if the example can be derived
        proof_result = self.inference_engine.submit_goal(example_ast, knowledge)
        
        return proof_result.goal_achieved
    
    def _get_background_knowledge(self, context_id: str) -> Set[AST_Node]:
        """
        Get background knowledge from the knowledge store.
        
        Args:
            context_id: The context ID for background knowledge
            
        Returns:
            A set of AST_Nodes representing the background knowledge
        """
        # Query all statements in the context
        query_result = self.ksi.query_statements_match_pattern(
            query_pattern_ast=None,  # Query all statements
            context_ids=[context_id]
        )
        
        # Extract the statements from the query result
        background_knowledge = set()
        for binding in query_result:
            for var, ast_node in binding.items():
                background_knowledge.add(ast_node)
        
        return background_knowledge
    
    def _get_constants_by_type(self, knowledge: Set[AST_Node]) -> Dict[str, List[ConstantNode]]:
        """
        Extract constants of each type from knowledge.
        
        Args:
            knowledge: Set of knowledge AST_Nodes
            
        Returns:
            A dictionary mapping type names to lists of constants
        """
        constants_by_type: DefaultDict[str, List[ConstantNode]] = defaultdict(list)
        
        for ast_node in knowledge:
            self._extract_constants(ast_node, constants_by_type)
        
        return constants_by_type
    
    def _extract_constants(self, ast_node: AST_Node, 
                          constants_by_type: DefaultDict[str, List[ConstantNode]]) -> None:
        """
        Recursively extract constants from an AST_Node.
        
        Args:
            ast_node: The AST_Node to extract constants from
            constants_by_type: Dictionary to populate with constants by type
        """
        if isinstance(ast_node, ConstantNode):
            type_name = ast_node.type.name
            if ast_node not in constants_by_type[type_name]:
                constants_by_type[type_name].append(ast_node)
        
        elif isinstance(ast_node, ApplicationNode):
            if isinstance(ast_node.operator, ConstantNode):
                type_name = ast_node.operator.type.name
                if ast_node.operator not in constants_by_type[type_name]:
                    constants_by_type[type_name].append(ast_node.operator)
            
            for arg in ast_node.arguments:
                self._extract_constants(arg, constants_by_type)
        
        elif isinstance(ast_node, ConnectiveNode):
            for operand in ast_node.operands:
                self._extract_constants(operand, constants_by_type)
    
    def _get_variables_in_clause(self, clause: Clause) -> Dict[str, VariableNode]:
        """
        Get all variables in a clause.
        
        Args:
            clause: The clause to extract variables from
            
        Returns:
            A dictionary mapping variable names to VariableNodes
        """
        variables = {}
        
        # Extract variables from the head
        self._extract_variables(clause.head, variables)
        
        # Extract variables from the body
        for literal in clause.body:
            self._extract_variables(literal, variables)
        
        return variables
    
    def _extract_variables(self, ast_node: AST_Node, variables: Dict[str, VariableNode]) -> None:
        """
        Recursively extract variables from an AST_Node.
        
        Args:
            ast_node: The AST_Node to extract variables from
            variables: Dictionary to populate with variables
        """
        if isinstance(ast_node, VariableNode):
            variables[ast_node.name] = ast_node
        
        elif isinstance(ast_node, ApplicationNode):
            self._extract_variables(ast_node.operator, variables)
            for arg in ast_node.arguments:
                self._extract_variables(arg, variables)
        
        elif isinstance(ast_node, ConnectiveNode):
            for operand in ast_node.operands:
                self._extract_variables(operand, variables)
    
    def _literal_signature(self, node: AST_Node) -> str:
        """Get a type-independent structural signature for an AST literal."""
        if isinstance(node, ApplicationNode):
            op_sig = self._literal_signature(node.operator)
            arg_sigs = tuple(self._literal_signature(a) for a in node.arguments)
            return f"App({op_sig}, {arg_sigs})"
        elif isinstance(node, ConstantNode):
            return f"Const({node.name})"
        elif isinstance(node, VariableNode):
            return f"Var({node.name}, {node.var_id})"
        else:
            return repr(node)

    def _is_redundant(self, clause: Clause) -> bool:
        """
        Check if a clause is redundant (contains duplicate literals).
        
        Args:
            clause: The clause to check
            
        Returns:
            True if the clause is redundant, False otherwise
        """
        # Check for duplicate literals in the body
        seen_literals = set()
        for literal in clause.body:
            literal_sig = self._literal_signature(literal)
            if literal_sig in seen_literals:
                return True
            seen_literals.add(literal_sig)
        
        return False
    
    def _contains_recursion(self, clause: Clause) -> bool:
        """
        Check if a clause contains recursion (the head predicate appears in the body).
        
        Args:
            clause: The clause to check
            
        Returns:
            True if the clause contains recursion, False otherwise
        """
        head_predicate = self._get_predicate_name(clause.head)
        
        for literal in clause.body:
            if isinstance(literal, ApplicationNode) and isinstance(literal.operator, ConstantNode):
                if literal.operator.name == head_predicate:
                    return True
        
        return False
    
    def _get_predicate_name(self, ast_node: AST_Node) -> Optional[str]:
        """
        Get the predicate name from an AST_Node.
        
        Args:
            ast_node: The AST_Node to get the predicate name from
            
        Returns:
            The predicate name, or None if not applicable
        """
        if isinstance(ast_node, ApplicationNode) and isinstance(ast_node.operator, ConstantNode):
            return ast_node.operator.name
        return None
    
    def _is_subtype(self, type_name: str, super_type_name: str) -> bool:
        """
        Check if a type is a subtype of another type.
        
        Args:
            type_name: The name of the type to check
            super_type_name: The name of the potential supertype
            
        Returns:
            True if type_name is a subtype of super_type_name, False otherwise
        """
        # This is a simplified implementation
        # In a real implementation, this would use the type system's subtype relation
        return type_name == super_type_name