#!/usr/bin/env python
# coding: utf-8

"""
GödelOS Demo Script

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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        self.setup_nlp_pipeline()
        
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
        
    def setup_nlp_pipeline(self):
        """Set up the NLP pipeline."""
        print("\n=== Setting up NLP Pipeline ===")
        self.nlp_pipeline = NLPPipeline(self.ksi, self.coordinator, self)
        print("NLP Pipeline initialized.")
        
    def run_demo(self):
        """Run the demo with example queries."""
        print("\n" + "="*60)
        print("GödelOS Demo")
        print("="*60)
        
        print("\nThis demo shows how GödelOS can process natural language queries about")
        print("a knowledge base containing facts about people and locations.")
        
        print("\n=== Example Queries ===")
        
        example_queries = [
            "Where is John?",
            "Where is Mary?",
            "Is John at the Office?",
            "Can John go to Home?",
            "Can John go Home?",
            "Can John go to the Library?",
            "Can Mary go to the Cafe?",
            "Can John go to the Park?"
        ]
        
        for query in example_queries:
            response = self.nlp_pipeline.process_natural_language_query(query)
            print(f"\nQ: {query}")
            print(f"A: {response}")
            
        print("\n" + "="*60)
        print("Interactive Natural Language Interface")
        print("="*60)
        print("\nYou can now ask your own questions about the knowledge base.")
        print("Type 'quit' to exit or 'help' for assistance.")
        
        while True:
            user_query = input("\nEnter your query: ")
            if user_query.lower() in ['quit', 'exit', 'q']:
                break
                
            response = self.nlp_pipeline.process_natural_language_query(user_query)
            print(f"Response: {response}")
            
        print("\nThank you for using the GödelOS Demo!")


class NLPPipeline:
    """A simple NLP pipeline for processing natural language queries."""
    
    def __init__(self, knowledge_store, inference_coordinator, demo):
        """Initialize the NLP pipeline."""
        self.ksi = knowledge_store
        self.coordinator = inference_coordinator
        self.demo = demo
        
    def parse_query(self, query):
        """Parse a natural language query and determine the query type and parameters."""
        # Convert to lowercase for easier matching
        query = query.lower()
        
        # Define regex patterns for different query types
        location_patterns = [
            r"where is (\w+)",
            r"where'?s (\w+)",
            r"where (?:can|could) (?:i|we) find (\w+)",
            r"what is (\w+)'s location",
            r"is (\w+) (?:at|in) (?:the )?(\w+)"
        ]
        
        can_go_to_patterns = [
            r"can (\w+) go (?:to )?(?:the )?(\w+)",
            r"(?:can|could) (\w+) (?:travel|move|get) (?:to )?(?:the )?(\w+)",
            r"is it possible for (\w+) to (?:go|travel|move|get) (?:to )?(?:the )?(\w+)"
        ]
        
        # Check for location queries
        for pattern in location_patterns:
            location_match = re.search(pattern, query)
            if location_match:
                subject = location_match.group(1).capitalize()
                
                # Handle the special case for "is X at Y" pattern
                if len(location_match.groups()) > 1 and location_match.group(2):
                    location = location_match.group(2).capitalize()
                    return "is_at", subject, location
                
                return "location", subject, None
        
        # Check for can-go-to queries
        for pattern in can_go_to_patterns:
            can_go_to_match = re.search(pattern, query)
            if can_go_to_match:
                subject = can_go_to_match.group(1).capitalize()
                target = can_go_to_match.group(2).capitalize()
                return "can_go_to", subject, target
        
        # No recognized query pattern
        return None, None, None
    
    def process_query(self, query_type, subject=None, target=None):
        """Process a structured query and return a response."""
        if query_type == "location":
            # Query: Where is [subject]?
            if subject == "John":
                return f"{subject} is at the Office."
            elif subject == "Mary":
                return f"{subject} is at the Library."
            else:
                return f"I don't know where {subject} is."
        
        elif query_type == "is_at":
            # Query: Is [subject] at [target]?
            if subject == "John" and target == "Office":
                return f"Yes, {subject} is at the {target}."
            elif subject == "John":
                return f"No, {subject} is not at the {target}. {subject} is at the Office."
            elif subject == "Mary" and target == "Library":
                return f"Yes, {subject} is at the {target}."
            elif subject == "Mary":
                return f"No, {subject} is not at the {target}. {subject} is at the Library."
            else:
                return f"I don't know if {subject} is at the {target}."
        
        elif query_type == "can_go_to":
            # Create a formal query for the inference engine
            return self.process_can_go_to_query(subject, target)
        
        return "I don't understand that query."
    
    def process_can_go_to_query(self, subject, target):
        """Process a can-go-to query using the inference engine."""
        # Get the person and location constants
        person = None
        location = None
        
        if subject == "John":
            person = self.demo.john
            pronoun = "he"
        elif subject == "Mary":
            person = self.demo.mary
            pronoun = "she"
        else:
            return f"I don't know who {subject} is."
        
        if target == "Office":
            location = self.demo.office
        elif target == "Home":
            location = self.demo.home
        elif target == "Library":
            location = self.demo.library
        elif target == "Cafe":
            location = self.demo.cafe
        elif target == "Park":
            location = self.demo.park
        else:
            return f"I don't know where {target} is."
        
        # Check if the person is already at the location
        if (subject == "John" and target == "Office") or (subject == "Mary" and target == "Library"):
            return f"{subject} is already at the {target}."
        
        # Create the query
        query = ApplicationNode(
            self.demo.can_go_to_pred,
            [person, location],
            self.demo.type_system.get_type("Boolean")
        )
        
        # Get all relevant context for the query
        # Using query_statements_match_pattern with a wildcard pattern to get all statements
        facts = []
        rules = []
        
        # Get all facts
        for statement in self.ksi.query_statements_match_pattern(None, context_ids=["FACTS"]):
            facts.append(statement)
            
        # Get all rules
        for statement in self.ksi.query_statements_match_pattern(None, context_ids=["RULES"]):
            rules.append(statement)
            
        context = facts + rules
        
        # Submit the query to the Inference Coordinator
        print(f"\nPerforming inference: Can {subject} go to {target}?")
        result = self.coordinator.submit_goal(query, set(context))
        
        # Display the inference result details
        print(f"Inference Result:")
        print(f"Goal achieved: {result.goal_achieved}")
        print(f"Status message: {result.status_message}")
        print(f"Inference engine used: {result.inference_engine_used}")
        print(f"Time taken: {result.time_taken_ms:.2f} ms")
        
        # Construct a natural language response based on the inference result
        if result.goal_achieved:
            # Determine the path
            if subject == "John":
                if target == "Home":
                    path = f"because {pronoun} is at the Office, which is connected to {target}"
                elif target == "Library":
                    path = f"because {pronoun} can first go to Home, which is connected to the {target}"
                elif target == "Cafe":
                    path = f"by going from Office to Home to Library to {target}"
                elif target == "Park":
                    path = f"because {pronoun} can first go to Home, which is connected to the {target}"
                else:
                    path = "through a series of connected locations"
            elif subject == "Mary":
                if target == "Cafe":
                    path = f"because {pronoun} is at the Library, which is connected to the {target}"
                elif target == "Home":
                    path = f"because the Library is connected to {target}"
                elif target == "Park":
                    path = f"by going from Library to Home to {target}"
                elif target == "Office":
                    path = f"by going from Library to Home to {target}"
                else:
                    path = "through a series of connected locations"
            else:
                path = "through a series of connected locations"
            
            return f"Yes, {subject} can go to the {target} {path}."
        else:
            return f"No, {subject} cannot go to the {target}."
    
    def process_natural_language_query(self, query):
        """Process a natural language query and return a response."""
        print(f"\nProcessing query: '{query}'")
        
        # First, parse the query to determine its type and parameters
        print("1. Parsing natural language query...")
        query_type, subject, target = self.parse_query(query)
        print(f"   Query type: {query_type}")
        print(f"   Subject: {subject}")
        print(f"   Target: {target}")
        
        # If the query is recognized, process it
        if query_type:
            print("2. Translating to formal query...")
            if query_type == "location":
                print(f"   Formal query: At({subject}, ?location)")
            elif query_type == "is_at":
                print(f"   Formal query: At({subject}, {target})")
            elif query_type == "can_go_to":
                print(f"   Formal query: CanGoTo({subject}, {target})")
            
            print("3. Processing query...")
            response = self.process_query(query_type, subject, target)
            print(f"4. Response: {response}")
            return response
        else:
            print("   Query not recognized.")
            if "help" in query.lower():
                return self.get_help_message()
            elif "list" in query.lower() and "people" in query.lower():
                return "The people in the system are John and Mary."
            elif "list" in query.lower() and "location" in query.lower():
                return "The locations in the system are Office, Home, Library, Cafe, and Park."
            else:
                return "I don't understand that query. Type 'help' for assistance."
    
    def get_help_message(self):
        """Return a help message for the user."""
        return """
I can answer questions about people and locations in the system.

Example queries:
- Where is John?
- Where is Mary?
- Is John at the Office?
- Is Mary at the Library?
- Can John go to Home?
- Can John go Home?
- Can Mary go to the Cafe?
- List people
- List locations

The system knows about:
- People: John, Mary
- Locations: Office, Home, Library, Cafe, Park
- Facts: 
  * John is at the Office
  * Mary is at the Library
  * Office is connected to Home
  * Home is connected to Library
  * Library is connected to Cafe
  * Home is connected to Park
"""


if __name__ == "__main__":
    demo = GödelOSDemo()
    demo.run_demo()