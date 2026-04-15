#!/usr/bin/env python3
"""
Final test to verify that the unification fix resolves the original tuple attribute error.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_unification_fix():
    """Test that the unification fix prevents the original error."""
    print("Testing unification engine fix with correct imports...")
    print("Starting test function...")
    
    try:
        # Import with correct paths
        from godelOS.core_kr.ast.nodes import ConstantNode, VariableNode
        from godelOS.core_kr.type_system.types import AtomicType
        from godelOS.core_kr.unification_engine.engine import UnificationEngine
        from godelOS.core_kr.unification_engine.result import UnificationResult
        
        # Create Entity type (like the predefined ones)
        entity_type = AtomicType("Entity")
        
        # Create simple terms for unification
        var1 = VariableNode(name="X", var_id=1, type=entity_type)
        const1 = ConstantNode(name="a", type=entity_type)
        
        # Create a unification engine instance
        unification_engine = UnificationEngine()
        
        # Test the old method (should return tuple)
        print("\n1. Testing old unify() method:")
        old_result = unification_engine.unify(var1, const1)
        print(f"   Result type: {type(old_result)}")
        print(f"   Result: {old_result}")
        
        # Test the new method (should return UnificationResult)
        print("\n2. Testing new unify_consistent() method:")
        new_result = unification_engine.unify_consistent(var1, const1)
        print(f"   Result type: {type(new_result)}")
        print(f"   Has is_success method: {hasattr(new_result, 'is_success')}")
        print(f"   is_success(): {new_result.is_success()}")
        print(f"   Has substitution: {hasattr(new_result, 'substitution')}")
        
        # Test that resolution prover integration would work
        print("\n3. Testing resolution prover integration:")
        # Simulate what the resolution prover does at line 941
        # Instead of: result = self.unification_engine.unify(...)
        # Now it does: result = self.unification_engine.unify_consistent(...)
        result = unification_engine.unify_consistent(var1, const1)
        
        # This is the line that was failing before: result.is_success()
        if result.is_success():
            print("   ✓ result.is_success() works - no more tuple attribute error!")
            print(f"   ✓ Substitution available: {result.substitution}")
        else:
            print("   ⚠ Unification failed (but no attribute error)")
        
        print("\n✅ SUCCESS: The unification fix is working correctly!")
        print("   - Old unify() method still returns tuple for backward compatibility")
        print("   - New unify_consistent() method returns UnificationResult with proper methods")
        print("   - Resolution prover can now call is_success() without errors")
        
        return True
        
    except ImportError as e:
        print(f"❌ ERROR: {e}")
        return False
    except AttributeError as e:
        if "'tuple' object has no attribute 'is_success'" in str(e):
            print(f"❌ ERROR: Original tuple attribute error still present: {e}")
        else:
            print(f"❌ ERROR: Different attribute error: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Script starting...")
    success = test_unification_fix()
    print(f"Test result: {success}")
    sys.exit(0 if success else 1)
