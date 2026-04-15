"""
Rule Compiler (Module 6.3).

This module implements the RuleCompiler class, which compiles logical rules
into more efficient executable forms, implements rule indexing for faster matching,
supports different compilation strategies based on rule complexity, and provides
methods to execute compiled rules.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union, DefaultDict
import time
import copy
import logging
from enum import Enum
from collections import defaultdict
import hashlib

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface


class RuleType(Enum):
    """Enumeration of rule types."""
    SIMPLE = 1  # Simple rules with a single condition and conclusion
    CONJUNCTIVE = 2  # Rules with multiple conjunctive conditions
    COMPLEX = 3  # Rules with complex conditions (e.g., disjunctions, negations)


class CompiledRule:
    """
    Class representing a compiled rule.
    
    A compiled rule is a rule that has been processed and optimized for
    efficient execution.
    """
    
    def __init__(self, rule_id: str, rule_ast: AST_Node, rule_type: RuleType):
        """
        Initialize the compiled rule.
        
        Args:
            rule_id: The ID of the rule
            rule_ast: The AST of the rule
            rule_type: The type of the rule
        """
        self.rule_id = rule_id
        self.original_rule_ast = rule_ast
        self.rule_type = rule_type
        self.compiled_form: Any = None
        self.condition_indices: Dict[str, Any] = {}
        self.last_matched: float = 0
        self.match_count: int = 0
        self.average_execution_time: float = 0
        self.total_execution_time: float = 0
    
    def __str__(self) -> str:
        """
        Get a string representation of the compiled rule.
        
        Returns:
            A string representation of the compiled rule
        """
        return f"CompiledRule(id={self.rule_id}, type={self.rule_type}, matches={self.match_count})"


class RuleIndex:
    """
    Class for indexing rules for faster matching.
    
    The RuleIndex maintains indices on rule conditions to quickly find
    rules that might match a given fact.
    """
    
    def __init__(self):
        """Initialize the rule index."""
        self.predicate_index: DefaultDict[str, Set[str]] = defaultdict(set)
        self.constant_index: DefaultDict[str, Set[str]] = defaultdict(set)
        self.type_index: DefaultDict[str, Set[str]] = defaultdict(set)
    
    def add_rule(self, rule: CompiledRule) -> None:
        """
        Add a rule to the index.
        
        Args:
            rule: The rule to add
        """
        # Extract conditions from the rule
        conditions = self._extract_conditions(rule.original_rule_ast)
        
        # Index the rule by predicates, constants, and types in its conditions
        for condition in conditions:
            self._index_condition(condition, rule.rule_id)
    
    def remove_rule(self, rule: CompiledRule) -> None:
        """
        Remove a rule from the index.
        
        Args:
            rule: The rule to remove
        """
        # Extract conditions from the rule
        conditions = self._extract_conditions(rule.original_rule_ast)
        
        # Remove the rule from indices
        for condition in conditions:
            self._remove_from_indices(condition, rule.rule_id)
    
    def find_matching_rules(self, fact: AST_Node) -> Set[str]:
        """
        Find rules that might match a given fact.
        
        Args:
            fact: The fact to match
            
        Returns:
            A set of rule IDs that might match the fact
        """
        matching_rule_ids = set()
        
        # Check predicate index
        if isinstance(fact, ApplicationNode) and isinstance(fact.operator, ConstantNode):
            predicate_name = fact.operator.name
            matching_rule_ids.update(self.predicate_index.get(predicate_name, set()))
        
        # Check constant index
        if isinstance(fact, ApplicationNode):
            for arg in fact.arguments:
                if isinstance(arg, ConstantNode):
                    constant_name = arg.name
                    matching_rule_ids.update(self.constant_index.get(constant_name, set()))
        
        # Check type index
        type_name = fact.type.name
        matching_rule_ids.update(self.type_index.get(type_name, set()))
        
        return matching_rule_ids
    
    def _extract_conditions(self, rule_ast: AST_Node) -> List[AST_Node]:
        """
        Extract conditions from a rule AST.
        
        Args:
            rule_ast: The rule AST
            
        Returns:
            A list of condition AST nodes
        """
        # This is a simplified implementation that assumes rules are
        # represented as ApplicationNodes with a specific structure.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just return the rule AST as the only condition
        return [rule_ast]
    
    def _index_condition(self, condition: AST_Node, rule_id: str) -> None:
        """
        Index a condition for a rule.
        
        Args:
            condition: The condition to index
            rule_id: The ID of the rule
        """
        # Index by type
        type_name = condition.type.name
        self.type_index[type_name].add(rule_id)
        
        # Index ApplicationNodes by predicate name and constants
        if isinstance(condition, ApplicationNode):
            # Index by predicate name
            if isinstance(condition.operator, ConstantNode):
                predicate_name = condition.operator.name
                self.predicate_index[predicate_name].add(rule_id)
            
            # Index by constants in the arguments
            for arg in condition.arguments:
                if isinstance(arg, ConstantNode):
                    constant_name = arg.name
                    self.constant_index[constant_name].add(rule_id)
    
    def _remove_from_indices(self, condition: AST_Node, rule_id: str) -> None:
        """
        Remove a condition from indices.
        
        Args:
            condition: The condition to remove
            rule_id: The ID of the rule
        """
        # Remove from type index
        type_name = condition.type.name
        if rule_id in self.type_index[type_name]:
            self.type_index[type_name].remove(rule_id)
        
        # Remove from predicate index
        if isinstance(condition, ApplicationNode) and isinstance(condition.operator, ConstantNode):
            predicate_name = condition.operator.name
            if rule_id in self.predicate_index[predicate_name]:
                self.predicate_index[predicate_name].remove(rule_id)
        
        # Remove from constant index
        if isinstance(condition, ApplicationNode):
            for arg in condition.arguments:
                if isinstance(arg, ConstantNode):
                    constant_name = arg.name
                    if rule_id in self.constant_index[constant_name]:
                        self.constant_index[constant_name].remove(rule_id)


class CompilationStrategy:
    """
    Base class for rule compilation strategies.
    
    A compilation strategy defines how a rule is compiled into an
    executable form.
    """
    
    def compile(self, rule: CompiledRule) -> None:
        """
        Compile a rule.
        
        Args:
            rule: The rule to compile
        """
        raise NotImplementedError("Subclasses must implement compile method")
    
    def execute(self, rule: CompiledRule, knowledge_store: KnowledgeStoreInterface, context_ids: List[str]) -> List[Dict[VariableNode, AST_Node]]:
        """
        Execute a compiled rule.
        
        Args:
            rule: The compiled rule
            knowledge_store: The knowledge store interface
            context_ids: The contexts to query
            
        Returns:
            The results of executing the rule
        """
        raise NotImplementedError("Subclasses must implement execute method")


class SimpleRuleStrategy(CompilationStrategy):
    """
    Compilation strategy for simple rules.
    
    Simple rules have a single condition and conclusion.
    """
    
    def compile(self, rule: CompiledRule) -> None:
        """
        Compile a simple rule.
        
        Args:
            rule: The rule to compile
        """
        # For simple rules, we just extract the condition and conclusion
        # This is a simplified implementation that assumes rules are
        # represented as ApplicationNodes with a specific structure.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just store the original AST as the compiled form
        rule.compiled_form = rule.original_rule_ast
    
    def execute(self, rule: CompiledRule, knowledge_store: KnowledgeStoreInterface, context_ids: List[str]) -> List[Dict[VariableNode, AST_Node]]:
        """
        Execute a compiled simple rule.
        
        Args:
            rule: The compiled rule
            knowledge_store: The knowledge store interface
            context_ids: The contexts to query
            
        Returns:
            The results of executing the rule
        """
        # For simple rules, we just query the condition and apply the conclusion
        # This is a simplified implementation that assumes rules are
        # represented as ApplicationNodes with a specific structure.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just return an empty list
        return []


class ConjunctiveRuleStrategy(CompilationStrategy):
    """
    Compilation strategy for conjunctive rules.
    
    Conjunctive rules have multiple conjunctive conditions.
    """
    
    def compile(self, rule: CompiledRule) -> None:
        """
        Compile a conjunctive rule.
        
        Args:
            rule: The rule to compile
        """
        # For conjunctive rules, we extract the conditions and conclusion,
        # and optimize the order of condition evaluation.
        # This is a simplified implementation that assumes rules are
        # represented as ApplicationNodes with a specific structure.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just store the original AST as the compiled form
        rule.compiled_form = rule.original_rule_ast
    
    def execute(self, rule: CompiledRule, knowledge_store: KnowledgeStoreInterface, context_ids: List[str]) -> List[Dict[VariableNode, AST_Node]]:
        """
        Execute a compiled conjunctive rule.
        
        Args:
            rule: The compiled rule
            knowledge_store: The knowledge store interface
            context_ids: The contexts to query
            
        Returns:
            The results of executing the rule
        """
        # For conjunctive rules, we query each condition in order,
        # join the results, and apply the conclusion.
        # This is a simplified implementation that assumes rules are
        # represented as ApplicationNodes with a specific structure.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just return an empty list
        return []


class ComplexRuleStrategy(CompilationStrategy):
    """
    Compilation strategy for complex rules.
    
    Complex rules have complex conditions (e.g., disjunctions, negations).
    """
    
    def compile(self, rule: CompiledRule) -> None:
        """
        Compile a complex rule.
        
        Args:
            rule: The rule to compile
        """
        # For complex rules, we transform the rule into a more efficient form,
        # such as a decision tree or a set of simpler rules.
        # This is a simplified implementation that assumes rules are
        # represented as ApplicationNodes with a specific structure.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just store the original AST as the compiled form
        rule.compiled_form = rule.original_rule_ast
    
    def execute(self, rule: CompiledRule, knowledge_store: KnowledgeStoreInterface, context_ids: List[str]) -> List[Dict[VariableNode, AST_Node]]:
        """
        Execute a compiled complex rule.
        
        Args:
            rule: The compiled rule
            knowledge_store: The knowledge store interface
            context_ids: The contexts to query
            
        Returns:
            The results of executing the rule
        """
        # For complex rules, we execute the transformed rule.
        # This is a simplified implementation that assumes rules are
        # represented as ApplicationNodes with a specific structure.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just return an empty list
        return []


class RuleCompiler:
    """
    Class for compiling logical rules into more efficient executable forms.
    
    The RuleCompiler analyzes rules, selects appropriate compilation strategies,
    and provides methods to execute compiled rules.
    """
    
    def __init__(self, knowledge_store: KnowledgeStoreInterface):
        """
        Initialize the rule compiler.
        
        Args:
            knowledge_store: The knowledge store interface
        """
        self.knowledge_store = knowledge_store
        self.compiled_rules: Dict[str, CompiledRule] = {}
        self.rule_index = RuleIndex()
        self.compilation_strategies: Dict[RuleType, CompilationStrategy] = {
            RuleType.SIMPLE: SimpleRuleStrategy(),
            RuleType.CONJUNCTIVE: ConjunctiveRuleStrategy(),
            RuleType.COMPLEX: ComplexRuleStrategy()
        }
        self.logger = logging.getLogger(__name__)
    
    def compile_rule(self, rule_ast: AST_Node, rule_id: Optional[str] = None) -> str:
        """
        Compile a rule.
        
        Args:
            rule_ast: The AST of the rule
            rule_id: Optional ID for the rule
            
        Returns:
            The ID of the compiled rule
        """
        # Generate a rule ID if not provided
        if rule_id is None:
            rule_id = self._generate_rule_id(rule_ast)
        
        # Check if the rule is already compiled
        if rule_id in self.compiled_rules:
            return rule_id
        
        # Determine the rule type
        rule_type = self._determine_rule_type(rule_ast)
        
        # Create a compiled rule
        rule = CompiledRule(rule_id, rule_ast, rule_type)
        
        # Select the appropriate compilation strategy
        strategy = self.compilation_strategies[rule_type]
        
        # Compile the rule
        try:
            strategy.compile(rule)
        except Exception as e:
            self.logger.error(f"Error compiling rule {rule_id}: {e}")
            raise
        
        # Store the compiled rule
        self.compiled_rules[rule_id] = rule
        
        # Index the rule
        self.rule_index.add_rule(rule)
        
        return rule_id
    
    def execute_rule(self, rule_id: str, context_ids: List[str]) -> List[Dict[VariableNode, AST_Node]]:
        """
        Execute a compiled rule.
        
        Args:
            rule_id: The ID of the rule
            context_ids: The contexts to query
            
        Returns:
            The results of executing the rule
        """
        # Check if the rule exists
        if rule_id not in self.compiled_rules:
            raise ValueError(f"Rule {rule_id} not found")
        
        rule = self.compiled_rules[rule_id]
        
        # Select the appropriate compilation strategy
        strategy = self.compilation_strategies[rule.rule_type]
        
        # Execute the rule and measure execution time
        start_time = time.time()
        results = strategy.execute(rule, self.knowledge_store, context_ids)
        end_time = time.time()
        
        # Update rule statistics
        execution_time = end_time - start_time
        rule.last_matched = end_time
        rule.match_count += 1
        rule.total_execution_time += execution_time
        rule.average_execution_time = rule.total_execution_time / rule.match_count
        
        return results
    
    def find_matching_rules(self, fact: AST_Node) -> List[str]:
        """
        Find rules that might match a given fact.
        
        Args:
            fact: The fact to match
            
        Returns:
            A list of rule IDs that might match the fact
        """
        # Use the rule index to find matching rules
        matching_rule_ids = self.rule_index.find_matching_rules(fact)
        
        # Sort by match frequency (most frequently matched first)
        sorted_rule_ids = sorted(
            matching_rule_ids,
            key=lambda rule_id: self.compiled_rules[rule_id].match_count,
            reverse=True
        )
        
        return sorted_rule_ids
    
    def remove_rule(self, rule_id: str) -> None:
        """
        Remove a compiled rule.
        
        Args:
            rule_id: The ID of the rule
        """
        # Check if the rule exists
        if rule_id not in self.compiled_rules:
            raise ValueError(f"Rule {rule_id} not found")
        
        # Remove the rule from the index
        self.rule_index.remove_rule(self.compiled_rules[rule_id])
        
        # Remove the rule
        del self.compiled_rules[rule_id]
    
    def _generate_rule_id(self, rule_ast: AST_Node) -> str:
        """
        Generate a unique ID for a rule.
        
        Args:
            rule_ast: The AST of the rule
            
        Returns:
            A unique ID for the rule
        """
        # Generate a hash of the rule AST
        rule_hash = hashlib.md5(str(rule_ast).encode()).hexdigest()
        return f"rule_{rule_hash}"
    
    def _determine_rule_type(self, rule_ast: AST_Node) -> RuleType:
        """
        Determine the type of a rule.
        
        Args:
            rule_ast: The AST of the rule
            
        Returns:
            The type of the rule
        """
        # This is a simplified implementation that assumes rules are
        # represented as ApplicationNodes with a specific structure.
        # In a real system, we would use a more sophisticated approach that
        # handles the actual AST structure.
        
        # For now, we'll just return SIMPLE for all rules
        return RuleType.SIMPLE