"""
Unit tests for the SurfaceRealizer module.
"""

import unittest
from unittest.mock import patch, MagicMock

from godelOS.nlu_nlg.nlg.sentence_generator import (
    SentencePlan, LinguisticConstituent, ReferringExpressionType, 
    GrammaticalRole, TenseAspect
)
from godelOS.nlu_nlg.nlg.surface_realizer import SurfaceRealizer


class TestSurfaceRealizer(unittest.TestCase):
    """Test cases for the SurfaceRealizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create the surface realizer
        self.surface_realizer = SurfaceRealizer()
    
    def test_realize_text_empty(self):
        """Test realizing text with an empty list of sentence plans."""
        # Realize text
        text = self.surface_realizer.realize_text([])
        
        # Check that the result is an empty string
        self.assertEqual(text, "")
    
    def test_realize_text_single_sentence(self):
        """Test realizing text with a single sentence plan."""
        # Create a sentence plan
        root = LinguisticConstituent(
            id="root",
            constituent_type="S"
        )
        
        # Add a subject
        subject = LinguisticConstituent(
            id="subject",
            constituent_type="NP",
            head="cat"
        )
        root.add_child(subject)
        
        # Add a verb
        verb = LinguisticConstituent(
            id="verb",
            constituent_type="VP",
            head="chase"
        )
        root.add_child(verb)
        
        # Add an object
        object_np = LinguisticConstituent(
            id="object",
            constituent_type="NP",
            head="mouse"
        )
        verb.add_child(object_np)
        
        # Create the sentence plan
        plan = SentencePlan(
            id="sentence_0",
            root=root,
            tense_aspect=TenseAspect.SIMPLE_PRESENT,
            voice="active",
            mood="indicative"
        )
        
        # Add referring expressions
        plan.add_referring_expression("subject", ReferringExpressionType.DEFINITE_NP)
        plan.add_referring_expression("object", ReferringExpressionType.DEFINITE_NP)
        
        # Realize text
        text = self.surface_realizer.realize_text([plan])
        
        # Check that the result is a non-empty string
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)
        
        # Check that the text contains the expected words
        self.assertIn("cat", text.lower())
        self.assertIn("chase", text.lower())
        self.assertIn("mouse", text.lower())
    
    def test_realize_text_multiple_sentences(self):
        """Test realizing text with multiple sentence plans."""
        # Create the first sentence plan
        root1 = LinguisticConstituent(
            id="root1",
            constituent_type="S"
        )
        
        # Add a subject
        subject1 = LinguisticConstituent(
            id="subject1",
            constituent_type="NP",
            head="cat"
        )
        root1.add_child(subject1)
        
        # Add a verb
        verb1 = LinguisticConstituent(
            id="verb1",
            constituent_type="VP",
            head="chase"
        )
        root1.add_child(verb1)
        
        # Add an object
        object1 = LinguisticConstituent(
            id="object1",
            constituent_type="NP",
            head="mouse"
        )
        verb1.add_child(object1)
        
        # Create the first sentence plan
        plan1 = SentencePlan(
            id="sentence_0",
            root=root1,
            tense_aspect=TenseAspect.SIMPLE_PRESENT,
            voice="active",
            mood="indicative"
        )
        
        # Add referring expressions
        plan1.add_referring_expression("subject1", ReferringExpressionType.DEFINITE_NP)
        plan1.add_referring_expression("object1", ReferringExpressionType.DEFINITE_NP)
        
        # Create the second sentence plan
        root2 = LinguisticConstituent(
            id="root2",
            constituent_type="S"
        )
        
        # Add a subject
        subject2 = LinguisticConstituent(
            id="subject2",
            constituent_type="NP",
            head="mouse"
        )
        root2.add_child(subject2)
        
        # Add a verb
        verb2 = LinguisticConstituent(
            id="verb2",
            constituent_type="VP",
            head="hide"
        )
        root2.add_child(verb2)
        
        # Create the second sentence plan
        plan2 = SentencePlan(
            id="sentence_1",
            root=root2,
            tense_aspect=TenseAspect.SIMPLE_PRESENT,
            voice="active",
            mood="indicative"
        )
        
        # Add referring expressions
        plan2.add_referring_expression("subject2", ReferringExpressionType.DEFINITE_NP)
        
        # Realize text
        text = self.surface_realizer.realize_text([plan1, plan2])
        
        # Check that the result is a non-empty string
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)
        
        # Check that the text contains the expected words
        self.assertIn("cat", text.lower())
        self.assertIn("chase", text.lower())
        self.assertIn("mouse", text.lower())
        self.assertIn("hide", text.lower())
        
        # Check that the text contains two sentences
        sentences = text.split(".")
        non_empty_sentences = [s.strip() for s in sentences if s.strip()]
        self.assertEqual(len(non_empty_sentences), 2)
    
    def test_realize_sentence(self):
        """Test realizing a sentence from a sentence plan."""
        # Create a sentence plan
        root = LinguisticConstituent(
            id="root",
            constituent_type="S"
        )
        
        # Add a subject
        subject = LinguisticConstituent(
            id="subject",
            constituent_type="NP",
            head="cat"
        )
        root.add_child(subject)
        
        # Add a verb
        verb = LinguisticConstituent(
            id="verb",
            constituent_type="VP",
            head="chase"
        )
        root.add_child(verb)
        
        # Add an object
        object_np = LinguisticConstituent(
            id="object",
            constituent_type="NP",
            head="mouse"
        )
        verb.add_child(object_np)
        
        # Create the sentence plan
        plan = SentencePlan(
            id="sentence_0",
            root=root,
            tense_aspect=TenseAspect.SIMPLE_PRESENT,
            voice="active",
            mood="indicative"
        )
        
        # Add referring expressions
        plan.add_referring_expression("subject", ReferringExpressionType.DEFINITE_NP)
        plan.add_referring_expression("object", ReferringExpressionType.DEFINITE_NP)
        
        # Realize the sentence
        sentence = self.surface_realizer._realize_sentence(plan, {})
        
        # Check that the result is a non-empty string
        self.assertIsInstance(sentence, str)
        self.assertGreater(len(sentence), 0)
        
        # Check that the sentence contains the expected words
        self.assertIn("cat", sentence.lower())
        self.assertIn("chase", sentence.lower())
        self.assertIn("mouse", sentence.lower())
        
        # Check that the sentence is properly capitalized and punctuated
        self.assertEqual(sentence[0], sentence[0].upper())
        self.assertTrue(sentence.endswith("."))
    
    def test_realize_constituent_np(self):
        """Test realizing a noun phrase constituent."""
        # Create a noun phrase constituent
        np = LinguisticConstituent(
            id="np",
            constituent_type="NP",
            head="cat",
            content_element_id="element_0"
        )
        
        # Create a sentence plan
        plan = SentencePlan(
            id="sentence_0",
            root=LinguisticConstituent(id="root", constituent_type="S"),
            tense_aspect=TenseAspect.SIMPLE_PRESENT,
            voice="active",
            mood="indicative"
        )
        
        # Add referring expressions
        plan.add_referring_expression("element_0", ReferringExpressionType.DEFINITE_NP)
        
        # Realize the constituent
        words = self.surface_realizer._realize_constituent(np, plan, {})
        
        # Check that the result is a list of words
        self.assertIsInstance(words, list)
        self.assertGreater(len(words), 0)
        
        # Check that the words include the determiner and the head noun
        self.assertEqual(words[0], "the")
        self.assertEqual(words[1], "cat")
    
    def test_realize_constituent_vp(self):
        """Test realizing a verb phrase constituent."""
        # Create a verb phrase constituent
        vp = LinguisticConstituent(
            id="vp",
            constituent_type="VP",
            head="chase"
        )
        
        # Create a sentence plan
        plan = SentencePlan(
            id="sentence_0",
            root=LinguisticConstituent(id="root", constituent_type="S"),
            tense_aspect=TenseAspect.SIMPLE_PRESENT,
            voice="active",
            mood="indicative"
        )
        
        # Realize the constituent
        words = self.surface_realizer._realize_constituent(vp, plan, {})
        
        # Check that the result is a list of words
        self.assertIsInstance(words, list)
        self.assertGreater(len(words), 0)
        
        # Check that the words include the verb
        self.assertEqual(words[0], "chases")
    
    def test_inflect_verb_regular(self):
        """Test inflecting regular verbs."""
        # Test simple present, third person singular
        words = self.surface_realizer._inflect_verb("chase", TenseAspect.SIMPLE_PRESENT, "3sg")
        self.assertEqual(words, ["chases"])
        
        # Test simple past
        words = self.surface_realizer._inflect_verb("chase", TenseAspect.SIMPLE_PAST, "3sg")
        self.assertEqual(words, ["chased"])
        
        # Test present progressive
        words = self.surface_realizer._inflect_verb("chase", TenseAspect.PRESENT_PROGRESSIVE, "3sg")
        self.assertEqual(words, ["is", "chasing"])
        
        # Test past progressive
        words = self.surface_realizer._inflect_verb("chase", TenseAspect.PAST_PROGRESSIVE, "3sg")
        self.assertEqual(words, ["was", "chasing"])
        
        # Test present perfect
        words = self.surface_realizer._inflect_verb("chase", TenseAspect.PRESENT_PERFECT, "3sg")
        self.assertEqual(words, ["has", "chased"])
        
        # Test past perfect
        words = self.surface_realizer._inflect_verb("chase", TenseAspect.PAST_PERFECT, "3sg")
        self.assertEqual(words, ["had", "chased"])
        
        # Test future
        words = self.surface_realizer._inflect_verb("chase", TenseAspect.FUTURE, "3sg")
        self.assertEqual(words, ["will", "chase"])
        
        # Test future perfect
        words = self.surface_realizer._inflect_verb("chase", TenseAspect.FUTURE_PERFECT, "3sg")
        self.assertEqual(words, ["will", "have", "chased"])
    
    def test_inflect_verb_irregular(self):
        """Test inflecting irregular verbs."""
        # Test simple present, third person singular
        words = self.surface_realizer._inflect_verb("be", TenseAspect.SIMPLE_PRESENT, "3sg")
        self.assertEqual(words, ["is"])
        
        # Test simple past
        words = self.surface_realizer._inflect_verb("be", TenseAspect.SIMPLE_PAST, "3sg")
        self.assertEqual(words, ["was"])
        
        # Test present progressive
        words = self.surface_realizer._inflect_verb("be", TenseAspect.PRESENT_PROGRESSIVE, "3sg")
        self.assertEqual(words, ["is", "being"])
        
        # Test past progressive
        words = self.surface_realizer._inflect_verb("be", TenseAspect.PAST_PROGRESSIVE, "3sg")
        self.assertEqual(words, ["was", "being"])
        
        # Test present perfect
        words = self.surface_realizer._inflect_verb("be", TenseAspect.PRESENT_PERFECT, "3sg")
        self.assertEqual(words, ["has", "been"])
        
        # Test past perfect
        words = self.surface_realizer._inflect_verb("be", TenseAspect.PAST_PERFECT, "3sg")
        self.assertEqual(words, ["had", "been"])
        
        # Test future
        words = self.surface_realizer._inflect_verb("be", TenseAspect.FUTURE, "3sg")
        self.assertEqual(words, ["will", "be"])
        
        # Test future perfect
        words = self.surface_realizer._inflect_verb("be", TenseAspect.FUTURE_PERFECT, "3sg")
        self.assertEqual(words, ["will", "have", "been"])
    
    def test_apply_sentence_formatting(self):
        """Test applying sentence-level formatting."""
        # Test formatting a statement
        sentence = self.surface_realizer._apply_sentence_formatting("cat chases mouse", "indicative")
        self.assertEqual(sentence, "Cat chases mouse.")
        
        # Test formatting a question
        sentence = self.surface_realizer._apply_sentence_formatting("does cat chase mouse", "interrogative")
        self.assertEqual(sentence, "Does cat chase mouse?")
        
        # Test formatting a command
        sentence = self.surface_realizer._apply_sentence_formatting("chase the mouse", "imperative")
        self.assertEqual(sentence, "Chase the mouse.")
    
    def test_apply_text_formatting(self):
        """Test applying text-level formatting."""
        # Test fixing spacing around punctuation
        text = self.surface_realizer._apply_text_formatting("Hello , world .")
        self.assertEqual(text, "Hello, world.")
        
        # Test fixing spacing after punctuation
        text = self.surface_realizer._apply_text_formatting("Hello,world.")
        self.assertEqual(text, "Hello, world.")
        
        # Test fixing multiple spaces
        text = self.surface_realizer._apply_text_formatting("Hello   world")
        self.assertEqual(text, "Hello world")
        
        # Test trimming whitespace
        text = self.surface_realizer._apply_text_formatting("  Hello world  ")
        self.assertEqual(text, "Hello world")


if __name__ == '__main__':
    unittest.main()