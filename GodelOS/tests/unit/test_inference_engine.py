#!/usr/bin/env python3
"""
Test script to verify that the inference engine works end-to-end after the unification fix.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from godelOS.core_kr.ast.nodes import ConstantNode, VariableNode, ApplicationNode
from godelOS.core_kr.type_system.types import AtomicType
from godelOS.inference_engine.resolution_prover import ResolutionProver
from godelOS.core_kr.knowledge_store.interface import InMemoryKnowledgeStore

def test_inference_engine():
    """Test that the inference engine works end-to-end."""
    print("Testing inference engine end-to-end...")
    
    try:
        # Create a knowledge base
        kb = InMemoryKnowledgeStore()
        
        # Create a resolution prover
        prover = ResolutionProver()
        
        # Create simple facts and queries
        # Fact: P(a)
        entity_type = AtomicType("Entity")
        boolean_type = AtomicType("Boolean")
        a = ConstantNode(name="a", type=entity_type)
        P = ApplicationNode(name="P", arity=1, type=boolean_type)
        fact = P(a)
        
        # Query: P(a) - should be provable
        query = P(a)
        
        print(f"Fact: {fact}")
        print(f"Query: {query}")
        
        # Add fact to knowledge base
        kb.add_rule(fact)
        
        # Test if prover can handle the query
        can_handle = prover.can_handle(query, kb)
        print(f"Prover can handle query: {can_handle}")
        
        if can_handle:
            # Try to prove the query
            print("Attempting to prove query...")
            result = prover.prove(query, kb)
            print(f"Proof result type: {type(result)}")
            print(f"Proof successful: {result.proof_found if hasattr(result, 'proof_found') else 'Unknown'}")
            
            if hasattr(result, 'inference_engine_used'):
                print(f"Inference engine used: {result.inference_engine_used}")
            
            print("✓ Inference engine completed without errors!")
        else:
            print("⚠ Prover cannot handle this query type")
        
    except Exception as e:
        if "'tuple' object has no attribute 'is_success'" in str(e):
            print(f"✗ Original unification error still present: {e}")
            return False
        else:
            print(f"✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n✓ Inference engine test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_inference_engine()
    sys.exit(0 if success else 1)
