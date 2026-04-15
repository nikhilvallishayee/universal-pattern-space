"""
Tests for the Type System module.
"""

import unittest

from godelOS.core_kr.type_system import (
    Type, AtomicType, FunctionType, TypeVariable, 
    ParametricTypeConstructor, InstantiatedParametricType,
    TypeSystemManager, TypeEnvironment
)
from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode
)


class TestTypeClasses(unittest.TestCase):
    """Test cases for the type classes."""
    
    def test_atomic_type(self):
        """Test AtomicType."""
        entity = AtomicType("Entity")
        self.assertEqual(entity.name, "Entity")
        self.assertEqual(str(entity), "Entity")
        
        # Test equality
        entity2 = AtomicType("Entity")
        self.assertEqual(entity, entity2)
        
        agent = AtomicType("Agent")
        self.assertNotEqual(entity, agent)
    
    def test_function_type(self):
        """Test FunctionType."""
        entity = AtomicType("Entity")
        boolean = AtomicType("Boolean")
        
        # Create a function type: Entity -> Boolean
        func_type = FunctionType([entity], boolean)
        self.assertEqual(func_type.arg_types, [entity])
        self.assertEqual(func_type.return_type, boolean)
        self.assertEqual(str(func_type), "(Entity) -> Boolean")
        
        # Test equality
        func_type2 = FunctionType([entity], boolean)
        self.assertEqual(func_type, func_type2)
        
        # Test inequality
        func_type3 = FunctionType([boolean], entity)
        self.assertNotEqual(func_type, func_type3)
    
    def test_type_variable(self):
        """Test TypeVariable."""
        t_var = TypeVariable("T")
        self.assertEqual(t_var.name, "T")
        self.assertEqual(str(t_var), "?T")
        
        # Test equality
        t_var2 = TypeVariable("T")
        self.assertEqual(t_var, t_var2)
        
        u_var = TypeVariable("U")
        self.assertNotEqual(t_var, u_var)
    
    def test_parametric_type_constructor(self):
        """Test ParametricTypeConstructor."""
        t_var = TypeVariable("T")
        list_constructor = ParametricTypeConstructor("List", [t_var])
        self.assertEqual(list_constructor.name, "List")
        self.assertEqual(list_constructor.type_params, [t_var])
        self.assertEqual(str(list_constructor), "List[?T]")
        
        # Test equality
        list_constructor2 = ParametricTypeConstructor("List", [t_var])
        self.assertEqual(list_constructor, list_constructor2)
        
        map_constructor = ParametricTypeConstructor("Map", [t_var, TypeVariable("U")])
        self.assertNotEqual(list_constructor, map_constructor)
    
    def test_instantiated_parametric_type(self):
        """Test InstantiatedParametricType."""
        t_var = TypeVariable("T")
        list_constructor = ParametricTypeConstructor("List", [t_var])
        entity = AtomicType("Entity")
        
        # Create a List[Entity] type
        list_entity = InstantiatedParametricType(list_constructor, [entity])
        self.assertEqual(list_entity.constructor, list_constructor)
        self.assertEqual(list_entity.actual_type_args, [entity])
        self.assertEqual(str(list_entity), "List[Entity]")
        
        # Test equality
        list_entity2 = InstantiatedParametricType(list_constructor, [entity])
        self.assertEqual(list_entity, list_entity2)
        
        boolean = AtomicType("Boolean")
        list_boolean = InstantiatedParametricType(list_constructor, [boolean])
        self.assertNotEqual(list_entity, list_boolean)
    
    def test_type_substitution(self):
        """Test type variable substitution."""
        t_var = TypeVariable("T")
        u_var = TypeVariable("U")
        entity = AtomicType("Entity")
        boolean = AtomicType("Boolean")
        
        # Test substitution in TypeVariable
        bindings = {t_var: entity}
        self.assertEqual(t_var.substitute_type_vars(bindings), entity)
        self.assertEqual(u_var.substitute_type_vars(bindings), u_var)  # Not in bindings
        
        # Test substitution in FunctionType
        func_type = FunctionType([t_var, u_var], boolean)
        substituted = func_type.substitute_type_vars(bindings)
        self.assertEqual(substituted.arg_types, [entity, u_var])
        self.assertEqual(substituted.return_type, boolean)
        
        # Test substitution in InstantiatedParametricType
        list_constructor = ParametricTypeConstructor("List", [t_var])
        list_t = InstantiatedParametricType(list_constructor, [t_var])
        substituted = list_t.substitute_type_vars(bindings)
        self.assertEqual(substituted.actual_type_args, [entity])


class TestTypeSystemManager(unittest.TestCase):
    """Test cases for the TypeSystemManager."""
    
    def setUp(self):
        """Set up the test case."""
        self.type_system = TypeSystemManager()
    
    def test_base_types(self):
        """Test that base types are initialized correctly."""
        # Check that basic types exist
        self.assertIsNotNone(self.type_system.get_type("Entity"))
        self.assertIsNotNone(self.type_system.get_type("Agent"))
        self.assertIsNotNone(self.type_system.get_type("Event"))
        self.assertIsNotNone(self.type_system.get_type("Action"))
        self.assertIsNotNone(self.type_system.get_type("Proposition"))
        self.assertIsNotNone(self.type_system.get_type("Boolean"))
        self.assertIsNotNone(self.type_system.get_type("Integer"))
        self.assertIsNotNone(self.type_system.get_type("String"))
    
    def test_define_atomic_type(self):
        """Test defining a new atomic type."""
        # Define a new type
        vehicle_type = self.type_system.define_atomic_type("Vehicle", ["Entity"])
        self.assertEqual(vehicle_type.name, "Vehicle")
        
        # Check that it's in the type registry
        self.assertEqual(self.type_system.get_type("Vehicle"), vehicle_type)
        
        # Check that it's a subtype of Entity
        entity_type = self.type_system.get_type("Entity")
        self.assertTrue(self.type_system.is_subtype(vehicle_type, entity_type))
        
        # Try to define a type with a non-existent supertype
        with self.assertRaises(ValueError):
            self.type_system.define_atomic_type("Car", ["NonExistentType"])
        
        # Try to redefine an existing type
        with self.assertRaises(ValueError):
            self.type_system.define_atomic_type("Vehicle")
    
    def test_define_function_signature(self):
        """Test defining a function signature."""
        # Define a function signature: Human(Entity) -> Boolean
        self.type_system.define_function_signature("Human", ["Entity"], "Boolean")
        
        # Try to redefine the same signature
        with self.assertRaises(ValueError):
            self.type_system.define_function_signature("Human", ["Entity"], "Boolean")
        
        # Try to define a signature with non-existent types
        with self.assertRaises(ValueError):
            self.type_system.define_function_signature("Test", ["NonExistentType"], "Boolean")
        
        with self.assertRaises(ValueError):
            self.type_system.define_function_signature("Test", ["Entity"], "NonExistentType")
    
    def test_is_subtype(self):
        """Test subtype checking."""
        entity_type = self.type_system.get_type("Entity")
        agent_type = self.type_system.get_type("Agent")
        event_type = self.type_system.get_type("Event")
        action_type = self.type_system.get_type("Action")
        
        # Check direct subtyping
        self.assertTrue(self.type_system.is_subtype(agent_type, entity_type))
        self.assertTrue(self.type_system.is_subtype(action_type, event_type))
        
        # Check non-subtyping
        self.assertFalse(self.type_system.is_subtype(entity_type, agent_type))
        self.assertFalse(self.type_system.is_subtype(agent_type, event_type))
        
        # Check transitive subtyping
        vehicle_type = self.type_system.define_atomic_type("Vehicle", ["Entity"])
        car_type = self.type_system.define_atomic_type("Car", ["Vehicle"])
        self.assertTrue(self.type_system.is_subtype(car_type, entity_type))
        
        # Check reflexivity
        self.assertTrue(self.type_system.is_subtype(entity_type, entity_type))
    
    def test_unify_types(self):
        """Test type unification."""
        t_var = TypeVariable("T")
        u_var = TypeVariable("U")
        entity_type = self.type_system.get_type("Entity")
        agent_type = self.type_system.get_type("Agent")
        boolean_type = self.type_system.get_type("Boolean")
        
        # Unify identical types
        self.assertEqual(self.type_system.unify_types(entity_type, entity_type), {})
        
        # Unify a type variable with a concrete type
        self.assertEqual(self.type_system.unify_types(t_var, entity_type), {t_var: entity_type})
        
        # Unify function types
        func1 = FunctionType([t_var], boolean_type)
        func2 = FunctionType([entity_type], boolean_type)
        self.assertEqual(self.type_system.unify_types(func1, func2), {t_var: entity_type})
        
        # Unify function types with multiple arguments
        func3 = FunctionType([t_var, u_var], boolean_type)
        func4 = FunctionType([entity_type, agent_type], boolean_type)
        unification = self.type_system.unify_types(func3, func4)
        self.assertEqual(unification[t_var], entity_type)
        self.assertEqual(unification[u_var], agent_type)
        
        # Unify parametric types
        list_constructor = ParametricTypeConstructor("List", [t_var])
        list_t = InstantiatedParametricType(list_constructor, [t_var])
        list_entity = InstantiatedParametricType(list_constructor, [entity_type])
        self.assertEqual(self.type_system.unify_types(list_t, list_entity), {t_var: entity_type})
        
        # Failed unification: incompatible types
        func5 = FunctionType([entity_type], boolean_type)
        func6 = FunctionType([entity_type, agent_type], boolean_type)
        self.assertIsNone(self.type_system.unify_types(func5, func6))
    
    def test_type_checking_and_inference(self):
        """Test type checking and inference with AST nodes."""
        # Set up types and environment
        entity_type = self.type_system.get_type("Entity")
        boolean_type = self.type_system.get_type("Boolean")
        environment = TypeEnvironment()
        
        # Define a predicate: Human(Entity) -> Boolean
        self.type_system.define_function_signature("Human", ["Entity"], "Boolean")
        
        # Create AST nodes
        socrates = ConstantNode("Socrates", entity_type)
        human_pred = ConstantNode("Human", FunctionType([entity_type], boolean_type))
        human_socrates = ApplicationNode(human_pred, [socrates], boolean_type)
        
        # Test type checking
        errors = self.type_system.check_expression_type(human_socrates, boolean_type, environment)
        self.assertEqual(len(errors), 0)
        
        # Test type inference
        inferred_type, errors = self.type_system.infer_expression_type(human_socrates, environment)
        self.assertEqual(inferred_type, boolean_type)
        self.assertEqual(len(errors), 0)
        
        # Test type checking with incorrect expected type
        integer_type = self.type_system.get_type("Integer")
        errors = self.type_system.check_expression_type(human_socrates, integer_type, environment)
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main()