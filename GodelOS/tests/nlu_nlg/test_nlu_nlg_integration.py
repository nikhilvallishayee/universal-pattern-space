"""
Integration tests for the NLU-NLG pipeline.

These tests verify that the NLU and NLG pipelines work together correctly,
converting natural language to AST nodes and back to natural language.
"""

import unittest
from unittest.mock import patch, MagicMock
import time
import re

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode
)
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType

from godelOS.nlu_nlg.nlu.pipeline import (
    NLUPipeline, NLUResult, create_nlu_pipeline
)
from godelOS.nlu_nlg.nlg.pipeline import (
    NLGPipeline, NLGResult, create_nlg_pipeline
)
from godelOS.nlu_nlg.nlu.discourse_manager import (
    DiscourseStateManager, DiscourseContext
)


class TestNLUNLGIntegration(unittest.TestCase):
    """Test cases for the integration of NLU and NLG pipelines."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a type system
        self.type_system = TypeSystemManager()
        
        # Register basic types
        self.entity_type = self.type_system.register_type(AtomicType("Entity"))
        self.boolean_type = self.type_system.register_type(AtomicType("Boolean"))
        self.proposition_type = self.type_system.register_type(AtomicType("Proposition"))
        
        # Create the NLU and NLG pipelines
        self.nlu_pipeline = create_nlu_pipeline(self.type_system)
        self.nlg_pipeline = create_nlg_pipeline(self.type_system)
    
    def test_nlu_nlg_roundtrip_simple(self):
        """Test a simple roundtrip from text to AST to text."""
        # Skip this test if we're running in a CI environment or don't have the required dependencies
        try:
            import spacy
            spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            self.skipTest("Skipping integration test due to missing dependencies")
        
        # Patch the _initialize_lexicon_ontology method to avoid loading WordNet
        with patch.object(self.nlu_pipeline, '_initialize_lexicon_ontology'):
            # Define a simple input text
            input_text = "The cat chases the mouse."
            
            # Process the text through the NLU pipeline
            nlu_result = self.nlu_pipeline.process(input_text)
            
            # Check that the NLU processing was successful
            self.assertTrue(nlu_result.success, f"NLU processing failed: {nlu_result.errors}")
            self.assertGreater(len(nlu_result.ast_nodes), 0, "No AST nodes were produced")
            
            # Process the AST nodes through the NLG pipeline
            nlg_result = self.nlg_pipeline.process(nlu_result.ast_nodes)
            
            # Check that the NLG processing was successful
            self.assertTrue(nlg_result.success, f"NLG processing failed: {nlg_result.errors}")
            self.assertIsNotNone(nlg_result.output_text, "No output text was produced")
            self.assertGreater(len(nlg_result.output_text), 0, "Output text is empty")
            
            # Check that the output text is semantically similar to the input text
            # For a simple test, we'll just check that the key words are present
            key_words = ["cat", "chase", "mouse"]
            for word in key_words:
                self.assertIn(word.lower(), nlg_result.output_text.lower(),
                             f"Key word '{word}' not found in output text")
    
    def test_nlu_nlg_roundtrip_with_context(self):
        """Test a roundtrip from text to AST to text with discourse context."""
        # Skip this test if we're running in a CI environment or don't have the required dependencies
        try:
            import spacy
            spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            self.skipTest("Skipping integration test due to missing dependencies")
        
        # Patch the _initialize_lexicon_ontology method to avoid loading WordNet
        with patch.object(self.nlu_pipeline, '_initialize_lexicon_ontology'):
            # Define a sequence of input texts
            input_texts = [
                "The cat chases the mouse.",
                "It is very fast.",
                "The mouse hides under the table."
            ]
            
            # Process the texts through the NLU pipeline, maintaining context
            discourse_context = None
            ast_nodes_list = []
            
            for text in input_texts:
                nlu_result = self.nlu_pipeline.process_with_context(text, discourse_context)
                self.assertTrue(nlu_result.success, f"NLU processing failed for '{text}': {nlu_result.errors}")
                ast_nodes_list.append(nlu_result.ast_nodes)
                discourse_context = nlu_result.discourse_context
            
            # Process the AST nodes through the NLG pipeline, maintaining context
            discourse_context = None
            output_texts = []
            
            for ast_nodes in ast_nodes_list:
                nlg_result = self.nlg_pipeline.process_with_context(ast_nodes, discourse_context)
                self.assertTrue(nlg_result.success, f"NLG processing failed: {nlg_result.errors}")
                output_texts.append(nlg_result.output_text)
                discourse_context = nlg_result.discourse_context
            
            # Check that the output texts are semantically similar to the input texts
            # For a simple test, we'll just check that the key words are present
            key_words_list = [
                ["cat", "chase", "mouse"],
                ["fast"],
                ["mouse", "hide", "table"]
            ]
            
            for i, (output_text, key_words) in enumerate(zip(output_texts, key_words_list)):
                for word in key_words:
                    self.assertIn(word.lower(), output_text.lower(),
                                 f"Key word '{word}' not found in output text {i+1}")
    
    def test_semantic_similarity(self):
        """Test the semantic similarity of input and output texts."""
        # Skip this test if we're running in a CI environment or don't have the required dependencies
        try:
            import spacy
            spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            self.skipTest("Skipping integration test due to missing dependencies")
        
        # Patch the _initialize_lexicon_ontology method to avoid loading WordNet
        with patch.object(self.nlu_pipeline, '_initialize_lexicon_ontology'):
            # Define test cases with input texts and expected key concepts
            test_cases = [
                {
                    "input": "The cat chases the mouse.",
                    "key_concepts": ["cat", "chase", "mouse"]
                },
                {
                    "input": "Every student reads a book.",
                    "key_concepts": ["student", "read", "book"]
                },
                {
                    "input": "John believes that it will rain tomorrow.",
                    "key_concepts": ["believe", "rain", "tomorrow"]
                }
            ]
            
            for test_case in test_cases:
                input_text = test_case["input"]
                key_concepts = test_case["key_concepts"]
                
                # Process the text through the NLU pipeline
                nlu_result = self.nlu_pipeline.process(input_text)
                
                # Check that the NLU processing was successful
                self.assertTrue(nlu_result.success, f"NLU processing failed for '{input_text}': {nlu_result.errors}")
                self.assertGreater(len(nlu_result.ast_nodes), 0, "No AST nodes were produced")
                
                # Process the AST nodes through the NLG pipeline
                nlg_result = self.nlg_pipeline.process(nlu_result.ast_nodes)
                
                # Check that the NLG processing was successful
                self.assertTrue(nlg_result.success, f"NLG processing failed: {nlg_result.errors}")
                self.assertIsNotNone(nlg_result.output_text, "No output text was produced")
                self.assertGreater(len(nlg_result.output_text), 0, "Output text is empty")
                
                # Check that the output text contains the key concepts
                output_text = nlg_result.output_text.lower()
                for concept in key_concepts:
                    # Check for the concept or its lemma (e.g., "chase" or "chases")
                    concept_pattern = re.compile(r'\b' + concept + r'[es]?\b')
                    self.assertTrue(concept_pattern.search(output_text),
                                   f"Key concept '{concept}' not found in output text: '{output_text}'")
    
    def test_nlu_nlg_with_manual_ast(self):
        """Test the NLG pipeline with manually created AST nodes."""
        # Create a simple AST node structure
        operator = ConstantNode(
            name="chase",
            type_ref=self.proposition_type,
            value=None
        )
        
        subject = ConstantNode(
            name="cat",
            type_ref=self.entity_type,
            value=None
        )
        
        object_node = ConstantNode(
            name="mouse",
            type_ref=self.entity_type,
            value=None
        )
        
        application_node = ApplicationNode(
            operator=operator,
            arguments=[subject, object_node],
            type_ref=self.boolean_type
        )
        
        # Process the AST node through the NLG pipeline
        nlg_result = self.nlg_pipeline.process([application_node])
        
        # Check that the NLG processing was successful
        self.assertTrue(nlg_result.success, f"NLG processing failed: {nlg_result.errors}")
        self.assertIsNotNone(nlg_result.output_text, "No output text was produced")
        self.assertGreater(len(nlg_result.output_text), 0, "Output text is empty")
        
        # Check that the output text contains the key concepts
        output_text = nlg_result.output_text.lower()
        key_concepts = ["cat", "chase", "mouse"]
        for concept in key_concepts:
            # Check for the concept or its lemma (e.g., "chase" or "chases")
            concept_pattern = re.compile(r'\b' + concept + r'[es]?\b')
            self.assertTrue(concept_pattern.search(output_text),
                           f"Key concept '{concept}' not found in output text: '{output_text}'")


if __name__ == '__main__':
    unittest.main()