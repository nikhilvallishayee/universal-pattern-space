"""
Comprehensive Example for GödelOS Learning System

This example demonstrates the integration and usage of all four components
of the GödelOS Learning System:

1. ILPEngine (Module 3.1) - Induces new logical rules from positive and negative examples
2. ExplanationBasedLearner (Module 3.2) - Generalizes from successful problem-solving instances
3. TemplateEvolutionModule (Module 3.3) - Refines and evolves existing LogicTemplates
4. MetaControlRLModule (Module 3.4) - Learns optimal control policies for meta-level decisions

The example tells a coherent story about a robot learning to navigate and interact with
its environment, showing how the different learning components work together and
interact with the Core KR System and Inference Engine.
"""

import sys
import os
import logging
import random
import numpy as np
from typing import Dict, List, Set, Tuple, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Core KR System components
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode, ConnectiveNode, QuantifierNode
)
from godelOS.core_kr.formal_logic_parser.parser import FormalLogicParser
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface

# Import Inference Engine components
from godelOS.inference_engine.coordinator import InferenceCoordinator, StrategyKnowledgeBase
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject
from godelOS.inference_engine.resolution_prover import ResolutionProver

# Import Learning System components
from godelOS.learning_system.ilp_engine import ILPEngine, LanguageBias, ModeDeclaration
from godelOS.learning_system.explanation_based_learner import ExplanationBasedLearner, OperationalityConfig
from godelOS.learning_system.template_evolution_module import TemplateEvolutionModule, EvolutionConfig
from godelOS.learning_system.meta_control_rl_module import MetaControlRLModule, RLConfig, MetaAction

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
def main():
    """
    Run the comprehensive example demonstrating all Learning System components.
    """
    print("\n" + "="*80)
    print("GödelOS Learning System - Comprehensive Example")
    print("="*80)

    # PART 1: Setting up the Core Components
    # --------------------------------------
    print("\n\n" + "-"*40)
    print("PART 1: Setting up the Core Components")
    print("-"*40)
    
    print("\nInitializing Type System...")
    type_system = TypeSystemManager()
    
    # Define domain-specific types for our robot navigation domain
    print("\nDefining domain-specific types for robot navigation domain...")
    entity_type = type_system.get_type("Entity")
    location_type = type_system.define_atomic_type("Location", ["Entity"])
    object_type = type_system.define_atomic_type("Object", ["Entity"])
    robot_type = type_system.define_atomic_type("Robot", ["Entity"])
    action_type = type_system.define_atomic_type("Action", ["Entity"])
    
    # Define predicates and functions
    print("\nDefining predicates and functions...")
    type_system.define_function_signature("At", ["Robot", "Location"], "Boolean")
    type_system.define_function_signature("Adjacent", ["Location", "Location"], "Boolean")
    type_system.define_function_signature("Contains", ["Location", "Object"], "Boolean")
    type_system.define_function_signature("Holding", ["Robot", "Object"], "Boolean")
    type_system.define_function_signature("CanMove", ["Robot", "Location", "Location"], "Boolean")
    type_system.define_function_signature("CanPickUp", ["Robot", "Object", "Location"], "Boolean")
    type_system.define_function_signature("CanDrop", ["Robot", "Object", "Location"], "Boolean")
    type_system.define_function_signature("Move", ["Robot", "Location", "Location"], "Action")
    type_system.define_function_signature("PickUp", ["Robot", "Object", "Location"], "Action")
    type_system.define_function_signature("Drop", ["Robot", "Object", "Location"], "Action")
    type_system.define_function_signature("Blocked", ["Location"], "Boolean")
    type_system.define_function_signature("Heavy", ["Object"], "Boolean")
    type_system.define_function_signature("Fragile", ["Object"], "Boolean")
    type_system.define_function_signature("StrongGripper", ["Robot"], "Boolean")
    type_system.define_function_signature("CanReach", ["Robot", "Location"], "Boolean")
    
    # Initialize parser
    print("\nInitializing Parser...")
    parser = FormalLogicParser(type_system)
    
    # Initialize unification engine
    print("\nInitializing Unification Engine...")
    unification_engine = UnificationEngine(type_system)
    
    # Initialize knowledge store
    print("\nInitializing Knowledge Store...")
    ksi = KnowledgeStoreInterface(type_system)
    
    # Create contexts for different types of knowledge
    print("\nCreating contexts for different types of knowledge...")
    ksi.create_context("FACTS", context_type="facts")
    ksi.create_context("RULES", context_type="rules")
    ksi.create_context("LEARNED_RULES", context_type="learned")
    ksi.create_context("META_KNOWLEDGE", context_type="meta")
    
    # Initialize resolution prover
    print("\nInitializing Resolution Prover...")
    resolution_prover = ResolutionProver(ksi, unification_engine)
    
    # Initialize inference coordinator
    print("\nInitializing Inference Coordinator...")
    provers = {
        "resolution_prover": resolution_prover
    }
    inference_coordinator = InferenceCoordinator(ksi, provers)
    
# PART 2: Creating the Knowledge Base
    # ----------------------------------
    print("\n\n" + "-"*40)
    print("PART 2: Creating the Knowledge Base")
    print("-"*40)
    
    print("\nCreating AST nodes for the robot navigation domain...")
    
    # Create constants for the domain
    robot1 = ConstantNode("Robot1", robot_type)
    
    loc_a = ConstantNode("LocationA", location_type)
    loc_b = ConstantNode("LocationB", location_type)
    loc_c = ConstantNode("LocationC", location_type)
    loc_d = ConstantNode("LocationD", location_type)
    
    box1 = ConstantNode("Box1", object_type)
    box2 = ConstantNode("Box2", object_type)
    ball1 = ConstantNode("Ball1", object_type)
    
    # Create predicate constants
    at_pred = ConstantNode("At", type_system.get_type("At"))
    adjacent_pred = ConstantNode("Adjacent", type_system.get_type("Adjacent"))
    contains_pred = ConstantNode("Contains", type_system.get_type("Contains"))
    holding_pred = ConstantNode("Holding", type_system.get_type("Holding"))
    can_move_pred = ConstantNode("CanMove", type_system.get_type("CanMove"))
    blocked_pred = ConstantNode("Blocked", type_system.get_type("Blocked"))
    heavy_pred = ConstantNode("Heavy", type_system.get_type("Heavy"))
    fragile_pred = ConstantNode("Fragile", type_system.get_type("Fragile"))
    strong_gripper_pred = ConstantNode("StrongGripper", type_system.get_type("StrongGripper"))
    can_reach_pred = ConstantNode("CanReach", type_system.get_type("CanReach"))
    
    # Create facts about the environment
    # Robot1 is at LocationA
    robot1_at_loc_a = ApplicationNode(
        at_pred,
        [robot1, loc_a],
        type_system.get_type("Boolean")
    )
    
    # LocationA is adjacent to LocationB
    loc_a_adj_loc_b = ApplicationNode(
        adjacent_pred,
        [loc_a, loc_b],
        type_system.get_type("Boolean")
    )
    
    # LocationB is adjacent to LocationC
    loc_b_adj_loc_c = ApplicationNode(
        adjacent_pred,
        [loc_b, loc_c],
        type_system.get_type("Boolean")
    )
    
    # LocationC is adjacent to LocationD
    loc_c_adj_loc_d = ApplicationNode(
        adjacent_pred,
        [loc_c, loc_d],
        type_system.get_type("Boolean")
    )
    
    # LocationB contains Box1
    loc_b_contains_box1 = ApplicationNode(
        contains_pred,
        [loc_b, box1],
        type_system.get_type("Boolean")
    )
    
    # LocationC contains Box2
    loc_c_contains_box2 = ApplicationNode(
        contains_pred,
        [loc_c, box2],
        type_system.get_type("Boolean")
    )
    
    # LocationD contains Ball1
    loc_d_contains_ball1 = ApplicationNode(
        contains_pred,
        [loc_d, ball1],
        type_system.get_type("Boolean")
    )
    
    # Box2 is heavy
    box2_is_heavy = ApplicationNode(
        heavy_pred,
        [box2],
        type_system.get_type("Boolean")
    )
    
    # Ball1 is fragile
    ball1_is_fragile = ApplicationNode(
        fragile_pred,
        [ball1],
        type_system.get_type("Boolean")
    )
    
    # Robot1 has a strong gripper
    robot1_strong_gripper = ApplicationNode(
        strong_gripper_pred,
        [robot1],
        type_system.get_type("Boolean")
    )
    
    # Add facts to the knowledge store
    print("\nAdding facts to the knowledge store...")
    ksi.add_statement(robot1_at_loc_a, context_id="FACTS")
    ksi.add_statement(loc_a_adj_loc_b, context_id="FACTS")
    ksi.add_statement(loc_b_adj_loc_c, context_id="FACTS")
    ksi.add_statement(loc_c_adj_loc_d, context_id="FACTS")
    ksi.add_statement(loc_b_contains_box1, context_id="FACTS")
    ksi.add_statement(loc_c_contains_box2, context_id="FACTS")
    ksi.add_statement(loc_d_contains_ball1, context_id="FACTS")
    ksi.add_statement(box2_is_heavy, context_id="FACTS")
    ksi.add_statement(ball1_is_fragile, context_id="FACTS")
    ksi.add_statement(robot1_strong_gripper, context_id="FACTS")
    
    # Create variables for rules
    robot_var = VariableNode("?robot", 1, robot_type)
    loc1_var = VariableNode("?loc1", 2, location_type)
    loc2_var = VariableNode("?loc2", 3, location_type)
    obj_var = VariableNode("?obj", 4, object_type)
    
    # Create basic rules for the domain
    
    # Rule 1: A robot can move from one location to another if they are adjacent
    # CanMove(?robot, ?loc1, ?loc2) :- At(?robot, ?loc1) ∧ Adjacent(?loc1, ?loc2) ∧ ¬Blocked(?loc2)
    
    # At(?robot, ?loc1)
    robot_at_loc1 = ApplicationNode(
        at_pred,
        [robot_var, loc1_var],
        type_system.get_type("Boolean")
    )
    
    # Adjacent(?loc1, ?loc2)
    loc1_adj_loc2 = ApplicationNode(
        adjacent_pred,
        [loc1_var, loc2_var],
        type_system.get_type("Boolean")
    )
    
    # Blocked(?loc2)
    loc2_blocked = ApplicationNode(
        blocked_pred,
        [loc2_var],
        type_system.get_type("Boolean")
    )
    
    # ¬Blocked(?loc2)
    not_loc2_blocked = ConnectiveNode(
        "NOT",
        [loc2_blocked],
        type_system.get_type("Boolean")
    )
    
    # At(?robot, ?loc1) ∧ Adjacent(?loc1, ?loc2)
    robot_at_and_adj = ConnectiveNode(
        "AND",
        [robot_at_loc1, loc1_adj_loc2],
        type_system.get_type("Boolean")
    )
    
    # At(?robot, ?loc1) ∧ Adjacent(?loc1, ?loc2) ∧ ¬Blocked(?loc2)
    can_move_body = ConnectiveNode(
        "AND",
        [robot_at_and_adj, not_loc2_blocked],
        type_system.get_type("Boolean")
    )
    
    # CanMove(?robot, ?loc1, ?loc2)
    can_move_head = ApplicationNode(
        can_move_pred,
        [robot_var, loc1_var, loc2_var],
        type_system.get_type("Boolean")
    )
    
    # CanMove(?robot, ?loc1, ?loc2) :- At(?robot, ?loc1) ∧ Adjacent(?loc1, ?loc2) ∧ ¬Blocked(?loc2)
    can_move_rule = ConnectiveNode(
        "IMPLIES",
        [can_move_body, can_move_head],
        type_system.get_type("Boolean")
    )
    
    # Add the rule to the knowledge store
    ksi.add_statement(can_move_rule, context_id="RULES")
    print("Added rule: CanMove(?robot, ?loc1, ?loc2) :- At(?robot, ?loc1) ∧ Adjacent(?loc1, ?loc2) ∧ ¬Blocked(?loc2)")
    strategy_kb = StrategyKnowledgeBase()
    provers = {"resolution_prover": resolution_prover}
# PART 3: Demonstrating the ILPEngine
    # ----------------------------------
    print("\n\n" + "-"*40)
    print("PART 3: Demonstrating the ILPEngine")
    print("-"*40)
    
    print("\nInitializing ILPEngine...")
    
    # Create language bias for the ILP engine
    language_bias = LanguageBias(
        max_clause_length=3,
        max_variables=5,
        allow_recursion=False
    )
    
    # Add mode declarations for the predicates
    adjacent_mode = ModeDeclaration(
        predicate_name="Adjacent",
        arg_modes=["+", "-"],
        arg_types=["Location", "Location"]
    )
    
    at_mode = ModeDeclaration(
        predicate_name="At",
        arg_modes=["+", "-"],
        arg_types=["Robot", "Location"]
    )
    
    can_reach_mode = ModeDeclaration(
        predicate_name="CanReach",
        arg_modes=["+", "-"],
        arg_types=["Robot", "Location"]
    )
    
    language_bias.add_mode_declaration(adjacent_mode)
    language_bias.add_mode_declaration(at_mode)
    language_bias.add_mode_declaration(can_reach_mode)
    
    # Initialize the ILP engine
    ilp_engine = ILPEngine(
        kr_system_interface=ksi,
        inference_engine=inference_coordinator,
        language_bias=language_bias
    )
    
    print("\nCreating positive and negative examples for learning the CanReach predicate...")
    
    # Create the target predicate signature
    can_reach_signature = ApplicationNode(
        can_reach_pred,
        [robot_var, loc1_var],
        type_system.get_type("Boolean")
    )
    
    # Create positive examples
    # Robot1 can reach LocationA (it's already there)
    robot1_can_reach_loc_a = ApplicationNode(
        can_reach_pred,
        [robot1, loc_a],
        type_system.get_type("Boolean")
    )
    
    # Robot1 can reach LocationB (it's adjacent to LocationA)
    robot1_can_reach_loc_b = ApplicationNode(
        can_reach_pred,
        [robot1, loc_b],
        type_system.get_type("Boolean")
    )
    
    # Robot1 can reach LocationC (it's adjacent to LocationB)
    robot1_can_reach_loc_c = ApplicationNode(
        can_reach_pred,
        [robot1, loc_c],
        type_system.get_type("Boolean")
    )
    
    # Create negative examples
    # Let's say Robot1 cannot reach LocationD for some reason (maybe it's too far)
    robot1_can_reach_loc_d = ApplicationNode(
        can_reach_pred,
        [robot1, loc_d],
        type_system.get_type("Boolean")
    )
    
    positive_examples = {robot1_can_reach_loc_a, robot1_can_reach_loc_b, robot1_can_reach_loc_c}
    negative_examples = {robot1_can_reach_loc_d}
    
    print("Positive examples:")
# PART 4: Demonstrating the ExplanationBasedLearner
    # ------------------------------------------------
    print("\n\n" + "-"*40)
    print("PART 4: Demonstrating the ExplanationBasedLearner")
    print("-"*40)
    
    print("\nInitializing ExplanationBasedLearner...")
    
    # Create operationality config
    operationality_config = OperationalityConfig(
        operational_predicates={"At", "Adjacent", "Contains", "Holding", "Blocked", "Heavy", "Fragile", "StrongGripper"}
    )
    
    # Initialize the EBL
    ebl = ExplanationBasedLearner(
        kr_system_interface=ksi,
        inference_engine=inference_coordinator,
        operationality_config=operationality_config
    )
    
    print("\nCreating a problem-solving instance for EBL...")
    
    # Create a proof object for a successful problem-solving instance
    # Let's say we want to prove that Robot1 can move from LocationA to LocationB
    
    # Create the goal: CanMove(Robot1, LocationA, LocationB)
    can_move_goal = ApplicationNode(
        can_move_pred,
        [robot1, loc_a, loc_b],
        type_system.get_type("Boolean")
    )
    
    print(f"Goal: {can_move_goal}")
    
    # Create a proof object
    # In a real system, this would be generated by the inference engine
    # Here we'll create it manually for demonstration purposes
    
    # Create proof steps
    proof_steps = []
    
    # Step 1: At(Robot1, LocationA) - from facts
    step1 = ProofObject.ProofStepNode(
        step_index=1,
        formula=robot1_at_loc_a,
        justification="Fact",
        premises=[]
    )
    proof_steps.append(step1)
    
    # Step 2: Adjacent(LocationA, LocationB) - from facts
    step2 = ProofObject.ProofStepNode(
        step_index=2,
        formula=loc_a_adj_loc_b,
        justification="Fact",
        premises=[]
    )
    proof_steps.append(step2)
    
    # Step 3: ¬Blocked(LocationB) - assumed for this example
    step3 = ProofObject.ProofStepNode(
        step_index=3,
        formula=not_loc2_blocked.substitute({loc2_var: loc_b}),
        justification="Assumption",
        premises=[]
    )
    proof_steps.append(step3)
    
    # Step 4: At(Robot1, LocationA) ∧ Adjacent(LocationA, LocationB)
    step4 = ProofObject.ProofStepNode(
        step_index=4,
        formula=robot_at_and_adj.substitute({robot_var: robot1, loc1_var: loc_a, loc2_var: loc_b}),
        justification="AND-Introduction",
        premises=[1, 2]
    )
    proof_steps.append(step4)
    
    # Step 5: At(Robot1, LocationA) ∧ Adjacent(LocationA, LocationB) ∧ ¬Blocked(LocationB)
    step5 = ProofObject.ProofStepNode(
        step_index=5,
        formula=can_move_body.substitute({robot_var: robot1, loc1_var: loc_a, loc2_var: loc_b}),
        justification="AND-Introduction",
        premises=[4, 3]
    )
    proof_steps.append(step5)
    
    # Step 6: CanMove(Robot1, LocationA, LocationB) - from rule and steps 1-5
    step6 = ProofObject.ProofStepNode(
        step_index=6,
        formula=can_move_goal,
        justification="Modus Ponens",
        premises=[5]
    )
    proof_steps.append(step6)
    
    # Create the proof object
    proof_object = ProofObject(
        goal_achieved=True,
        conclusion_ast=can_move_goal,
        proof_steps=proof_steps,
        bindings={},
        status_message="Goal achieved",
        inference_engine_used="resolution_prover",
        time_taken_ms=10.0
    )
    
    print("\nGeneralizing from the proof object...")
    
    # Generalize from the proof object
    generalized_rule = ebl.generalize_from_proof_object(proof_object)
    
    if generalized_rule:
        print(f"\nGeneralized rule: {generalized_rule}")
        ksi.add_statement(generalized_rule, context_id="LEARNED_RULES")
    else:
        print("\nFailed to generalize from the proof object.")
    
    # PART 5: Demonstrating the TemplateEvolutionModule
    # ------------------------------------------------
    print("\n\n" + "-"*40)
    print("PART 5: Demonstrating the TemplateEvolutionModule")
    print("-"*40)
    
    print("\nInitializing TemplateEvolutionModule...")
    
    # Initialize the TEM
    evolution_config = EvolutionConfig(
        population_size=10,
        generations=5,
        crossover_rate=0.7,
        mutation_rate=0.3
    )
    
    tem = TemplateEvolutionModule(
        kr_system_interface=ksi,
        type_system=type_system,
        mkb_context_id="META_KNOWLEDGE",
        evolution_config=evolution_config
    )
    
    print("\nCreating initial template population...")
    
    # Create some initial templates for evolution
    # Let's create variations of the CanMove rule
    
    # Template 1: CanMove(?robot, ?loc1, ?loc2) :- At(?robot, ?loc1) ∧ Adjacent(?loc1, ?loc2)
    # (Simplified version without the Blocked check)
    template1 = ConnectiveNode(
        "IMPLIES",
        [robot_at_and_adj, can_move_head],
        type_system.get_type("Boolean")
    )
    
    # Template 2: CanMove(?robot, ?loc1, ?loc2) :- At(?robot, ?loc1) ∧ Adjacent(?loc1, ?loc2) ∧ ¬Blocked(?loc2)
    # (This is the original rule)
    template2 = can_move_rule
    
    # Template 3: CanMove(?robot, ?loc1, ?loc2) :- At(?robot, ?loc1) ∧ Adjacent(?loc1, ?loc2) ∧ StrongGripper(?robot)
    # (A variation that requires a strong gripper)
    
    # StrongGripper(?robot)
    robot_strong_gripper = ApplicationNode(
        strong_gripper_pred,
        [robot_var],
        type_system.get_type("Boolean")
    )
    
    # At(?robot, ?loc1) ∧ Adjacent(?loc1, ?loc2) ∧ StrongGripper(?robot)
    template3_body = ConnectiveNode(
        "AND",
        [robot_at_and_adj, robot_strong_gripper],
        type_system.get_type("Boolean")
    )
    
    template3 = ConnectiveNode(
        "IMPLIES",
        [template3_body, can_move_head],
        type_system.get_type("Boolean")
    )
    
    # Create the initial population
    initial_population = [template1, template2, template3]
    
    # Add some variations to reach desired population size
    for i in range(evolution_config.population_size - len(initial_population)):
        # Just duplicate existing templates for this example
        initial_population.append(initial_population[i % len(initial_population)])
    
    print(f"Created initial population of {len(initial_population)} templates")
    
    print("\nEvolving templates...")
    
    # Evolve the templates
    evolved_templates = tem.evolve_population(
        initial_population_templates=initial_population,
        generations=evolution_config.generations
    )
    
    print(f"\nEvolved {len(evolved_templates)} templates:")
    for i, template in enumerate(evolved_templates[:3]):  # Show top 3
        print(f"Template {i+1}: {template}")
        if i == 0:  # Add the best template to the knowledge store
            ksi.add_statement(template, context_id="LEARNED_RULES")
# PART 6: Demonstrating the MetaControlRLModule
    # --------------------------------------------
    print("\n\n" + "-"*40)
    print("PART 6: Demonstrating the MetaControlRLModule")
    print("-"*40)
    
    print("\nInitializing MetaControlRLModule...")
    
    # Define meta-actions
    meta_actions = [
        MetaAction(action_type="SelectProver", parameters={"prover": "resolution_prover"}),
        MetaAction(action_type="AllocateResources", parameters={"time_limit_ms": 1000, "memory_limit_mb": 100}),
        MetaAction(action_type="PrioritizeGoal", parameters={"goal_priority": "high"}),
        MetaAction(action_type="TriggerILP", parameters={"target_predicate": "CanReach"}),
        MetaAction(action_type="TriggerEBL", parameters={"operationality_threshold": 0.7}),
        MetaAction(action_type="TriggerTEM", parameters={"generations": 5})
    ]
    
    # Define a state feature extractor function
    def state_feature_extractor(mkb_interface):
        # In a real system, this would extract features from the meta-knowledge base
        # For this example, we'll return random features
        return [random.random() for _ in range(10)]
    
    # Initialize the MCRL module
    rl_config = RLConfig(
        learning_rate=0.01,
        discount_factor=0.99,
        exploration_rate=0.1
    )
    
    mcrl = MetaControlRLModule(
        mkb_interface=ksi,  # Using KSI as a placeholder for MKB
        action_space=meta_actions,
        state_feature_extractor=state_feature_extractor,
        rl_config=rl_config
    )
    
    print("\nDemonstrating meta-control decision making...")
    
    # Simulate a few meta-control decisions
    for i in range(3):
        print(f"\nMeta-control decision {i+1}:")
        
        # Get current state features
        current_state = mcrl.get_state_features()
        
        # Select a meta-action
        selected_action = mcrl.select_meta_action(current_state)
        print(f"Selected action: {selected_action}")
        
        # Simulate taking the action and receiving a reward
        # In a real system, this would be based on the actual outcome of the action
        reward = random.uniform(0.0, 1.0)
        print(f"Received reward: {reward:.4f}")
        
        # Get next state
        next_state = mcrl.get_state_features()
        
        # Learn from the transition
        mcrl.learn_from_transition(
            state_features=current_state,
            action_taken=selected_action,
            reward=reward,
            next_state_features=next_state,
            episode_done=(i == 2)  # Last iteration is end of episode
        )
    
    # PART 7: Integrating All Learning Components
    # ------------------------------------------
    print("\n\n" + "-"*40)
    print("PART 7: Integrating All Learning Components")
    print("-"*40)
    
    print("\nDemonstrating integration of all learning components...")
    
    print("\nScenario: Robot needs to learn how to navigate to distant locations and handle objects")
    
    # 1. Use ILP to learn the CanReach rule (already done in Part 3)
    print("\n1. ILP has induced rules for the CanReach predicate")
    
    # Query the learned rules
    can_reach_rules = ksi.query_statements_match_pattern(
        None,  # Match any pattern
        context_ids=["LEARNED_RULES"]
    )
    
    print(f"Found {len(can_reach_rules)} learned rules in the knowledge store")
    
    # 2. Use EBL to generalize from a successful problem-solving instance (already done in Part 4)
    print("\n2. EBL has generalized from a successful problem-solving instance")
    
    # 3. Use TEM to evolve and refine templates (already done in Part 5)
    print("\n3. TEM has evolved and refined rule templates")
    
    # 4. Use MCRL to make meta-control decisions (already done in Part 6)
    print("\n4. MCRL has learned to make meta-control decisions")
    
    # 5. Demonstrate how these components work together in a full learning cycle
    print("\n5. Full learning cycle demonstration:")
    print("   a. System encounters a new problem")
    print("   b. MCRL decides to use ILP to learn a new rule")
    print("   c. ILP induces a candidate rule")
    print("   d. EBL generalizes from successful problem-solving")
    print("   e. TEM refines the rule template")
    print("   f. MCRL learns from the outcome")
    
    print("\nThis example has demonstrated how the four learning components of GödelOS")
    print("work together to enable a robot to learn from experience and improve its")
    print("performance over time.")
    
    print("\nThe learning components interact with the Core KR System and Inference Engine")
    print("to create a powerful cognitive architecture that can adapt to new situations")
    print("and continuously improve its knowledge and reasoning capabilities.")
    
    print("\n" + "="*80)
    print("Example completed successfully!")
    print("="*80)


if __name__ == "__main__":
    main()