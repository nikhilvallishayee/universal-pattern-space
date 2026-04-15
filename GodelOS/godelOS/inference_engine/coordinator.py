"""
Inference Coordinator for the Inference Engine Architecture.

This module implements the InferenceCoordinator class, which is responsible for
receiving reasoning tasks (goals) from other parts of the system, analyzing the goal's
logical structure, type, and context, selecting the most appropriate inference engine(s)
or strategy, and managing the overall proof search process.
"""

import time
from typing import Dict, List, Optional, Set, Tuple, Type, Any
import logging

from godelOS.core_kr.ast.nodes import (
    AST_Node, VariableNode, ConnectiveNode, QuantifierNode, 
    ModalOpNode, ApplicationNode
)
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject

# Set up logging
logger = logging.getLogger(__name__)


class StrategyKnowledgeBase:
    """
    Knowledge base for prover selection strategies.
    
    This class encapsulates the knowledge and rules used to select the most appropriate
    prover for a given goal and context.
    """
    
    def __init__(self):
        """Initialize the strategy knowledge base."""
        self.strategy_rules = []
    
    def add_strategy_rule(self, rule_name: str, condition_fn, prover_name: str, priority: int = 0):
        """
        Add a strategy rule to the knowledge base.
        
        Args:
            rule_name: Name of the rule
            condition_fn: Function that takes a goal AST and context ASTs and returns True if the rule applies
            prover_name: Name of the prover to use if the rule applies
            priority: Priority of the rule (higher priority rules are checked first)
        """
        self.strategy_rules.append({
            'name': rule_name,
            'condition': condition_fn,
            'prover': prover_name,
            'priority': priority
        })
        # Sort rules by priority (descending)
        self.strategy_rules.sort(key=lambda r: -r['priority'])
    
    def select_prover(self, goal_ast: AST_Node, context_asts: Set[AST_Node], 
                     available_provers: Dict[str, BaseProver], 
                     strategy_hint: Optional[str] = None) -> Optional[str]:
        """
        Select the most appropriate prover for a given goal and context.
        
        Args:
            goal_ast: The goal to prove
            context_asts: The set of context assertions
            available_provers: Dictionary of available provers (name -> prover)
            strategy_hint: Optional hint for strategy selection
            
        Returns:
            The name of the selected prover, or None if no suitable prover is found
        """
        # If a strategy hint is provided and the corresponding prover is available,
        # use it directly
        if strategy_hint and strategy_hint in available_provers:
            if available_provers[strategy_hint].can_handle(goal_ast, context_asts):
                return strategy_hint
        
        # Otherwise, apply the strategy rules
        for rule in self.strategy_rules:
            if rule['prover'] in available_provers and rule['condition'](goal_ast, context_asts):
                prover = available_provers[rule['prover']]
                if prover.can_handle(goal_ast, context_asts):
                    logger.info(f"Selected prover {rule['prover']} using rule {rule['name']}")
                    return rule['prover']
        
        # If no rule applies, try each prover in turn
        for name, prover in available_provers.items():
            if prover.can_handle(goal_ast, context_asts):
                logger.info(f"Selected prover {name} as fallback")
                return name
        
        # If no prover can handle the goal, return None
        logger.warning(f"No suitable prover found for goal: {goal_ast}")
        return None


class InferenceCoordinator:
    """
    Coordinator for the Inference Engine Architecture.
    
    This class is responsible for receiving reasoning tasks (goals) from other parts
    of the system, analyzing the goal's logical structure, type, and context, selecting
    the most appropriate inference engine(s) or strategy, and managing the overall
    proof search process.
    """
    
    def __init__(self, kr_system_interface: KnowledgeStoreInterface, 
                provers_map: Dict[str, BaseProver],
                strategy_kb: Optional[StrategyKnowledgeBase] = None):
        """
        Initialize the inference coordinator.
        
        Args:
            kr_system_interface: Interface to the Knowledge Representation system
            provers_map: Dictionary mapping prover names to prover instances
            strategy_kb: Optional strategy knowledge base for prover selection
        """
        self.kr_system_interface = kr_system_interface
        self.provers = provers_map
        self.strategy_kb = strategy_kb or self._create_default_strategy_kb()
    
    def _create_default_strategy_kb(self) -> StrategyKnowledgeBase:
        """
        Create a default strategy knowledge base.
        
        Returns:
            A default strategy knowledge base with basic rules
        """
        kb = StrategyKnowledgeBase()
        
        # Add basic rules based on goal structure
        kb.add_strategy_rule(
            "modal_logic_rule",
            lambda goal, _: self._contains_modal_operator(goal),
            "modal_tableau_prover",
            priority=100
        )
        
        kb.add_strategy_rule(
            "arithmetic_rule",
            lambda goal, _: self._contains_arithmetic(goal),
            "smt_interface",
            priority=90
        )
        
        kb.add_strategy_rule(
            "constraint_rule",
            lambda goal, _: self._contains_constraints(goal),
            "clp_module",
            priority=80
        )
        
        kb.add_strategy_rule(
            "first_order_rule",
            lambda goal, _: True,  # Default rule for first-order logic
            "resolution_prover",
            priority=10
        )
        
        return kb
    
    def _contains_modal_operator(self, ast: AST_Node) -> bool:
        """
        Check if an AST contains a modal operator.
        
        Args:
            ast: The AST to check
            
        Returns:
            True if the AST contains a modal operator, False otherwise
        """
        if isinstance(ast, ModalOpNode):
            return True
        
        # Recursively check child nodes
        if isinstance(ast, ApplicationNode):
            if self._contains_modal_operator(ast.operator):
                return True
            for arg in ast.arguments:
                if self._contains_modal_operator(arg):
                    return True
        elif isinstance(ast, ConnectiveNode):
            for operand in ast.operands:
                if self._contains_modal_operator(operand):
                    return True
        elif isinstance(ast, QuantifierNode):
            return self._contains_modal_operator(ast.scope)
        
        return False
    
    def _contains_arithmetic(self, ast: AST_Node) -> bool:
        """
        Check if an AST contains arithmetic operations or predicates.
        
        This is a simplified check that looks for common arithmetic operation names.
        A more sophisticated implementation would use the type system.
        
        Args:
            ast: The AST to check
            
        Returns:
            True if the AST contains arithmetic, False otherwise
        """
        # Check for common arithmetic operations
        if isinstance(ast, ApplicationNode):
            op = ast.operator
            if hasattr(op, 'name') and isinstance(op.name, str):
                arithmetic_ops = {'+', '-', '*', '/', '<', '<=', '>', '>=', '='}
                if op.name in arithmetic_ops:
                    return True
            
            # Recursively check operator and arguments
            if self._contains_arithmetic(op):
                return True
            for arg in ast.arguments:
                if self._contains_arithmetic(arg):
                    return True
        
        # Recursively check other node types
        if isinstance(ast, ConnectiveNode):
            for operand in ast.operands:
                if self._contains_arithmetic(operand):
                    return True
        elif isinstance(ast, QuantifierNode):
            return self._contains_arithmetic(ast.scope)
        elif isinstance(ast, ModalOpNode):
            if ast.agent_or_world and self._contains_arithmetic(ast.agent_or_world):
                return True
            return self._contains_arithmetic(ast.proposition)
        
        return False
    
    def _contains_constraints(self, ast: AST_Node) -> bool:
        """
        Check if an AST contains constraint predicates.
        
        This is a simplified check that looks for common constraint predicate names.
        A more sophisticated implementation would use the type system or annotations.
        
        Args:
            ast: The AST to check
            
        Returns:
            True if the AST contains constraints, False otherwise
        """
        # Check for common constraint predicates
        if isinstance(ast, ApplicationNode):
            op = ast.operator
            if hasattr(op, 'name') and isinstance(op.name, str):
                constraint_ops = {'AllDifferent', 'SumEquals', 'Element', 'Cumulative', 'GlobalCardinality'}
                if op.name in constraint_ops or op.name.startswith('Constraint'):
                    return True
            
            # Recursively check operator and arguments
            if self._contains_constraints(op):
                return True
            for arg in ast.arguments:
                if self._contains_constraints(arg):
                    return True
        
        # Recursively check other node types
        if isinstance(ast, ConnectiveNode):
            for operand in ast.operands:
                if self._contains_constraints(operand):
                    return True
        elif isinstance(ast, QuantifierNode):
            return self._contains_constraints(ast.scope)
        elif isinstance(ast, ModalOpNode):
            if ast.agent_or_world and self._contains_constraints(ast.agent_or_world):
                return True
            return self._contains_constraints(ast.proposition)
        
        return False
    
    def submit_goal(self, goal_ast: AST_Node, context_ast_set: Set[AST_Node], 
                   strategy_hint: Optional[str] = None, 
                   resources: Optional[ResourceLimits] = None) -> ProofObject:
        """
        Submit a goal for proof.
        
        This is the main entry point for the Inference Coordinator. It analyzes the goal,
        selects an appropriate prover, and manages the proof process.
        
        Args:
            goal_ast: The goal to prove
            context_ast_set: The set of context assertions (axioms, facts, rules)
            strategy_hint: Optional hint for strategy selection
            resources: Optional resource limits for the proof attempt
            
        Returns:
            A ProofObject representing the result of the proof attempt
        """
        start_time = time.time()
        
        # Set default resource limits if none provided
        if resources is None:
            resources = ResourceLimits(time_limit_ms=10000, depth_limit=100)
        
        # Log the goal submission
        logger.info(f"Goal submitted: {goal_ast}")
        logger.info(f"Context size: {len(context_ast_set)}")
        logger.info(f"Strategy hint: {strategy_hint}")
        logger.info(f"Resource limits: {resources}")
        
        # Select an appropriate prover
        selected_prover_name = self.strategy_kb.select_prover(
            goal_ast, context_ast_set, self.provers, strategy_hint
        )
        
        if selected_prover_name and selected_prover_name in self.provers:
            selected_prover = self.provers[selected_prover_name]
            logger.info(f"Selected prover: {selected_prover_name}")
            
            try:
                # Attempt to prove the goal
                proof_object = selected_prover.prove(goal_ast, context_ast_set, resources)
                
                # Calculate time taken
                end_time = time.time()
                time_taken_ms = (end_time - start_time) * 1000
                
                # Update the proof object with time information
                resources_consumed = proof_object.resources_consumed.copy()
                resources_consumed['time_taken_ms'] = time_taken_ms
                updated_proof_object = proof_object.with_time_and_resources(
                    time_taken_ms, resources_consumed
                )
                
                logger.info(f"Proof result: {updated_proof_object.goal_achieved}")
                logger.info(f"Status message: {updated_proof_object.status_message}")
                logger.info(f"Time taken: {time_taken_ms:.2f} ms")
                
                return updated_proof_object
                
            except Exception as e:
                # Handle exceptions during proof
                logger.error(f"Error during proof: {str(e)}", exc_info=True)
                end_time = time.time()
                time_taken_ms = (end_time - start_time) * 1000
                
                return ProofObject.create_failure(
                    status_message=f"Error: {str(e)}",
                    inference_engine_used=selected_prover_name,
                    time_taken_ms=time_taken_ms,
                    resources_consumed={'error': 1}
                )
        else:
            # No suitable prover found
            end_time = time.time()
            time_taken_ms = (end_time - start_time) * 1000
            
            logger.warning("No suitable prover found")
            return ProofObject.create_failure(
                status_message="No suitable prover found or strategy failed.",
                inference_engine_used="none",
                time_taken_ms=time_taken_ms,
                resources_consumed={}
            )