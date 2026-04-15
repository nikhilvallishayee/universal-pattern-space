"""
Unit tests for the LexicalAnalyzerParser module.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.nlu_nlg.nlu.lexical_analyzer_parser import (

import pytest
import importlib

class TestLexicalAnalyzerParser(unittest.TestCase):
    """Test cases for the LexicalAnalyzerParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock spaCy model to avoid actual NLP processing during tests
        self.nlp_patcher = patch('godelOS.nlu_nlg.nlu.lexical_analyzer_parser.spacy.load')
        self.mock_nlp = self.nlp_patcher.start()
        
        # Create a mock Doc object
        self.mock_doc = MagicMock()
        self.mock_nlp.return_value = MagicMock(return_value=self.mock_doc)
        
        # Initialize the parser with the mock model
        self.parser = LexicalAnalyzerParser()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.nlp_patcher.stop()
    
    def test_token_from_spacy_token(self):
        """Test creating a Token from a spaCy Token."""
        # Create a mock spaCy token
        mock_spacy_token = MagicMock()
        mock_spacy_token.text = "test"
        mock_spacy_token.lemma_ = "test"
        mock_spacy_token.pos_ = "NOUN"
        mock_spacy_token.tag_ = "NN"
        mock_spacy_token.dep_ = "nsubj"
        mock_spacy_token.is_stop = False
        mock_spacy_token.is_punct = False
        mock_spacy_token.is_space = False
        mock_spacy_token.ent_type_ = ""
        mock_spacy_token.ent_iob_ = "O"
        mock_spacy_token.idx = 0
        mock_spacy_token.i = 0
        mock_spacy_token.is_alpha = True
        mock_spacy_token.is_digit = False
        mock_spacy_token.is_lower = True
        mock_spacy_token.is_upper = False
        mock_spacy_token.is_title = False
        mock_spacy_token.is_sent_start = True
        mock_spacy_token.morph = MagicMock(to_dict=MagicMock(return_value={}))
        
        # Create a Token from the mock spaCy token
        token = Token.from_spacy_token(mock_spacy_token, sent_idx=0)
        
        # Check that the Token was created correctly
        self.assertEqual(token.text, "test")
        self.assertEqual(token.lemma, "test")
        self.assertEqual(token.pos, "NOUN")
        self.assertEqual(token.tag, "NN")
        self.assertEqual(token.dep, "nsubj")
        self.assertFalse(token.is_stop)
        self.assertFalse(token.is_punct)
        self.assertFalse(token.is_space)
        self.assertFalse(token.is_ent)
        self.assertEqual(token.ent_type, "")
        self.assertEqual(token.ent_iob, "O")
        self.assertEqual(token.idx, 0)
        self.assertEqual(token.i, 0)
        self.assertTrue(token.is_alpha)
        self.assertFalse(token.is_digit)
        self.assertTrue(token.is_lower)
        self.assertFalse(token.is_upper)
        self.assertFalse(token.is_title)
        self.assertTrue(token.is_sent_start)
        self.assertEqual(token.morphology, {})
        self.assertEqual(token.sent_idx, 0)
    
    def test_process_simple_sentence(self):
        """Test processing a simple sentence."""
        # Set up the mock Doc object
        text = "The cat chased the mouse."
        self.mock_doc.text = text
        
        # Create mock tokens
        mock_tokens = []
        token_data = [
            {"text": "The", "lemma_": "the", "pos_": "DET", "tag_": "DT", "dep_": "det", "i": 0},
            {"text": "cat", "lemma_": "cat", "pos_": "NOUN", "tag_": "NN", "dep_": "nsubj", "i": 1},
            {"text": "chased", "lemma_": "chase", "pos_": "VERB", "tag_": "VBD", "dep_": "ROOT", "i": 2},
            {"text": "the", "lemma_": "the", "pos_": "DET", "tag_": "DT", "dep_": "det", "i": 3},
            {"text": "mouse", "lemma_": "mouse", "pos_": "NOUN", "tag_": "NN", "dep_": "dobj", "i": 4},
            {"text": ".", "lemma_": ".", "pos_": "PUNCT", "tag_": ".", "dep_": "punct", "i": 5}
        ]
        
        for i, data in enumerate(token_data):
            mock_token = MagicMock()
            for key, value in data.items():
                setattr(mock_token, key, value)
            
            # Set default values for attributes not in the data
            mock_token.is_stop = False
            mock_token.is_punct = data["pos_"] == "PUNCT"
            mock_token.is_space = False
            mock_token.ent_type_ = ""
            mock_token.ent_iob_ = "O"
            mock_token.idx = i * 5  # Simple approximation
            mock_token.is_alpha = not mock_token.is_punct
            mock_token.is_digit = False
            mock_token.is_lower = data["text"].islower()
            mock_token.is_upper = data["text"].isupper()
            mock_token.is_title = data["text"].istitle()
            mock_token.is_sent_start = i == 0
            mock_token.morph = MagicMock(to_dict=MagicMock(return_value={}))
            
            mock_tokens.append(mock_token)
        
        # Create a mock sentence
        mock_sent = MagicMock()
        mock_sent.text = text
        mock_sent.start_char = 0
        mock_sent.end_char = len(text)
        mock_sent.__iter__.return_value = iter(mock_tokens)
        
        # Set up the mock Doc with the tokens and sentence
        self.mock_doc.__iter__.return_value = iter(mock_tokens)
        self.mock_doc.sents = [mock_sent]
        self.mock_doc.ents = []  # No named entities
        
        # Create mock noun chunks
        mock_np1 = MagicMock()
        mock_np1.text = "The cat"
        mock_np1.start = 0
        mock_np1.end = 2
        mock_np1.start_char = 0
        mock_np1.end_char = 7
        mock_np1.__iter__.return_value = iter(mock_tokens[0:2])
        
        mock_np2 = MagicMock()
        mock_np2.text = "the mouse"
        mock_np2.start = 3
        mock_np2.end = 5
        mock_np2.start_char = 14
        mock_np2.end_char = 23
        mock_np2.__iter__.return_value = iter(mock_tokens[3:5])
        
        self.mock_doc.noun_chunks = [mock_np1, mock_np2]
        
        # Process the text
        result = self.parser.process(text)
        
        # Check that the result is a SyntacticParseOutput
        self.assertIsInstance(result, SyntacticParseOutput)
        
        # Check that the text was preserved
        self.assertEqual(result.text, text)
        
        # Check that the tokens were processed
        self.assertEqual(len(result.tokens), 6)
        self.assertEqual(result.tokens[0].text, "The")
        self.assertEqual(result.tokens[1].text, "cat")
        self.assertEqual(result.tokens[2].text, "chased")
        self.assertEqual(result.tokens[3].text, "the")
        self.assertEqual(result.tokens[4].text, "mouse")
        self.assertEqual(result.tokens[5].text, ".")
        
        # Check that the sentence was processed
        self.assertEqual(len(result.sentences), 1)
        self.assertEqual(result.sentences[0].text, text)
        
        # Check that the noun phrases were processed
        self.assertEqual(len(result.noun_phrases), 2)
        self.assertEqual(result.noun_phrases[0].text, "The cat")
        self.assertEqual(result.noun_phrases[1].text, "the mouse")
    
    def test_process_with_named_entities(self):
        """Test processing a sentence with named entities."""
        # Set up the mock Doc object
        text = "John visited New York last week."
        self.mock_doc.text = text
        
        # Create mock tokens
        mock_tokens = []
        token_data = [
            {"text": "John", "lemma_": "john", "pos_": "PROPN", "tag_": "NNP", "dep_": "nsubj", "i": 0, "ent_type_": "PERSON", "ent_iob_": "B"},
            {"text": "visited", "lemma_": "visit", "pos_": "VERB", "tag_": "VBD", "dep_": "ROOT", "i": 1, "ent_type_": "", "ent_iob_": "O"},
            {"text": "New", "lemma_": "new", "pos_": "PROPN", "tag_": "NNP", "dep_": "compound", "i": 2, "ent_type_": "GPE", "ent_iob_": "B"},
            {"text": "York", "lemma_": "york", "pos_": "PROPN", "tag_": "NNP", "dep_": "dobj", "i": 3, "ent_type_": "GPE", "ent_iob_": "I"},
            {"text": "last", "lemma_": "last", "pos_": "ADJ", "tag_": "JJ", "dep_": "amod", "i": 4, "ent_type_": "DATE", "ent_iob_": "B"},
            {"text": "week", "lemma_": "week", "pos_": "NOUN", "tag_": "NN", "dep_": "npadvmod", "i": 5, "ent_type_": "DATE", "ent_iob_": "I"},
            {"text": ".", "lemma_": ".", "pos_": "PUNCT", "tag_": ".", "dep_": "punct", "i": 6, "ent_type_": "", "ent_iob_": "O"}
        ]
        
        for i, data in enumerate(token_data):
            mock_token = MagicMock()
            for key, value in data.items():
                setattr(mock_token, key, value)
            
            # Set default values for attributes not in the data
            mock_token.is_stop = False
            mock_token.is_punct = data["pos_"] == "PUNCT"
            mock_token.is_space = False
            mock_token.idx = i * 5  # Simple approximation
            mock_token.is_alpha = not mock_token.is_punct
            mock_token.is_digit = False
            mock_token.is_lower = data["text"].islower()
            mock_token.is_upper = data["text"].isupper()
            mock_token.is_title = data["text"].istitle()
            mock_token.is_sent_start = i == 0
            mock_token.morph = MagicMock(to_dict=MagicMock(return_value={}))
            
            mock_tokens.append(mock_token)
        
        # Create a mock sentence
        mock_sent = MagicMock()
        mock_sent.text = text
        mock_sent.start_char = 0
        mock_sent.end_char = len(text)
        mock_sent.__iter__.return_value = iter(mock_tokens)
        
        # Set up the mock Doc with the tokens and sentence
        self.mock_doc.__iter__.return_value = iter(mock_tokens)
        self.mock_doc.sents = [mock_sent]
        
        # Create mock entities
        mock_ent1 = MagicMock()
        mock_ent1.text = "John"
        mock_ent1.label_ = "PERSON"
        mock_ent1.start_char = 0
        mock_ent1.end_char = 4
        mock_ent1.start = 0
        mock_ent1.end = 1
        mock_ent1.__iter__.return_value = iter(mock_tokens[0:1])
        
        mock_ent2 = MagicMock()
        mock_ent2.text = "New York"
        mock_ent2.label_ = "GPE"
        mock_ent2.start_char = 13
        mock_ent2.end_char = 21
        mock_ent2.start = 2
        mock_ent2.end = 4
        mock_ent2.__iter__.return_value = iter(mock_tokens[2:4])
        
        mock_ent3 = MagicMock()
        mock_ent3.text = "last week"
        mock_ent3.label_ = "DATE"
        mock_ent3.start_char = 22
        mock_ent3.end_char = 31
        mock_ent3.start = 4
        mock_ent3.end = 6
        mock_ent3.__iter__.return_value = iter(mock_tokens[4:6])
        
        self.mock_doc.ents = [mock_ent1, mock_ent2, mock_ent3]
        
        # Create mock noun chunks
        mock_np1 = MagicMock()
        mock_np1.text = "John"
        mock_np1.start = 0
        mock_np1.end = 1
        mock_np1.start_char = 0
        mock_np1.end_char = 4
        mock_np1.__iter__.return_value = iter(mock_tokens[0:1])
        
        mock_np2 = MagicMock()
        mock_np2.text = "New York"
        mock_np2.start = 2
        mock_np2.end = 4
        mock_np2.start_char = 13
        mock_np2.end_char = 21
        mock_np2.__iter__.return_value = iter(mock_tokens[2:4])
        
        mock_np3 = MagicMock()
        mock_np3.text = "last week"
        mock_np3.start = 4
        mock_np3.end = 6
        mock_np3.start_char = 22
        mock_np3.end_char = 31
        mock_np3.__iter__.return_value = iter(mock_tokens[4:6])
        
        self.mock_doc.noun_chunks = [mock_np1, mock_np2, mock_np3]
        
        # Process the text
        result = self.parser.process(text)
        
        # Check that the result is a SyntacticParseOutput
        self.assertIsInstance(result, SyntacticParseOutput)
        
        # Check that the text was preserved
        self.assertEqual(result.text, text)
        
        # Check that the tokens were processed
        self.assertEqual(len(result.tokens), 7)
        
        # Check that the entities were processed
        self.assertEqual(len(result.entities), 3)
        self.assertEqual(result.entities[0].text, "John")
        self.assertEqual(result.entities[0].label, "PERSON")
        self.assertEqual(result.entities[1].text, "New York")
        self.assertEqual(result.entities[1].label, "GPE")
        self.assertEqual(result.entities[2].text, "last week")
        self.assertEqual(result.entities[2].label, "DATE")
        
        # Check that the noun phrases were processed
        self.assertEqual(len(result.noun_phrases), 3)
        self.assertEqual(result.noun_phrases[0].text, "John")
        self.assertEqual(result.noun_phrases[1].text, "New York")
        self.assertEqual(result.noun_phrases[2].text, "last week")
    
    def test_is_dependent_on(self):
        """Test the _is_dependent_on method."""
        # Create mock tokens
        token1 = Token(
            text="cat", lemma="cat", pos="NOUN", tag="NN", dep="nsubj",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=4, i=1, sent_idx=0
        )
        
        token2 = Token(
            text="chased", lemma="chase", pos="VERB", tag="VBD", dep="ROOT",
            is_stop=False, is_punct=False, is_space=False, is_ent=False,
            ent_type="", ent_iob="O", idx=8, i=2, sent_idx=0
        )
        
        # Test direct dependency
        self.assertTrue(self.parser._is_dependent_on(token1, token2, [token1, token2]))
        
        # Test self-dependency
        self.assertTrue(self.parser._is_dependent_on(token2, token2, [token1, token2]))
        
        # Test non-dependency
        self.assertFalse(self.parser._is_dependent_on(token2, token1, [token1, token2]))


if __name__ == '__main__':
    unittest.main()