# demo.py
# This file provides a structured and practical demonstration of key GödelOS components.

import sys
import os

# Add the parent directory to the sys.path to allow importing modules from godelOS
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("--- Running GödelOS Practical Demo ---")
print("This script steps through various examples, highlighting different aspects of the GödelOS system.")
print("Each section explains the purpose and expected behavior of the example.")

# --- Example 1: Simple Example - Core KR Interaction ---
print("\n" + "="*60)
print("Example 1: Simple Example - Core KR Interaction")
print("="*60)
print("\nPurpose:")
print("This example demonstrates basic interaction with the Core Knowledge Representation (KR) system.")
print("It shows how to define types and predicates, create AST nodes for facts and rules,")
print("add them to the knowledge store, and perform simple queries and unification.")
print("Expected Output:")
print("You should see output indicating the initialization of KR components,")
print("the creation and addition of facts/rules, and the results of queries and unification.")
print("-" * 60)
try:
    from examples import simple_example
    print("Executing simple_example.py...")
    simple_example.main()
except ImportError:
    print("Could not import simple_example.py. Make sure it exists in the examples directory.")
except Exception as e:
    print(f"An error occurred while trying to demonstrate simple_example.py: {e}")
print("-" * 60)


# --- Example 2: Core Knowledge Representation - Comprehensive Demo ---
print("\n" + "="*60)
print("Example 2: Core Knowledge Representation - Comprehensive Demo")
print("="*60)
print("\nPurpose:")
print("This example provides a comprehensive demonstration of the Core Knowledge Representation (KR) system.")
print("It covers defining types, predicates, creating AST nodes, using the knowledge store,")
print("performing unification, probabilistic logic, and belief revision within a family relationships domain.")
print("Expected Output:")
print("You will see detailed output as the script initializes KR components, defines family concepts,")
print("adds facts and rules, performs queries, demonstrates unification and probabilistic inference,")
print("and shows how the belief revision system handles conflicting information.")
print("-" * 60)
try:
    from examples import core_kr_example
    print("Executing core_kr_example.py...")
    core_kr_example.main()
except ImportError:
    print("Could not import core_kr_example.py. Make sure it exists in the examples directory.")
except Exception as e:
    print(f"An error occurred while trying to demonstrate core_kr_example.py: {e}")
print("-" * 60)


# --- Example 3: Inference Engine - Comprehensive Demo ---
print("\n" + "="*60)
print("Example 3: Inference Engine - Comprehensive Demo")
print("="*60)
print("\nPurpose:")
print("This example demonstrates the capabilities of the GödelOS Inference Engine.")
print("It showcases how different provers (Resolution, Modal Tableau, SMT, CLP, Analogical Reasoning)")
print("can be used and coordinated to solve various types of logical and constraint-based problems.")
print("Expected Output:")
print("You will see output detailing the initialization of the Inference Engine components,")
print("the creation of knowledge bases for different domains (smart home, office),")
print("and the results of submitting queries to the Inference Coordinator, demonstrating different reasoning types.")
print("-" * 60)
try:
    from examples import inference_engine_example
    print("Executing inference_engine_example.py...")
    inference_engine_example.main()
except ImportError:
    print("Could not import inference_engine_example.py. Make sure it exists in the examples directory.")
except Exception as e:
    print(f"An error occurred while trying to demonstrate inference_engine_example.py: {e}")
print("-" * 60)


# --- Example 4: Learning System - Comprehensive Demo ---
print("\n" + "="*60)
print("Example 4: Learning System - Comprehensive Demo")
print("="*60)
print("\nPurpose:")
print("This example demonstrates the capabilities of the GödelOS Learning System.")
print("It showcases how the ILP Engine, Explanation-Based Learner, Template Evolution Module,")
print("and Meta-Control RL Module work together to enable a robot to learn from experience.")
print("Expected Output:")
print("You will see output detailing the initialization of learning components,")
print("the creation of a knowledge base for a robot navigation domain,")
print("and demonstrations of ILP, EBL, TEM, and MCRL in action, simulating a learning cycle.")
print("-" * 60)
try:
    from examples import learning_system_example
    print("Executing learning_system_example.py...")
    learning_system_example.main()
except ImportError:
    print("Could not import learning_system_example.py. Make sure it exists in the examples directory.")
except Exception as e:
    print(f"An error occurred while trying to demonstrate learning_system_example.py: {e}")
print("-" * 60)


# --- Example 5: Test Runner - Comprehensive Demo ---
print("\n" + "="*60)
print("Example 5: Test Runner - Comprehensive Demo")
print("="*60)
print("\nPurpose:")
print("This example demonstrates the comprehensive features of the GödelOS Test Runner.")
print("It covers test discovery, explicit registration, different verbosity levels,")
print("custom categories, timing, and report generation (HTML/JSON).")
print("Expected Output:")
print("You will see output from various test runs with different configurations,")
print("and messages indicating the generation of test reports in the 'test_output' directory.")
print("-" * 60)
try:
    from examples import test_runner_demo
    print("Executing test_runner_demo.py...")
    test_runner_demo.main()
except ImportError:
    print("Could not import test_runner_demo.py. Make sure it exists in the examples directory.")
except Exception as e:
    print(f"An error occurred while trying to demonstrate test_runner_demo.py: {e}")
print("-" * 60)


# --- Example 6: Enhanced Test Runner - Feature Demonstration ---
print("\n" + "="*60)
print("Example 6: Enhanced Test Runner - Feature Demonstration")
print("="*60)
print("\nPurpose:")
print("This example specifically highlights the enhanced features of the Test Runner,")
print("such as HTML report generation, docstring extraction, and improved console output.")
print("Expected Output:")
print("You will see test output formatted with enhanced details, and messages indicating")
print("the generation of enhanced test reports.")
print("-" * 60)
try:
    from examples import enhanced_test_runner_example
    print("Executing enhanced_test_runner_example.py...")
    enhanced_test_runner_example.main()
except ImportError:
    print("Could not import enhanced_test_runner_example.py. Make sure it exists in the examples directory.")
except Exception as e:
    print(f"An error occurred while trying to demonstrate enhanced_test_runner_example.py: {e}")
print("-" * 60)


# --- Example 7: GödelOS System - Comprehensive Integration Demo ---
print("\n" + "="*60)
print("Example 7: GödelOS System - Comprehensive Integration Demo")
print("="*60)
print("\nPurpose:")
print("This is the most comprehensive example, demonstrating the integration of all major GödelOS components.")
print("It simulates a workflow where the system processes natural language, grounds symbols,")
print("uses common sense and inference to answer queries, performs metacognitive monitoring,")
print("and generates new abstractions.")
print("Expected Output:")
print("You will see output indicating the initialization of the entire GödelOS system,")
print("the processing of natural language queries, symbol grounding results, common sense reasoning,")
print("metacognitive analysis, and the final natural language responses.")
print("-" * 60)
try:
    from examples import godel_os_example
    print("Executing godel_os_example.py...")
    godel_os_example.main()
except ImportError:
    print("Could not import godel_os_example.py. Make sure it exists in the examples directory.")
except Exception as e:
    print(f"An error occurred while trying to demonstrate godel_os_example.py: {e}")
print("-" * 60)


print("\n" + "="*60)
print("--- GödelOS Practical Demo Complete ---")
print("="*60)
print("\nThis script has stepped through various examples demonstrating key GödelOS components.")
print("Review the output above to see the results of each example.")
print("For more details on each example, refer to the individual example files in the 'examples' directory.")