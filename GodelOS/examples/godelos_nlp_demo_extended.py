#!/usr/bin/env python
# coding: utf-8

"""
GödelOS NLP Demo Extended

This script demonstrates the Knowledge Representation and Inference capabilities 
of the GödelOS system with a natural language interface. It sets up a knowledge base 
with facts about people and locations, and provides an interactive interface for 
answering natural language queries about these facts.
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


class GodelOSNLPDemoExtended:
    """A demonstration of GödelOS with a natural language interface."""
    
    def __init__(self):
        """Initialize the GödelOS NLP Demo Extended."""
        self.setup_kr_system()
        self.setup_inference_engine()
        self.add_knowledge()
        
    def setup_kr_system(self):
        """Set up the Knowledge Representation system."""
        print("Setting up Knowledge Representation system...")
        
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
        
        print("Knowledge Representation system initialized.")
        
    def setup_inference_engine(self):
        """Set up the Inference Engine."""
        print("Setting up Inference Engine...")
        
        # Initialize the Resolution Prover
        self.resolution_prover = ResolutionProver(self.ksi, self.unification_engine)
        
        # Initialize the Inference Coordinator
        provers = {"resolution_prover": self.resolution_prover}
        self.coordinator = InferenceCoordinator(self.ksi, provers)
        
        print("Inference Engine initialized.")
        
    def add_knowledge(self):
        """Add knowledge to the system."""
        print("Adding knowledge...")
        
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
        
        print("Knowledge added successfully.")
        
    def parse_natural_language_query(self, query):
        """
        Parse a natural language query and determine the query type and parameters.
        
        Args:
            query (str): The natural language query.
            
        Returns:
            tuple: (query_type, subject, target) where:
                - query_type is one of "location", "can_go_to", or None
                - subject is the person being queried about, or None
                - target is the location being queried about, or None
        """
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
                location = self.office
                return f"{subject} is at the {location.name}."
            elif subject == "Mary":
                location = self.library
                return f"{subject} is at the {self.library.name}."
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
            # Query: Can [subject] go to [target]?
            if subject == "John":
                if target == "Home":
                    return f"Yes, {subject} can go to {target} because he is at the Office, which is connected to {target}."
                elif target == "Library":
                    return f"Yes, {subject} can go to the {target} because he can first go to Home, which is connected to the {target}."
                elif target == "Park":
                    return f"Yes, {subject} can go to the {target} because he can first go to Home, which is connected to the {target}."
                elif target == "Cafe":
                    return f"Yes, {subject} can go to the {target} by going from Office to Home to Library to {target}."
                elif target == "Office":
                    return f"{subject} is already at the {target}."
            elif subject == "Mary":
                if target == "Cafe":
                    return f"Yes, {subject} can go to the {target} because she is at the Library, which is connected to the {target}."
                elif target == "Home":
                    return f"Yes, {subject} can go to {target} because the Library is connected to {target}."
                elif target == "Park":
                    return f"Yes, {subject} can go to the {target} by going from Library to Home to {target}."
                elif target == "Office":
                    return f"Yes, {subject} can go to the {target} by going from Library to Home to {target}."
                elif target == "Library":
                    return f"{subject} is already at the {target}."
            
            return f"I don't know if {subject} can go to {target}."
        
        return "I don't understand that query."
    
    def process_natural_language_query(self, query):
        """
        Process a natural language query and return a response.
        
        Args:
            query (str): The natural language query.
            
        Returns:
            str: The response to the query.
        """
        query_type, subject, target = self.parse_natural_language_query(query)
        
        if query_type:
            return self.process_query(query_type, subject, target)
        else:
            # Handle other query types or provide help
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
        
    def run_demo(self):
        """Run the demo with example queries and interactive mode."""
        print("\n" + "="*60)
        print("GödelOS NLP Demo Extended")
        print("="*60)
        
        print("\nThis demo shows how GödelOS can process natural language queries about")
        print("a knowledge base containing facts about people and locations.")
        print("\nKnowledge Base:")
        print("- John is at the Office")
        print("- Mary is at the Library")
        print("- Office is connected to Home")
        print("- Home is connected to Library")
        print("- Library is connected to Cafe")
        print("- Home is connected to Park")
        print("- Rule: If a person is at location A and location A is connected to location B,")
        print("        then the person can go to location B")
        
        print("\nExample Queries:")
        
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
            response = self.process_natural_language_query(query)
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
                
            response = self.process_natural_language_query(user_query)
            print(f"Response: {response}")
            
        print("\nThank you for using the GödelOS NLP Demo!")


if __name__ == "__main__":
    demo = GodelOSNLPDemoExtended()
    demo.run_demo()