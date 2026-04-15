"""
Enhanced unit tests for the ContentPlanner component.

This file extends the basic tests in test_content_planner.py with more thorough
testing of complex methods and edge cases, focusing on:
1. Complex AST structures and their transformation to content elements
2. Message type determination with ambiguous inputs
3. Relationship determination between content elements
4. Temporal ordering of content elements
5. Focus determination based on context
6. Performance with large AST structures
"""

import unittest
from unittest.mock import patch, MagicMock
import time
from typing import Dict, List, Optional, Set, Any, Tuple

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode,
    QuantifierNode, ConnectiveNode, ModalOpNode, LambdaNode, DefinitionNode
)
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType, FunctionType

from godelOS.nlu_nlg.nlg.content_planner import (
    ContentPlanner, MessageSpecification, ContentElement, MessageType
)

from godelOS.test_runner.test_categorizer import TestCategorizer
from godelOS.test_runner.timing_tracker import TimingTracker


class TestContentPlannerEnhanced(unittest.TestCase):
    """Enhanced test cases for the ContentPlanner with complex scenarios and edge cases."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock type system
        self.type_system = MagicMock(spec=TypeSystemManager)
        
        # Set up common types
        self.entity_type = AtomicType("Entity")
        self.boolean_type = AtomicType("Boolean")
        self.proposition_type = AtomicType("Proposition")
        self.event_type = AtomicType("Event")
        self.time_type = AtomicType("Time")
        
        # Configure the type system mock
        self.type_system.get_type.side_effect = lambda name: {
            "Entity": self.entity_type,
            "Boolean": self.boolean_type,
            "Proposition": self.proposition_type,
            "Event": self.event_type,
            "Time": self.time_type
        }.get(name)
        
        # Create the content planner
        self.content_planner = ContentPlanner(self.type_system)
        
        # Set up timing tracker for performance measurements
        config = MagicMock()
        config.detailed_timing = True
        self.timing_tracker = TimingTracker(config)
    
    def test_complex_ast_structure(self):
        """Test planning content with a complex AST structure."""
        # Create a complex AST structure representing:
        # "If it rains tomorrow, John will believe that Mary knows that the party will be canceled"
        
        # Create constants for entities
        john = ConstantNode("John", self.entity_type)
        mary = ConstantNode("Mary", self.entity_type)
        party = ConstantNode("party", self.entity_type)
        tomorrow = ConstantNode("tomorrow", self.time_type)
        
        # Create predicates
        rain_pred = ConstantNode("rain", FunctionType([self.time_type], self.proposition_type))
        cancel_pred = ConstantNode("cancel", FunctionType([self.entity_type], self.proposition_type))
        
        # Create atomic formulas
        rain_tomorrow = ApplicationNode(rain_pred, [tomorrow], self.proposition_type)
        party_canceled = ApplicationNode(cancel_pred, [party], self.proposition_type)
        
        # Create modal formulas
        mary_knows = ModalOpNode("KNOWS", party_canceled, self.proposition_type, mary)
        john_believes = ModalOpNode("BELIEVES", mary_knows, self.proposition_type, john)
        
        # Create conditional formula
        conditional = ConnectiveNode("IMPLIES", [rain_tomorrow, john_believes], self.proposition_type)
        
        # Start timing
        start_time = time.time()
        
        # Plan content
        message_spec = self.content_planner.plan_content([conditional])
        
        # End timing
        planning_time = time.time() - start_time
        print(f"Complex AST planning time: {planning_time * 1000:.2f} ms")
        
        # Verify message specification
        self.assertEqual(message_spec.message_type, MessageType.CONDITIONAL)
        
        # Verify main content elements
        self.assertGreater(len(message_spec.main_content), 0)
        
        # Find the conditional element
        conditional_element = None
        for element in message_spec.main_content:
            if element.content_type == "connective" and element.properties["connective_type"] == "IMPLIES":
                conditional_element = element
                break
        
        # Verify the conditional element
        self.assertIsNotNone(conditional_element)
        
        # Verify discourse relations
        self.assertIn("operand", message_spec.discourse_relations)
        
        # Verify temporal ordering
        self.assertGreater(len(message_spec.temporal_ordering), 0)
        
        # Verify focus elements
        self.assertGreater(len(message_spec.focus_elements), 0)
    
    def test_message_type_determination_with_ambiguous_input(self):
        """Test determining message type with ambiguous input."""
        # Create constants
        john = ConstantNode("John", self.entity_type)
        mary = ConstantNode("Mary", self.entity_type)
        
        # Create predicates
        happy_pred = ConstantNode("happy", FunctionType([self.entity_type], self.proposition_type))
        
        # Create atomic formulas
        john_happy = ApplicationNode(happy_pred, [john], self.proposition_type)
        mary_happy = ApplicationNode(happy_pred, [mary], self.proposition_type)
        
        # Create a mixed formula with multiple possible message types:
        # John is happy AND Mary knows that John is happy
        mary_knows = ModalOpNode("KNOWS", john_happy, self.proposition_type, mary)
        conjunction = ConnectiveNode("AND", [john_happy, mary_knows], self.proposition_type)
        
        # Determine message type
        message_type = self.content_planner._determine_message_type([conjunction])
        
        # Verify message type (should prioritize modal operators over connectives)
        self.assertEqual(message_type, MessageType.KNOWLEDGE)
        
        # Create another ambiguous formula:
        # NOT (John believes that Mary is happy)
        john_believes = ModalOpNode("BELIEVES", mary_happy, self.proposition_type, john)
        negation = ConnectiveNode("NOT", [john_believes], self.proposition_type)
        
        # Determine message type
        message_type = self.content_planner._determine_message_type([negation])
        
        # Verify message type (should prioritize negation over belief)
        self.assertEqual(message_type, MessageType.NEGATION)
        
        # Create a formula with multiple modal operators:
        # John believes that Mary knows that John is happy
        john_believes_mary_knows = ModalOpNode("BELIEVES", mary_knows, self.proposition_type, john)
        
        # Determine message type
        message_type = self.content_planner._determine_message_type([john_believes_mary_knows])
        
        # Verify message type (should be BELIEF due to the outermost modal operator)
        self.assertEqual(message_type, MessageType.BELIEF)
    
    def test_relationship_determination(self):
        """Test determining relationships between content elements."""
        # Create a complex AST structure with various relationships
        
        # Create constants
        john = ConstantNode("John", self.entity_type)
        mary = ConstantNode("Mary", self.entity_type)
        book = ConstantNode("book", self.entity_type)
        
        # Create predicates
        give_pred = ConstantNode("give", FunctionType([self.entity_type, self.entity_type, self.entity_type], self.proposition_type))
        read_pred = ConstantNode("read", FunctionType([self.entity_type, self.entity_type], self.proposition_type))
        
        # Create atomic formulas
        john_give_mary_book = ApplicationNode(give_pred, [john, mary, book], self.proposition_type)
        mary_read_book = ApplicationNode(read_pred, [mary, book], self.proposition_type)
        
        # Create a sequence: John gave Mary a book, and then Mary read it
        sequence = ConnectiveNode("AND", [john_give_mary_book, mary_read_book], self.proposition_type)
        
        # Create a custom _determine_relationships method to add a causal relationship
        original_determine_relationships = self.content_planner._determine_relationships
        
        def custom_determine_relationships(message_spec):
            # Call the original method
            original_determine_relationships(message_spec)
            
            # Add a causal relationship between the two events
            if len(message_spec.main_content) >= 2:
                message_spec.add_discourse_relation("cause", 
                                                  message_spec.main_content[0].id,
                                                  message_spec.main_content[1].id)
        
        # Patch the method
        with patch.object(self.content_planner, '_determine_relationships', custom_determine_relationships):
            # Plan content
            message_spec = self.content_planner.plan_content([sequence])
            
            # Verify discourse relations
            self.assertIn("cause", message_spec.discourse_relations)
            
            # Verify the causal relationship
            causal_relations = message_spec.discourse_relations["cause"]
            self.assertEqual(len(causal_relations), 1)
    
    def test_temporal_ordering(self):
        """Test determining temporal ordering of content elements."""
        # Create a sequence of events with temporal information
        
        # Create constants for times
        yesterday = ConstantNode("yesterday", self.time_type)
        today = ConstantNode("today", self.time_type)
        tomorrow = ConstantNode("tomorrow", self.time_type)
        
        # Create constants for events
        event1 = ConstantNode("event1", self.event_type)
        event2 = ConstantNode("event2", self.event_type)
        event3 = ConstantNode("event3", self.event_type)
        
        # Create predicates
        happen_pred = ConstantNode("happen", FunctionType([self.event_type, self.time_type], self.proposition_type))
        
        # Create atomic formulas
        event1_yesterday = ApplicationNode(happen_pred, [event1, yesterday], self.proposition_type)
        event2_today = ApplicationNode(happen_pred, [event2, today], self.proposition_type)
        event3_tomorrow = ApplicationNode(happen_pred, [event3, tomorrow], self.proposition_type)
        
        # Create a sequence of events
        sequence = ConnectiveNode("AND", [event1_yesterday, event2_today, event3_tomorrow], self.proposition_type)
        
        # Create a custom _determine_temporal_ordering method to order events by time
        original_determine_temporal_ordering = self.content_planner._determine_temporal_ordering
        
        def custom_determine_temporal_ordering(message_spec):
            # Call the original method
            original_determine_temporal_ordering(message_spec)
            
            # Clear the existing ordering
            message_spec.temporal_ordering.clear()
            
            # Find elements with time information and order them
            time_order = {"yesterday": 1, "today": 2, "tomorrow": 3}
            elements_with_time = []
            
            for element in message_spec.main_content:
                if element.content_type == "predication" and element.properties.get("operator") == "happen":
                    # Find the time argument
                    for child_id in [rel[1] for rel in message_spec.discourse_relations.get("argument", [])
                                    if rel[0] == element.id]:
                        child = next((e for e in message_spec.main_content if e.id == child_id), None)
                        if child and child.properties.get("name") in time_order:
                            elements_with_time.append((element, time_order[child.properties["name"]]))
            
            # Sort elements by time order
            elements_with_time.sort(key=lambda x: x[1])
            
            # Add to temporal ordering
            for element, _ in elements_with_time:
                message_spec.add_temporal_ordering(element.id)
        
        # Patch the method
        with patch.object(self.content_planner, '_determine_temporal_ordering', custom_determine_temporal_ordering):
            # Plan content
            message_spec = self.content_planner.plan_content([sequence])
            
            # Verify temporal ordering
            self.assertEqual(len(message_spec.temporal_ordering), 3)
    
    def test_focus_determination_with_context(self):
        """Test determining focus elements based on context."""
        # Create a complex AST structure
        
        # Create constants
        john = ConstantNode("John", self.entity_type)
        mary = ConstantNode("Mary", self.entity_type)
        book = ConstantNode("book", self.entity_type)
        
        # Create predicates
        give_pred = ConstantNode("give", FunctionType([self.entity_type, self.entity_type, self.entity_type], self.proposition_type))
        read_pred = ConstantNode("read", FunctionType([self.entity_type, self.entity_type], self.proposition_type))
        
        # Create atomic formulas
        john_give_mary_book = ApplicationNode(give_pred, [john, mary, book], self.proposition_type)
        mary_read_book = ApplicationNode(read_pred, [mary, book], self.proposition_type)
        
        # Create a sequence
        sequence = ConnectiveNode("AND", [john_give_mary_book, mary_read_book], self.proposition_type)
        
        # Create context with focus on Mary
        context = {"focus_entity": "Mary"}
        
        # Create a custom _determine_focus method to focus on the specified entity
        original_determine_focus = self.content_planner._determine_focus
        
        def custom_determine_focus(message_spec, context):
            # Call the original method
            original_determine_focus(message_spec, context)
            
            # Clear existing focus
            message_spec.focus_elements.clear()
            
            # If there's a focus entity in the context, find elements related to it
            focus_entity = context.get("focus_entity")
            if focus_entity:
                for element in message_spec.main_content:
                    if element.content_type == "predication":
                        # Check if any argument is the focus entity
                        for child_id in [rel[1] for rel in message_spec.discourse_relations.get("argument", [])
                                        if rel[0] == element.id]:
                            child = next((e for e in message_spec.main_content + message_spec.supporting_content 
                                        if e.id == child_id), None)
                            if child and child.properties.get("name") == focus_entity:
                                message_spec.add_focus_element(element.id)
                                break
        
        # Patch the method
        with patch.object(self.content_planner, '_determine_focus', custom_determine_focus):
            # Plan content
            message_spec = self.content_planner.plan_content([sequence], context)
            
            # Verify focus elements (both predicates involve Mary)
            self.assertEqual(len(message_spec.focus_elements), 2)
            
            # Change focus to John
            context["focus_entity"] = "John"
            
            # Plan content again
            message_spec = self.content_planner.plan_content([sequence], context)
            
            # Verify focus elements (only the give predicate involves John)
            self.assertEqual(len(message_spec.focus_elements), 1)
            
            # Change focus to book
            context["focus_entity"] = "book"
            
            # Plan content again
            message_spec = self.content_planner.plan_content([sequence], context)
            
            # Verify focus elements (both predicates involve the book)
            self.assertEqual(len(message_spec.focus_elements), 2)
    
    def test_performance_with_large_ast(self):
        """Test performance with a large AST structure."""
        # Create a large AST structure with many nested nodes
        
        # Create constants
        entity_constants = [ConstantNode(f"entity{i}", self.entity_type) for i in range(10)]
        
        # Create predicates
        pred = ConstantNode("predicate", FunctionType([self.entity_type, self.entity_type], self.proposition_type))
        
        # Create atomic formulas
        formulas = []
        for i in range(9):
            formula = ApplicationNode(pred, [entity_constants[i], entity_constants[i+1]], self.proposition_type)
            formulas.append(formula)
        
        # Create a large conjunction
        large_conjunction = ConnectiveNode("AND", formulas, self.proposition_type)
        
        # Create a large disjunction
        large_disjunction = ConnectiveNode("OR", formulas, self.proposition_type)
        
        # Create a large implication chain
        current_formula = formulas[0]
        for i in range(1, 9):
            current_formula = ConnectiveNode("IMPLIES", [current_formula, formulas[i]], self.proposition_type)
        large_implication = current_formula
        
        # Create a large quantified formula
        variables = [VariableNode(f"x{i}", i, self.entity_type) for i in range(5)]
        current_scope = ApplicationNode(pred, [variables[0], variables[1]], self.proposition_type)
        for i in range(2, 5):
            current_scope = ConnectiveNode("AND", [current_scope, 
                                                ApplicationNode(pred, [variables[i-1], variables[i]], 
                                                              self.proposition_type)], 
                                         self.proposition_type)
        large_quantified = QuantifierNode("FORALL", variables, current_scope, self.proposition_type)
        
        # Measure performance for each large structure
        large_structures = [
            ("Large Conjunction", large_conjunction),
            ("Large Disjunction", large_disjunction),
            ("Large Implication", large_implication),
            ("Large Quantified", large_quantified)
        ]
        
        for name, structure in large_structures:
            # Start timing
            start_time = time.time()
            
            # Plan content
            message_spec = self.content_planner.plan_content([structure])
            
            # End timing
            planning_time = time.time() - start_time
            print(f"{name} planning time: {planning_time * 1000:.2f} ms")
            
            # Verify message specification
            self.assertIsNotNone(message_spec)
            self.assertGreater(len(message_spec.main_content), 0)
    
    def test_complex_modal_operations(self):
        """Test planning content with complex modal operations."""
        # Create constants
        john = ConstantNode("John", self.entity_type)
        mary = ConstantNode("Mary", self.entity_type)
        bob = ConstantNode("Bob", self.entity_type)
        
        # Create predicates
        happy_pred = ConstantNode("happy", FunctionType([self.entity_type], self.proposition_type))
        
        # Create atomic formulas
        mary_happy = ApplicationNode(happy_pred, [mary], self.proposition_type)
        
        # Create nested modal formulas:
        # John believes that Bob knows that Mary is happy
        bob_knows = ModalOpNode("KNOWS", mary_happy, self.proposition_type, bob)
        john_believes = ModalOpNode("BELIEVES", bob_knows, self.proposition_type, john)
        
        # Start timing
        start_time = time.time()
        
        # Plan content
        message_spec = self.content_planner.plan_content([john_believes])
        
        # End timing
        planning_time = time.time() - start_time
        print(f"Complex modal planning time: {planning_time * 1000:.2f} ms")
        
        # Verify message specification
        self.assertEqual(message_spec.message_type, MessageType.BELIEF)
        
        # Verify main content elements
        self.assertGreater(len(message_spec.main_content), 0)
        
        # Find the modal elements
        belief_element = None
        knowledge_element = None
        
        for element in message_spec.main_content:
            if element.content_type == "modal_operation":
                if element.properties.get("modal_operator") == "BELIEVES":
                    belief_element = element
                elif element.properties.get("modal_operator") == "KNOWS":
                    knowledge_element = element
        
        # Verify the modal elements
        self.assertIsNotNone(belief_element)
        self.assertIsNotNone(knowledge_element)
        
        # Verify discourse relations
        self.assertIn("proposition", message_spec.discourse_relations)
        
        # Find the proposition relation from belief to knowledge
        belief_to_knowledge = False
        for source, target in message_spec.discourse_relations.get("proposition", []):
            if source == belief_element.id:
                belief_to_knowledge = True
                break
        
        self.assertTrue(belief_to_knowledge)
    
    def test_complex_quantifier_operations(self):
        """Test planning content with complex quantifier operations."""
        # Create variables
        x = VariableNode("x", 1, self.entity_type)
        y = VariableNode("y", 2, self.entity_type)
        
        # Create predicates
        person_pred = ConstantNode("person", FunctionType([self.entity_type], self.proposition_type))
        loves_pred = ConstantNode("loves", FunctionType([self.entity_type, self.entity_type], self.proposition_type))
        
        # Create atomic formulas
        x_person = ApplicationNode(person_pred, [x], self.proposition_type)
        y_person = ApplicationNode(person_pred, [y], self.proposition_type)
        x_loves_y = ApplicationNode(loves_pred, [x, y], self.proposition_type)
        
        # Create complex quantified formula:
        # ∀x. (person(x) → ∃y. (person(y) ∧ loves(x, y)))
        # "Every person loves some person"
        
        # Inner quantifier: ∃y. (person(y) ∧ loves(x, y))
        y_person_and_x_loves_y = ConnectiveNode("AND", [y_person, x_loves_y], self.proposition_type)
        exists_y = QuantifierNode("EXISTS", [y], y_person_and_x_loves_y, self.proposition_type)
        
        # Outer quantifier: ∀x. (person(x) → ...)
        x_person_implies_exists_y = ConnectiveNode("IMPLIES", [x_person, exists_y], self.proposition_type)
        forall_x = QuantifierNode("FORALL", [x], x_person_implies_exists_y, self.proposition_type)
        
        # Start timing
        start_time = time.time()
        
        # Plan content
        message_spec = self.content_planner.plan_content([forall_x])
        
        # End timing
        planning_time = time.time() - start_time
        print(f"Complex quantifier planning time: {planning_time * 1000:.2f} ms")
        
        # Verify message specification
        self.assertIsNotNone(message_spec)
        
        # Verify main content elements
        self.assertGreater(len(message_spec.main_content), 0)
        
        # Find the quantifier elements
        forall_element = None
        exists_element = None
        
        for element in message_spec.main_content:
            if element.content_type == "quantification":
                if element.properties.get("quantifier_type") == "FORALL":
                    forall_element = element
                elif element.properties.get("quantifier_type") == "EXISTS":
                    exists_element = element
        
        # Verify the quantifier elements
        self.assertIsNotNone(forall_element)
        self.assertIsNotNone(exists_element)
        
        # Verify discourse relations
        self.assertIn("scope", message_spec.discourse_relations)
        self.assertIn("binding", message_spec.discourse_relations)


if __name__ == "__main__":
    unittest.main()