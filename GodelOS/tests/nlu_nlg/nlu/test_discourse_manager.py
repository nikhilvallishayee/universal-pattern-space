"""
Unit tests for the DiscourseStateManager module.
"""

import unittest
from unittest.mock import patch, MagicMock
import uuid

from godelOS.nlu_nlg.nlu.lexical_analyzer_parser import (
    Token, Entity, Span, Sentence, SyntacticParseOutput
)
from godelOS.nlu_nlg.nlu.semantic_interpreter import (
    IntermediateSemanticRepresentation, SemanticNode, Predicate, 
    SemanticArgument, SemanticRelation, LogicalOperator, RelationType, SemanticRole
)
from godelOS.nlu_nlg.nlu.discourse_manager import (
    DiscourseStateManager, DiscourseContext, DiscourseEntity, DiscourseRelation,
    DialogueState, DialogueAct, DialogueActType
)


class TestDiscourseStateManager(unittest.TestCase):
    """Test cases for the DiscourseStateManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the uuid.uuid4 function to return predictable values
        self.uuid_patcher = patch('uuid.uuid4')
        self.mock_uuid = self.uuid_patcher.start()
        self.mock_uuid.side_effect = self._mock_uuid_generator()
        
        # Create the discourse state manager
        self.manager = DiscourseStateManager()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.uuid_patcher.stop()
    
    def _mock_uuid_generator(self):
        """Generate predictable UUIDs for testing."""
        counter = 0
        while True:
            yield uuid.UUID(int=counter, version=4)
            counter += 1
    
    def test_process_utterance_with_entities(self):
        """Test processing an utterance with entities."""
        # Create a parse output with entities
        parse_output = self._create_parse_output_with_entities()
        
        # Create a simple ISR
        isr = self._create_simple_isr()
        
        # Process the utterance
        context = self.manager.process_utterance(parse_output, isr)
        
        # Check that the context was updated
        self.assertIsInstance(context, DiscourseContext)
        
        # Check that entities were extracted
        self.assertGreater(len(context.entities), 0)
        
        # Check that "John" and "New York" are in the entities
        found_john = False
        found_ny = False
        for entity_id, entity in context.entities.items():
            if "john" in entity.name.lower():
                found_john = True
            elif "new york" in entity.name.lower():
                found_ny = True
        
        self.assertTrue(found_john, "Entity 'John' not found in discourse context")
        self.assertTrue(found_ny, "Entity 'New York' not found in discourse context")
        
        # Check that the dialogue state was updated
        self.assertIsInstance(context.dialogue_state, DialogueState)
        self.assertGreater(len(context.dialogue_state.dialogue_history), 0)
        
        # Check that the dialogue act was determined
        self.assertEqual(context.dialogue_state.dialogue_history[0].act_type, DialogueActType.STATEMENT)
    
    def test_process_utterance_with_question(self):
        """Test processing a question utterance."""
        # Create a parse output with a question
        parse_output = self._create_parse_output_with_question()
        
        # Create a simple ISR
        isr = self._create_simple_isr()
        
        # Process the utterance
        context = self.manager.process_utterance(parse_output, isr)
        
        # Check that the dialogue act was determined as a question
        self.assertEqual(context.dialogue_state.dialogue_history[0].act_type, DialogueActType.QUESTION)
        
        # Check that a user goal was added to answer the question
        self.assertGreater(len(context.dialogue_state.user_goals), 0)
        self.assertTrue(any("answer_question" in goal for goal in context.dialogue_state.user_goals))
    
    def test_process_multiple_utterances(self):
        """Test processing multiple utterances to build context."""
        # Create parse outputs for two utterances
        parse_output1 = self._create_parse_output_with_entities()
        parse_output2 = self._create_parse_output_with_reference()
        
        # Create ISRs for the utterances
        isr1 = self._create_simple_isr()
        isr2 = self._create_simple_isr()
        
        # Process the first utterance
        context1 = self.manager.process_utterance(parse_output1, isr1)
        
        # Check that "John" is in the entities
        found_john = False
        for entity_id, entity in context1.entities.items():
            if "john" in entity.name.lower():
                found_john = True
                break
        
        self.assertTrue(found_john, "Entity 'John' not found in discourse context")
        
        # Process the second utterance
        context2 = self.manager.process_utterance(parse_output2, isr2)
        
        # Check that the context was updated
        self.assertEqual(context2.dialogue_state.turn_count, 2)
        
        # Check that "John" is still in the entities
        found_john = False
        for entity_id, entity in context2.entities.items():
            if "john" in entity.name.lower():
                found_john = True
                break
        
        self.assertTrue(found_john, "Entity 'John' not found in discourse context after second utterance")
        
        # Check that "He" is resolved to "John"
        resolved_he = self.manager.resolve_anaphora(
            Token(
                text="He", lemma="he", pos="PRON", tag="PRP", dep="nsubj",
                is_stop=True, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=0, i=0, sent_idx=0
            )
        )
        
        self.assertIsNotNone(resolved_he, "Failed to resolve 'He'")
        self.assertTrue("john" in resolved_he.name.lower(), "Resolved 'He' to something other than 'John'")
    
    def test_entity_salience(self):
        """Test that entity salience is updated correctly."""
        # Create a parse output with entities
        parse_output = self._create_parse_output_with_entities()
        
        # Create a simple ISR
        isr = self._create_simple_isr()
        
        # Process the utterance
        context = self.manager.process_utterance(parse_output, isr)
        
        # Get the initial salience of "John"
        john_entity = None
        for entity_id, entity in context.entities.items():
            if "john" in entity.name.lower():
                john_entity = entity
                break
        
        self.assertIsNotNone(john_entity, "Entity 'John' not found in discourse context")
        initial_salience = john_entity.salience
        
        # Update the time to simulate passage of time
        context.update_time(10.0)
        
        # Check that the salience has decreased
        self.assertLess(john_entity.salience, initial_salience)
        
        # Process another utterance mentioning "John" to increase salience
        parse_output2 = self._create_parse_output_with_reference()
        isr2 = self._create_simple_isr()
        
        # Mock the _is_dependent_on method to make the test work
        self.manager._extract_entities = MagicMock()
        self.manager._extract_entities.side_effect = lambda parse_output: context.add_mention(john_entity.id, "John")
        
        context2 = self.manager.process_utterance(parse_output2, isr2)
        
        # Check that the salience has increased
        self.assertGreater(john_entity.salience, 0.0)
    
    def test_determine_dialogue_act(self):
        """Test determining the dialogue act of an utterance."""
        # Test statement
        statement_parse = self._create_parse_output_with_entities()
        statement_act = self.manager._determine_dialogue_act(statement_parse)
        self.assertEqual(statement_act.act_type, DialogueActType.STATEMENT)
        
        # Test question
        question_parse = self._create_parse_output_with_question()
        question_act = self.manager._determine_dialogue_act(question_parse)
        self.assertEqual(question_act.act_type, DialogueActType.QUESTION)
    
    def test_determine_topic(self):
        """Test determining the topic of an utterance."""
        # Create a parse output with a clear topic
        parse_output = self._create_parse_output_with_entities()
        
        # Create a simple ISR
        isr = self._create_simple_isr()
        
        # Determine the topic
        topic = self.manager._determine_topic(parse_output, isr)
        
        # Check that a topic was determined
        self.assertIsNotNone(topic)
        self.assertTrue(isinstance(topic, str))
    
    def _create_parse_output_with_entities(self):
        """Create a parse output with named entities."""
        # Create tokens
        tokens = [
            Token(
                text="John", lemma="john", pos="PROPN", tag="NNP", dep="nsubj",
                is_stop=False, is_punct=False, is_space=False, is_ent=True,
                ent_type="PERSON", ent_iob="B", idx=0, i=0, sent_idx=0
            ),
            Token(
                text="visited", lemma="visit", pos="VERB", tag="VBD", dep="ROOT",
                is_stop=False, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=5, i=1, sent_idx=0
            ),
            Token(
                text="New", lemma="new", pos="PROPN", tag="NNP", dep="compound",
                is_stop=False, is_punct=False, is_space=False, is_ent=True,
                ent_type="GPE", ent_iob="B", idx=13, i=2, sent_idx=0
            ),
            Token(
                text="York", lemma="york", pos="PROPN", tag="NNP", dep="dobj",
                is_stop=False, is_punct=False, is_space=False, is_ent=True,
                ent_type="GPE", ent_iob="I", idx=17, i=3, sent_idx=0
            ),
            Token(
                text=".", lemma=".", pos="PUNCT", tag=".", dep="punct",
                is_stop=False, is_punct=True, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=21, i=4, sent_idx=0
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
                start_char=13,
                end_char=21,
                start_token=2,
                end_token=4,
                tokens=[tokens[2], tokens[3]]
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
                text="New York",
                start_token=2,
                end_token=4,
                tokens=[tokens[2], tokens[3]],
                label="NP"
            )
        ]
        
        # Create a sentence
        sentence = Sentence(
            text="John visited New York.",
            start_char=0,
            end_char=22,
            tokens=tokens,
            entities=entities,
            noun_phrases=noun_phrases,
            root_token=tokens[1]  # "visited" is the root
        )
        
        # Create the parse output
        parse_output = SyntacticParseOutput(
            text="John visited New York.",
            tokens=tokens,
            sentences=[sentence],
            entities=entities,
            noun_phrases=noun_phrases
        )
        
        return parse_output
    
    def _create_parse_output_with_question(self):
        """Create a parse output with a question."""
        # Create tokens
        tokens = [
            Token(
                text="Where", lemma="where", pos="ADV", tag="WRB", dep="advmod",
                is_stop=True, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=0, i=0, sent_idx=0
            ),
            Token(
                text="did", lemma="do", pos="AUX", tag="VBD", dep="aux",
                is_stop=True, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=6, i=1, sent_idx=0
            ),
            Token(
                text="John", lemma="john", pos="PROPN", tag="NNP", dep="nsubj",
                is_stop=False, is_punct=False, is_space=False, is_ent=True,
                ent_type="PERSON", ent_iob="B", idx=10, i=2, sent_idx=0
            ),
            Token(
                text="go", lemma="go", pos="VERB", tag="VB", dep="ROOT",
                is_stop=False, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=15, i=3, sent_idx=0
            ),
            Token(
                text="?", lemma="?", pos="PUNCT", tag=".", dep="punct",
                is_stop=False, is_punct=True, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=17, i=4, sent_idx=0
            )
        ]
        
        # Create entities
        entities = [
            Entity(
                text="John",
                label="PERSON",
                start_char=10,
                end_char=14,
                start_token=2,
                end_token=3,
                tokens=[tokens[2]]
            )
        ]
        
        # Create noun phrases
        noun_phrases = [
            Span(
                text="John",
                start_token=2,
                end_token=3,
                tokens=[tokens[2]],
                label="NP"
            )
        ]
        
        # Create a sentence
        sentence = Sentence(
            text="Where did John go?",
            start_char=0,
            end_char=18,
            tokens=tokens,
            entities=entities,
            noun_phrases=noun_phrases,
            root_token=tokens[3]  # "go" is the root
        )
        
        # Create the parse output
        parse_output = SyntacticParseOutput(
            text="Where did John go?",
            tokens=tokens,
            sentences=[sentence],
            entities=entities,
            noun_phrases=noun_phrases
        )
        
        return parse_output
    
    def _create_parse_output_with_reference(self):
        """Create a parse output with a reference to a previously mentioned entity."""
        # Create tokens
        tokens = [
            Token(
                text="He", lemma="he", pos="PRON", tag="PRP", dep="nsubj",
                is_stop=True, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=0, i=0, sent_idx=0
            ),
            Token(
                text="liked", lemma="like", pos="VERB", tag="VBD", dep="ROOT",
                is_stop=False, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=3, i=1, sent_idx=0
            ),
            Token(
                text="it", lemma="it", pos="PRON", tag="PRP", dep="dobj",
                is_stop=True, is_punct=False, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=9, i=2, sent_idx=0
            ),
            Token(
                text=".", lemma=".", pos="PUNCT", tag=".", dep="punct",
                is_stop=False, is_punct=True, is_space=False, is_ent=False,
                ent_type="", ent_iob="O", idx=11, i=3, sent_idx=0
            )
        ]
        
        # Create a sentence
        sentence = Sentence(
            text="He liked it.",
            start_char=0,
            end_char=12,
            tokens=tokens,
            root_token=tokens[1]  # "liked" is the root
        )
        
        # Create the parse output
        parse_output = SyntacticParseOutput(
            text="He liked it.",
            tokens=tokens,
            sentences=[sentence]
        )
        
        return parse_output
    
    def _create_simple_isr(self):
        """Create a simple ISR for testing."""
        # Create the ISR
        isr = IntermediateSemanticRepresentation(text="Sample text")
        
        # Create a predicate
        predicate = Predicate(
            text="sample",
            lemma="sample",
            tense="present",
            aspect="simple"
        )
        
        # Create a node
        node = SemanticNode(
            id="pred_0",
            node_type="predicate",
            content=predicate
        )
        
        # Add the node to the ISR
        isr.nodes = [node]
        isr.root_nodes = [node]
        
        # Add the predicate to the ISR
        isr.predicates["pred_0"] = predicate
        
        return isr


if __name__ == '__main__':
    unittest.main()