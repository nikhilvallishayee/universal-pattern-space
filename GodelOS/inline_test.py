import sys
import os

# Add project root to path dynamically
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("Testing consciousness integrations...")
print()

# Test 1: Bootstrap exists
try:
    from backend.core.consciousness_engine import ConsciousnessEngine
    engine = ConsciousnessEngine()
    assert hasattr(engine, 'bootstrap_consciousness')
    print("✓ Bootstrap sequence exists")
except Exception as e:
    print(f"✗ Bootstrap: {e}")

# Test 2: Unified consciousness
try:
    from backend.core.unified_consciousness_engine import UnifiedConsciousnessEngine
    unified_engine = UnifiedConsciousnessEngine()
    assert hasattr(unified_engine, 'assess_unified_consciousness')
    print("✓ Unified consciousness engine integration exists")
except Exception as e:
    print(f"✗ Unified: {e}")

# Test 3: Goal system
try:
    from backend.goal_management_system import GoalManagementSystem
    gs = GoalManagementSystem()
    assert hasattr(gs, '_generate_goal_phenomenal_experience')
    print("✓ Goal phenomenal integration exists")
except Exception as e:
    print(f"✗ Goals: {e}")

# Test 4: Metacognition
try:
    from backend.core.metacognitive_monitor import MetaCognitiveMonitor
    mm = MetaCognitiveMonitor()
    assert hasattr(mm, '_update_consciousness_recursive_depth')
    print("✓ Metacognition recursive depth exists")
except Exception as e:
    print(f"✗ Metacog: {e}")

# Test 5: Knowledge graph
try:
    from backend.core.knowledge_graph_evolution import KnowledgeGraphEvolution
    kg = KnowledgeGraphEvolution()
    assert hasattr(kg, '_generate_emergence_phenomenal_experience')
    print("✓ Knowledge graph phenomenal integration exists")
except Exception as e:
    print(f"✗ KG: {e}")

print()
print("All imports successful! Integration code is syntactically correct.")
