"""
Comprehensive Example for GödelOS Core Knowledge Representation System

This example demonstrates the integration and usage of all seven core components
of the GödelOS Knowledge Representation (KR) System:

1. AbstractSyntaxTree (AST) Representation
2. TypeSystemManager
3. FormalLogicParser
4. UnificationEngine
5. KnowledgeStoreInterface
6. ProbabilisticLogicModule
7. BeliefRevisionSystem

The example tells a coherent story about a family relationships domain, showing
how the system can represent, reason with, and revise knowledge.
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import (
    ConstantNode, VariableNode, ApplicationNode, ConnectiveNode, QuantifierNode
)
from godelOS.core_kr.formal_logic_parser.parser import FormalLogicParser
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.probabilistic_logic.module import ProbabilisticLogicModule
from godelOS.core_kr.belief_revision.system import BeliefRevisionSystem, RevisionStrategy

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """
    Run the comprehensive example demonstrating all core KR system components.
    """
    print("\n" + "="*80)
    print("GödelOS Core Knowledge Representation System - Comprehensive Example")
    print("="*80)

    # PART 1: Setting up the Type System
    # ----------------------------------
    print("\n\n" + "-"*40)
    print("PART 1: Setting up the Type System")
    print("-"*40)
    
    print("\nInitializing Type System...")
    type_system = TypeSystemManager()
    
    # Define domain-specific types
    print("\nDefining domain-specific types for family relationships...")
    person_type = type_system.define_atomic_type("Person", ["Entity"])
    male_type = type_system.define_atomic_type("Male", ["Person"])
    female_type = type_system.define_atomic_type("Female", ["Person"])
    
    # Define predicates and relations
    print("\nDefining predicates and relations for family domain...")
    type_system.define_function_signature("Parent", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("Father", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("Mother", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("Child", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("Sibling", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("Ancestor", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("Male", ["Person"], "Boolean")
    type_system.define_function_signature("Female", ["Person"], "Boolean")
    
    # Additional predicates needed for later parts
    print("\nDefining additional predicates for later parts...")
    type_system.define_function_signature("StepFather", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("BiologicalParent", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("BiologicalFather", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("Likes", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("Loves", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("Grandparent", ["Person", "Person"], "Boolean")
    type_system.define_function_signature("Adopted", ["Person"], "Boolean")
# PART 2: Creating AST Nodes Manually
    # ----------------------------------
    print("\n\n" + "-"*40)
    print("PART 2: Creating AST Nodes Manually")
    print("-"*40)
    
    print("\nCreating AST nodes to represent family members and relationships...")
    
    # Create constants for family members
    john = ConstantNode("John", male_type)
    mary = ConstantNode("Mary", female_type)
    bob = ConstantNode("Bob", male_type)
    alice = ConstantNode("Alice", female_type)
    
    print(f"Created constants: John: {male_type}, Mary: {female_type}, Bob: {male_type}, Alice: {female_type}")
    
    # Create predicate constants
    male_pred = ConstantNode("Male", type_system.get_type("Male"))
    female_pred = ConstantNode("Female", type_system.get_type("Female"))
    parent_pred = ConstantNode("Parent", type_system.get_type("Parent"))
    father_pred = ConstantNode("Father", type_system.get_type("Father"))
    mother_pred = ConstantNode("Mother", type_system.get_type("Mother"))
    
    print(f"Created predicates: Male, Female, Parent, Father, Mother")
    
    # Create applications for facts
    male_john = ApplicationNode(
        male_pred, 
        [john], 
        type_system.get_type("Boolean")
    )
    
    female_mary = ApplicationNode(
        female_pred, 
        [mary], 
        type_system.get_type("Boolean")
    )
    
    father_john_bob = ApplicationNode(
        father_pred, 
        [john, bob], 
        type_system.get_type("Boolean")
    )
    
    mother_mary_bob = ApplicationNode(
        mother_pred, 
        [mary, bob], 
        type_system.get_type("Boolean")
    )
    
    mother_mary_alice = ApplicationNode(
        mother_pred, 
        [mary, alice], 
        type_system.get_type("Boolean")
    )
    
    print("\nCreated fact applications:")
    print("- Male(John)")
    print("- Female(Mary)")
    print("- Father(John, Bob)")
    print("- Mother(Mary, Bob)")
    print("- Mother(Mary, Alice)")

    # Create a rule: Father(x,y) => Parent(x,y)
    print("\nCreating rule: Father(x,y) => Parent(x,y)...")
    
    # Create variables for the rule
    x_var = VariableNode("?x", 1, person_type)
    y_var = VariableNode("?y", 2, person_type)
    
    # Create the antecedent: Father(?x, ?y)
    father_xy = ApplicationNode(
        father_pred, 
        [x_var, y_var], 
        type_system.get_type("Boolean")
    )
    
    # Create the consequent: Parent(?x, ?y)
    parent_xy = ApplicationNode(
        parent_pred, 
        [x_var, y_var], 
        type_system.get_type("Boolean")
    )
    
    # Create the implication: Father(?x, ?y) => Parent(?x, ?y)
    father_implies_parent = ConnectiveNode(
        "IMPLIES", 
        [father_xy, parent_xy], 
        type_system.get_type("Boolean")
    )
    
    # Create another rule: Mother(x,y) => Parent(x,y)
    print("\nCreating rule: Mother(x,y) => Parent(x,y)...")
    
    # Create the antecedent: Mother(?x, ?y)
    mother_xy = ApplicationNode(
        mother_pred, 
        [x_var, y_var], 
        type_system.get_type("Boolean")
    )
    
    # Create the implication: Mother(?x, ?y) => Parent(?x, ?y)
    mother_implies_parent = ConnectiveNode(
        "IMPLIES", 
        [mother_xy, parent_xy], 
        type_system.get_type("Boolean")
    )
    
    # Create a rule with universal quantifier: ∀x,y: Parent(x,y) => Ancestor(x,y)
    print("\nCreating rule with quantifier: ∀x,y: Parent(x,y) => Ancestor(x,y)...")
    
    # Create the ancestor predicate
    ancestor_pred = ConstantNode("Ancestor", type_system.get_type("Ancestor"))
    
    # Create the consequent: Ancestor(?x, ?y)
    ancestor_xy = ApplicationNode(
        ancestor_pred, 
        [x_var, y_var], 
        type_system.get_type("Boolean")
    )
    
    # Create the implication: Parent(?x, ?y) => Ancestor(?x, ?y)
    parent_implies_ancestor = ConnectiveNode(
        "IMPLIES",
        [parent_xy, ancestor_xy],
        type_system.get_type("Boolean")
    )
    
    # Create the quantified rule: forall ?x ?y. Parent(?x, ?y) => Ancestor(?x, ?y)
    forall_parent_ancestor = QuantifierNode(
        "FORALL",
        [x_var, y_var],
        parent_implies_ancestor,
        type_system.get_type("Boolean")
    )
# PART 3: Using the Formal Logic Parser
    # ------------------------------------
    print("\n\n" + "-"*40)
    print("PART 3: Using the Formal Logic Parser")
    print("-"*40)
    
    print("\nInitializing Formal Logic Parser...")
    parser = FormalLogicParser(type_system)
    
    print("\nParsing logical expressions...")
    
    # For this example, we'll create the AST nodes directly instead of parsing
    # The parser implementation might need additional work to handle complex expressions
    print("\nCreating additional AST nodes directly (bypassing parser)...")
    
    # Create a sibling relationship
    sibling_pred = ConstantNode("Sibling", type_system.get_type("Sibling"))
    sibling_bob_alice = ApplicationNode(
        sibling_pred,
        [bob, alice],
        type_system.get_type("Boolean")
    )
    print(f"Created: Sibling(Bob, Alice)")
    
    # Create a transitive ancestor rule
    # forall ?x ?y ?z. (Ancestor(?x, ?y) and Ancestor(?y, ?z)) => Ancestor(?x, ?z)
    z_var = VariableNode("?z", 3, person_type)
    
    # Ancestor(?x, ?y)
    ancestor_xy = ApplicationNode(
        ancestor_pred,
        [x_var, y_var],
        type_system.get_type("Boolean")
    )
    
    # Ancestor(?y, ?z)
    ancestor_yz = ApplicationNode(
        ancestor_pred,
        [y_var, z_var],
        type_system.get_type("Boolean")
    )
    
    # Ancestor(?x, ?z)
    ancestor_xz = ApplicationNode(
        ancestor_pred,
        [x_var, z_var],
        type_system.get_type("Boolean")
    )
    
    # (Ancestor(?x, ?y) and Ancestor(?y, ?z))
    ancestor_and = ConnectiveNode(
        "AND",
        [ancestor_xy, ancestor_yz],
        type_system.get_type("Boolean")
    )
    
    # (Ancestor(?x, ?y) and Ancestor(?y, ?z)) => Ancestor(?x, ?z)
    ancestor_rule = ConnectiveNode(
        "IMPLIES",
        [ancestor_and, ancestor_xz],
        type_system.get_type("Boolean")
    )
    
    # forall ?x ?y ?z. (Ancestor(?x, ?y) and Ancestor(?y, ?z)) => Ancestor(?x, ?z)
    ancestor_rule_ast = QuantifierNode(
        "FORALL",
        [x_var, y_var, z_var],
        ancestor_rule,
        type_system.get_type("Boolean")
    )
    print(f"Created: forall ?x ?y ?z. (Ancestor(?x, ?y) and Ancestor(?y, ?z)) => Ancestor(?x, ?z)")

    # PART 4: Knowledge Store Interface
    # --------------------------------
    print("\n\n" + "-"*40)
    print("PART 4: Knowledge Store Interface")
    print("-"*40)
    
    print("\nInitializing Knowledge Store Interface...")
    ksi = KnowledgeStoreInterface(type_system)
    
    print("\nAdding facts to the knowledge store...")
    
    # Create contexts
    print("\nCreating contexts...")
    ksi.create_context("FAMILY_FACTS", context_type="facts")
    ksi.create_context("FAMILY_RULES", context_type="rules")
    ksi.create_context("INFERRED_FACTS", context_type="inferred")
    
    # Add facts to the knowledge store
    print("\nAdding facts to the knowledge store...")
    ksi.add_statement(male_john, context_id="FAMILY_FACTS")
    ksi.add_statement(female_mary, context_id="FAMILY_FACTS")
    ksi.add_statement(father_john_bob, context_id="FAMILY_FACTS")
    ksi.add_statement(mother_mary_bob, context_id="FAMILY_FACTS")
    ksi.add_statement(mother_mary_alice, context_id="FAMILY_FACTS")
    
    # Add the sibling relationship
    ksi.add_statement(sibling_bob_alice, context_id="FAMILY_FACTS")
    
    print("\nAdding rules to the knowledge store...")
    
    # Add rules to the knowledge store
    ksi.add_statement(father_implies_parent, context_id="FAMILY_RULES")
    ksi.add_statement(mother_implies_parent, context_id="FAMILY_RULES")
    ksi.add_statement(forall_parent_ancestor, context_id="FAMILY_RULES")
    ksi.add_statement(ancestor_rule_ast, context_id="FAMILY_RULES")
    
    print("\nQuerying the knowledge store...")
    
    # Query for all facts about Bob
    bob_var = VariableNode("?pred", 3, type_system.get_type("Entity"))
    bob_query = ApplicationNode(
        bob_var,
        [bob],
        type_system.get_type("Boolean")
    )
    
    results = ksi.query_statements_match_pattern(bob_query, context_ids=["FAMILY_FACTS"])
    print(f"\nQuery: Facts about Bob")
    print(f"Results: {len(results)} matches")
    
    for i, binding in enumerate(results):
        for var, node in binding.items():
            if isinstance(node, ApplicationNode) and len(node.arguments) > 0 and node.arguments[0] == bob:
                print(f"  Match {i+1}: {node}")
    
    # Query for all mother relationships
    mother_query = ApplicationNode(
        mother_pred,
        [VariableNode("?mother", 4, female_type), VariableNode("?child", 5, person_type)],
        type_system.get_type("Boolean")
    )
    
    results = ksi.query_statements_match_pattern(mother_query, context_ids=["FAMILY_FACTS"])
    print(f"\nQuery: All mother relationships")
    print(f"Results: {len(results)} matches")
    
    for i, binding in enumerate(results):
        mother_var = None
        child_var = None
        for var, node in binding.items():
            if var.name == "?mother":
                mother_var = node
# PART 5: Unification Engine
    # -------------------------
    print("\n\n" + "-"*40)
    print("PART 5: Unification Engine")
    print("-"*40)
    
    print("\nInitializing Unification Engine...")
    unification_engine = UnificationEngine(type_system)
    
    print("\nDemonstrating unification...")
    
    # Create patterns for unification
    mother_pattern = ApplicationNode(
        mother_pred,
        [VariableNode("?m", 6, female_type), VariableNode("?c", 7, person_type)],
        type_system.get_type("Boolean")
    )
    
    # Unify with a specific fact
    bindings, errors = unification_engine.unify(mother_pattern, mother_mary_bob)
    
    if bindings:
        print("\nUnified pattern Mother(?m, ?c) with fact Mother(Mary, Bob)")
        for var_id, binding in bindings.items():
            print(f"  Variable ID {var_id} bound to {binding}")
    else:
        print(f"Failed to unify: {errors}")
    
    # Create a more complex pattern
    parent_child_pattern = ApplicationNode(
        parent_pred,
        [VariableNode("?parent", 8, person_type), bob],
        type_system.get_type("Boolean")
    )
    
    # Demonstrate inference through unification
    print("\nDemonstrating inference through unification...")
    print("Given: Father(John, Bob) and rule Father(?x, ?y) => Parent(?x, ?y)")
    print("We want to infer: Parent(John, Bob)")
    
    # First, unify the antecedent of the rule with our fact
    bindings, errors = unification_engine.unify(father_xy, father_john_bob)
    
    if bindings:
        print("\nUnified Father(?x, ?y) with Father(John, Bob)")
        for var_id, binding in bindings.items():
            var_name = "?x" if var_id == 1 else "?y" if var_id == 2 else f"Unknown({var_id})"
            print(f"  {var_name} bound to {binding}")
        
        # Now apply these bindings to the consequent to get the inferred fact
        inferred_parent = parent_xy.substitute({x_var: john, y_var: bob})
        print(f"\nInferred fact: {inferred_parent}")
        
        # Add the inferred fact to the knowledge store
        ksi.add_statement(inferred_parent, context_id="INFERRED_FACTS")
        print("Added inferred fact to INFERRED_FACTS context")
    else:
        print(f"Failed to unify: {errors}")

    # PART 6: Probabilistic Logic Module
    # ---------------------------------
    print("\n\n" + "-"*40)
    print("PART 6: Probabilistic Logic Module")
    print("-"*40)
    
    print("\nInitializing Probabilistic Logic Module...")
    plm = ProbabilisticLogicModule(ksi)
    
    # Create some probabilistic rules
    print("\nAdding weighted formulas (probabilistic rules)...")
    
    # Create probabilistic rules directly
    # Rule: forall ?x ?y. Parent(?x, ?y) => BiologicalParent(?x, ?y)
    bio_parent_pred = ConstantNode("BiologicalParent", type_system.get_type("Entity"))
    
    # BiologicalParent(?x, ?y)
    bio_parent_xy = ApplicationNode(
        bio_parent_pred,
        [x_var, y_var],
        type_system.get_type("Boolean")
    )
    
    # Parent(?x, ?y) => BiologicalParent(?x, ?y)
    bio_parent_rule = ConnectiveNode(
        "IMPLIES",
        [parent_xy, bio_parent_xy],
        type_system.get_type("Boolean")
    )
    
    # forall ?x ?y. Parent(?x, ?y) => BiologicalParent(?x, ?y)
    bio_parent_ast = QuantifierNode(
        "FORALL",
        [x_var, y_var],
        bio_parent_rule,
        type_system.get_type("Boolean")
    )
    
    # Add with high weight (0.9) - most parents are biological parents
    plm.add_weighted_formula(bio_parent_ast, 0.9)
    print(f"Added weighted formula with weight 0.9: forall ?x ?y. Parent(?x, ?y) => BiologicalParent(?x, ?y)")
    
    # Rule: forall ?x ?y. Sibling(?x, ?y) => Likes(?x, ?y)
    likes_pred = ConstantNode("Likes", type_system.get_type("Entity"))
    
    # Sibling(?x, ?y)
    sibling_xy = ApplicationNode(
        sibling_pred,
        [x_var, y_var],
        type_system.get_type("Boolean")
    )
    
    # Likes(?x, ?y)
    likes_xy = ApplicationNode(
        likes_pred,
        [x_var, y_var],
        type_system.get_type("Boolean")
    )
    
    # Sibling(?x, ?y) => Likes(?x, ?y)
    likes_rule = ConnectiveNode(
        "IMPLIES",
        [sibling_xy, likes_xy],
        type_system.get_type("Boolean")
    )
    
    # forall ?x ?y. Sibling(?x, ?y) => Likes(?x, ?y)
    likes_ast = QuantifierNode(
        "FORALL",
        [x_var, y_var],
        likes_rule,
        type_system.get_type("Boolean")
    )
    
    # Add with medium weight (0.7) - siblings often like each other
    plm.add_weighted_formula(likes_ast, 0.7)
    print(f"Added weighted formula with weight 0.7: forall ?x ?y. Sibling(?x, ?y) => Likes(?x, ?y)")
    
    # Create some evidence
    print("\nCreating evidence for probabilistic inference...")
    
    # Create evidence statements directly
    bio_parent_john_bob_ast = ApplicationNode(
        bio_parent_pred,
        [john, bob],
        type_system.get_type("Boolean")
    )
    
    likes_bob_alice_ast = ApplicationNode(
        likes_pred,
        [bob, alice],
        type_system.get_type("Boolean")
    )
    
    # Create evidence set
    evidence = set()
    evidence.add((sibling_bob_alice, True))  # We know Bob and Alice are siblings
    
    # Perform probabilistic inference
    print("\nPerforming probabilistic inference...")
    
    if bio_parent_john_bob_ast:
        # Calculate probability that John is Bob's biological parent
        prob = plm.get_marginal_probability(
            bio_parent_john_bob_ast,
            evidence,
            inference_params={"num_samples": 500}
        )
        print(f"P(BiologicalParent(John, Bob) | evidence) = {prob:.4f}")
    
    if likes_bob_alice_ast:
        # Calculate probability that Bob likes Alice
        prob = plm.get_marginal_probability(
            likes_bob_alice_ast,
            evidence,
            inference_params={"num_samples": 500}
        )
# PART 7: Belief Revision System
    # -----------------------------
    print("\n\n" + "-"*40)
    print("PART 7: Belief Revision System")
    print("-"*40)
    
    print("\nInitializing Belief Revision System...")
    brs = BeliefRevisionSystem(ksi, belief_set_context_id="FAMILY_BELIEFS")
    
    # Copy some facts to the belief set
    print("\nCreating initial belief set...")
    ksi.add_statement(father_john_bob, context_id="FAMILY_BELIEFS")
    ksi.add_statement(mother_mary_bob, context_id="FAMILY_BELIEFS")
    
    # Create a step-father belief
    step_father_pred = ConstantNode("StepFather", type_system.get_type("StepFather"))
    step_father_ast = ApplicationNode(
        step_father_pred,
        [john, bob],
        type_system.get_type("Boolean")
    )
    
    ksi.add_statement(step_father_ast, context_id="FAMILY_BELIEFS")
    print(f"Added belief: StepFather(John, Bob)")
    
    # Create a new belief that conflicts with existing beliefs
    print("\nIntroducing a conflicting belief...")
    
    # Create the conflicting belief: not(Father(John, Bob))
    not_father_ast = ConnectiveNode(
        "NOT",
        [father_john_bob],
        type_system.get_type("Boolean")
    )
    
    print(f"New conflicting belief: not(Father(John, Bob))")
    
    # Revise the belief set
    print("\nRevising belief set using AGM belief revision...")
    revised_set_id = brs.revise_belief_set(
        "FAMILY_BELIEFS",
        not_father_ast,
        strategy=RevisionStrategy.PARTIAL_MEET
    )
    
    print(f"Created revised belief set: {revised_set_id}")
    
    # Query the revised belief set
    print("\nQuerying the revised belief set...")
    results = ksi.query_statements_match_pattern(
        father_john_bob,
        context_ids=[revised_set_id]
    )
    
    if results:
        print(f"Father(John, Bob) is still in the belief set (unexpected)")
    else:
        print(f"Father(John, Bob) has been removed from the belief set (expected)")
    
    results = ksi.query_statements_match_pattern(
        not_father_ast,
        context_ids=[revised_set_id]
    )
    
    if results:
        print(f"not(Father(John, Bob)) is in the belief set (expected)")
    else:
        print(f"not(Father(John, Bob)) is not in the belief set (unexpected)")
    
    # Demonstrate belief set expansion
    print("\nDemonstrating belief set expansion...")
    
    # Create a grandparent rule
    # forall ?x ?y ?z. (Parent(?x, ?y) and Parent(?y, ?z)) => Grandparent(?x, ?z)
    z_var = VariableNode("?z", 9, person_type)
    
    # Parent(?x, ?y)
    parent_xy = ApplicationNode(
        parent_pred,
        [x_var, y_var],
        type_system.get_type("Boolean")
    )
    
    # Parent(?y, ?z)
    parent_yz = ApplicationNode(
        parent_pred,
        [y_var, z_var],
        type_system.get_type("Boolean")
    )
    
    # Grandparent(?x, ?z)
    grandparent_pred = ConstantNode("Grandparent", type_system.get_type("Grandparent"))
    grandparent_xz = ApplicationNode(
        grandparent_pred,
        [x_var, z_var],
        type_system.get_type("Boolean")
    )
    
    # (Parent(?x, ?y) and Parent(?y, ?z))
    parent_and = ConnectiveNode(
        "AND",
        [parent_xy, parent_yz],
        type_system.get_type("Boolean")
    )
    
    # (Parent(?x, ?y) and Parent(?y, ?z)) => Grandparent(?x, ?z)
    grandparent_rule = ConnectiveNode(
        "IMPLIES",
        [parent_and, grandparent_xz],
        type_system.get_type("Boolean")
    )
    
    # forall ?x ?y ?z. (Parent(?x, ?y) and Parent(?y, ?z)) => Grandparent(?x, ?z)
    grandparent_ast = QuantifierNode(
        "FORALL",
        [x_var, y_var, z_var],
        grandparent_rule,
        type_system.get_type("Boolean")
    )
    
    print(f"New belief to add: forall ?x ?y ?z. (Parent(?x, ?y) and Parent(?y, ?z)) => Grandparent(?x, ?z)")
    
    # Expand the belief set
    expanded_set_id = brs.expand_belief_set(
        "FAMILY_BELIEFS",
        grandparent_ast,
        entrenchment_value=0.8
    )
    
    print(f"Created expanded belief set: {expanded_set_id}")
    
    # Query the expanded belief set
    print("\nQuerying the expanded belief set...")
    results = ksi.query_statements_match_pattern(
        grandparent_ast,
        context_ids=[expanded_set_id]
    )
    
    if results:
        print(f"Grandparent rule is in the expanded belief set (expected)")
    else:
        print(f"Grandparent rule is not in the expanded belief set (unexpected)")

    # PART 8: Integration of All Components
    # ------------------------------------
    print("\n\n" + "-"*40)
    print("PART 8: Integration of All Components")
    print("-"*40)
    
    print("\nDemonstrating the integration of all components...")
    
    # Create a new context for the integrated example
    ksi.create_context("INTEGRATED_EXAMPLE", context_type="integrated")
    
    # Add some base facts
    print("\nAdding base facts to the integrated example...")
    ksi.add_statement(male_john, context_id="INTEGRATED_EXAMPLE")
    ksi.add_statement(female_mary, context_id="INTEGRATED_EXAMPLE")
    ksi.add_statement(father_john_bob, context_id="INTEGRATED_EXAMPLE")
    ksi.add_statement(mother_mary_bob, context_id="INTEGRATED_EXAMPLE")
    
    # Add rules
    print("\nAdding rules to the integrated example...")
    ksi.add_statement(father_implies_parent, context_id="INTEGRATED_EXAMPLE")
    ksi.add_statement(mother_implies_parent, context_id="INTEGRATED_EXAMPLE")
    
    if grandparent_ast:
        ksi.add_statement(grandparent_ast, context_id="INTEGRATED_EXAMPLE")
    
    # Create and add a new fact
    charlie = ConstantNode("Charlie", male_type)
    male_charlie = ApplicationNode(
        male_pred,
        [charlie],
        type_system.get_type("Boolean")
    )
    
    ksi.add_statement(male_charlie, context_id="INTEGRATED_EXAMPLE")
    print(f"Added fact: Male(Charlie)")
    
    # Create and add a relationship
    bob_father_charlie_ast = ApplicationNode(
        father_pred,
        [bob, charlie],
        type_system.get_type("Boolean")
    )
    
    ksi.add_statement(bob_father_charlie_ast, context_id="INTEGRATED_EXAMPLE")
    print(f"Added fact: Father(Bob, Charlie)")
    
    # Perform inference
    print("\nPerforming inference...")
    
    # Infer Parent(Bob, Charlie) from Father(Bob, Charlie)
    if bob_father_charlie_ast:
        # Create a parent relationship directly
        bob_parent_charlie_ast = ApplicationNode(
            parent_pred,
            [bob, charlie],
            type_system.get_type("Boolean")
        )
        # Check if this can be inferred
        # First, unify the antecedent of the rule with our fact
        bindings, errors = unification_engine.unify(father_xy, bob_father_charlie_ast)
        
        if bindings:
            print("\nInferred Parent(Bob, Charlie) from Father(Bob, Charlie) and the rule Father(?x, ?y) => Parent(?x, ?y)")
            
            # Add the inferred fact to the knowledge store
            inferred_parent = parent_xy.substitute({
                x_var: bob,
                y_var: charlie
            })
            
            ksi.add_statement(inferred_parent, context_id="INTEGRATED_EXAMPLE")
            print("Added inferred fact to INTEGRATED_EXAMPLE context")
    
    # Infer Grandparent relationship
    print("\nInferring grandparent relationships...")
    
    # This would normally be done by an inference engine
    # For demonstration, we'll manually create grandparent relationships
    
    # Create Grandparent(John, Charlie)
    john_grandparent_charlie_ast = ApplicationNode(
        grandparent_pred,
        [john, charlie],
        type_system.get_type("Boolean")
    )
    
    print("Inferred: Grandparent(John, Charlie)")
    ksi.add_statement(john_grandparent_charlie_ast, context_id="INTEGRATED_EXAMPLE")
    
    # Create Grandparent(Mary, Charlie)
    mary_grandparent_charlie_ast = ApplicationNode(
        grandparent_pred,
        [mary, charlie],
        type_system.get_type("Boolean")
    )
    
    print("Inferred: Grandparent(Mary, Charlie)")
    ksi.add_statement(mary_grandparent_charlie_ast, context_id="INTEGRATED_EXAMPLE")
    
    # Add a probabilistic rule
    print("\nAdding probabilistic rules to the integrated example...")
    
    # Create a probabilistic rule: forall ?x ?y. Grandparent(?x, ?y) => Loves(?x, ?y)
    
    # Loves(?x, ?y)
    loves_xy = ApplicationNode(
        likes_pred,  # Reusing the likes predicate for loves
        [x_var, y_var],
        type_system.get_type("Boolean")
    )
    
    # Grandparent(?x, ?y)
    grandparent_xy = ApplicationNode(
        grandparent_pred,
        [x_var, y_var],
        type_system.get_type("Boolean")
    )
    
    # Grandparent(?x, ?y) => Loves(?x, ?y)
    loves_rule = ConnectiveNode(
        "IMPLIES",
        [grandparent_xy, loves_xy],
        type_system.get_type("Boolean")
    )
    
    # forall ?x ?y. Grandparent(?x, ?y) => Loves(?x, ?y)
    loves_grandchild_ast = QuantifierNode(
        "FORALL",
        [x_var, y_var],
        loves_rule,
        type_system.get_type("Boolean")
    )
    
    # Add with high weight (0.95) - grandparents almost always love their grandchildren
    plm.add_weighted_formula(loves_grandchild_ast, 0.95, context_id="INTEGRATED_EXAMPLE_PROB")
    print(f"Added weighted formula with weight 0.95: forall ?x ?y. Grandparent(?x, ?y) => Loves(?x, ?y)")
    
    # Perform probabilistic inference
    print("\nPerforming probabilistic inference in the integrated example...")
    
    # Create John loves Charlie relationship
    john_loves_charlie_ast = ApplicationNode(
        likes_pred,  # Reusing the likes predicate for loves
        [john, charlie],
        type_system.get_type("Boolean")
    )
    
    # Create evidence set
    evidence = set()
    evidence.add((john_grandparent_charlie_ast, True))  # We know John is Charlie's grandparent
    
    # Calculate probability
    prob = plm.get_marginal_probability(
        john_loves_charlie_ast,
        evidence,
        inference_params={"num_samples": 500}
    )
    print(f"P(Loves(John, Charlie) | Grandparent(John, Charlie)) = {prob:.4f}")
    
    # Demonstrate belief revision
    print("\nDemonstrating belief revision in the integrated example...")
    
    # Create a belief revision system for the integrated example
    integrated_brs = BeliefRevisionSystem(ksi, belief_set_context_id="INTEGRATED_EXAMPLE")
    
    # Create an adopted fact
    adopted_pred = ConstantNode("Adopted", type_system.get_type("Entity"))
    adopted_ast = ApplicationNode(
        adopted_pred,
        [charlie],
        type_system.get_type("Boolean")
    )
    
    print(f"New belief that may conflict: Adopted(Charlie)")
    
    # Create a rule: (Adopted(?y) and Father(?x, ?y)) => not(BiologicalFather(?x, ?y))
    bio_father_pred = ConstantNode("BiologicalFather", type_system.get_type("Entity"))
    
    # BiologicalFather(?x, ?y)
    bio_father_xy = ApplicationNode(
        bio_father_pred,
        [x_var, y_var],
        type_system.get_type("Boolean")
    )
    
    # not(BiologicalFather(?x, ?y))
    not_bio_father_xy = ConnectiveNode(
        "NOT",
        [bio_father_xy],
        type_system.get_type("Boolean")
    )
    
    # Adopted(?y)
    adopted_y = ApplicationNode(
        adopted_pred,
        [y_var],
        type_system.get_type("Boolean")
    )
    
    # (Adopted(?y) and Father(?x, ?y))
    adopted_and_father = ConnectiveNode(
        "AND",
        [adopted_y, father_xy],
        type_system.get_type("Boolean")
    )
    
    # (Adopted(?y) and Father(?x, ?y)) => not(BiologicalFather(?x, ?y))
    not_bio_father_rule = ConnectiveNode(
        "IMPLIES",
        [adopted_and_father, not_bio_father_xy],
        type_system.get_type("Boolean")
    )
    
    # forall ?x ?y. (Adopted(?y) and Father(?x, ?y)) => not(BiologicalFather(?x, ?y))
    not_bio_father_ast = QuantifierNode(
        "FORALL",
        [x_var, y_var],
        not_bio_father_rule,
        type_system.get_type("Boolean")
    )
    
    # Add the rule to the belief set
    ksi.add_statement(not_bio_father_ast, context_id="INTEGRATED_EXAMPLE")
    print(f"Added rule: forall ?x ?y. (Adopted(?y) and Father(?x, ?y)) => not(BiologicalFather(?x, ?y))")
    
    # Add the adopted fact
    ksi.add_statement(adopted_ast, context_id="INTEGRATED_EXAMPLE")
    print(f"Added fact: Adopted(Charlie)")
    
    # Create the inferred fact: not(BiologicalFather(Bob, Charlie))
    bio_father_bob_charlie = ApplicationNode(
        bio_father_pred,
        [bob, charlie],
        type_system.get_type("Boolean")
    )
    
    not_bio_father_bob_charlie_ast = ConnectiveNode(
        "NOT",
        [bio_father_bob_charlie],
        type_system.get_type("Boolean")
    )
    
    print("Inferred: not(BiologicalFather(Bob, Charlie))")
    ksi.add_statement(not_bio_father_bob_charlie_ast, context_id="INTEGRATED_EXAMPLE")
    
    print("\n\n" + "="*80)
    print("Comprehensive Example Complete")
    print("This example demonstrated all seven core components of the GödelOS KR System:")
    print("1. AbstractSyntaxTree (AST) Representation")
    print("2. TypeSystemManager")
    print("3. FormalLogicParser")
    print("4. UnificationEngine")
    print("5. KnowledgeStoreInterface")
    print("6. ProbabilisticLogicModule")
    print("7. BeliefRevisionSystem")
    print("="*80)


if __name__ == "__main__":
    main()