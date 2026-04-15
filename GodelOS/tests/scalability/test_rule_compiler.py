"""
Unit tests for the Rule Compiler.

This module contains tests for the RuleCompiler, RuleIndex, CompiledRule,
and various compilation strategy classes.
"""

import unittest
from unittest.mock import MagicMock, patch

from godelOS.core_kr.ast.nodes import AST_Node, VariableNode, ConstantNode, ApplicationNode
from godelOS.core_kr.type_system.types import Type
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface

from godelOS.scalability.rule_compiler import (
    RuleCompiler,
    RuleIndex,
    CompiledRule,
    RuleType,
    SimpleRuleStrategy,
    ConjunctiveRuleStrategy,
    ComplexRuleStrategy
)


class TestCompiledRule(unittest.TestCase):
    """Test cases for the CompiledRule class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create a rule AST
        self.x = VariableNode("?x", "x", self.entity_type)
        self.person = ConstantNode("Person", "Person", self.entity_type)
        self.is_a = ConstantNode("is_a", "is_a", self.entity_type)
        self.rule_ast = ApplicationNode(self.is_a, [self.x, self.person], self.entity_type)
        
        # Create a compiled rule
        self.rule_id = "test_rule"
        self.rule_type = RuleType.SIMPLE
        self.rule = CompiledRule(self.rule_id, self.rule_ast, self.rule_type)
    
    def test_initialization(self):
        """Test initialization of a compiled rule."""
        # Check if the rule is initialized correctly
        self.assertEqual(self.rule.rule_id, self.rule_id)
        self.assertEqual(self.rule.original_rule_ast, self.rule_ast)
        self.assertEqual(self.rule.rule_type, self.rule_type)
        self.assertIsNone(self.rule.compiled_form)
        self.assertEqual(self.rule.condition_indices, {})
        self.assertEqual(self.rule.last_matched, 0)
        self.assertEqual(self.rule.match_count, 0)
        self.assertEqual(self.rule.average_execution_time, 0)
        self.assertEqual(self.rule.total_execution_time, 0)
    
    def test_str_representation(self):
        """Test string representation of a compiled rule."""
        # Set some statistics for the rule
        self.rule.match_count = 5
        
        # Check if the string representation is correct
        expected_str = f"CompiledRule(id={self.rule_id}, type={self.rule_type}, matches=5)"
        self.assertEqual(str(self.rule), expected_str)


class TestRuleIndex(unittest.TestCase):
    """Test cases for the RuleIndex class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create rule ASTs
        self.x = VariableNode("?x", "x", self.entity_type)
        self.person = ConstantNode("Person", "Person", self.entity_type)
        self.car = ConstantNode("Car", "Car", self.entity_type)
        self.is_a = ConstantNode("is_a", "is_a", self.entity_type)
        
        self.rule1_ast = ApplicationNode(self.is_a, [self.x, self.person], self.entity_type)
        self.rule2_ast = ApplicationNode(self.is_a, [self.x, self.car], self.entity_type)
        
        # Create compiled rules
        self.rule1 = CompiledRule("rule1", self.rule1_ast, RuleType.SIMPLE)
        self.rule2 = CompiledRule("rule2", self.rule2_ast, RuleType.SIMPLE)
        
        # Create a rule index
        self.index = RuleIndex()
    
    def test_add_rule(self):
        """Test adding a rule to the index."""
        # Add rules to the index
        self.index.add_rule(self.rule1)
        self.index.add_rule(self.rule2)
        
        # Check if the rules are indexed correctly
        self.assertIn("rule1", self.index.predicate_index["is_a"])
        self.assertIn("rule2", self.index.predicate_index["is_a"])
        self.assertIn("rule1", self.index.constant_index["Person"])
        self.assertIn("rule2", self.index.constant_index["Car"])
        self.assertIn("rule1", self.index.type_index[self.entity_type.name])
        self.assertIn("rule2", self.index.type_index[self.entity_type.name])
    
    def test_remove_rule(self):
        """Test removing a rule from the index."""
        # Add rules to the index
        self.index.add_rule(self.rule1)
        self.index.add_rule(self.rule2)
        
        # Remove a rule
        self.index.remove_rule(self.rule1)
        
        # Check if the rule is removed correctly
        self.assertNotIn("rule1", self.index.predicate_index["is_a"])
        self.assertIn("rule2", self.index.predicate_index["is_a"])
        self.assertNotIn("rule1", self.index.constant_index["Person"])
        self.assertIn("rule2", self.index.constant_index["Car"])
        self.assertNotIn("rule1", self.index.type_index[self.entity_type.name])
        self.assertIn("rule2", self.index.type_index[self.entity_type.name])
    
    def test_find_matching_rules(self):
        """Test finding rules that match a fact."""
        # Add rules to the index
        self.index.add_rule(self.rule1)
        self.index.add_rule(self.rule2)
        
        # Create a fact that matches rule1
        john = ConstantNode("John", "John", self.entity_type)
        fact = ApplicationNode(self.is_a, [john, self.person], self.entity_type)
        
        # Find matching rules
        matching_rules = self.index.find_matching_rules(fact)
        
        # Check if the matching rules are correct
        self.assertIn("rule1", matching_rules)
        
        # Create a fact that matches rule2
        my_car = ConstantNode("MyCar", "MyCar", self.entity_type)
        fact = ApplicationNode(self.is_a, [my_car, self.car], self.entity_type)
        
        # Find matching rules
        matching_rules = self.index.find_matching_rules(fact)
        
        # Check if the matching rules are correct
        self.assertIn("rule2", matching_rules)


class TestCompilationStrategies(unittest.TestCase):
    """Test cases for the compilation strategy classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create a rule AST
        self.x = VariableNode("?x", "x", self.entity_type)
        self.person = ConstantNode("Person", "Person", self.entity_type)
        self.is_a = ConstantNode("is_a", "is_a", self.entity_type)
        self.rule_ast = ApplicationNode(self.is_a, [self.x, self.person], self.entity_type)
        
        # Create compiled rules
        self.simple_rule = CompiledRule("simple_rule", self.rule_ast, RuleType.SIMPLE)
        self.conjunctive_rule = CompiledRule("conjunctive_rule", self.rule_ast, RuleType.CONJUNCTIVE)
        self.complex_rule = CompiledRule("complex_rule", self.rule_ast, RuleType.COMPLEX)
        
        # Create compilation strategies
        self.simple_strategy = SimpleRuleStrategy()
        self.conjunctive_strategy = ConjunctiveRuleStrategy()
        self.complex_strategy = ComplexRuleStrategy()
        
        # Create a mock knowledge store
        self.knowledge_store = MagicMock(spec=KnowledgeStoreInterface)
    
    def test_simple_rule_strategy(self):
        """Test the simple rule compilation strategy."""
        # Compile the rule
        self.simple_strategy.compile(self.simple_rule)
        
        # Check if the rule is compiled correctly
        self.assertEqual(self.simple_rule.compiled_form, self.rule_ast)
        
        # Execute the rule
        results = self.simple_strategy.execute(self.simple_rule, self.knowledge_store, ["TEST"])
        
        # Check if the results are empty (since this is a simplified implementation)
        self.assertEqual(results, [])
    
    def test_conjunctive_rule_strategy(self):
        """Test the conjunctive rule compilation strategy."""
        # Compile the rule
        self.conjunctive_strategy.compile(self.conjunctive_rule)
        
        # Check if the rule is compiled correctly
        self.assertEqual(self.conjunctive_rule.compiled_form, self.rule_ast)
        
        # Execute the rule
        results = self.conjunctive_strategy.execute(self.conjunctive_rule, self.knowledge_store, ["TEST"])
        
        # Check if the results are empty (since this is a simplified implementation)
        self.assertEqual(results, [])
    
    def test_complex_rule_strategy(self):
        """Test the complex rule compilation strategy."""
        # Compile the rule
        self.complex_strategy.compile(self.complex_rule)
        
        # Check if the rule is compiled correctly
        self.assertEqual(self.complex_rule.compiled_form, self.rule_ast)
        
        # Execute the rule
        results = self.complex_strategy.execute(self.complex_rule, self.knowledge_store, ["TEST"])
        
        # Check if the results are empty (since this is a simplified implementation)
        self.assertEqual(results, [])


class TestRuleCompiler(unittest.TestCase):
    """Test cases for the RuleCompiler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock knowledge store
        self.knowledge_store = MagicMock(spec=KnowledgeStoreInterface)
        
        # Create a rule compiler
        self.compiler = RuleCompiler(self.knowledge_store)
        
        # Create a type system manager
        self.type_system = TypeSystemManager()
        self.type_system.register_type("Entity", None)
        
        # Create some test data
        self.entity_type = self.type_system.get_type("Entity")
        
        # Create a rule AST
        self.x = VariableNode("?x", "x", self.entity_type)
        self.person = ConstantNode("Person", "Person", self.entity_type)
        self.is_a = ConstantNode("is_a", "is_a", self.entity_type)
        self.rule_ast = ApplicationNode(self.is_a, [self.x, self.person], self.entity_type)
    
    def test_compile_rule(self):
        """Test compiling a rule."""
        # Compile the rule
        rule_id = self.compiler.compile_rule(self.rule_ast)
        
        # Check if the rule is compiled correctly
        self.assertIn(rule_id, self.compiler.compiled_rules)
        self.assertEqual(self.compiler.compiled_rules[rule_id].original_rule_ast, self.rule_ast)
        self.assertEqual(self.compiler.compiled_rules[rule_id].rule_type, RuleType.SIMPLE)
        self.assertIsNotNone(self.compiler.compiled_rules[rule_id].compiled_form)
    
    def test_execute_rule(self):
        """Test executing a compiled rule."""
        # Compile the rule
        rule_id = self.compiler.compile_rule(self.rule_ast)
        
        # Execute the rule
        results = self.compiler.execute_rule(rule_id, ["TEST"])
        
        # Check if the results are empty (since this is a simplified implementation)
        self.assertEqual(results, [])
        
        # Check if the rule statistics are updated
        self.assertEqual(self.compiler.compiled_rules[rule_id].match_count, 1)
        self.assertGreater(self.compiler.compiled_rules[rule_id].last_matched, 0)
        self.assertGreater(self.compiler.compiled_rules[rule_id].total_execution_time, 0)
        self.assertGreater(self.compiler.compiled_rules[rule_id].average_execution_time, 0)
    
    def test_find_matching_rules(self):
        """Test finding rules that match a fact."""
        # Compile some rules
        rule1_id = self.compiler.compile_rule(self.rule_ast)
        
        # Create a fact that matches the rule
        john = ConstantNode("John", "John", self.entity_type)
        fact = ApplicationNode(self.is_a, [john, self.person], self.entity_type)
        
        # Find matching rules
        matching_rules = self.compiler.find_matching_rules(fact)
        
        # Check if the matching rules are correct
        self.assertIn(rule1_id, matching_rules)
    
    def test_remove_rule(self):
        """Test removing a compiled rule."""
        # Compile a rule
        rule_id = self.compiler.compile_rule(self.rule_ast)
        
        # Remove the rule
        self.compiler.remove_rule(rule_id)
        
        # Check if the rule is removed
        self.assertNotIn(rule_id, self.compiler.compiled_rules)
        
        # Check if trying to execute the removed rule raises an exception
        with self.assertRaises(ValueError):
            self.compiler.execute_rule(rule_id, ["TEST"])


if __name__ == "__main__":
    unittest.main()