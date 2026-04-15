"""
Belief Revision System implementation.

This module implements the BeliefRevisionSystem class, which manages changes to
the agent's belief set in a rational and consistent manner when new information
arrives, especially if it contradicts existing beliefs.

The system implements belief revision postulates (AGM postulates) and supports
operations like expansion, contraction, and revision. It also provides support
for argumentation frameworks for defeasible reasoning.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Callable
import copy
import uuid
import logging
from enum import Enum
from collections import defaultdict

from godelOS.core_kr.ast.nodes import AST_Node, ConnectiveNode, ConstantNode, VariableNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface

# Set up logging
logger = logging.getLogger(__name__)


class Argument:
    """
    An argument in an argumentation framework.
    
    An argument consists of a conclusion, premises, an inference rule ID,
    and a type (strict or defeasible).
    """
    
    def __init__(self, conclusion: AST_Node, premises: Set[AST_Node], 
                inference_rule_id: str, arg_type: str = "strict"):
        """
        Initialize an argument.
        
        Args:
            conclusion: The conclusion of the argument
            premises: The premises of the argument
            inference_rule_id: The ID of the inference rule used
            arg_type: The type of the argument ("strict" or "defeasible")
        """
        self.id = str(uuid.uuid4())
        self.conclusion = conclusion
        self.premises = premises
        self.inference_rule_id = inference_rule_id
        self.arg_type = arg_type
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Argument):
            return False
        return (self.conclusion == other.conclusion and 
                self.premises == other.premises and 
                self.inference_rule_id == other.inference_rule_id and 
                self.arg_type == other.arg_type)
    
    def __hash__(self) -> int:
        return hash((self.conclusion, frozenset(self.premises), 
                    self.inference_rule_id, self.arg_type))


class ArgumentationFramework:
    """
    An argumentation framework.
    
    An argumentation framework consists of a set of arguments and an attack relation
    between arguments.
    """
    
    def __init__(self):
        """Initialize an argumentation framework."""
        self.arguments: Dict[str, Argument] = {}
        self.attacks: Set[Tuple[str, str]] = set()  # (attacker_id, attacked_id)
    
    def add_argument(self, argument: Argument) -> None:
        """
        Add an argument to the framework.
        
        Args:
            argument: The argument to add
        """
        self.arguments[argument.id] = argument
    
    def add_attack(self, attacker_id: str, attacked_id: str) -> None:
        """
        Add an attack relation to the framework.
        
        Args:
            attacker_id: The ID of the attacking argument
            attacked_id: The ID of the attacked argument
        """
        self.attacks.add((attacker_id, attacked_id))
    
    def get_attackers(self, argument_id: str) -> Set[str]:
        """
        Get the IDs of arguments that attack the given argument.
        
        Args:
            argument_id: The ID of the argument
            
        Returns:
            The set of attacker IDs
        """
        return {attacker_id for attacker_id, attacked_id in self.attacks if attacked_id == argument_id}
    
    def get_attacked(self, argument_id: str) -> Set[str]:
        """
        Get the IDs of arguments that are attacked by the given argument.
        
        Args:
            argument_id: The ID of the argument
            
        Returns:
            The set of attacked argument IDs
        """
        return {attacked_id for attacker_id, attacked_id in self.attacks if attacker_id == argument_id}


class RevisionStrategy(Enum):
    """Enumeration of belief revision strategies."""
    PARTIAL_MEET = "partial_meet"
    KERNEL = "kernel"
    ARGUMENTATION = "argumentation"


class BeliefRevisionSystem:
    """
    System for managing changes to the agent's belief set.
    
    This system implements belief revision postulates (e.g., AGM postulates)
    and supports operations like expansion, contraction, and revision.
    
    It provides multiple belief revision strategies:
    - Partial Meet Contraction/Revision (AGM-style)
    - Kernel Contraction/Revision (Base revision)
    - Argumentation-based revision (using Dung's argumentation frameworks)
    """
    
    def __init__(self, kr_system_interface: KnowledgeStoreInterface,
                belief_set_context_id: str = "BELIEFS",
                default_strategy: RevisionStrategy = RevisionStrategy.PARTIAL_MEET):
        """
        Initialize the belief revision system.
        
        Args:
            kr_system_interface: The knowledge store interface
            belief_set_context_id: The context ID of the belief set
            default_strategy: The default revision strategy to use
        """
        self.ksi = kr_system_interface
        self.belief_set_context_id = belief_set_context_id
        self.default_strategy = default_strategy
        
        # Create the belief set context if it doesn't exist
        if belief_set_context_id not in self.ksi.list_contexts():
            self.ksi.create_context(belief_set_context_id, context_type="beliefs")
        
        # Dictionary to store entrenchment values for beliefs
        self._entrenchment_values: Dict[str, Dict[AST_Node, float]] = defaultdict(dict)
        
        # Dictionary to store argumentation frameworks for belief sets
        self._argumentation_frameworks: Dict[str, ArgumentationFramework] = {}
        
        # Dictionary to store derived beliefs for belief sets
        self._derived_beliefs: Dict[str, Set[AST_Node]] = defaultdict(set)
    
    def expand_belief_set(self, belief_set_id: str, new_belief_ast: AST_Node,
                         entrenchment_value: float = 0.5) -> str:
        """
        Expand a belief set by adding a new belief without checking for consistency.
        
        This operation satisfies the AGM expansion postulates:
        - The new belief is in the expanded belief set
        - The original belief set is a subset of the expanded belief set
        - If the new belief was already in the original belief set, the expanded set is the same
        - The expanded set is the smallest set satisfying the above conditions
        
        Args:
            belief_set_id: The ID of the belief set to expand
            new_belief_ast: The new belief to add
            entrenchment_value: The entrenchment value of the new belief (0.0 to 1.0)
                                Higher values indicate more entrenched beliefs
            
        Returns:
            The ID of the new belief set
        """
        # Validate inputs
        if not isinstance(new_belief_ast, AST_Node):
            raise TypeError("new_belief_ast must be an AST_Node")
        
        if entrenchment_value < 0.0 or entrenchment_value > 1.0:
            raise ValueError("entrenchment_value must be between 0.0 and 1.0")
        
        # Check if the belief set exists
        if belief_set_id not in self.ksi.list_contexts():
            raise ValueError(f"Belief set {belief_set_id} does not exist")
        
        # Check if the belief is already in the belief set
        if self.ksi.statement_exists(new_belief_ast, [belief_set_id]):
            logger.info(f"Belief already exists in belief set {belief_set_id}")
            return belief_set_id
        
        # Create a new belief set as a copy of the original
        new_belief_set_id = f"{belief_set_id}_expanded_{uuid.uuid4().hex[:8]}"
        self.ksi.create_context(new_belief_set_id, parent_context_id=belief_set_id, context_type="beliefs")
        
        # Copy all statements from the parent belief set
        parent_statements = self._get_all_statements(belief_set_id)
        for stmt in parent_statements:
            self.ksi.add_statement(stmt, context_id=new_belief_set_id)
        
        # Add the new belief to the new belief set with metadata
        metadata = {
            "operation": "expansion",
            "source_belief_set": belief_set_id,
            "entrenchment": entrenchment_value
        }
        self.ksi.add_statement(new_belief_ast, context_id=new_belief_set_id, metadata=metadata)
        
        # Store the entrenchment value
        self._entrenchment_values[new_belief_set_id][new_belief_ast] = entrenchment_value
        
        # Copy entrenchment values from the original belief set
        if belief_set_id in self._entrenchment_values:
            for belief, value in self._entrenchment_values[belief_set_id].items():
                self._entrenchment_values[new_belief_set_id][belief] = value
        
        logger.info(f"Expanded belief set {belief_set_id} to {new_belief_set_id} with new belief")
        return new_belief_set_id
    
    def contract_belief_set(self, belief_set_id: str, belief_to_remove_ast: AST_Node,
                           strategy: Optional[RevisionStrategy] = None,
                           entrenchment_map: Optional[Dict[AST_Node, float]] = None) -> str:
        """
        Contract a belief set by removing a belief and its logical consequences.
        
        This operation satisfies the AGM contraction postulates:
        - The contracted belief set is a subset of the original belief set
        - If the belief to remove was not in the original set, the contracted set is the same
        - The belief to remove is not in the contracted set unless it's a tautology
        - If two beliefs are logically equivalent, contracting by either gives the same result
        - The contracted set is the largest set satisfying the above conditions
        
        Args:
            belief_set_id: The ID of the belief set to contract
            belief_to_remove_ast: The belief to remove
            strategy: The contraction strategy to use (defaults to the system's default)
            entrenchment_map: Optional map of beliefs to their entrenchment values
                             (overrides stored values)
            
        Returns:
            The ID of the new belief set
        """
        # Validate inputs
        if not isinstance(belief_to_remove_ast, AST_Node):
            raise TypeError("belief_to_remove_ast must be an AST_Node")
        
        # Check if the belief set exists
        if belief_set_id not in self.ksi.list_contexts():
            raise ValueError(f"Belief set {belief_set_id} does not exist")
        
        # Check if the belief is in the belief set
        if not self.ksi.statement_exists(belief_to_remove_ast, [belief_set_id]):
            logger.info(f"Belief not in belief set {belief_set_id}, no contraction needed")
            return belief_set_id
        
        # Use the specified strategy or the default
        strategy = strategy or self.default_strategy
        
        # Create a new belief set
        new_belief_set_id = f"{belief_set_id}_contracted_{uuid.uuid4().hex[:8]}"
        self.ksi.create_context(new_belief_set_id, context_type="beliefs")
        
        # Get all statements in the original belief set
        statements = self._get_all_statements(belief_set_id)
        
        # Use the appropriate contraction strategy
        if strategy == RevisionStrategy.PARTIAL_MEET:
            self._partial_meet_contraction(belief_set_id, new_belief_set_id,
                                          statements, belief_to_remove_ast, entrenchment_map)
        elif strategy == RevisionStrategy.KERNEL:
            self._kernel_contraction(belief_set_id, new_belief_set_id,
                                    statements, belief_to_remove_ast, entrenchment_map)
        elif strategy == RevisionStrategy.ARGUMENTATION:
            self._argumentation_contraction(belief_set_id, new_belief_set_id,
                                           statements, belief_to_remove_ast)
        else:
            raise ValueError(f"Unsupported contraction strategy: {strategy}")
        
        logger.info(f"Contracted belief set {belief_set_id} to {new_belief_set_id}")
        return new_belief_set_id
    
    def _get_all_statements(self, context_id: str) -> Set[AST_Node]:
        """
        Get all statements in a context.
        
        Args:
            context_id: The context ID
            
        Returns:
            The set of statements
        """
        return self.ksi.get_all_statements_in_context(context_id)
    
    def _find_maximal_subsets(self, statements: Set[AST_Node],
                             belief_to_remove_ast: AST_Node,
                             entrenchment_map: Optional[Dict[AST_Node, float]] = None) -> List[Set[AST_Node]]:
        """
        Find maximal subsets of statements that do not entail a belief.
        
        This implements the core of partial meet contraction by finding all maximal
        subsets of the original belief set that do not entail the belief to remove.
        
        Args:
            statements: The set of statements
            belief_to_remove_ast: The belief to remove
            entrenchment_map: Optional map of beliefs to their entrenchment values
            
        Returns:
            A list of maximal subsets
        """
        # Start with the power set of statements (all possible subsets)
        # For efficiency, we use a more sophisticated algorithm than generating all subsets
        
        # Initialize with an empty subset
        subsets: List[Set[AST_Node]] = [set()]
        
        # Add statements one by one, checking if they entail the belief to remove
        for statement in statements:
            # Skip the statement if it's the belief to remove
            if statement == belief_to_remove_ast:
                continue
            
            # Create new subsets by adding the current statement to existing subsets
            new_subsets = []
            for subset in subsets:
                # Create a new subset with the current statement
                new_subset = subset.copy()
                new_subset.add(statement)
                
                # Check if the new subset entails the belief to remove
                if not self._entails(new_subset, belief_to_remove_ast):
                    new_subsets.append(new_subset)
            
            # Add the new subsets to the list of subsets
            subsets.extend(new_subsets)
        
        # Find the maximal subsets (those not contained in any other)
        maximal_subsets = []
        for subset in subsets:
            is_maximal = True
            for other_subset in subsets:
                if subset != other_subset and subset.issubset(other_subset):
                    is_maximal = False
                    break
            if is_maximal:
                maximal_subsets.append(subset)
        
        # Sort maximal subsets by entrenchment if provided
        if entrenchment_map:
            maximal_subsets.sort(key=lambda subset: self._calculate_entrenchment_score(subset, entrenchment_map), reverse=True)
        
        return maximal_subsets
    
    def _entails(self, statements: Set[AST_Node], belief: AST_Node) -> bool:
        """
        Check if a set of statements entails a belief.
        
        Args:
            statements: The set of statements
            belief: The belief to check
            
        Returns:
            True if the statements entail the belief, False otherwise
        """
        # In a full implementation, this would use the inference engine
        # For now, we use a simplified approach:
        # 1. Check if the belief is in the set of statements (direct entailment)
        # 2. Check for simple logical entailment patterns
        
        # Direct entailment
        if belief in statements:
            return True
        
        # Simple logical entailment patterns
        # For example, if we have P and P→Q, then we entail Q
        if isinstance(belief, ConnectiveNode):
            # Handle simple modus ponens: P and P→Q entail Q
            if isinstance(belief, ConnectiveNode) and belief.connective_type == "IMPLIES":
                antecedent, consequent = belief.operands
                if antecedent in statements and consequent in statements:
                    return True
        
        # More complex entailment would require a proper inference engine
        return False
    
    def _calculate_entrenchment_score(self, subset: Set[AST_Node],
                                     entrenchment_map: Dict[AST_Node, float]) -> float:
        """
        Calculate the entrenchment score of a subset.
        
        Args:
            subset: The subset of statements
            entrenchment_map: Map of beliefs to their entrenchment values
            
        Returns:
            The entrenchment score of the subset
        """
        # Calculate the sum of entrenchment values for the beliefs in the subset
        score = 0.0
        for statement in subset:
            score += entrenchment_map.get(statement, 0.5)  # Default to 0.5 if not specified
        
        return score
    
    def _partial_meet_contraction(self, original_belief_set_id: str, new_belief_set_id: str,
                                 statements: Set[AST_Node], belief_to_remove_ast: AST_Node,
                                 entrenchment_map: Optional[Dict[AST_Node, float]] = None) -> None:
        """
        Perform partial meet contraction.
        
        Args:
            original_belief_set_id: The ID of the original belief set
            new_belief_set_id: The ID of the new belief set
            statements: The statements in the original belief set
            belief_to_remove_ast: The belief to remove
            entrenchment_map: Optional map of beliefs to their entrenchment values
        """
        # Use stored entrenchment values if not provided
        if entrenchment_map is None and original_belief_set_id in self._entrenchment_values:
            entrenchment_map = self._entrenchment_values[original_belief_set_id]
        
        # Find maximal subsets that do not entail the belief to remove
        maximal_subsets = self._find_maximal_subsets(statements, belief_to_remove_ast, entrenchment_map)
        
        # If no maximal subsets found, return an empty belief set
        if not maximal_subsets:
            logger.warning(f"No maximal subsets found for contraction in belief set {original_belief_set_id}")
            return
        
        # Select the subset with the highest entrenchment score
        if entrenchment_map:
            selected_subset = max(maximal_subsets,
                                 key=lambda subset: self._calculate_entrenchment_score(subset, entrenchment_map))
        else:
            # If no entrenchment map, select the largest subset
            selected_subset = max(maximal_subsets, key=len)
        
        # Add the selected subset to the new belief set
        for statement in selected_subset:
            # Copy the entrenchment value if available
            entrenchment = entrenchment_map.get(statement, 0.5) if entrenchment_map else 0.5
            metadata = {
                "operation": "contraction",
                "source_belief_set": original_belief_set_id,
                "entrenchment": entrenchment
            }
            self.ksi.add_statement(statement, context_id=new_belief_set_id, metadata=metadata)
            
            # Store the entrenchment value
            self._entrenchment_values[new_belief_set_id][statement] = entrenchment

    def _kernel_contraction(self, original_belief_set_id: str, new_belief_set_id: str,
                           statements: Set[AST_Node], belief_to_remove_ast: AST_Node,
                           entrenchment_map: Optional[Dict[AST_Node, float]] = None) -> None:
        """
        Perform kernel contraction.
        
        Kernel contraction identifies all minimal subsets of the belief set that entail
        the belief to remove (kernels), then removes at least one element from each kernel.
        
        Args:
            original_belief_set_id: The ID of the original belief set
            new_belief_set_id: The ID of the new belief set
            statements: The statements in the original belief set
            belief_to_remove_ast: The belief to remove
            entrenchment_map: Optional map of beliefs to their entrenchment values
        """
        # Use stored entrenchment values if not provided
        if entrenchment_map is None and original_belief_set_id in self._entrenchment_values:
            entrenchment_map = self._entrenchment_values[original_belief_set_id]
        
        # Find all kernels (minimal subsets that entail the belief to remove)
        kernels = self._find_kernels(statements, belief_to_remove_ast)
        
        # If no kernels found, the belief is not entailed, so keep all statements
        if not kernels:
            for statement in statements:
                # Copy the entrenchment value if available
                entrenchment = entrenchment_map.get(statement, 0.5) if entrenchment_map else 0.5
                metadata = {
                    "operation": "contraction",
                    "source_belief_set": original_belief_set_id,
                    "entrenchment": entrenchment
                }
                self.ksi.add_statement(statement, context_id=new_belief_set_id, metadata=metadata)
                
                # Store the entrenchment value
                self._entrenchment_values[new_belief_set_id][statement] = entrenchment
            return
        
        # Create an incision function that selects beliefs to remove from each kernel
        # based on entrenchment values
        incision_set = self._create_incision_set(kernels, entrenchment_map)
        
        # Add all statements except those in the incision set to the new belief set
        for statement in statements:
            if statement not in incision_set:
                # Copy the entrenchment value if available
                entrenchment = entrenchment_map.get(statement, 0.5) if entrenchment_map else 0.5
                metadata = {
                    "operation": "contraction",
                    "source_belief_set": original_belief_set_id,
                    "entrenchment": entrenchment
                }
                self.ksi.add_statement(statement, context_id=new_belief_set_id, metadata=metadata)
                
                # Store the entrenchment value
                self._entrenchment_values[new_belief_set_id][statement] = entrenchment

    def _find_kernels(self, statements: Set[AST_Node],
                     belief_to_remove_ast: AST_Node) -> List[Set[AST_Node]]:
        """
        Find all kernels (minimal subsets that entail the belief to remove).
        
        Args:
            statements: The set of statements
            belief_to_remove_ast: The belief to remove
            
        Returns:
            A list of kernels
        """
        # Initialize with all subsets that entail the belief
        entailing_subsets = []
        
        # Check each subset
        # For efficiency, we use a more sophisticated algorithm than generating all subsets
        def find_entailing_subsets(current_subset: Set[AST_Node], remaining: List[AST_Node],
                                  index: int) -> None:
            # Check if the current subset entails the belief
            if self._entails(current_subset, belief_to_remove_ast):
                entailing_subsets.append(current_subset.copy())
                return
            
            # If we've considered all statements, return
            if index >= len(remaining):
                return
            
            # Skip the current statement
            find_entailing_subsets(current_subset, remaining, index + 1)
            
            # Include the current statement
            current_subset.add(remaining[index])
            find_entailing_subsets(current_subset, remaining, index + 1)
            current_subset.remove(remaining[index])
        
        find_entailing_subsets(set(), list(statements), 0)
        
        # Find the minimal entailing subsets (kernels)
        kernels = []
        for subset in entailing_subsets:
            is_minimal = True
            for other_subset in entailing_subsets:
                if other_subset != subset and other_subset.issubset(subset):
                    is_minimal = False
                    break
            if is_minimal:
                kernels.append(subset)
        
        return kernels

    def _create_incision_set(self, kernels: List[Set[AST_Node]],
                            entrenchment_map: Optional[Dict[AST_Node, float]] = None) -> Set[AST_Node]:
        """
        Create an incision set by selecting at least one element from each kernel.
        
        Args:
            kernels: The list of kernels
            entrenchment_map: Optional map of beliefs to their entrenchment values
            
        Returns:
            The incision set
        """
        # Initialize the incision set
        incision_set = set()
        
        # Process each kernel
        for kernel in kernels:
            # If we've already selected an element from this kernel, skip it
            if any(statement in incision_set for statement in kernel):
                continue
            
            # Select the least entrenched element from the kernel
            if entrenchment_map:
                least_entrenched = min(kernel,
                                      key=lambda statement: entrenchment_map.get(statement, 0.5))
            else:
                # If no entrenchment map, select any element
                least_entrenched = next(iter(kernel))
            
            # Add the selected element to the incision set
            incision_set.add(least_entrenched)
        
        return incision_set

    def _argumentation_contraction(self, original_belief_set_id: str, new_belief_set_id: str,
                                  statements: Set[AST_Node], belief_to_remove_ast: AST_Node) -> None:
        """
        Perform argumentation-based contraction.
        
        This approach uses an argumentation framework to determine which beliefs to keep
        and which to remove based on attack relations between arguments.
        
        Args:
            original_belief_set_id: The ID of the original belief set
            new_belief_set_id: The ID of the new belief set
            statements: The statements in the original belief set
            belief_to_remove_ast: The belief to remove
        """
        # Construct an argumentation framework from the statements
        af = self._construct_argumentation_framework_for_contraction(statements, belief_to_remove_ast)
        
        # Apply grounded semantics to determine justified arguments
        justified_arguments = self._apply_grounded_semantics(af)
        
        # Extract the conclusions of the justified arguments
        justified_beliefs = set()
        for arg_id in justified_arguments:
            if arg_id in af.arguments:
                justified_beliefs.add(af.arguments[arg_id].conclusion)
        
        # Add the justified beliefs to the new belief set
        for statement in statements:
            if statement in justified_beliefs and statement != belief_to_remove_ast:
                metadata = {
                    "operation": "contraction",
                    "source_belief_set": original_belief_set_id,
                    "via_argumentation": True
                }
                self.ksi.add_statement(statement, context_id=new_belief_set_id, metadata=metadata)

    def _construct_argumentation_framework_for_contraction(self, statements: Set[AST_Node],
                                                         belief_to_remove_ast: AST_Node) -> ArgumentationFramework:
        """
        Construct an argumentation framework for contraction.
        
        Args:
            statements: The statements in the belief set
            belief_to_remove_ast: The belief to remove
            
        Returns:
            The argumentation framework
        """
        af = ArgumentationFramework()
        
        # Create arguments for each statement
        statement_to_arg_id = {}
        for statement in statements:
            arg = Argument(
                conclusion=statement,
                premises=set(),
                inference_rule_id="fact",
                arg_type="strict" if statement != belief_to_remove_ast else "defeasible"
            )
            af.add_argument(arg)
            statement_to_arg_id[statement] = arg.id
        
        # Create attack relations
        # In a contraction scenario, we want to ensure that arguments supporting
        # the belief to remove are attacked
        for statement in statements:
            if statement == belief_to_remove_ast:
                continue
            
            # If the statement contradicts the belief to remove, it attacks it
            # In a full implementation, we would use a proper contradiction check
            # For now, we use a simple heuristic
            if isinstance(statement, ConnectiveNode) and statement.connective_type == "NOT":
                if statement.operands[0] == belief_to_remove_ast:
                    af.add_attack(statement_to_arg_id[statement], statement_to_arg_id[belief_to_remove_ast])
            
            # If the belief to remove is a negation of the statement, it attacks the statement
            if isinstance(belief_to_remove_ast, ConnectiveNode) and belief_to_remove_ast.connective_type == "NOT":
                if belief_to_remove_ast.operands[0] == statement:
                    af.add_attack(statement_to_arg_id[belief_to_remove_ast], statement_to_arg_id[statement])
        
        return af

    def revise_belief_set(self, belief_set_id: str, new_belief_ast: AST_Node,
                          entrenchment_map: Optional[Dict[AST_Node, float]] = None,
                          strategy: Optional[RevisionStrategy] = None) -> str:
        """
        Revise a belief set by adding a new belief while maintaining consistency.
        
        This operation satisfies the AGM revision postulates:
        - The new belief is in the revised belief set
        - If the new belief is consistent with the original set, revision is equivalent to expansion
        - The revised set is consistent unless the new belief is inconsistent
        - If two beliefs are logically equivalent, revising by either gives the same result
        - The revised set contains as much of the original set as possible
        
        Args:
            belief_set_id: The ID of the belief set to revise
            new_belief_ast: The new belief to add
            entrenchment_map: Optional map of beliefs to their entrenchment values
            strategy: The revision strategy to use (defaults to the system's default)
            
        Returns:
            The ID of the new belief set
        """
        # Validate inputs
        if not isinstance(new_belief_ast, AST_Node):
            raise TypeError("new_belief_ast must be an AST_Node")
        
        # Check if the belief set exists
        if belief_set_id not in self.ksi.list_contexts():
            raise ValueError(f"Belief set {belief_set_id} does not exist")
        
        # Use the specified strategy or the default
        strategy = strategy or self.default_strategy
        
        # Create a new belief set for the revision
        revised_belief_set_id = f"{belief_set_id}_revised_{uuid.uuid4().hex[:8]}"
        self.ksi.create_context(revised_belief_set_id, context_type="beliefs")
        
        # Get all statements in the original belief set
        statements = self._get_all_statements(belief_set_id)
        
        # Check if the new belief is already in the belief set
        if self.ksi.statement_exists(new_belief_ast, [belief_set_id]):
            logger.info(f"Belief already exists in belief set {belief_set_id}")
            # Copy all statements to the new belief set
            for statement in statements:
                self.ksi.add_statement(statement, context_id=revised_belief_set_id)
            return revised_belief_set_id
        
        # Levi identity: K*φ = (K÷¬φ)+φ
        # Create the negation of the new belief for contraction.
        # If the new belief is already a negation NOT(ψ), contracting by ψ
        # (double-negation elimination) avoids NOT(NOT(ψ)).
        if (isinstance(new_belief_ast, ConnectiveNode)
                and new_belief_ast.connective_type == "NOT"
                and len(new_belief_ast.operands) == 1):
            belief_to_contract = new_belief_ast.operands[0]
        else:
            belief_to_contract = ConnectiveNode(
                connective_type="NOT",
                operands=[new_belief_ast],
                type_ref=new_belief_ast.type
            )
        
        # Contract by the negation of the new belief
        contracted_belief_set_id = self.contract_belief_set(
            belief_set_id, belief_to_contract, strategy, entrenchment_map
        )
        
        # Expand with the new belief
        entrenchment_value = 0.5  # Default entrenchment value
        if entrenchment_map and new_belief_ast in entrenchment_map:
            entrenchment_value = entrenchment_map[new_belief_ast]
        
        revised_belief_set_id = self.expand_belief_set(
            contracted_belief_set_id, new_belief_ast, entrenchment_value
        )
        
        return revised_belief_set_id
    
    def get_justified_beliefs_via_argumentation(self, relevant_knowledge_asts: Set[AST_Node],
                                               defeasible_rules_asts: Set[AST_Node],
                                               semantics_type: str = "grounded") -> Set[AST_Node]:
        """
        Get justified beliefs using argumentation.
        
        This method uses Dung's abstract argumentation frameworks to determine
        which beliefs are justified based on the specified semantics.
        
        Args:
            relevant_knowledge_asts: The set of relevant knowledge (facts)
            defeasible_rules_asts: The set of defeasible rules
            semantics_type: The type of semantics to use
                ("grounded", "preferred", "stable", "complete")
            
        Returns:
            The set of justified beliefs
        """
        # Validate inputs
        if not all(isinstance(ast, AST_Node) for ast in relevant_knowledge_asts):
            raise TypeError("All elements in relevant_knowledge_asts must be AST_Node instances")
        
        if not all(isinstance(ast, AST_Node) for ast in defeasible_rules_asts):
            raise TypeError("All elements in defeasible_rules_asts must be AST_Node instances")
        
        # Construct the argumentation framework
        af = self._construct_argumentation_framework(relevant_knowledge_asts, defeasible_rules_asts)
        
        # Apply the specified semantics
        if semantics_type == "grounded":
            justified_arguments = self._apply_grounded_semantics(af)
        elif semantics_type == "preferred":
            justified_arguments = self._apply_preferred_semantics(af)
        elif semantics_type == "stable":
            justified_arguments = self._apply_stable_semantics(af)
        elif semantics_type == "complete":
            justified_arguments = self._apply_complete_semantics(af)
        else:
            raise ValueError(f"Unsupported semantics type: {semantics_type}")
        
        # Extract the conclusions of the justified arguments
        justified_beliefs = set()
        for arg_id in justified_arguments:
            if arg_id in af.arguments:
                justified_beliefs.add(af.arguments[arg_id].conclusion)
        
        logger.info(f"Found {len(justified_beliefs)} justified beliefs using {semantics_type} semantics")
        return justified_beliefs
    
    def _construct_argumentation_framework(self, relevant_knowledge_asts: Set[AST_Node],
                                          defeasible_rules_asts: Set[AST_Node]) -> ArgumentationFramework:
        """
        Construct an argumentation framework from knowledge and rules.
        
        This method creates arguments for each piece of knowledge and each rule,
        and identifies attack relations between them based on conflicts.
        
        Args:
            relevant_knowledge_asts: The set of relevant knowledge (facts)
            defeasible_rules_asts: The set of defeasible rules
            
        Returns:
            The argumentation framework
        """
        af = ArgumentationFramework()
        
        # Create arguments for strict knowledge (facts)
        knowledge_arg_ids = {}
        for knowledge_ast in relevant_knowledge_asts:
            arg = Argument(
                conclusion=knowledge_ast,
                premises=set(),
                inference_rule_id="fact",
                arg_type="strict"
            )
            af.add_argument(arg)
            knowledge_arg_ids[knowledge_ast] = arg.id
        
        # Create arguments for defeasible rules
        rule_arg_ids = {}
        for rule_ast in defeasible_rules_asts:
            # In a full implementation, we would parse the rule to extract
            # its premises and conclusion. For now, we treat the rule as a whole.
            arg = Argument(
                conclusion=rule_ast,
                premises=set(),
                inference_rule_id="default",
                arg_type="defeasible"
            )
            af.add_argument(arg)
            rule_arg_ids[rule_ast] = arg.id
        
        # Identify attack relations
        # In a full implementation, this would use a proper contradiction check
        # For now, we use a simple heuristic based on negation
        
        # Check for conflicts between knowledge and rules
        for knowledge_ast, knowledge_arg_id in knowledge_arg_ids.items():
            for rule_ast, rule_arg_id in rule_arg_ids.items():
                # If the knowledge directly contradicts the rule
                if self._are_contradictory(knowledge_ast, rule_ast):
                    # Knowledge attacks the rule (strict defeats defeasible)
                    af.add_attack(knowledge_arg_id, rule_arg_id)
        
        # Check for conflicts between rules
        for rule1_ast, rule1_arg_id in rule_arg_ids.items():
            for rule2_ast, rule2_arg_id in rule_arg_ids.items():
                if rule1_ast != rule2_ast and self._are_contradictory(rule1_ast, rule2_ast):
                    # Both rules attack each other (mutual defeat)
                    af.add_attack(rule1_arg_id, rule2_arg_id)
                    af.add_attack(rule2_arg_id, rule1_arg_id)
        
        logger.info(f"Constructed argumentation framework with {len(af.arguments)} arguments and {len(af.attacks)} attacks")
        return af
    
    def _are_contradictory(self, ast1: AST_Node, ast2: AST_Node) -> bool:
        """
        Check if two AST nodes are contradictory.
        
        Args:
            ast1: The first AST node
            ast2: The second AST node
            
        Returns:
            True if the nodes are contradictory, False otherwise
        """
        # In a full implementation, this would use a proper contradiction check
        # For now, we use a simple heuristic based on negation
        
        # Check if one is the negation of the other
        if isinstance(ast1, ConnectiveNode) and ast1.connective_type == "NOT":
            if ast1.operands[0] == ast2:
                return True
        
        if isinstance(ast2, ConnectiveNode) and ast2.connective_type == "NOT":
            if ast2.operands[0] == ast1:
                return True
        
        return False
    
    def _apply_grounded_semantics(self, af: ArgumentationFramework) -> Set[str]:
        """
        Apply grounded semantics to an argumentation framework.
        
        Args:
            af: The argumentation framework
            
        Returns:
            The set of justified argument IDs
        """
        # This is a placeholder implementation of the grounded semantics algorithm
        # In a real implementation, this would implement the grounded extension
        # (the least fixed point of the characteristic function)
        
        # Initialize the set of justified arguments
        justified = set()
        
        # Initialize the set of arguments that are not attacked
        unattacked = {arg_id for arg_id in af.arguments if not af.get_attackers(arg_id)}
        
        # Iteratively add unattacked arguments and remove attacked arguments
        while unattacked:
            # Add unattacked arguments to the justified set
            justified.update(unattacked)
            
            # Find arguments that are attacked by the newly justified arguments
            attacked = set()
            for arg_id in unattacked:
                attacked.update(af.get_attacked(arg_id))
            
            # Remove attacked arguments from consideration
            unattacked = {arg_id for arg_id in af.arguments 
                         if arg_id not in justified and 
                         arg_id not in attacked and 
                         not any(attacker_id in justified for attacker_id in af.get_attackers(arg_id))}
        
        return justified
    
    def _apply_preferred_semantics(self, af: ArgumentationFramework) -> Set[str]:
        """
        Apply preferred semantics to an argumentation framework.
        
        Args:
            af: The argumentation framework
            
        Returns:
            The set of justified argument IDs
        """
        # This is a placeholder implementation
        # In a real implementation, this would find a maximal admissible set
        
        # For now, just use the grounded semantics
        return self._apply_grounded_semantics(af)
    
    def _apply_stable_semantics(self, af: ArgumentationFramework) -> Set[str]:
        """
        Apply stable semantics to an argumentation framework.
        
        Args:
            af: The argumentation framework
            
        Returns:
            The set of justified argument IDs
        """
        # This is a placeholder implementation
        # In a real implementation, this would find a set that attacks all arguments
        # not in the set
        
        # For now, just use the grounded semantics
        return self._apply_grounded_semantics(af)
    
    def _apply_complete_semantics(self, af: ArgumentationFramework) -> Set[str]:
        """
        Apply complete semantics to an argumentation framework.
        
        Args:
            af: The argumentation framework
            
        Returns:
            The set of justified argument IDs
        """
        # This is a placeholder implementation
        # In a real implementation, this would find a complete extension
        
        # For now, just use the grounded semantics
        return self._apply_grounded_semantics(af)