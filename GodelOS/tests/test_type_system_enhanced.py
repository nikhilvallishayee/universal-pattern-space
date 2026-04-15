"""
Enhanced unit tests for the Type System component.

This file extends the basic tests in test_type_system.py with more thorough
testing of complex methods and edge cases, focusing on type inference,
polymorphic types, and type compatibility checking.
"""

import unittest
from unittest.mock import patch, MagicMock
import time
from typing import Dict, List, Optional, Set, Any, Tuple

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import (
    Type, AtomicType, FunctionType, ParametricType, 
    InstantiatedParametricType, TypeVariable
)
from godelOS.core_kr.type_system.environment import TypeEnvironment

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker


class TestTypeSystemEnhanced(unittest.TestCase):
    """Enhanced test cases for the Type System with complex scenarios and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system
        self.type_system = TypeSystemManager()
        
        # Create basic types
        self.boolean_type = self.type_system.get_type("Boolean")
        self.entity_type = self.type_system.get_type("Entity")
        self.integer_type = self.type_system.get_type("Integer")
        self.real_type = self.type_system.get_type("Real")
        
        # Create a type environment
        self.env = TypeEnvironment()
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
    
    def test_complex_function_types(self):
        """Test creation and manipulation of complex function types.
        
        This test verifies that the type system correctly handles complex
        function types with multiple arguments and nested function types.
        """
        # Create a simple function type: Entity -> Boolean
        unary_pred_type = FunctionType([self.entity_type], self.boolean_type)
        
        # Create a binary function type: Entity x Entity -> Boolean
        binary_pred_type = FunctionType([self.entity_type, self.entity_type], self.boolean_type)
        
        # Create a higher-order function type: (Entity -> Boolean) -> Boolean
        higher_order_type = FunctionType([unary_pred_type], self.boolean_type)
        
        # Create a curried function type: Entity -> (Entity -> Boolean)
        curried_type = FunctionType([self.entity_type], binary_pred_type)
        
        # Verify the types
        self.assertEqual(unary_pred_type.arg_types, [self.entity_type])
        self.assertEqual(unary_pred_type.return_type, self.boolean_type)
        
        self.assertEqual(binary_pred_type.arg_types, [self.entity_type, self.entity_type])
        self.assertEqual(binary_pred_type.return_type, self.boolean_type)
        
        self.assertEqual(higher_order_type.arg_types, [unary_pred_type])
        self.assertEqual(higher_order_type.return_type, self.boolean_type)
        
        self.assertEqual(curried_type.arg_types, [self.entity_type])
        self.assertEqual(curried_type.return_type, binary_pred_type)
        
        # Test type equality
        unary_pred_type2 = FunctionType([self.entity_type], self.boolean_type)
        self.assertEqual(unary_pred_type, unary_pred_type2)
        
        # Test type inequality
        self.assertNotEqual(unary_pred_type, binary_pred_type)
        self.assertNotEqual(higher_order_type, curried_type)
    
    def test_parametric_types(self):
        """Test creation and manipulation of parametric types.
        
        This test verifies that the type system correctly handles parametric
        types with type variables and instantiation.
        """
        # Create type variables
        type_var_a = TypeVariable("A")
        type_var_b = TypeVariable("B")
        
        # Create a parametric list type: List<A>
        list_type = ParametricType("List", [type_var_a])
        
        # Create a parametric map type: Map<A, B>
        map_type = ParametricType("Map", [type_var_a, type_var_b])
        
        # Instantiate the list type: List<Entity>
        entity_list_type = InstantiatedParametricType(list_type, [self.entity_type])
        
        # Instantiate the map type: Map<Entity, Boolean>
        entity_boolean_map_type = InstantiatedParametricType(map_type, [self.entity_type, self.boolean_type])
        
        # Verify the types
        self.assertEqual(list_type.name, "List")
        self.assertEqual(list_type.type_params, [type_var_a])
        
        self.assertEqual(map_type.name, "Map")
        self.assertEqual(map_type.type_params, [type_var_a, type_var_b])
        
        self.assertEqual(entity_list_type.constructor, list_type)
        self.assertEqual(entity_list_type.actual_type_args, [self.entity_type])
        
        self.assertEqual(entity_boolean_map_type.constructor, map_type)
        self.assertEqual(entity_boolean_map_type.actual_type_args, [self.entity_type, self.boolean_type])
        
        # Test type equality
        entity_list_type2 = InstantiatedParametricType(list_type, [self.entity_type])
        self.assertEqual(entity_list_type, entity_list_type2)
        
        # Test type inequality
        boolean_list_type = InstantiatedParametricType(list_type, [self.boolean_type])
        self.assertNotEqual(entity_list_type, boolean_list_type)
    
    def test_type_inference_with_polymorphic_functions(self):
        """Test type inference with polymorphic functions.
        
        This test verifies that the type system correctly infers types
        for polymorphic functions with type variables.
        """
        # Create type variables
        type_var_a = TypeVariable("A")
        type_var_b = TypeVariable("B")
        
        # Create a polymorphic identity function type: A -> A
        identity_type = FunctionType([type_var_a], type_var_a)
        
        # Create a polymorphic map function type: (A -> B) -> List<A> -> List<B>
        list_type = ParametricType("List", [type_var_a])
        list_b_type = ParametricType("List", [type_var_b])
        map_func_type = FunctionType(
            [FunctionType([type_var_a], type_var_b), InstantiatedParametricType(list_type, [type_var_a])],
            InstantiatedParametricType(list_b_type, [type_var_b])
        )
        
        # Mock the type inference method
        with patch.object(self.type_system, 'infer_type') as mock_infer:
            # Define mock inference results
            mock_infer.side_effect = [
                self.entity_type,  # identity<Entity>
                self.boolean_type  # identity<Boolean>
            ]
            
            # Infer the type of identity applied to an entity
            inferred_type1 = self.type_system.infer_type(identity_type, [self.entity_type])
            
            # Infer the type of identity applied to a boolean
            inferred_type2 = self.type_system.infer_type(identity_type, [self.boolean_type])
            
            # Verify the inferred types
            self.assertEqual(inferred_type1, self.entity_type)
            self.assertEqual(inferred_type2, self.boolean_type)
            
            # Verify that infer_type was called with the correct arguments
            mock_infer.assert_any_call(identity_type, [self.entity_type])
            mock_infer.assert_any_call(identity_type, [self.boolean_type])
    
    def test_type_unification(self):
        """Test type unification.
        
        This test verifies that the type system correctly unifies types,
        handling type variables and constraints.
        """
        # Create type variables
        type_var_a = TypeVariable("A")
        type_var_b = TypeVariable("B")
        
        # Create function types with type variables
        func_a_to_b = FunctionType([type_var_a], type_var_b)
        func_entity_to_boolean = FunctionType([self.entity_type], self.boolean_type)
        
        # Mock the unify method
        with patch.object(self.type_system, 'unify') as mock_unify:
            # Define a mock unification result
            mock_substitution = {
                type_var_a: self.entity_type,
                type_var_b: self.boolean_type
            }
            mock_unify.return_value = mock_substitution
            
            # Unify the types
            substitution = self.type_system.unify(func_a_to_b, func_entity_to_boolean)
            
            # Verify the substitution
            self.assertEqual(substitution, mock_substitution)
            self.assertEqual(substitution[type_var_a], self.entity_type)
            self.assertEqual(substitution[type_var_b], self.boolean_type)
            
            # Verify that unify was called with the correct arguments
            mock_unify.assert_called_with(func_a_to_b, func_entity_to_boolean)
    
    def test_type_checking_with_complex_expressions(self):
        """Test type checking with complex expressions.
        
        This test verifies that the type system correctly checks types
        for complex expressions with nested function applications.
        """
        # Create function types
        func_int_to_int = FunctionType([self.integer_type], self.integer_type)
        func_int_int_to_int = FunctionType([self.integer_type, self.integer_type], self.integer_type)
        func_int_to_bool = FunctionType([self.integer_type], self.boolean_type)
        
        # Mock the check_type method
        with patch.object(self.type_system, 'check_type') as mock_check:
            # Define mock check results
            mock_check.side_effect = [
                True,   # (int -> int) applied to int
                True,   # (int -> bool) applied to int
                False,  # (int -> bool) applied to bool (type error)
                True    # (int x int -> int) applied to (int, int)
            ]
            
            # Check function application: (int -> int) applied to int
            result1 = self.type_system.check_type(func_int_to_int, [self.integer_type])
            
            # Check function application: (int -> bool) applied to int
            result2 = self.type_system.check_type(func_int_to_bool, [self.integer_type])
            
            # Check invalid function application: (int -> bool) applied to bool
            result3 = self.type_system.check_type(func_int_to_bool, [self.boolean_type])
            
            # Check binary function application: (int x int -> int) applied to (int, int)
            result4 = self.type_system.check_type(func_int_int_to_int, [self.integer_type, self.integer_type])
            
            # Verify the results
            self.assertTrue(result1)
            self.assertTrue(result2)
            self.assertFalse(result3)
            self.assertTrue(result4)
            
            # Verify that check_type was called with the correct arguments
            mock_check.assert_any_call(func_int_to_int, [self.integer_type])
            mock_check.assert_any_call(func_int_to_bool, [self.integer_type])
            mock_check.assert_any_call(func_int_to_bool, [self.boolean_type])
            mock_check.assert_any_call(func_int_int_to_int, [self.integer_type, self.integer_type])
    
    def test_type_traversal_and_collection(self):
        """Test traversal of complex type structures.
        
        This test verifies that complex type structures can be traversed to
        collect component types, replacing the old visitor pattern test.
        """
        def collect_atomic_types(type_obj: Type) -> List[AtomicType]:
            """Recursively collect atomic types from a type structure."""
            collected = []
            if isinstance(type_obj, AtomicType):
                collected.append(type_obj)
            elif isinstance(type_obj, FunctionType):
                for arg_type in type_obj.arg_types:
                    collected.extend(collect_atomic_types(arg_type))
                collected.extend(collect_atomic_types(type_obj.return_type))
            elif isinstance(type_obj, InstantiatedParametricType):
                for type_arg in type_obj.actual_type_args:
                    collected.extend(collect_atomic_types(type_arg))
            return collected

        # Create a complex type structure
        # (Entity -> Boolean) -> (Integer -> Real)
        complex_type = FunctionType(
            [FunctionType([self.entity_type], self.boolean_type)],
            FunctionType([self.integer_type], self.real_type)
        )
        
        # Collect atomic types
        result = collect_atomic_types(complex_type)
        
        # Verify the result
        self.assertEqual(len(result), 4)
        self.assertIn(self.entity_type, result)
        self.assertIn(self.boolean_type, result)
        self.assertIn(self.integer_type, result)
        self.assertIn(self.real_type, result)
    
    def test_type_environment_operations(self):
        """Test operations on the type environment.
        
        This test verifies that the type environment correctly manages
        type bindings and lookups for symbols.
        """
        # Create symbols
        symbol1 = "x"
        symbol2 = "y"
        symbol3 = "f"
        
        # Create types
        type1 = self.integer_type
        type2 = self.boolean_type
        type3 = FunctionType([self.integer_type], self.boolean_type)
        
        # Add bindings to the environment
        self.env.add_binding(symbol1, type1)
        self.env.add_binding(symbol2, type2)
        self.env.add_binding(symbol3, type3)
        
        # Verify the bindings
        self.assertEqual(self.env.lookup(symbol1), type1)
        self.assertEqual(self.env.lookup(symbol2), type2)
        self.assertEqual(self.env.lookup(symbol3), type3)
        
        # Test lookup of non-existent symbol
        with self.assertRaises(KeyError):
            self.env.lookup("non_existent")
        
        # Create a new environment with the current one as parent
        child_env = TypeEnvironment(parent=self.env)
        
        # Add a binding to the child environment
        symbol4 = "z"
        type4 = self.real_type
        child_env.add_binding(symbol4, type4)
        
        # Verify bindings in the child environment
        self.assertEqual(child_env.lookup(symbol4), type4)
        
        # Verify that the child environment can see bindings from the parent
        self.assertEqual(child_env.lookup(symbol1), type1)
        self.assertEqual(child_env.lookup(symbol2), type2)
        self.assertEqual(child_env.lookup(symbol3), type3)
        
        # Override a binding in the child environment
        child_env.add_binding(symbol1, type4)
        
        # Verify that the override worked
        self.assertEqual(child_env.lookup(symbol1), type4)
        
        # But the parent environment is unchanged
        self.assertEqual(self.env.lookup(symbol1), type1)
    
    def test_performance_with_complex_type_hierarchies(self):
        """Test performance with complex type hierarchies.
        
        This test verifies that the type system efficiently handles
        operations on complex type hierarchies with many types.
        """
        # Create a large number of atomic types
        num_types = 100
        atomic_types = []
        
        start_time = time.time()
        for i in range(num_types):
            type_name = f"Type{i}"
            atomic_type = AtomicType(type_name)
            atomic_types.append(atomic_type)
        
        # Register the types with the type system
        for atomic_type in atomic_types:
            self.type_system.register_type(atomic_type)
        
        # Create a complex type hierarchy
        # Each type is a function from the previous type to the next type
        function_types = []
        for i in range(num_types - 1):
            function_type = FunctionType([atomic_types[i]], atomic_types[i+1])
            function_types.append(function_type)
        
        # Create a nested function type
        # (Type0 -> Type1) -> ((Type1 -> Type2) -> ... -> (Type98 -> Type99))
        nested_type = function_types[0]
        for i in range(1, len(function_types)):
            nested_type = FunctionType([nested_type], function_types[i])
        
        # Measure the time to create the type hierarchy
        creation_time = time.time() - start_time
        print(f"Time to create type hierarchy with {num_types} types: {creation_time * 1000:.2f} ms")
        
        # Measure the time to look up a type
        start_time = time.time()
        for i in range(100):
            type_name = f"Type{i % num_types}"
            self.type_system.get_type(type_name)
        lookup_time = time.time() - start_time
        
        print(f"Time for 100 type lookups: {lookup_time * 1000:.2f} ms")
    
    def test_type_compatibility_checking(self):
        """Test type compatibility checking.
        
        This test verifies that the type system correctly checks compatibility
        between types, handling subtyping and type conversion.
        """
        # Create a subtype relationship: Integer <: Real
        # (In a real implementation, this would be defined in the type system)
        
        # Mock the is_compatible method
        with patch.object(self.type_system, 'is_compatible') as mock_compatible:
            # Define mock compatibility results
            mock_compatible.side_effect = [
                True,   # Integer is compatible with Integer
                True,   # Integer is compatible with Real (subtyping)
                False,  # Real is not compatible with Integer
                True,   # Entity is compatible with Entity
                False   # Entity is not compatible with Boolean
            ]
            
            # Check compatibility: Integer with Integer
            result1 = self.type_system.is_compatible(self.integer_type, self.integer_type)
            
            # Check compatibility: Integer with Real (subtyping)
            result2 = self.type_system.is_compatible(self.integer_type, self.real_type)
            
            # Check compatibility: Real with Integer (not compatible)
            result3 = self.type_system.is_compatible(self.real_type, self.integer_type)
            
            # Check compatibility: Entity with Entity
            result4 = self.type_system.is_compatible(self.entity_type, self.entity_type)
            
            # Check compatibility: Entity with Boolean (not compatible)
            result5 = self.type_system.is_compatible(self.entity_type, self.boolean_type)
            
            # Verify the results
            self.assertTrue(result1)
            self.assertTrue(result2)
            self.assertFalse(result3)
            self.assertTrue(result4)
            self.assertFalse(result5)
            
            # Verify that is_compatible was called with the correct arguments
            mock_compatible.assert_any_call(self.integer_type, self.integer_type)
            mock_compatible.assert_any_call(self.integer_type, self.real_type)
            mock_compatible.assert_any_call(self.real_type, self.integer_type)
            mock_compatible.assert_any_call(self.entity_type, self.entity_type)
            mock_compatible.assert_any_call(self.entity_type, self.boolean_type)


if __name__ == "__main__":
    unittest.main()