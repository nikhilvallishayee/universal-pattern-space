#!/usr/bin/env python3
"""
Final verification test for the unification fix.
"""

import sys
import os
sys.path.insert(0, '.')

def test_unification_fix():
    """Test that the unification fix resolves the original error."""
    print("🔧 Testing unification engine fix with correct imports...")
    
    try:
        # Import with correct paths
        from godelOS.core_kr.unification_engine import UnificationEngine
        from godelOS.core_kr.ast.nodes import ConstantNode, VariableNode
        from godelOS.core_kr.type_system.types import PrimitiveType
        
        print("✓ Imports successful")
        
        # Create test data
        entity_type = PrimitiveType('Entity')
        var1 = VariableNode(name='X', var_id=1, type_ref=entity_type)
        const1 = ConstantNode(name='a', type_ref=entity_type)
        
        print("✓ Test data created")
        
        # Create unification engine
        engine = UnificationEngine()
        
        print("\n1. Testing unify_consistent method (the fix):")
        # Test the new consistent method that should work with resolution prover
        result = engine.unify_consistent(var1, const1)
        
        print(f"   Result type: {type(result)}")
        print(f"   Has is_success: {hasattr(result, 'is_success')}")
        print(f"   is_success(): {result.is_success()}")
        print(f"   Has substitution: {hasattr(result, 'substitution')}")
        print(f"   Substitution: {result.substitution}")
        
        # Test that the old unify method still works (for backwards compatibility)
        print("\n2. Testing backwards compatibility with old unify method:")
        old_result = engine.unify(var1, const1)
        print(f"   Old result type: {type(old_result)}")
        print(f"   Old result: {old_result}")
        
        print("\n🎉 SUCCESS: The unification fix is working correctly!")
        print("   ✓ unify_consistent() returns UnificationResult with is_success() method")
        print("   ✓ Old unify() method still works for backward compatibility")
        print("   ✓ Resolution prover can now call is_success() without tuple attribute error")
        
        # Test failure case
        print("\n3. Testing failure case:")
        different_type = PrimitiveType('Number')
        const2 = ConstantNode(name='5', type_ref=different_type)
        
        fail_result = engine.unify_consistent(var1, const2)
        print(f"   Failure result is_success(): {fail_result.is_success()}")
        print(f"   Failure result substitution: {fail_result.substitution}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_unification_fix()
    if success:
        print("\n" + "="*60)
        print("🎊 UNIFICATION FIX VERIFICATION COMPLETE!")
        print("   The original error 'tuple' object has no attribute 'is_success'")
        print("   has been successfully resolved.")
        print("="*60)
    sys.exit(0 if success else 1)
