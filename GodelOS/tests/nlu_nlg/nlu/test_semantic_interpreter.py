"""
Unit tests for the SemanticInterpreter module.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.nlu_nlg.nlu.lexical_analyzer_parser import (
    Token, Entity, Span, Sentence, SyntacticParseOutput
)
from godelOS.nlu_nlg.nlu.semantic_interpreter import (
    SemanticInterpreter, IntermediateSemanticRepresentation, SemanticNode,
    Predicate, SemanticArgument, SemanticRelation, LogicalOperator,
    RelationType, SemanticRole
)


class TestSemanticInterpreter(unittest.TestCase):
    """Test cases for the SemanticInterpreter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.interpreter = SemanticInterpreter()
    
    def test_interpret_simple_sentence(self):
        """Test interpreting a simple sentence."""
        # Create a simple syntactic parse output
        parse_output = self._create_simple_parse_output()
        
        # Interpret the parse output
        isr = self.interpreter.interpret(parse_output)
        
        # Check that the result is an IntermediateSemanticRepresentation
        self.assertIsInstance(isr, IntermediateSemanticRepresentation)
        
        # Check that the text was preserved
        self.assertEqual(isr.text, "The cat chased the mouse.")
        
        # Check that predicates were extracted
        self.assertGreater(len(isr.predicates), 0)
        
        # Check that the main predicate is "chase"
        found_chase = False
        for pred_id, pred in isr.predicates.items():
            if pred.lemma == "chase":
                found_chase = True
                # Check that the predicate has arguments
                self.assertGreater(len(pred.arguments), 0)
                
                # Check that the agent is "cat"
                found_agent = False
                for arg in pred.arguments:
                    if arg.role == SemanticRole.AGENT and "cat" in arg.text.lower():
                        found_agent = True
                        break
                self.assertTrue(found_agent, "Agent 'cat' not found in predicate arguments")
                
                # Check that the patient is "mouse"
                found_patient = False
                for arg in pred.arguments:
                    if arg.role == SemanticRole.PATIENT and "mouse" in arg.text.lower():
                        found_patient = True
                        break
                self.assertTrue(found_patient, "Patient 'mouse' not found in predicate arguments")
                
                break
        
        self.assertTrue(found_chase, "Predicate 'chase' not found in ISR")
        
        # Check that nodes were created
        self.assertGreater(len(isr.nodes), 0)
        
        # Check that root nodes were identified
        self.assertGreater(len(isr.root_nodes), 0)
    
    def test_interpret_complex_sentence(self):
        """Test interpreting a more complex sentence with entities and modifiers."""
        # Create a more complex syntactic parse output
        parse_output = self._create_complex_parse_output()
        
        # Interpret the parse output
        isr = self.interpreter.interpret(parse_output)
        
        # Check that the result is an IntermediateSemanticRepresentation
        self.assertIsInstance(isr, IntermediateSemanticRepresentation)
        
        # Check that the text was preserved
        self.assertEqual(isr.text, "John quickly ran to the big house in New York.")
        
        # Check that predicates were extracted
        self.assertGreater(len(isr.predicates), 0)
        
        # Check that the main predicate is "run"
        found_run = False
        for pred_id, pred in isr.predicates.items():
            if pred.lemma == "run":
                found_run = True
                # Check that the predicate has arguments
                self.assertGreater(len(pred.arguments), 0)
                
                # Check that the agent is "John"
                found_agent = False
                for arg in pred.arguments:
                    if arg.role == SemanticRole.AGENT and "john" in arg.text.lower():
                        found_agent = True
                        break
                self.assertTrue(found_agent, "Agent 'John' not found in predicate arguments")
                
                # Check that there's a goal argument with "house"
                found_goal = False
                for arg in pred.arguments:
                    if arg.role == SemanticRole.GOAL and "house" in arg.text.lower():
                        found_goal = True
                        break
                self.assertTrue(found_goal, "Goal 'house' not found in predicate arguments")
                
                # Check that there's a location argument with "New York"
                found_location = False
                for arg in pred.arguments:
                    if arg.role == SemanticRole.LOCATION and "new york" in arg.text.lower():
                        found_location = True
                        break
                self.assertTrue(found_location, "Location 'New York' not found in predicate arguments")
                
                break
        
        self.assertTrue(found_run, "Predicate 'run' not found in ISR")
        
        # Check that entities were extracted
        self.assertGreater(len(isr.entities), 0)
        
        # Check that "John" and "New York" are in the entities
        found_john = False
        found_ny = False
        for entity_id, entity in isr.entities.items():
            if "john" in entity.text.lower():
                found_john = True
            elif "new york" in entity.text.lower():
                found_ny = True
        
        self.assertTrue(found_john, "Entity 'John' not found in ISR")
        self.assertTrue(found_ny, "Entity 'New York' not found in ISR")
    
    def test_extract_tense(self):
        """Test extracting tense from a verb token."""
        # Create a past tense verb token
        past_token = Token(
            text="chased", lemma="chase", pos="VERB", tag="VBD", dep="ROOT",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=8, i=2, sent_idx=0,
            morphology={"Tense": "Past"}
        )
        
        # Create a present tense verb token
        present_token = Token(
            text="chases", lemma="chase", pos="VERB", tag="VBZ", dep="ROOT",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=8, i=2, sent_idx=0,
            morphology={"Tense": "Pres"}
        )
        
        # Test tense extraction
        self.assertEqual(self.interpreter._extract_tense(past_token), "past")
        self.assertEqual(self.interpreter._extract_tense(present_token), "pres")
    
    def test_extract_aspect(self):
        """Test extracting aspect from a verb token."""
        # Create a simple aspect verb token
        simple_token = Token(
            text="chased", lemma="chase", pos="VERB", tag="VBD", dep="ROOT",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=8, i=2, sent_idx=0,
            morphology={}
        )
        
        # Create a progressive aspect verb token
        prog_token = Token(
            text="chasing", lemma="chase", pos="VERB", tag="VBG", dep="ROOT",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=8, i=2, sent_idx=0,
            morphology={"Aspect": "Prog"}
        )
        
        # Test aspect extraction
        self.assertEqual(self.interpreter._extract_aspect(simple_token), "simple")
        self.assertEqual(self.interpreter._extract_aspect(prog_token), "prog")
    
    def test_is_negated(self):
        """Test detecting negation in a verb."""
        # Create a non-negated verb token
        verb_token = Token(
            text="chased", lemma="chase", pos="VERB", tag="VBD", dep="ROOT",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=8, i=2, sent_idx=0
        )
        
        # Create a negation token
        neg_token = Token(
            text="not", lemma="not", pos="ADV", tag="RB", dep="neg",
            is_stop=True, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=6, i=1, sent_idx=0
        )
        
        # Create a sentence with no negation
        non_neg_sentence = Sentence(
            text="The cat chased the mouse.",
            start_char=0, end_char=26,
            tokens=[verb_token]
        )
        
        # Create a sentence with negation
        neg_sentence = Sentence(
            text="The cat did not chase the mouse.",
            start_char=0, end_char=32,
            tokens=[neg_token, verb_token]
        )
        
        # Test negation detection
        self.assertFalse(self.interpreter._is_negated(verb_token, non_neg_sentence))
        
        # Mock the _is_dependent_on method to make the test work
        self.interpreter._is_dependent_on = MagicMock(return_value=True)
        self.assertTrue(self.interpreter._is_negated(verb_token, neg_sentence))
    
    def test_determine_prep_role(self):
        """Test determining semantic role from a preposition."""
        # Test various prepositions
        self.assertEqual(self.interpreter._determine_prep_role("in"), SemanticRole.LOCATION)
        self.assertEqual(self.interpreter._determine_prep_role("with"), SemanticRole.INSTRUMENT)
        self.assertEqual(self.interpreter._determine_prep_role("for"), SemanticRole.PURPOSE)
        self.assertEqual(self.interpreter._determine_prep_role("to"), SemanticRole.GOAL)
        self.assertEqual(self.interpreter._determine_prep_role("from"), SemanticRole.SOURCE)
        self.assertEqual(self.interpreter._determine_prep_role("because of"), SemanticRole.CAUSE)
        self.assertEqual(self.interpreter._determine_prep_role("during"), SemanticRole.TIME)
        
        # Test unknown preposition
        self.assertEqual(self.interpreter._determine_prep_role("xyz"), SemanticRole.UNKNOWN)
    
    def test_map_semantic_role_to_relation_type(self):
        """Test mapping semantic roles to relation types."""
        # Test various semantic roles
        self.assertEqual(self.interpreter._map_semantic_role_to_relation_type(SemanticRole.AGENT), RelationType.AGENT_ACTION)
        self.assertEqual(self.interpreter._map_semantic_role_to_relation_type(SemanticRole.PATIENT), RelationType.ACTION_PATIENT)
        self.assertEqual(self.interpreter._map_semantic_role_to_relation_type(SemanticRole.LOCATION), RelationType.LOCATED_AT)
        self.assertEqual(self.interpreter._map_semantic_role_to_relation_type(SemanticRole.INSTRUMENT), RelationType.PART_OF)
        self.assertEqual(self.interpreter._map_semantic_role_to_relation_type(SemanticRole.PURPOSE), RelationType.CAUSES)
        
        # Test unknown role
        self.assertEqual(self.interpreter._map_semantic_role_to_relation_type(SemanticRole.UNKNOWN), RelationType.CUSTOM)
    
    def _create_simple_parse_output(self):
        """Create a simple syntactic parse output for testing."""
        # Create tokens
        tokens = [
            Token(
                text="The", lemma="the", pos="DET", tag="DT", dep="det",
                is_stop=True, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=0, i=0, sent_idx=0
            ),
            Token(
                text="cat", lemma="cat", pos="NOUN", tag="NN", dep="nsubj",
                is_stop=False, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=4, i=1, sent_idx=0
            ),
            Token(
                text="chased", lemma="chase", pos="VERB", tag="VBD", dep="ROOT",
                is_stop=False, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=8, i=2, sent_idx=0,
                morphology={"Tense": "Past"}
            ),
            Token(
                text="the", lemma="the", pos="DET", tag="DT", dep="det",
                is_stop=True, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=15, i=3, sent_idx=0
            ),
            Token(
                text="mouse", lemma="mouse", pos="NOUN", tag="NN", dep="dobj",
                is_stop=False, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=19, i=4, sent_idx=0
            ),
            Token(
                text=".", lemma=".", pos="PUNCT", tag=".", dep="punct",
                is_stop=False, is_punct=True, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=24, i=5, sent_idx=0
            )
        ]
        
        # Create noun phrases
        noun_phrases = [
            Span(
                text="The cat",
                start_token=0,
                end_token=2,
                tokens=tokens[0:2],
                label="NP"
            ),
            Span(
                text="the mouse",
                start_token=3,
                end_token=5,
                tokens=tokens[3:5],
                label="NP"
            )
        ]
        
        # Create a sentence
        sentence = Sentence(
            text="The cat chased the mouse.",
            start_char=0,
            end_char=25,
            tokens=tokens,
            noun_phrases=noun_phrases,
            root_token=tokens[2]  # "chased" is the root
        )
        
        # Create the parse output
        parse_output = SyntacticParseOutput(
            text="The cat chased the mouse.",
            tokens=tokens,
            sentences=[sentence],
            noun_phrases=noun_phrases
        )
        
        return parse_output
    
    def _create_complex_parse_output(self):
        """Create a more complex syntactic parse output for testing."""
        # Create tokens
        tokens = [
            Token(
                text="John", lemma="john", pos="PROPN", tag="NNP", dep="nsubj",
                is_stop=False, is_punct=False, is_space=False, is_ent=True,
                ent_type="PERSON", ent_iob="B", idx=0, i=0, sent_idx=0
            ),
            Token(
                text="quickly", lemma="quickly", pos="ADV", tag="RB", dep="advmod",
                is_stop=False, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=5, i=1, sent_idx=0
            ),
            Token(
                text="ran", lemma="run", pos="VERB", tag="VBD", dep="ROOT",
                is_stop=False, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=13, i=2, sent_idx=0,
                morphology={"Tense": "Past"}
            ),
            Token(
                text="to", lemma="to", pos="ADP", tag="IN", dep="prep",
                is_stop=True, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=17, i=3, sent_idx=0
            ),
            Token(
                text="the", lemma="the", pos="DET", tag="DT", dep="det",
                is_stop=True, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=20, i=4, sent_idx=0
            ),
            Token(
                text="big", lemma="big", pos="ADJ", tag="JJ", dep="amod",
                is_stop=False, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=24, i=5, sent_idx=0
            ),
            Token(
                text="house", lemma="house", pos="NOUN", tag="NN", dep="pobj",
                is_stop=False, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=28, i=6, sent_idx=0
            ),
            Token(
                text="in", lemma="in", pos="ADP", tag="IN", dep="prep",
                is_stop=True, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=34, i=7, sent_idx=0
            ),
            Token(
                text="New", lemma="new", pos="PROPN", tag="NNP", dep="compound",
                is_stop=False, is_punct=False, is_space=False, is_ent=True,
                ent_type="GPE", ent_iob="B", idx=37, i=8, sent_idx=0
            ),
            Token(
                text="York", lemma="york", pos="PROPN", tag="NNP", dep="pobj",
                is_stop=False, is_punct=False, is_space=False, is_ent=True,
                ent_type="GPE", ent_iob="I", idx=41, i=9, sent_idx=0
            ),
            Token(
                text=".", lemma=".", pos="PUNCT", tag=".", dep="punct",
                is_stop=False, is_punct=True, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=45, i=10, sent_idx=0
            )
        ]
        
        # Create entities
        entities = [
            Entity(
                text="John",
                label="PERSON",
                start_char=0,
                end_char=4,
                start_token=0,
                end_token=1,
                tokens=[tokens[0]]
            ),
            Entity(
                text="New York",
                label="GPE",
                start_char=37,
                end_char=45,
                start_token=8,
                end_token=10,
                tokens=[tokens[8], tokens[9]]
            )
        ]
        
        # Create noun phrases
        noun_phrases = [
            Span(
                text="John",
                start_token=0,
                end_token=1,
                tokens=[tokens[0]],
                label="NP"
            ),
            Span(
                text="the big house",
                start_token=4,
                end_token=7,
                tokens=tokens[4:7],
                label="NP"
            ),
            Span(
                text="New York",
                start_token=8,
                end_token=10,
                tokens=[tokens[8], tokens[9]],
                label="NP"
            )
        ]
        
        # Create a sentence
        sentence = Sentence(
            text="John quickly ran to the big house in New York.",
            start_char=0,
            end_char=46,
            tokens=tokens,
            entities=entities,
            noun_phrases=noun_phrases,
            root_token=tokens[2]  # "ran" is the root
        )
        
        # Create the parse output
        parse_output = SyntacticParseOutput(
            text="John quickly ran to the big house in New York.",
            tokens=tokens,
            sentences=[sentence],
            entities=entities,
            noun_phrases=noun_phrases
        )
        
        return parse_output


if __name__ == '__main__':
    unittest.main()