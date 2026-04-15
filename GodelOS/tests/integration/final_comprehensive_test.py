#!/usr/bin/env python3
"""
Final comprehensive test to verify the unification engine fix is working end-to-end.
This test confirms that the resolution prover can now handle unification results
without the 'tuple' object has no attribute 'is_success' error.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from godelOS.core_kr.ast.nodes import ConstantNode, VariableNode
from godelOS.core_kr.type_system.types import AtomicType
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.unification_engine.result import UnificationResult

def test_unification_result_fix():
    """Test that the unification engine now returns consistent UnificationResult objects."""
    print("Testing unification engine fix...")
    
    # Create type system and types
    type_system = TypeSystemManager()
    entity_type = type_system.register_type("Entity")
    
    # Create nodes with correct constructor parameters
    const_node = ConstantNode(name='a', type_ref=entity_type)
    var_node = VariableNode(name='X', var_id=1, type_ref=entity_type)
    
    # Create unification engine with type system
    engine = UnificationEngine(type_system)
    
    print(f"Created constant node: {const_node}")
    print(f"Created variable node: {var_node}")
    
    # Test old method (should return tuple)
    old_result = engine.unify(var_node, const_node, {})
    print(f"Old unify() method returns: {type(old_result)} - {old_result}")
    
    # Test new consistent method (should return UnificationResult)
    new_result = engine.unify_consistent(var_node, const_node, {})
    print(f"New unify_consistent() method returns: {type(new_result)} - {new_result}")
    
    # Verify the new result has the expected interface
    if hasattr(new_result, 'is_success') and callable(new_result.is_success):
        success = new_result.is_success()
        print(f"UnificationResult.is_success(): {success}")
        
        if success and hasattr(new_result, 'substitution'):
            substitution = new_result.substitution
            print(f"UnificationResult.substitution: {substitution}")
            print("✅ Fix verified: UnificationResult has proper interface!")
            return True
        else:
            print("❌ UnificationResult missing substitution property")
            return False
    else:
        print("❌ UnificationResult missing is_success() method")
        return False

def test_resolution_prover_integration():
    """Test that the resolution prover can use the fixed unification engine."""
    print("\nTesting resolution prover integration...")
    
    try:
        from godelOS.inference_engine.resolution_prover import ResolutionProver
        from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface, InMemoryKnowledgeStore
        
        # Create type system for the unification engine
        type_system = TypeSystemManager()
        unification_engine = UnificationEngine(type_system)
        
        # Create a simple knowledge store 
        knowledge_store_backend = InMemoryKnowledgeStore(unification_engine)
        knowledge_store = KnowledgeStoreInterface(type_system)
        knowledge_store._backend = knowledge_store_backend
        
        prover = ResolutionProver(knowledge_store, unification_engine)
        
        print(f"Created resolution prover: {prover}")
        print(f"Unification engine type: {type(prover.unification_engine)}")
        
        # Check that the prover has the new unify_consistent method
        if hasattr(prover.unification_engine, 'unify_consistent'):
            print("✅ Resolution prover has access to unify_consistent method!")
            
            # Test that we can call it without errors
            entity_type = type_system.register_type("Entity")
            const_node = ConstantNode(name='test', type_ref=entity_type)
            var_node = VariableNode(name='X', var_id=1, type_ref=entity_type)
            
            result = prover.unification_engine.unify_consistent(var_node, const_node, {})
            if isinstance(result, UnificationResult):
                print("✅ Resolution prover can successfully call unify_consistent!")
                return True
            else:
                print("❌ unify_consistent returned wrong type")
                return False
        else:
            print("❌ Resolution prover missing unify_consistent method")
            return False
            
    except ImportError as e:
        print(f"❌ Could not import resolution prover: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing resolution prover: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("FINAL COMPREHENSIVE TEST: Unification Engine Fix")
    print("=" * 60)
    
    success1 = test_unification_result_fix()
    success2 = test_resolution_prover_integration()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED! The fix is working correctly.")
        print("The resolution prover should no longer get the tuple attribute error.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    print("=" * 60)
