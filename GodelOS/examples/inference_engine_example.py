"""
Comprehensive Example for GödelOS Inference Engine Architecture

This example demonstrates the integration and usage of all five provers in the GödelOS
Inference Engine Architecture:

1. ResolutionProver: For First-Order Logic (FOL) and propositional logic
2. ModalTableauProver: For modal logics
3. SMTInterface: For problems involving theories like arithmetic
4. ConstraintLogicProgrammingModule (CLP): For constraint satisfaction problems
5. AnalogicalReasoningEngine (ARE): For analogical reasoning

The example tells a coherent story about a smart home system that uses different
reasoning approaches to solve various problems:
- Basic logical reasoning about device states and rules (FOL)
- Reasoning about permissions and necessities (Modal Logic)
- Arithmetic reasoning for energy optimization (SMT)
- Constraint satisfaction for scheduling (CLP)
- Analogical reasoning for transferring knowledge between domains (ARE)

The example demonstrates how the InferenceCoordinator selects the appropriate prover
for each type of goal, and how the different provers work together to solve complex
problems.
"""

import sys
import os
import logging
from typing import Dict, List, Optional, Set, Tuple, Any

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import (
    ConstantNode, VariableNode, ApplicationNode, ConnectiveNode, 
    QuantifierNode, ModalOpNode
)
from godelOS.core_kr.formal_logic_parser.parser import FormalLogicParser
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.core_kr.type_system.types import AtomicType

from godelOS.inference_engine.coordinator import InferenceCoordinator, StrategyKnowledgeBase
from godelOS.inference_engine.base_prover import BaseProver, ResourceLimits
from godelOS.inference_engine.proof_object import ProofObject
from godelOS.inference_engine.resolution_prover import ResolutionProver
from godelOS.inference_engine.modal_tableau_prover import ModalTableauProver, ModalSystem
from godelOS.inference_engine.smt_interface import SMTInterface, SMTSolverConfiguration
from godelOS.inference_engine.clp_module import CLPModule
from godelOS.inference_engine.analogical_reasoning_engine import AnalogicalReasoningEngine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """
    Run the comprehensive example demonstrating all Inference Engine components.
    """
    print("\n" + "="*80)
    print("GödelOS Inference Engine Architecture - Comprehensive Example")
    print("="*80)

    # PART 1: Setting up the Core Components
    # --------------------------------------
    print("\n\n" + "-"*40)
    print("PART 1: Setting up the Core Components")
    print("-"*40)
    
    print("\nInitializing Type System...")
    type_system = TypeSystemManager()
    
    # Define domain-specific types for our smart home system
    device_type = type_system.define_atomic_type("Device", ["Entity"])
    room_type = type_system.define_atomic_type("Room", ["Entity"])
    user_type = type_system.define_atomic_type("User", ["Entity"])
    time_type = type_system.define_atomic_type("Time", ["Entity"])
    energy_type = type_system.define_atomic_type("Energy", ["Entity"])
    
    # Define predicates and functions
    print("\nDefining predicates and functions...")
    type_system.define_function_signature("IsOn", ["Device"], "Boolean")
    type_system.define_function_signature("IsOff", ["Device"], "Boolean")
    type_system.define_function_signature("IsIn", ["Device", "Room"], "Boolean")
    type_system.define_function_signature("IsUserIn", ["User", "Room"], "Boolean")
    type_system.define_function_signature("HasAccess", ["User", "Device"], "Boolean")
    type_system.define_function_signature("CanControl", ["User", "Device"], "Boolean")
    type_system.define_function_signature("EnergyConsumption", ["Device"], "Integer")
    type_system.define_function_signature("TotalEnergyConsumption", [], "Integer")
    type_system.define_function_signature("ScheduledAt", ["Device", "Time"], "Boolean")
    type_system.define_function_signature("Temperature", ["Room"], "Integer")
    type_system.define_function_signature("SetTemperature", ["Room", "Integer"], "Boolean")
    
    # Initialize other core components
    print("\nInitializing other core components...")
    parser = FormalLogicParser(type_system)
    unification_engine = UnificationEngine(type_system)
    ksi = KnowledgeStoreInterface(type_system)
    
# PART 2: Creating the Knowledge Base
    # ----------------------------------
    print("\n\n" + "-"*40)
    print("PART 2: Creating the Knowledge Base")
    print("-"*40)
    
    print("\nCreating contexts for different types of knowledge...")
    ksi.create_context("DEVICES", context_type="facts")
    ksi.create_context("RULES", context_type="rules")
    ksi.create_context("MODAL_KNOWLEDGE", context_type="modal")
    ksi.create_context("ARITHMETIC", context_type="arithmetic")
    ksi.create_context("CONSTRAINTS", context_type="constraints")
    ksi.create_context("SOURCE_DOMAIN", context_type="analogical")
    ksi.create_context("TARGET_DOMAIN", context_type="analogical")
    
    print("\nCreating AST nodes for devices and rooms...")
    # Create constants for devices, rooms, and users
    living_room = ConstantNode("LivingRoom", room_type)
    kitchen = ConstantNode("Kitchen", room_type)
    bedroom = ConstantNode("Bedroom", room_type)
    
    tv = ConstantNode("TV", device_type)
    lights = ConstantNode("Lights", device_type)
    thermostat = ConstantNode("Thermostat", device_type)
    oven = ConstantNode("Oven", device_type)
    
    alice = ConstantNode("Alice", user_type)
    bob = ConstantNode("Bob", user_type)
    
    # Create predicate constants
    is_on_pred = ConstantNode("IsOn", type_system.get_type("IsOn"))
    is_off_pred = ConstantNode("IsOff", type_system.get_type("IsOff"))
    is_in_pred = ConstantNode("IsIn", type_system.get_type("IsIn"))
    is_user_in_pred = ConstantNode("IsUserIn", type_system.get_type("IsUserIn"))
    has_access_pred = ConstantNode("HasAccess", type_system.get_type("HasAccess"))
    can_control_pred = ConstantNode("CanControl", type_system.get_type("CanControl"))
    energy_consumption_pred = ConstantNode("EnergyConsumption", type_system.get_type("EnergyConsumption"))
    scheduled_at_pred = ConstantNode("ScheduledAt", type_system.get_type("ScheduledAt"))
    temperature_pred = ConstantNode("Temperature", type_system.get_type("Temperature"))
    
    # Create applications for facts about device locations
    tv_in_living_room = ApplicationNode(
        is_in_pred, 
        [tv, living_room], 
        type_system.get_type("Boolean")
    )
    
    lights_in_living_room = ApplicationNode(
        is_in_pred, 
        [lights, living_room], 
        type_system.get_type("Boolean")
    )
    
    thermostat_in_living_room = ApplicationNode(
        is_in_pred, 
        [thermostat, living_room], 
        type_system.get_type("Boolean")
    )
    
    oven_in_kitchen = ApplicationNode(
        is_in_pred, 
        [oven, kitchen], 
        type_system.get_type("Boolean")
    )
    
    # Create applications for facts about device states
    tv_is_on = ApplicationNode(
        is_on_pred, 
        [tv], 
        type_system.get_type("Boolean")
    )
    
    lights_are_on = ApplicationNode(
        is_on_pred, 
        [lights], 
        type_system.get_type("Boolean")
    )
    
    oven_is_off = ApplicationNode(
        is_off_pred, 
        [oven], 
        type_system.get_type("Boolean")
    )
    
    # Create applications for facts about user locations
    alice_in_living_room = ApplicationNode(
        is_user_in_pred, 
        [alice, living_room], 
        type_system.get_type("Boolean")
    )
    
    bob_in_kitchen = ApplicationNode(
        is_user_in_pred, 
        [bob, kitchen], 
        type_system.get_type("Boolean")
    )
    
    # Create applications for facts about user access
    alice_has_access_to_tv = ApplicationNode(
        has_access_pred, 
        [alice, tv], 
        type_system.get_type("Boolean")
    )
    
    bob_has_access_to_oven = ApplicationNode(
        has_access_pred, 
        [bob, oven], 
        type_system.get_type("Boolean")
    )
    
    # Add facts to the knowledge store
    print("\nAdding facts to the knowledge store...")
    ksi.add_statement(tv_in_living_room, context_id="DEVICES")
    ksi.add_statement(lights_in_living_room, context_id="DEVICES")
    ksi.add_statement(thermostat_in_living_room, context_id="DEVICES")
    ksi.add_statement(oven_in_kitchen, context_id="DEVICES")
    ksi.add_statement(tv_is_on, context_id="DEVICES")
    ksi.add_statement(lights_are_on, context_id="DEVICES")
    ksi.add_statement(oven_is_off, context_id="DEVICES")
    ksi.add_statement(alice_in_living_room, context_id="DEVICES")
    ksi.add_statement(bob_in_kitchen, context_id="DEVICES")
    ksi.add_statement(alice_has_access_to_tv, context_id="DEVICES")
    ksi.add_statement(bob_has_access_to_oven, context_id="DEVICES")
    
    # Create rules
    print("\nCreating rules...")
    
    # Rule 1: If a user is in the same room as a device and has access to it, they can control it
    # ∀?user ∀?device ∀?room. (IsUserIn(?user, ?room) ∧ IsIn(?device, ?room) ∧ HasAccess(?user, ?device)) → CanControl(?user, ?device)
    
    # Create variables for the rule
    user_var = VariableNode("?user", 1, user_type)
    device_var = VariableNode("?device", 2, device_type)
    room_var = VariableNode("?room", 3, room_type)
    
    # Create the antecedent parts
    user_in_room = ApplicationNode(
        is_user_in_pred, 
        [user_var, room_var], 
        type_system.get_type("Boolean")
    )
    
    device_in_room = ApplicationNode(
        is_in_pred, 
        [device_var, room_var], 
        type_system.get_type("Boolean")
    )
    
    user_has_access = ApplicationNode(
        has_access_pred, 
        [user_var, device_var], 
        type_system.get_type("Boolean")
    )
    
    # Combine the antecedent parts with AND
    antecedent1 = ConnectiveNode(
        "AND",
        [user_in_room, device_in_room],
        type_system.get_type("Boolean")
    )
    
    antecedent = ConnectiveNode(
        "AND",
        [antecedent1, user_has_access],
        type_system.get_type("Boolean")
    )
    
    # Create the consequent
    consequent = ApplicationNode(
        can_control_pred,
        [user_var, device_var],
        type_system.get_type("Boolean")
    )
    
    # Create the implication
    implication = ConnectiveNode(
        "IMPLIES",
        [antecedent, consequent],
        type_system.get_type("Boolean")
    )
    
    # Create the quantified rule
    control_rule = QuantifierNode(
        "FORALL",
        [user_var, device_var, room_var],
        implication,
        type_system.get_type("Boolean")
    )
    
    # Add the rule to the knowledge store
    ksi.add_statement(control_rule, context_id="RULES")
# PART 3: Setting up the Inference Engine
    # --------------------------------------
    print("\n\n" + "-"*40)
    print("PART 3: Setting up the Inference Engine")
    print("-"*40)
    
    print("\nInitializing provers...")
    
    # Initialize the Resolution Prover
    resolution_prover = ResolutionProver(ksi, unification_engine)
    
    # Initialize the Modal Tableau Prover
    modal_prover = ModalTableauProver(ksi, type_system)
    
    # Initialize the SMT Interface
    # In a real implementation, we would configure actual SMT solvers
    smt_config = SMTSolverConfiguration("Z3", "z3", ["-smt2"])
    smt_interface = SMTInterface([smt_config], type_system)
    
    # Initialize the Constraint Logic Programming Module
    clp_module = CLPModule(ksi, unification_engine)
    
    # Initialize the Analogical Reasoning Engine
    are = AnalogicalReasoningEngine(ksi)
    
    # Create a dictionary of provers
    provers = {
        "resolution_prover": resolution_prover,
        "modal_tableau_prover": modal_prover,
        "smt_interface": smt_interface,
        "clp_module": clp_module,
        "analogical_reasoning_engine": are
    }
    
    # Initialize the Inference Coordinator
    print("\nInitializing Inference Coordinator...")
    coordinator = InferenceCoordinator(ksi, provers)
    
    # PART 4: Demonstrating the Resolution Prover (FOL)
    # ------------------------------------------------
    print("\n\n" + "-"*40)
    print("PART 4: Demonstrating the Resolution Prover (FOL)")
    print("-"*40)
    
    print("\nCreating a FOL query: Can Alice control the TV?")
    
    # Create the query: CanControl(Alice, TV)
    alice_control_tv_query = ApplicationNode(
        can_control_pred,
        [alice, tv],
        type_system.get_type("Boolean")
    )
    
    # Get all relevant context for the query
    fol_context = ksi.query_all_statements(context_ids=["DEVICES", "RULES"])
    
    print("\nSubmitting the query to the Inference Coordinator...")
    fol_result = coordinator.submit_goal(alice_control_tv_query, set(fol_context))
    
    print("\nResolution Prover Result:")
# PART 5: Demonstrating the Modal Tableau Prover
    # ---------------------------------------------
    print("\n\n" + "-"*40)
    print("PART 5: Demonstrating the Modal Tableau Prover")
    print("-"*40)
    
    print("\nCreating modal knowledge...")
    
    # Create modal operators for necessity and possibility
    necessary_op = ConstantNode("NECESSARY", type_system.get_type("Entity"))
    possible_op = ConstantNode("POSSIBLE", type_system.get_type("Entity"))
    
    # Create modal knowledge: It is necessary that if a device is on, it consumes energy
    # □(∀?device. IsOn(?device) → EnergyConsumption(?device) > 0)
    
    # Create the inner formula: IsOn(?device) → EnergyConsumption(?device) > 0
    device_var = VariableNode("?device", 4, device_type)
    
    # IsOn(?device)
    device_is_on = ApplicationNode(
        is_on_pred,
        [device_var],
        type_system.get_type("Boolean")
    )
    
    # EnergyConsumption(?device)
    device_energy = ApplicationNode(
        energy_consumption_pred,
        [device_var],
        type_system.get_type("Integer")
    )
    
    # Create a constant for zero
    zero = ConstantNode("0", type_system.get_type("Integer"))
    
    # Create the comparison: EnergyConsumption(?device) > 0
    greater_than_op = ConstantNode(">", type_system.get_type("Entity"))
    energy_greater_than_zero = ApplicationNode(
        greater_than_op,
        [device_energy, zero],
        type_system.get_type("Boolean")
    )
    
    # Create the implication: IsOn(?device) → EnergyConsumption(?device) > 0
    energy_implication = ConnectiveNode(
        "IMPLIES",
        [device_is_on, energy_greater_than_zero],
        type_system.get_type("Boolean")
    )
    
    # Quantify over devices: ∀?device. IsOn(?device) → EnergyConsumption(?device) > 0
    quantified_energy_rule = QuantifierNode(
        "FORALL",
        [device_var],
        energy_implication,
        type_system.get_type("Boolean")
    )
    
    # Create the modal formula: □(∀?device. IsOn(?device) → EnergyConsumption(?device) > 0)
    necessary_energy_rule = ModalOpNode(
        "NECESSARY",
        None,  # No agent or world specified
        quantified_energy_rule,
        type_system.get_type("Boolean")
    )
    
    # Add the modal knowledge to the knowledge store
    ksi.add_statement(necessary_energy_rule, context_id="MODAL_KNOWLEDGE")
    
    # Create another modal knowledge: It is possible that all devices are off
    # ◇(∀?device. IsOff(?device))
    
    # Create the inner formula: ∀?device. IsOff(?device)
    device_var = VariableNode("?device", 5, device_type)
    
    # IsOff(?device)
    device_is_off = ApplicationNode(
        is_off_pred,
        [device_var],
        type_system.get_type("Boolean")
    )
    
    # Quantify over devices: ∀?device. IsOff(?device)
    all_devices_off = QuantifierNode(
        "FORALL",
        [device_var],
        device_is_off,
        type_system.get_type("Boolean")
    )
    
    # Create the modal formula: ◇(∀?device. IsOff(?device))
    possible_all_off = ModalOpNode(
        "POSSIBLE",
        None,  # No agent or world specified
        all_devices_off,
        type_system.get_type("Boolean")
    )
    
    # Add the modal knowledge to the knowledge store
    ksi.add_statement(possible_all_off, context_id="MODAL_KNOWLEDGE")
    
    print("\nCreating a modal query: Is it necessary that the TV consumes energy (since it is on)?")
    
    # Create the query: □(EnergyConsumption(TV) > 0)
    tv_energy = ApplicationNode(
        energy_consumption_pred,
        [tv],
        type_system.get_type("Integer")
    )
    
    tv_energy_gt_zero = ApplicationNode(
        greater_than_op,
        [tv_energy, zero],
        type_system.get_type("Boolean")
    )
    
    necessary_tv_energy = ModalOpNode(
        "NECESSARY",
        None,
        tv_energy_gt_zero,
        type_system.get_type("Boolean")
    )
    
    # Get all relevant context for the query
    modal_context = ksi.query_all_statements(context_ids=["DEVICES", "MODAL_KNOWLEDGE"])
    
    print("\nSubmitting the query to the Inference Coordinator...")
    modal_result = coordinator.submit_goal(necessary_tv_energy, set(modal_context))
    
    print("\nModal Tableau Prover Result:")
    print(f"Goal achieved: {modal_result.goal_achieved}")
    print(f"Status message: {modal_result.status_message}")
    print(f"Inference engine used: {modal_result.inference_engine_used}")
    print(f"Time taken: {modal_result.time_taken_ms:.2f} ms")
    
    # PART 6: Demonstrating the SMT Interface
    # --------------------------------------
    print("\n\n" + "-"*40)
    print("PART 6: Demonstrating the SMT Interface")
    print("-"*40)
    
    print("\nCreating arithmetic knowledge...")
    
    # Create energy consumption facts for devices
    # EnergyConsumption(TV) = 100
    tv_energy_val = ConstantNode("100", type_system.get_type("Integer"))
    equals_op = ConstantNode("=", type_system.get_type("Entity"))
    
    tv_energy_consumption = ApplicationNode(
        equals_op,
        [tv_energy, tv_energy_val],
        type_system.get_type("Boolean")
    )
    
    # EnergyConsumption(Lights) = 50
    lights_energy = ApplicationNode(
        energy_consumption_pred,
        [lights],
        type_system.get_type("Integer")
    )
    
    lights_energy_val = ConstantNode("50", type_system.get_type("Integer"))
    
    lights_energy_consumption = ApplicationNode(
        equals_op,
        [lights_energy, lights_energy_val],
        type_system.get_type("Boolean")
    )
    
    # Add the arithmetic knowledge to the knowledge store
    ksi.add_statement(tv_energy_consumption, context_id="ARITHMETIC")
    ksi.add_statement(lights_energy_consumption, context_id="ARITHMETIC")
    
    print("\nCreating an arithmetic query: Is the total energy consumption of on devices > 125?")
    
    # Create a predicate for total energy consumption
    total_energy_pred = ConstantNode("TotalEnergyConsumption", type_system.get_type("TotalEnergyConsumption"))
    
    # Create the total energy consumption term
    total_energy = ApplicationNode(
        total_energy_pred,
        [],
        type_system.get_type("Integer")
    )
    
    # Create the constant for comparison
    threshold = ConstantNode("125", type_system.get_type("Integer"))
    
    # Create the comparison: TotalEnergyConsumption() > 125
    total_energy_gt_threshold = ApplicationNode(
        greater_than_op,
        [total_energy, threshold],
        type_system.get_type("Boolean")
    )
    
    # Create the definition of total energy consumption
    # TotalEnergyConsumption() = EnergyConsumption(TV) + EnergyConsumption(Lights)
    plus_op = ConstantNode("+", type_system.get_type("Entity"))
    
    sum_energy = ApplicationNode(
        plus_op,
        [tv_energy, lights_energy],
        type_system.get_type("Integer")
    )
    
    total_energy_def = ApplicationNode(
        equals_op,
        [total_energy, sum_energy],
        type_system.get_type("Boolean")
    )
    
    # Add the definition to the knowledge store
    ksi.add_statement(total_energy_def, context_id="ARITHMETIC")
    
# PART 7: Demonstrating the Constraint Logic Programming Module
    # -----------------------------------------------------------
    print("\n\n" + "-"*40)
    print("PART 7: Demonstrating the Constraint Logic Programming Module")
    print("-"*40)
    
    print("\nCreating constraint knowledge for device scheduling...")
    
    # Create time constants
    time_8am = ConstantNode("8AM", time_type)
    time_12pm = ConstantNode("12PM", time_type)
    time_6pm = ConstantNode("6PM", time_type)
    
    # Create scheduling constraints
    
    # Constraint 1: AllDifferent - Devices should be scheduled at different times
    all_different_op = ConstantNode("AllDifferent", type_system.get_type("Entity"))
    
    # Create scheduling variables for each device
    tv_time_var = VariableNode("?tv_time", 6, time_type)
    lights_time_var = VariableNode("?lights_time", 7, time_type)
    oven_time_var = VariableNode("?oven_time", 8, time_type)
    
    # Create the AllDifferent constraint
    all_different_constraint = ApplicationNode(
        all_different_op,
        [tv_time_var, lights_time_var, oven_time_var],
        type_system.get_type("Boolean")
    )
    
    # Constraint 2: Domain constraints - Times must be one of 8AM, 12PM, or 6PM
    in_op = ConstantNode("In", type_system.get_type("Entity"))
    
    # Create domain sets
    domain_set = [time_8am, time_12pm, time_6pm]
    
    # Create domain constraints for each variable
    tv_domain_constraint = ApplicationNode(
        in_op,
        [tv_time_var] + domain_set,
        type_system.get_type("Boolean")
    )
    
    lights_domain_constraint = ApplicationNode(
        in_op,
        [lights_time_var] + domain_set,
        type_system.get_type("Boolean")
    )
    
    oven_domain_constraint = ApplicationNode(
        in_op,
        [oven_time_var] + domain_set,
        type_system.get_type("Boolean")
    )
    
    # Add constraints to the knowledge store
    ksi.add_statement(all_different_constraint, context_id="CONSTRAINTS")
    ksi.add_statement(tv_domain_constraint, context_id="CONSTRAINTS")
    ksi.add_statement(lights_domain_constraint, context_id="CONSTRAINTS")
    ksi.add_statement(oven_domain_constraint, context_id="CONSTRAINTS")
    
    print("\nCreating a constraint query: Find a valid schedule for the devices")
    
    # Create a query to find a valid schedule
    # ScheduledAt(TV, ?tv_time) ∧ ScheduledAt(Lights, ?lights_time) ∧ ScheduledAt(Oven, ?oven_time)
    tv_scheduled = ApplicationNode(
        scheduled_at_pred,
        [tv, tv_time_var],
        type_system.get_type("Boolean")
    )
    
    lights_scheduled = ApplicationNode(
        scheduled_at_pred,
        [lights, lights_time_var],
        type_system.get_type("Boolean")
    )
    
    oven_scheduled = ApplicationNode(
        scheduled_at_pred,
        [oven, oven_time_var],
        type_system.get_type("Boolean")
    )
    
    # Combine the scheduling goals
    scheduling_query1 = ConnectiveNode(
        "AND",
        [tv_scheduled, lights_scheduled],
        type_system.get_type("Boolean")
    )
    
    scheduling_query = ConnectiveNode(
        "AND",
        [scheduling_query1, oven_scheduled],
        type_system.get_type("Boolean")
    )
    
    # Get all relevant context for the query
    constraint_context = ksi.query_all_statements(context_ids=["DEVICES", "CONSTRAINTS"])
    
    print("\nSubmitting the query to the Inference Coordinator...")
    constraint_result = coordinator.submit_goal(scheduling_query, set(constraint_context))
    
    print("\nConstraint Logic Programming Module Result:")
    print(f"Goal achieved: {constraint_result.goal_achieved}")
    print(f"Status message: {constraint_result.status_message}")
    print(f"Inference engine used: {constraint_result.inference_engine_used}")
    print(f"Time taken: {constraint_result.time_taken_ms:.2f} ms")
    
    if constraint_result.bindings:
        print("\nSolution found:")
        for var, value in constraint_result.bindings.items():
            if var.name == "?tv_time":
                print(f"  TV scheduled at: {value}")
            elif var.name == "?lights_time":
                print(f"  Lights scheduled at: {value}")
            elif var.name == "?oven_time":
                print(f"  Oven scheduled at: {value}")
    
    # PART 8: Demonstrating the Analogical Reasoning Engine
    # ---------------------------------------------------
    print("\n\n" + "-"*40)
    print("PART 8: Demonstrating the Analogical Reasoning Engine")
    print("-"*40)
    
    print("\nCreating source domain knowledge (home automation)...")
    
    # Create source domain facts about the smart home system
    # These are similar to what we've already defined
    
    # Create target domain knowledge (office automation)
    print("\nCreating target domain knowledge (office automation)...")
    
    # Create constants for the office domain
    office = ConstantNode("Office", room_type)
    conference_room = ConstantNode("ConferenceRoom", room_type)
    
    projector = ConstantNode("Projector", device_type)
    ac = ConstantNode("AC", device_type)
    coffee_machine = ConstantNode("CoffeeMachine", device_type)
    
    manager = ConstantNode("Manager", user_type)
    employee = ConstantNode("Employee", user_type)
    
    # Create facts for the office domain
    projector_in_conference = ApplicationNode(
        is_in_pred, 
        [projector, conference_room], 
        type_system.get_type("Boolean")
    )
    
    ac_in_office = ApplicationNode(
        is_in_pred, 
        [ac, office], 
        type_system.get_type("Boolean")
    )
    
    coffee_in_office = ApplicationNode(
        is_in_pred, 
        [coffee_machine, office], 
        type_system.get_type("Boolean")
    )
    
    # Add target domain facts to the knowledge store
    ksi.add_statement(projector_in_conference, context_id="TARGET_DOMAIN")
    ksi.add_statement(ac_in_office, context_id="TARGET_DOMAIN")
    ksi.add_statement(coffee_in_office, context_id="TARGET_DOMAIN")
    
    # Add some source domain facts to the knowledge store
    ksi.add_statement(tv_in_living_room, context_id="SOURCE_DOMAIN")
    ksi.add_statement(thermostat_in_living_room, context_id="SOURCE_DOMAIN")
    ksi.add_statement(oven_in_kitchen, context_id="SOURCE_DOMAIN")
    
    print("\nCreating an analogical reasoning query: Find mapping between home and office domains")
    
    # Create a query to find analogical mappings
    find_analogy_op = ConstantNode("FindAnalogy", type_system.get_type("Entity"))
    source_domain_id = ConstantNode("SOURCE_DOMAIN", type_system.get_type("Entity"))
    target_domain_id = ConstantNode("TARGET_DOMAIN", type_system.get_type("Entity"))
    
    find_analogy_query = ApplicationNode(
        find_analogy_op,
        [source_domain_id, target_domain_id],
        type_system.get_type("Boolean")
    )
    
    # Get all relevant context for the query
    analogical_context = ksi.query_all_statements(context_ids=["SOURCE_DOMAIN", "TARGET_DOMAIN"])
    
    print("\nSubmitting the query to the Inference Coordinator...")
    analogical_result = coordinator.submit_goal(find_analogy_query, set(analogical_context))
    
    print("\nAnalogical Reasoning Engine Result:")
    print(f"Goal achieved: {analogical_result.goal_achieved}")
    print(f"Status message: {analogical_result.status_message}")
    print(f"Inference engine used: {analogical_result.inference_engine_used}")
    print(f"Time taken: {analogical_result.time_taken_ms:.2f} ms")
    
    print("\nPotential analogical mappings:")
    print("  TV ↔ Projector (both are display devices)")
    print("  Thermostat ↔ AC (both control temperature)")
    print("  Oven ↔ Coffee Machine (both are kitchen/refreshment devices)")
    print("  Living Room ↔ Conference Room (both are gathering spaces)")
    print("  Kitchen ↔ Office (both are functional spaces)")
    
    # PART 9: Summary and Conclusion
    # ----------------------------
    print("\n\n" + "-"*40)
    print("PART 9: Summary and Conclusion")
    print("-"*40)
    
    print("\nThis example has demonstrated the integration and usage of all five provers")
    print("in the GödelOS Inference Engine Architecture:")
    print("  1. ResolutionProver: For First-Order Logic (FOL) reasoning")
    print("  2. ModalTableauProver: For modal logic reasoning")
    print("  3. SMTInterface: For arithmetic reasoning")
    print("  4. CLPModule: For constraint satisfaction problems")
    print("  5. AnalogicalReasoningEngine: For analogical reasoning")
    
    print("\nThe example showed how the InferenceCoordinator selects the appropriate prover")
    print("for each type of goal, and how the different provers work together to solve")
    print("complex problems in a smart home automation system.")


    # Get all relevant context for the query
    arithmetic_context = ksi.query_all_statements(context_ids=["DEVICES", "ARITHMETIC"])
    
    print("\nSubmitting the query to the Inference Coordinator...")
    arithmetic_result = coordinator.submit_goal(total_energy_gt_threshold, set(arithmetic_context))
    
    print("\nSMT Interface Result:")
    print(f"Goal achieved: {arithmetic_result.goal_achieved}")
    print(f"Status message: {arithmetic_result.status_message}")
    print(f"Inference engine used: {arithmetic_result.inference_engine_used}")
    print(f"Time taken: {arithmetic_result.time_taken_ms:.2f} ms")
    
    # Print FOL result again for demonstration
    print(f"Goal achieved: {fol_result.goal_achieved}")
    print(f"Status message: {fol_result.status_message}")
    print(f"Inference engine used: {fol_result.inference_engine_used}")
    print(f"Time taken: {fol_result.time_taken_ms:.2f} ms")
    
    if fol_result.proof_steps:
        print("\nProof steps:")
        for i, step in enumerate(fol_result.proof_steps):
            print(f"  Step {i+1}: {step.rule_name} - {step.explanation}")

if __name__ == "__main__":
    main()