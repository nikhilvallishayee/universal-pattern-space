"""
Unit tests for the SentenceGenerator module.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.nlu_nlg.nlg.content_planner import (
    MessageSpecification, ContentElement, MessageType
)
from godelOS.nlu_nlg.nlg.sentence_generator import (
    SentenceGenerator, SentencePlan, LinguisticConstituent,
    ReferringExpressionType, GrammaticalRole, TenseAspect
)


class TestSentenceGenerator(unittest.TestCase):
    """Test cases for the SentenceGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create the sentence generator
        self.sentence_generator = SentenceGenerator()
        
        # Create a mock message specification
        self.message_spec = MagicMock(spec=MessageSpecification)
        self.message_spec.message_type = MessageType.STATEMENT
        self.message_spec.main_content = []
        self.message_spec.supporting_content = []
        self.message_spec.discourse_relations = {}
        self.message_spec.temporal_ordering = []
        self.message_spec.focus_elements = []
    
    def test_generate_sentence_plans_empty(self):
        """Test generating sentence plans with an empty message specification."""
        # Generate sentence plans
        sentence_plans = self.sentence_generator.generate_sentence_plans(self.message_spec)
        
        # Check that the result is a list
        self.assertIsInstance(sentence_plans, list)
        
        # Check that the list is empty (no content to express)
        self.assertEqual(len(sentence_plans), 0)
    
    def test_generate_sentence_plans_with_content(self):
        """Test generating sentence plans with content."""
        # Create content elements
        main_element = ContentElement(
            id="element_0",
            content_type="predication",
            source_node=MagicMock(),
            properties={"operator": "chase"}
        )
        
        supporting_element1 = ContentElement(
            id="element_1",
            content_type="entity",
            source_node=MagicMock(),
            properties={"name": "cat"}
        )
        
        supporting_element2 = ContentElement(
            id="element_2",
            content_type="entity",
            source_node=MagicMock(),
            properties={"name": "mouse"}
        )
        
        # Add the elements to the message specification
        self.message_spec.main_content = [main_element]
        self.message_spec.supporting_content = [supporting_element1, supporting_element2]
        
        # Add discourse relations
        self.message_spec.discourse_relations = {
            "argument": [("element_0", "element_1"), ("element_0", "element_2")]
        }
        
        # Generate sentence plans
        sentence_plans = self.sentence_generator.generate_sentence_plans(self.message_spec)
        
        # Check that the result is a list
        self.assertIsInstance(sentence_plans, list)
        
        # Check that there is at least one sentence plan
        self.assertGreater(len(sentence_plans), 0)
        
        # Check the first sentence plan
        plan = sentence_plans[0]
        self.assertIsInstance(plan, SentencePlan)
        self.assertEqual(plan.tense_aspect, TenseAspect.SIMPLE_PRESENT)
        self.assertEqual(plan.voice, "active")
        self.assertEqual(plan.mood, "indicative")
    
    def test_determine_sentence_boundaries(self):
        """Test determining sentence boundaries."""
        # Create content elements
        main_element1 = ContentElement(
            id="element_0",
            content_type="predication",
            source_node=MagicMock(),
            properties={"operator": "chase"}
        )
        
        main_element2 = ContentElement(
            id="element_1",
            content_type="predication",
            source_node=MagicMock(),
            properties={"operator": "eat"}
        )
        
        supporting_element1 = ContentElement(
            id="element_2",
            content_type="entity",
            source_node=MagicMock(),
            properties={"name": "cat"}
        )
        
        supporting_element2 = ContentElement(
            id="element_3",
            content_type="entity",
            source_node=MagicMock(),
            properties={"name": "mouse"}
        )
        
        # Add the elements to the message specification
        self.message_spec.main_content = [main_element1, main_element2]
        self.message_spec.supporting_content = [supporting_element1, supporting_element2]
        
        # Add discourse relations
        self.message_spec.discourse_relations = {
            "argument": [("element_0", "element_2"), ("element_0", "element_3"),
                        ("element_1", "element_2"), ("element_1", "element_3")]
        }
        
        # Determine sentence boundaries
        boundaries = self.sentence_generator._determine_sentence_boundaries(self.message_spec)
        
        # Check that the result is a list
        self.assertIsInstance(boundaries, list)
        
        # Check that there are two sentence groups (one for each main content element)
        self.assertEqual(len(boundaries), 2)
        
        # Check that each group contains the main content element
        self.assertIn("element_0", boundaries[0])
        self.assertIn("element_1", boundaries[1])
    
    def test_determine_sentence_features(self):
        """Test determining sentence features based on message type."""
        # Test for statement
        tense_aspect, voice, mood = self.sentence_generator._determine_sentence_features(MessageType.STATEMENT)
        self.assertEqual(tense_aspect, TenseAspect.SIMPLE_PRESENT)
        self.assertEqual(voice, "active")
        self.assertEqual(mood, "indicative")
        
        # Test for question
        tense_aspect, voice, mood = self.sentence_generator._determine_sentence_features(MessageType.QUESTION)
        self.assertEqual(tense_aspect, TenseAspect.SIMPLE_PRESENT)
        self.assertEqual(voice, "active")
        self.assertEqual(mood, "interrogative")
        
        # Test for command
        tense_aspect, voice, mood = self.sentence_generator._determine_sentence_features(MessageType.COMMAND)
        self.assertEqual(tense_aspect, TenseAspect.SIMPLE_PRESENT)
        self.assertEqual(voice, "active")
        self.assertEqual(mood, "imperative")
    
    def test_build_sentence_structure_predication(self):
        """Test building sentence structure for a predication."""
        # Create content elements
        main_element = ContentElement(
            id="element_0",
            content_type="predication",
            source_node=MagicMock(),
            properties={"operator": "chase"}
        )
        
        supporting_element1 = ContentElement(
            id="element_1",
            content_type="entity",
            source_node=MagicMock(),
            properties={"name": "cat"}
        )
        
        supporting_element2 = ContentElement(
            id="element_2",
            content_type="entity",
            source_node=MagicMock(),
            properties={"name": "mouse"}
        )
        
        # Add the elements to the message specification
        self.message_spec.main_content = [main_element]
        self.message_spec.supporting_content = [supporting_element1, supporting_element2]
        
        # Add discourse relations
        self.message_spec.discourse_relations = {
            "argument": [("element_0", "element_1"), ("element_0", "element_2")]
        }
        
        # Create a root constituent
        root = LinguisticConstituent(
            id="root",
            constituent_type="S"
        )
        
        # Build the sentence structure
        self.sentence_generator._build_sentence_structure(
            root, ["element_0", "element_1", "element_2"], self.message_spec
        )
        
        # Check that the root has children
        self.assertGreater(len(root.children), 0)
        
        # Check that there is a subject and a verb
        subject = None
        verb = None
        for child in root.children:
            if child.constituent_type == "NP":
                subject = child
            elif child.constituent_type == "VP":
                verb = child
        
        self.assertIsNotNone(subject)
        self.assertIsNotNone(verb)
        
        # Check that the verb has the correct head
        self.assertEqual(verb.head, "chase")
    
    def test_build_sentence_structure_quantification(self):
        """Test building sentence structure for a quantification."""
        # Create content elements
        main_element = ContentElement(
            id="element_0",
            content_type="quantification",
            source_node=MagicMock(),
            properties={"quantifier_type": "FORALL"}
        )
        
        supporting_element = ContentElement(
            id="element_1",
            content_type="bound_variable",
            source_node=MagicMock(),
            properties={"name": "x"}
        )
        
        scope_element = ContentElement(
            id="element_2",
            content_type="predication",
            source_node=MagicMock(),
            properties={"operator": "human"}
        )
        
        # Add the elements to the message specification
        self.message_spec.main_content = [main_element]
        self.message_spec.supporting_content = [supporting_element]
        
        # Add discourse relations
        self.message_spec.discourse_relations = {
            "binding": [("element_0", "element_1")],
            "scope": [("element_0", "element_2")]
        }
        
        # Create a root constituent
        root = LinguisticConstituent(
            id="root",
            constituent_type="S"
        )
        
        # Build the sentence structure
        self.sentence_generator._build_sentence_structure(
            root, ["element_0", "element_1", "element_2"], self.message_spec
        )
        
        # Check that the root has children
        self.assertGreater(len(root.children), 0)
        
        # Check that there is a determiner
        determiner = None
        for child in root.children:
            if child.constituent_type == "DET":
                determiner = child
        
        self.assertIsNotNone(determiner)
        
        # Check that the determiner has the correct head
        self.assertEqual(determiner.head, "every")
    
    def test_quantifier_to_determiner(self):
        """Test converting a quantifier type to a determiner."""
        # Test for universal quantifier
        determiner = self.sentence_generator._quantifier_to_determiner("FORALL")
        self.assertEqual(determiner, "every")
        
        # Test for existential quantifier
        determiner = self.sentence_generator._quantifier_to_determiner("EXISTS")
        self.assertEqual(determiner, "some")
        
        # Test for unknown quantifier
        determiner = self.sentence_generator._quantifier_to_determiner("UNKNOWN")
        self.assertEqual(determiner, "the")
    
    def test_modal_operator_to_verb(self):
        """Test converting a modal operator to a verb."""
        # Test for belief
        verb = self.sentence_generator._modal_operator_to_verb("BELIEVES")
        self.assertEqual(verb, "believes that")
        
        # Test for knowledge
        verb = self.sentence_generator._modal_operator_to_verb("KNOWS")
        self.assertEqual(verb, "knows that")
        
        # Test for possibility
        verb = self.sentence_generator._modal_operator_to_verb("POSSIBLE_WORLD_TRUTH")
        self.assertEqual(verb, "it is possible that")
        
        # Test for obligation
        verb = self.sentence_generator._modal_operator_to_verb("OBLIGATORY")
        self.assertEqual(verb, "must")
        
        # Test for unknown modal operator
        verb = self.sentence_generator._modal_operator_to_verb("UNKNOWN")
        self.assertEqual(verb, "is")
    
    def test_determine_referring_expressions(self):
        """Test determining referring expressions."""
        # Create content elements
        entity_element = ContentElement(
            id="element_0",
            content_type="entity",
            source_node=MagicMock(),
            properties={"name": "John"}
        )
        
        variable_element = ContentElement(
            id="element_1",
            content_type="variable",
            source_node=MagicMock(),
            properties={"name": "x"}
        )
        
        # Add the elements to the message specification
        self.message_spec.main_content = [entity_element]
        self.message_spec.supporting_content = [variable_element]
        
        # Create a sentence plan
        plan = SentencePlan(
            id="sentence_0",
            root=LinguisticConstituent(id="root", constituent_type="S"),
            tense_aspect=TenseAspect.SIMPLE_PRESENT,
            voice="active",
            mood="indicative"
        )
        
        # Determine referring expressions
        self.sentence_generator._determine_referring_expressions(
            plan, ["element_0", "element_1"], self.message_spec, {}
        )
        
        # Check that the referring expressions were determined
        self.assertIn("element_0", plan.referring_expressions)
        self.assertIn("element_1", plan.referring_expressions)
        
        # Check that the referring expressions are correct
        self.assertEqual(plan.referring_expressions["element_0"], ReferringExpressionType.PROPER_NAME)
        self.assertEqual(plan.referring_expressions["element_1"], ReferringExpressionType.INDEFINITE_NP)
    
    def test_add_discourse_connectives(self):
        """Test adding discourse connectives."""
        # Create a sentence plan
        plan = SentencePlan(
            id="sentence_0",
            root=LinguisticConstituent(id="root", constituent_type="S"),
            tense_aspect=TenseAspect.SIMPLE_PRESENT,
            voice="active",
            mood="indicative"
        )
        
        # Add discourse connectives for the first sentence
        self.message_spec.message_type = MessageType.CONDITIONAL
        self.sentence_generator._add_discourse_connectives(plan, 0, self.message_spec)
        
        # Check that the discourse connectives were added
        self.assertIn("If", plan.discourse_connectives)
        
        # Create another sentence plan
        plan2 = SentencePlan(
            id="sentence_1",
            root=LinguisticConstituent(id="root", constituent_type="S"),
            tense_aspect=TenseAspect.SIMPLE_PRESENT,
            voice="active",
            mood="indicative"
        )
        
        # Add discourse connectives for a subsequent sentence
        self.message_spec.message_type = MessageType.STATEMENT
        self.sentence_generator._add_discourse_connectives(plan2, 1, self.message_spec)
        
        # Check that the discourse connectives were added
        self.assertIn("Additionally", plan2.discourse_connectives)


if __name__ == '__main__':
    unittest.main()