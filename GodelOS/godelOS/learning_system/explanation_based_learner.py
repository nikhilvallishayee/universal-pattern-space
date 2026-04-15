"""
Explanation-Based Learning (EBL) for GödelOS.

This module implements the ExplanationBasedLearner component (Module 3.2) of the Learning System,
which is responsible for analyzing successful problem-solving instances (ProofObjects) and
forming generalized rules (LogicTemplates) that capture the essence of the solutions.

The ExplanationBasedLearner generalizes specific instances by abstracting constants into
variables while ensuring the derived rules remain valid and operational.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any, DefaultDict
from dataclasses import dataclass, field
from collections import defaultdict

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode, ConnectiveNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.coordinator import InferenceCoordinator
from godelOS.inference_engine.proof_object import ProofObject, ProofStepNode

logger = logging.getLogger(__name__)


@dataclass
class OperationalityConfig:
    """
    Configuration for determining which predicates are considered operational.
    
    Operational predicates are those that are considered "easier" to satisfy or match
    than the original goal, such as directly perceivable predicates, efficiently
    computable predicates, or built-in predicates.
    """
    operational_predicates: Set[str] = field(default_factory=set)
    max_unfolding_depth: int = 2
    
    def is_operational(self, predicate_name: str) -> bool:
        """
        Check if a predicate is considered operational.
        
        Args:
            predicate_name: The name of the predicate to check
            
        Returns:
            True if the predicate is operational, False otherwise
        """
        return predicate_name in self.operational_predicates


@dataclass
class GeneralizedExplanation:
    """
    Represents a generalized explanation structure.
    
    This is an intermediate structure representing the proof with variables
    replacing constants, used during the explanation-based learning process.
    """
    goal: AST_Node
    premises: List[AST_Node] = field(default_factory=list)
    variable_bindings: Dict[str, VariableNode] = field(default_factory=dict)
    constant_to_variable_map: Dict[str, VariableNode] = field(default_factory=dict)
    
    def to_logic_template(self) -> AST_Node:
        """
        Convert the generalized explanation to a logic template (rule).
        
        Returns:
            An AST_Node representing the generalized rule
        """
        if not self.premises:
            return self.goal
        
        # Create a conjunction of the premises
        if len(self.premises) == 1:
            body_ast = self.premises[0]
        else:
            body_ast = ConnectiveNode(
                connective_type="AND",
                operands=self.premises,
                type_ref=self.premises[0].type  # Assuming all premises have the same type
            )
        
        # Create an implication: body -> goal
        return ConnectiveNode(
            connective_type="IMPLIES",
            operands=[body_ast, self.goal],
            type_ref=self.goal.type
        )


class ExplanationBasedLearner:
    """
    Explanation-Based Learner for GödelOS.
    
    This class implements the ExplanationBasedLearner component (Module 3.2) of the Learning System,
    which analyzes successful problem-solving instances (ProofObjects) and forms generalized
    rules (LogicTemplates) that capture the essence of the solutions.
    """
    
    def __init__(self, kr_system_interface: KnowledgeStoreInterface, 
                 inference_engine: InferenceCoordinator,
                 operationality_config: Optional[OperationalityConfig] = None):
        """
        Initialize the Explanation-Based Learner.
        
        Args:
            kr_system_interface: Interface to the Knowledge Representation system
            inference_engine: The inference engine for checking entailment
            operationality_config: Configuration for determining which predicates are operational
        """
        self.ksi = kr_system_interface
        self.inference_engine = inference_engine
        self.op_config = operationality_config or OperationalityConfig()
        
    def generalize_from_proof_object(self, proof_object: ProofObject) -> Optional[AST_Node]:
        """
        Generalize from a successful proof object to form a rule.
        
        This method analyzes a successful proof object and forms a generalized rule
        that captures the essence of the solution by abstracting constants into variables.
        
        Args:
            proof_object: The successful proof object to generalize from
            
        Returns:
            A generalized rule as an AST_Node, or None if generalization failed
        """
        if not proof_object.goal_achieved:
            logger.warning("Cannot generalize from unsuccessful proof")
            return None
        
        if not proof_object.conclusion_ast:
            logger.warning("Proof object has no conclusion")
            return None
        
        logger.info(f"Generalizing from proof for: {proof_object.conclusion_ast}")
        
        # Step 1: Extract the explanation structure from the proof object
        explanation = self._extract_explanation(proof_object)
        
        # Step 2: Generalize the explanation by variabilizing constants
        generalized_explanation = self._generalize_explanation(explanation, proof_object)
        
        # Step 3: Check operationality of the generalized explanation
        operational_explanation = self._ensure_operationality(generalized_explanation)
        
        if not operational_explanation:
            logger.warning("Failed to create an operational explanation")
            return None
        
        # Step 4: Create a logic template from the generalized explanation
        logic_template = operational_explanation.to_logic_template()
        
        logger.info(f"Generated logic template: {logic_template}")
        return logic_template
    
    def _extract_explanation(self, proof_object: ProofObject) -> Dict[int, ProofStepNode]:
        """
        Extract the explanation structure from a proof object.
        
        This method extracts the specific rules and ground facts from the proof object
        that constitute the explanation for the goal.
        
        Args:
            proof_object: The proof object to extract the explanation from
            
        Returns:
            A dictionary mapping step indices to ProofStepNodes
        """
        explanation = {}
        
        # Add all proof steps to the explanation
        for i, step in enumerate(proof_object.proof_steps):
            explanation[i] = step
        
        return explanation
    
    def _generalize_explanation(self, explanation: Dict[int, ProofStepNode], 
                               proof_object: ProofObject) -> GeneralizedExplanation:
        """
        Generalize the explanation by variabilizing constants.
        
        This method identifies constants in the goal that are candidates for variabilization
        and replaces them with new distinct variables, then traces these variabilizations
        back through the proof structure.
        
        Args:
            explanation: The explanation structure extracted from the proof object
            proof_object: The original proof object
            
        Returns:
            A generalized explanation structure
        """
        # Start with the goal (conclusion) of the proof
        goal = proof_object.conclusion_ast
        
        # Create a generalized explanation structure
        gen_explanation = GeneralizedExplanation(goal=goal)
        
        # Identify constants in the goal that are candidates for variabilization
        constants = self._identify_constants(goal)
        
        # Create a mapping from constants to variables
        constant_to_variable_map = {}
        next_var_id = 1
        
        for const_name, const_node in constants.items():
            var_name = f"?{const_name[0].lower()}{next_var_id}"
            var_node = VariableNode(
                name=var_name,
                var_id=next_var_id,
                type_ref=const_node.type
            )
            constant_to_variable_map[const_name] = var_node
            next_var_id += 1
        
        # Variabilize the goal
        generalized_goal = self._variabilize_ast(goal, constant_to_variable_map)
        gen_explanation.goal = generalized_goal
        gen_explanation.constant_to_variable_map = constant_to_variable_map
        
        # Trace back through the proof to identify the premises
        leaf_steps = self._identify_leaf_steps(explanation)
        
        # Generalize the premises (leaf steps)
        generalized_premises = []
        for step_idx in leaf_steps:
            step = explanation[step_idx]
            generalized_formula = self._variabilize_ast(step.formula, constant_to_variable_map)
            generalized_premises.append(generalized_formula)
        
        gen_explanation.premises = generalized_premises
        
        return gen_explanation
    
    def _ensure_operationality(self, gen_explanation: GeneralizedExplanation) -> Optional[GeneralizedExplanation]:
        """
        Ensure that the generalized explanation is operational.
        
        This method checks if each literal in the premises of the generalized explanation
        meets the operationality criteria. If not, it attempts to unfold non-operational
        predicates until operational predicates are reached.
        
        Args:
            gen_explanation: The generalized explanation to check
            
        Returns:
            An operational generalized explanation, or None if operationality cannot be ensured
        """
        # Check if all premises are operational
        all_operational = True
        for premise in gen_explanation.premises:
            if not self._is_operational(premise):
                all_operational = False
                break
        
        if all_operational:
            return gen_explanation
        
        # If not all premises are operational, try to unfold them
        unfolding_depth = 0
        current_explanation = gen_explanation
        
        while not all_operational and unfolding_depth < self.op_config.max_unfolding_depth:
            unfolding_depth += 1
            
            # Try to unfold non-operational premises
            new_premises = []
            for premise in current_explanation.premises:
                if self._is_operational(premise):
                    new_premises.append(premise)
                else:
                    # Attempt to unfold this premise
                    unfolded = self._unfold_premise(premise, current_explanation.constant_to_variable_map)
                    if unfolded:
                        new_premises.extend(unfolded)
                    else:
                        # If we can't unfold, keep the original premise
                        new_premises.append(premise)
            
            # Update the explanation with the new premises
            current_explanation = GeneralizedExplanation(
                goal=current_explanation.goal,
                premises=new_premises,
                variable_bindings=current_explanation.variable_bindings,
                constant_to_variable_map=current_explanation.constant_to_variable_map
            )
            
            # Check if all premises are now operational
            all_operational = True
            for premise in current_explanation.premises:
                if not self._is_operational(premise):
                    all_operational = False
                    break
        
        if all_operational:
            return current_explanation
        
        # If we've reached the maximum unfolding depth and still have non-operational premises,
        # we can either return None or return the best we could do
        logger.warning(f"Could not ensure operationality after {unfolding_depth} unfolding steps")
        return current_explanation
    
    def _identify_constants(self, ast_node: AST_Node) -> Dict[str, ConstantNode]:
        """
        Identify constants in an AST node that are candidates for variabilization.
        
        Args:
            ast_node: The AST node to analyze
            
        Returns:
            A dictionary mapping constant names to ConstantNodes
        """
        constants = {}
        
        if isinstance(ast_node, ConstantNode):
            # Skip predicate/function names
            if ast_node.type.name != "Predicate" and ast_node.type.name != "Function":
                constants[ast_node.name] = ast_node
        
        elif isinstance(ast_node, ApplicationNode):
            # Skip the operator (predicate/function name)
            for arg in ast_node.arguments:
                arg_constants = self._identify_constants(arg)
                constants.update(arg_constants)
        
        elif isinstance(ast_node, ConnectiveNode):
            for operand in ast_node.operands:
                operand_constants = self._identify_constants(operand)
                constants.update(operand_constants)
        
        return constants
    
    def _variabilize_ast(self, ast_node: AST_Node, 
                        constant_to_variable_map: Dict[str, VariableNode]) -> AST_Node:
        """
        Replace constants with variables in an AST node.
        
        Args:
            ast_node: The AST node to variabilize
            constant_to_variable_map: Mapping from constant names to variables
            
        Returns:
            A variabilized AST node
        """
        if isinstance(ast_node, ConstantNode):
            # If this constant is in the map, replace it with the corresponding variable
            if ast_node.name in constant_to_variable_map and ast_node.type.name != "Predicate" and ast_node.type.name != "Function":
                return constant_to_variable_map[ast_node.name]
            return ast_node
        
        elif isinstance(ast_node, VariableNode):
            return ast_node
        
        elif isinstance(ast_node, ApplicationNode):
            # Variabilize the operator and arguments
            variabilized_operator = self._variabilize_ast(ast_node.operator, constant_to_variable_map)
            variabilized_arguments = [
                self._variabilize_ast(arg, constant_to_variable_map)
                for arg in ast_node.arguments
            ]
            
            return ApplicationNode(
                operator=variabilized_operator,
                arguments=variabilized_arguments,
                type_ref=ast_node.type
            )
        
        elif isinstance(ast_node, ConnectiveNode):
            # Variabilize the operands
            variabilized_operands = [
                self._variabilize_ast(operand, constant_to_variable_map)
                for operand in ast_node.operands
            ]
            
            return ConnectiveNode(
                connective_type=ast_node.connective_type,
                operands=variabilized_operands,
                type_ref=ast_node.type
            )
        
        # For other node types, return as is
        return ast_node
    
    def _identify_leaf_steps(self, explanation: Dict[int, ProofStepNode]) -> List[int]:
        """
        Identify the leaf steps in the proof.
        
        Leaf steps are those that don't depend on other steps, typically
        representing axioms or facts from the knowledge base.
        
        Args:
            explanation: The explanation structure
            
        Returns:
            A list of indices of leaf steps
        """
        # Find all steps that are referenced as premises
        referenced_steps = set()
        for step in explanation.values():
            referenced_steps.update(step.premises)
        
        # Leaf steps are those that aren't referenced as premises
        leaf_steps = []
        for step_idx in explanation:
            if not explanation[step_idx].premises:
                leaf_steps.append(step_idx)
        
        return leaf_steps
    
    def _is_operational(self, ast_node: AST_Node) -> bool:
        """
        Check if an AST node is operational.
        
        An AST node is operational if it uses only predicates that are
        considered operational according to the operationality configuration.
        
        Args:
            ast_node: The AST node to check
            
        Returns:
            True if the AST node is operational, False otherwise
        """
        if isinstance(ast_node, ApplicationNode):
            # Check if the predicate is operational
            if isinstance(ast_node.operator, ConstantNode):
                predicate_name = ast_node.operator.name
                return self.op_config.is_operational(predicate_name)
            
            # If the operator is not a constant (e.g., a variable), it's not operational
            return False
        
        elif isinstance(ast_node, ConnectiveNode):
            # A connective is operational if all its operands are operational
            return all(self._is_operational(operand) for operand in ast_node.operands)
        
        # Other node types are considered operational
        return True
    
    def _unfold_premise(self, premise: AST_Node, 
                       constant_to_variable_map: Dict[str, VariableNode]) -> Optional[List[AST_Node]]:
        """
        Unfold a non-operational premise into more operational ones.
        
        This method attempts to replace a non-operational predicate with its definition
        from the knowledge base, effectively "unfolding" it into more primitive predicates.
        
        Args:
            premise: The premise to unfold
            constant_to_variable_map: Mapping from constant names to variables
            
        Returns:
            A list of unfolded premises, or None if unfolding failed
        """
        if not isinstance(premise, ApplicationNode):
            return None
        
        if not isinstance(premise.operator, ConstantNode):
            return None
        
        predicate_name = premise.operator.name
        
        # Query the knowledge store for the definition of this predicate
        definition_query = VariableNode(
            name="?definition",
            var_id=1,
            type_ref=premise.type
        )
        
        # Create a pattern to match definitions of this predicate
        # This is a simplified approach; in a real system, you would need a more sophisticated
        # way to find predicate definitions
        query_result = self.ksi.query_statements_match_pattern(
            query_pattern_ast=definition_query,
            context_ids=["TRUTHS"]
        )
        
        for binding in query_result:
            definition = binding.get(definition_query)
            if definition and isinstance(definition, ConnectiveNode) and definition.connective_type == "IMPLIES":
                # Check if this definition applies to our premise
                head = definition.operands[1]
                if isinstance(head, ApplicationNode) and isinstance(head.operator, ConstantNode) and head.operator.name == predicate_name:
                    # This definition applies to our premise
                    # Now we need to unify the head with our premise and apply the resulting bindings to the body
                    unification_result = self.ksi.unification_engine.unify(head, premise)
                    if unification_result[0]:  # If unification succeeded
                        bindings = unification_result[0]
                        
                        # Apply the bindings to the body of the definition
                        body = definition.operands[0]
                        instantiated_body = self._apply_bindings(body, bindings)
                        
                        # If the body is a conjunction, return its operands as separate premises
                        if isinstance(instantiated_body, ConnectiveNode) and instantiated_body.connective_type == "AND":
                            return instantiated_body.operands
                        else:
                            return [instantiated_body]
        
        # If we couldn't find a suitable definition, return None
        return None
    
    def _apply_bindings(self, ast_node: AST_Node, 
                       bindings: Dict[int, AST_Node]) -> AST_Node:
        """
        Apply variable bindings to an AST node.
        
        Args:
            ast_node: The AST node to apply bindings to
            bindings: Dictionary mapping variable IDs to AST nodes
            
        Returns:
            An AST node with bindings applied
        """
        if isinstance(ast_node, VariableNode):
            # If this variable is in the bindings, replace it
            if ast_node.var_id in bindings:
                return bindings[ast_node.var_id]
            return ast_node
        
        elif isinstance(ast_node, ConstantNode):
            return ast_node
        
        elif isinstance(ast_node, ApplicationNode):
            # Apply bindings to the operator and arguments
            bound_operator = self._apply_bindings(ast_node.operator, bindings)
            bound_arguments = [
                self._apply_bindings(arg, bindings)
                for arg in ast_node.arguments
            ]
            
            return ApplicationNode(
                operator=bound_operator,
                arguments=bound_arguments,
                type_ref=ast_node.type
            )
        
        elif isinstance(ast_node, ConnectiveNode):
            # Apply bindings to the operands
            bound_operands = [
                self._apply_bindings(operand, bindings)
                for operand in ast_node.operands
            ]
            
            return ConnectiveNode(
                connective_type=ast_node.connective_type,
                operands=bound_operands,
                type_ref=ast_node.type
            )
        
        # For other node types, return as is
        return ast_node