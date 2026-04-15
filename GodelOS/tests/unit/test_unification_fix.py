#!/usr/bin/env python3
"""
Test script to verify the unification engine fix.
"""

from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.unification_engine.result import UnificationResult
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import ConstantNode, VariableNode
from godelOS.core_kr.type_system.types import AtomicType

def test_unification_fix():
    """Test that the unification fix works correctly."""
    print("Testing unification engine fix...")
    
    # Create a simple test
    type_system = TypeSystemManager()
    engine = UnificationEngine(type_system)
    
    # Create test nodes
    entity_type = type_system.get_type('Entity')
    var_x = VariableNode('?x', 1, entity_type)
    const_a = ConstantNode('a', entity_type)
    
    # Test the old unify method
    print('\nTesting old unify method:')
    old_result = engine.unify(var_x, const_a)
    print(f'Old result type: {type(old_result)}')
    print(f'Old result: {old_result}')
    
    # Test the new unify_consistent method
    print('\nTesting new unify_consistent method:')
    new_result = engine.unify_consistent(var_x, const_a)
    print(f'New result type: {type(new_result)}')
    print(f'New result is_success: {new_result.is_success()}')
    print(f'New result substitution: {new_result.substitution}')
    
    # Test with failure case
    print('\nTesting failure case:')
    const_b = ConstantNode('b', entity_type)
    fail_result = engine.unify_consistent(const_a, const_b)
    print(f'Fail result is_success: {fail_result.is_success()}')
    print(f'Fail result substitution: {fail_result.substitution}')
    
    print("\nUnification fix test completed successfully!")

if __name__ == "__main__":
    test_unification_fix()
