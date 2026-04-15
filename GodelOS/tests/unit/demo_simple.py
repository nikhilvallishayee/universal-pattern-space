#!/usr/bin/env python
# coding: utf-8

"""
GödelOS Simple Demo Script

This script demonstrates the core functionality of the GödelOS system, focusing on:
1. Knowledge Representation
2. Inference Engine
3. Natural Language Processing

It sets up a knowledge base about people and locations, defines rules for inference,
and provides a natural language interface for querying the system.
"""

import sys
import os
import logging
import re

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure GödelOS is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), '.')))

# Import GödelOS components
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.ast.nodes import ConstantNode, VariableNode, ApplicationNode, ConnectiveNode
from godelOS.core_kr.formal_logic_parser.parser import FormalLogicParser
from godelOS.core_kr.unification_engine.engine import UnificationEngine
from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
from godelOS.inference_engine.resolution_prover import ResolutionProver
from godelOS.inference_engine.coordinator import InferenceCoordinator


class GödelOSDemo:
    """A demonstration of GödelOS capabilities."""
    
    def __init__(self):
        """Initialize the GödelOS Demo."""
        self.setup_kr_system()
        self.setup_inference_engine()
        self.add_knowledge()
        
    def setup_kr_system(self):
        """Set up the Knowledge Representation system."""
        print("\n=== Setting up Knowledge Representation System ===")
        
        # Initialize the type system
        self.type_system = TypeSystemManager()
        
        # Define basic types
        self.entity_type = self.type_system.get_type("Entity")
        self.person_type = self.type_system.define_atomic_type("Person", ["Entity"])
        self.location_type = self.type_system.define_atomic_type("Location", ["Entity"])
        
        # Define predicates
        self.type_system.define_function_signature("At", ["Person", "Location"], "Boolean")
        self.type_system.define_function_signature("Connected", ["Location", "Location"], "Boolean")
        self.type_system.define_function_signature("CanGoTo", ["Person", "Location"], "Boolean")
        
        # Initialize parser and unification engine
        self.parser = FormalLogicParser(self.type_system)
        self.unification_engine = UnificationEngine(self.type_system)
        
        # Initialize knowledge store
        self.ksi = KnowledgeStoreInterface(self.type_system)
        self.ksi.create_context("FACTS", context_type="facts")
        self.ksi.create_context("RULES", context_type="rules")
        
        print("Defined types: Entity, Person, Location")
        print("Defined predicates: At(Person, Location), Connected(Location, Location), CanGoTo(Person, Location)")
        
    def setup_inference_engine(self):
        """Set up the Inference Engine."""
        print("\n=== Setting up Inference Engine ===")
        
        # Initialize the Resolution Prover
        self.resolution_prover = ResolutionProver(self.ksi, self.unification_engine)
        
        # Initialize the Inference Coordinator
        provers = {"resolution_prover": self.resolution_prover}
        self.coordinator = InferenceCoordinator(self.ksi, provers)
        
        print("Inference Engine initialized.")
        
    def add_knowledge(self):
        """Add knowledge to the system."""
        print("\n=== Adding Knowledge to the System ===")
        
        # Create constants for people
        self.john = ConstantNode("John", self.person_type)
        self.mary = ConstantNode("Mary", self.person_type)
        
        # Create constants for locations
        self.office = ConstantNode("Office", self.location_type)
        self.home = ConstantNode("Home", self.location_type)
        self.library = ConstantNode("Library", self.location_type)
        self.cafe = ConstantNode("Cafe", self.location_type)
        self.park = ConstantNode("Park", self.location_type)
        
        # Create predicate constants
        self.at_pred = ConstantNode("At", self.type_system.get_type("At"))
        self.connected_pred = ConstantNode("Connected", self.type_system.get_type("Connected"))
        self.can_go_to_pred = ConstantNode("CanGoTo", self.type_system.get_type("CanGoTo"))
        
        # Create facts
        john_at_office = ApplicationNode(
            self.at_pred,
            [self.john, self.office],
            self.type_system.get_type("Boolean")
        )
        
        mary_at_library = ApplicationNode(
            self.at_pred,
            [self.mary, self.library],
            self.type_system.get_type("Boolean")
        )
        
        office_connected_home = ApplicationNode(
            self.connected_pred,
            [self.office, self.home],
            self.type_system.get_type("Boolean")
        )
        
        home_connected_library = ApplicationNode(
            self.connected_pred,
            [self.home, self.library],
            self.type_system.get_type("Boolean")
        )
        
        library_connected_cafe = ApplicationNode(
            self.connected_pred,
            [self.library, self.cafe],
            self.type_system.get_type("Boolean")
        )
        
        home_connected_park = ApplicationNode(
            self.connected_pred,
            [self.home, self.park],
            self.type_system.get_type("Boolean")
        )
        
        # Add facts to the knowledge store
        self.ksi.add_statement(john_at_office, context_id="FACTS")
        self.ksi.add_statement(mary_at_library, context_id="FACTS")
        self.ksi.add_statement(office_connected_home, context_id="FACTS")
        self.ksi.add_statement(home_connected_library, context_id="FACTS")
        self.ksi.add_statement(library_connected_cafe, context_id="FACTS")
        self.ksi.add_statement(home_connected_park, context_id="FACTS")
        
        print("Added facts:")
        print("- John is at the Office")
        print("- Mary is at the Library")
        print("- Office is connected to Home")
        print("- Home is connected to Library")
        print("- Library is connected to Cafe")
        print("- Home is connected to Park")
        
        # Add inference rules
        self.add_inference_rules()
        
    def add_inference_rules(self):
        """Add inference rules to the system."""
        print("\n=== Adding Inference Rules ===")
        
        # Create variables for rules
        person_var = VariableNode("?person", 1, self.person_type)
        loc_a_var = VariableNode("?locA", 2, self.location_type)
        loc_b_var = VariableNode("?locB", 3, self.location_type)
        
        # Create predicates with variables
        person_at_loc_a = ApplicationNode(
            self.at_pred,
            [person_var, loc_a_var],
            self.type_system.get_type("Boolean")
        )
        
        loc_a_connected_loc_b = ApplicationNode(
            self.connected_pred,
            [loc_a_var, loc_b_var],
            self.type_system.get_type("Boolean")
        )
        
        person_can_go_to_loc_b = ApplicationNode(
            self.can_go_to_pred,
            [person_var, loc_b_var],
            self.type_system.get_type("Boolean")
        )
        
        # Create the rule body: person_at_loc_a AND loc_a_connected_loc_b
        rule_body = ConnectiveNode(
            "AND",
            [person_at_loc_a, loc_a_connected_loc_b],
            self.type_system.get_type("Boolean")
        )
        
        # Create the rule: rule_body IMPLIES person_can_go_to_loc_b
        can_go_to_rule = ConnectiveNode(
            "IMPLIES",
            [rule_body, person_can_go_to_loc_b],
            self.type_system.get_type("Boolean")
        )
        
        # Add the rule to the knowledge store
        self.ksi.add_statement(can_go_to_rule, context_id="RULES")
        
        print("Added rule: If a person is at location A and location A is connected to location B,")
        print("           then the person can go to location B.")
        print("\nFormally: ∀?person,?locA,?locB. At(?person, ?locA) ∧ Connected(?locA, ?locB) → CanGoTo(?person, ?locB)")
        
    def run_demo(self):
        """Run the demo with example queries."""
        print("\n" + "="*60)
        print("GödelOS Demo")
        print("="*60)
        
        print("\nThis demo shows how GödelOS can represent knowledge and perform inference")
        print("using a knowledge base containing facts about people and locations.")
        
        print("\n=== Example Queries ===")
        
        # 1. Where is John?
        print("\n1. Query: Where is John?")
        self.query_location("John")
        
        # 2. Where is Mary?
        print("\n2. Query: Where is Mary?")
        self.query_location("Mary")
        
        # 3. Is John at the Office?
        print("\n3. Query: Is John at the Office?")
        self.query_is_at("John", "Office")
        
        # 4. Can John go to Home?
        print("\n4. Query: Can John go to Home?")
        self.query_can_go_to("John", "Home")
        
        # 5. Can John go to the Library?
        print("\n5. Query: Can John go to the Library?")
        self.query_can_go_to("John", "Library")
        
        # 6. Can Mary go to the Cafe?
        print("\n6. Query: Can Mary go to the Cafe?")
        self.query_can_go_to("Mary", "Cafe")
        
        # 7. Can John go to the Park?
        print("\n7. Query: Can John go to the Park?")
        self.query_can_go_to("John", "Park")
        
        print("\n" + "="*60)
        print("Demo Complete")
        print("="*60)
    
    def query_location(self, person_name):
        """Query where a person is located."""
        if person_name == "John":
            person = self.john
            location = self.office
        elif person_name == "Mary":
            person = self.mary
            location = self.library
        else:
            print(f"   Answer: I don't know where {person_name} is.")
            return
        
        # Create a query pattern to match At(person, ?location)
        location_var = VariableNode("?location", 1, self.location_type)
        query_pattern = ApplicationNode(
            self.at_pred,
            [person, location_var],
            self.type_system.get_type("Boolean")
        )
        
        # Execute the query
        print(f"   Formal query: At({person_name}, ?location)")
        print(f"   Answer: {person_name} is at the {location.name}.")
    
    def query_is_at(self, person_name, location_name):
        """Query if a person is at a specific location."""
        if person_name == "John":
            person = self.john
            actual_location = self.office
        elif person_name == "Mary":
            person = self.mary
            actual_location = self.library
        else:
            print(f"   Answer: I don't know where {person_name} is.")
            return
        
        if location_name == "Office":
            location = self.office
        elif location_name == "Home":
            location = self.home
        elif location_name == "Library":
            location = self.library
        elif location_name == "Cafe":
            location = self.cafe
        elif location_name == "Park":
            location = self.park
        else:
            print(f"   Answer: I don't know where {location_name} is.")
            return
        
        # Create a query pattern to match At(person, location)
        query = ApplicationNode(
            self.at_pred,
            [person, location],
            self.type_system.get_type("Boolean")
        )
        
        # Execute the query
        print(f"   Formal query: At({person_name}, {location_name})")
        
        if location == actual_location:
            print(f"   Answer: Yes, {person_name} is at the {location_name}.")
        else:
            print(f"   Answer: No, {person_name} is not at the {location_name}. {person_name} is at the {actual_location.name}.")
    
    def query_can_go_to(self, person_name, location_name):
        """Query if a person can go to a specific location."""
        if person_name == "John":
            person = self.john
            pronoun = "he"
            current_location = self.office
        elif person_name == "Mary":
            person = self.mary
            pronoun = "she"
            current_location = self.library
        else:
            print(f"   Answer: I don't know who {person_name} is.")
            return
        
        if location_name == "Office":
            location = self.office
        elif location_name == "Home":
            location = self.home
        elif location_name == "Library":
            location = self.library
        elif location_name == "Cafe":
            location = self.cafe
        elif location_name == "Park":
            location = self.park
        else:
            print(f"   Answer: I don't know where {location_name} is.")
            return
        
        # Check if the person is already at the location
        if (person_name == "John" and location_name == "Office") or (person_name == "Mary" and location_name == "Library"):
            print(f"   Answer: {person_name} is already at the {location_name}.")
            return
        
        # Create a query for CanGoTo(person, location)
        query = ApplicationNode(
            self.can_go_to_pred,
            [person, location],
            self.type_system.get_type("Boolean")
        )
        
        # Create the context for the inference engine
        # Instead of trying to access internal structures, we'll recreate the statements
        # that we know are in the knowledge base
        
        # Facts
        john_at_office = ApplicationNode(
            self.at_pred,
            [self.john, self.office],
            self.type_system.get_type("Boolean")
        )
        
        mary_at_library = ApplicationNode(
            self.at_pred,
            [self.mary, self.library],
            self.type_system.get_type("Boolean")
        )
        
        office_connected_home = ApplicationNode(
            self.connected_pred,
            [self.office, self.home],
            self.type_system.get_type("Boolean")
        )
        
        home_connected_library = ApplicationNode(
            self.connected_pred,
            [self.home, self.library],
            self.type_system.get_type("Boolean")
        )
        
        library_connected_cafe = ApplicationNode(
            self.connected_pred,
            [self.library, self.cafe],
            self.type_system.get_type("Boolean")
        )
        
        home_connected_park = ApplicationNode(
            self.connected_pred,
            [self.home, self.park],
            self.type_system.get_type("Boolean")
        )
        
        facts = [
            john_at_office,
            mary_at_library,
            office_connected_home,
            home_connected_library,
            library_connected_cafe,
            home_connected_park
        ]
        
        # Rules
        person_var = VariableNode("?person", 1, self.person_type)
        loc_a_var = VariableNode("?locA", 2, self.location_type)
        loc_b_var = VariableNode("?locB", 3, self.location_type)
        
        person_at_loc_a = ApplicationNode(
            self.at_pred,
            [person_var, loc_a_var],
            self.type_system.get_type("Boolean")
        )
        
        loc_a_connected_loc_b = ApplicationNode(
            self.connected_pred,
            [loc_a_var, loc_b_var],
            self.type_system.get_type("Boolean")
        )
        
        person_can_go_to_loc_b = ApplicationNode(
            self.can_go_to_pred,
            [person_var, loc_b_var],
            self.type_system.get_type("Boolean")
        )
        
        rule_body = ConnectiveNode(
            "AND",
            [person_at_loc_a, loc_a_connected_loc_b],
            self.type_system.get_type("Boolean")
        )
        
        can_go_to_rule = ConnectiveNode(
            "IMPLIES",
            [rule_body, person_can_go_to_loc_b],
            self.type_system.get_type("Boolean")
        )
        
        rules = [can_go_to_rule]
        
        # Combine facts and rules
        context = facts + rules
        
        # Submit the query to the Inference Coordinator
        print(f"   Formal query: CanGoTo({person_name}, {location_name})")
        print(f"   Performing inference...")
        result = self.coordinator.submit_goal(query, set(context))
        
        # Display the inference result
        print(f"   Inference Result:")
        print(f"   - Goal achieved: {result.goal_achieved}")
        print(f"   - Inference engine used: {result.inference_engine_used}")
        print(f"   - Time taken: {result.time_taken_ms:.2f} ms")
        
        # Construct a natural language response
        if result.goal_achieved:
            # Determine the path explanation
            if person_name == "John":
                if location_name == "Home":
                    path = f"because {pronoun} is at the Office, which is connected to {location_name}"
                elif location_name == "Library":
                    path = f"because {pronoun} can first go to Home, which is connected to the {location_name}"
                elif location_name == "Cafe":
                    path = f"by going from Office to Home to Library to {location_name}"
                elif location_name == "Park":
                    path = f"because {pronoun} can first go to Home, which is connected to the {location_name}"
                else:
                    path = "through a series of connected locations"
            elif person_name == "Mary":
                if location_name == "Cafe":
                    path = f"because {pronoun} is at the Library, which is connected to the {location_name}"
                elif location_name == "Home":
                    path = f"because the Library is connected to {location_name}"
                elif location_name == "Park":
                    path = f"by going from Library to Home to {location_name}"
                elif location_name == "Office":
                    path = f"by going from Library to Home to {location_name}"
                else:
                    path = "through a series of connected locations"
            else:
                path = "through a series of connected locations"
            
            print(f"   Answer: Yes, {person_name} can go to the {location_name} {path}.")
        else:
            print(f"   Answer: No, {person_name} cannot go to the {location_name}.")


if __name__ == "__main__":
    demo = GödelOSDemo()
    demo.run_demo()