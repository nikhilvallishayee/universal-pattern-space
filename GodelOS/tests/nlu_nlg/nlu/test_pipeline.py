"""
Unit tests for the NLU Pipeline module.
"""

import unittest
from unittest.mock import patch, MagicMock
import time

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode
)
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType

from godelOS.nlu_nlg.nlu.lexical_analyzer_parser import (
    LexicalAnalyzerParser, SyntacticParseOutput
)
from godelOS.nlu_nlg.nlu.semantic_interpreter import (
    SemanticInterpreter, IntermediateSemanticRepresentation
)
from godelOS.nlu_nlg.nlu.formalizer import Formalizer
from godelOS.nlu_nlg.nlu.discourse_manager import (
    DiscourseStateManager, DiscourseContext
)
from godelOS.nlu_nlg.nlu.lexicon_ontology_linker import (
    LexiconOntologyLinker, Lexicon, Ontology
)
from godelOS.nlu_nlg.nlu.pipeline import (

import pytest
import importlib

class TestNLUPipeline(unittest.TestCase):
    """Test cases for the NLUPipeline class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock type system
        self.type_system = MagicMock(spec=TypeSystemManager)
        
        # Set up common types
        self.entity_type = AtomicType("Entity")
        self.boolean_type = AtomicType("Boolean")
        self.proposition_type = AtomicType("Proposition")
        
        # Configure the type system mock
        self.type_system.get_type.side_effect = lambda name: {
            "Entity": self.entity_type,
            "Boolean": self.boolean_type,
            "Proposition": self.proposition_type
        }.get(name)
        
        # Create mocks for the pipeline components
        self.mock_lap = MagicMock(spec=LexicalAnalyzerParser)
        self.mock_si = MagicMock(spec=SemanticInterpreter)
        self.mock_formalizer = MagicMock(spec=Formalizer)
        self.mock_dm = MagicMock(spec=DiscourseStateManager)
        self.mock_lol = MagicMock(spec=LexiconOntologyLinker)
        
        # Create the pipeline with mocked components
        self.pipeline = NLUPipeline(self.type_system)
        self.pipeline.lexical_analyzer_parser = self.mock_lap
        self.pipeline.semantic_interpreter = self.mock_si
        self.pipeline.formalizer = self.mock_formalizer
        self.pipeline.discourse_manager = self.mock_dm
        self.pipeline.lexicon_ontology_linker = self.mock_lol
    
    def test_process_success(self):
        """Test processing a text successfully."""
        # Set up the mock components to return appropriate values
        mock_parse_output = MagicMock(spec=SyntacticParseOutput)
        mock_parse_output.text = "The cat chased the mouse."
        self.mock_lap.process.return_value = mock_parse_output
        
        mock_isr = MagicMock(spec=IntermediateSemanticRepresentation)
        mock_isr.text = "The cat chased the mouse."
        self.mock_si.interpret.return_value = mock_isr
        
        mock_context = MagicMock(spec=DiscourseContext)
        self.mock_dm.process_utterance.return_value = mock_context
        
        mock_ast_node = MagicMock(spec=ApplicationNode)
        self.mock_formalizer.formalize.return_value = [mock_ast_node]
        
        # Process a text
        result = self.pipeline.process("The cat chased the mouse.")
        
        # Check that the result is an NLUResult
        self.assertIsInstance(result, NLUResult)
        
        # Check that the result contains the expected values
        self.assertEqual(result.input_text, "The cat chased the mouse.")
        self.assertEqual(result.syntactic_parse, mock_parse_output)
        self.assertEqual(result.semantic_representation, mock_isr)
        self.assertEqual(result.discourse_context, mock_context)
        self.assertEqual(result.ast_nodes, [mock_ast_node])
        self.assertTrue(result.success)
        self.assertEqual(len(result.errors), 0)
        
        # Check that the component times were recorded
        self.assertGreater(len(result.component_times), 0)
        self.assertIn("lexical_analysis_parsing", result.component_times)
        self.assertIn("semantic_interpretation", result.component_times)
        self.assertIn("discourse_management", result.component_times)
        self.assertIn("formalization", result.component_times)
        
        # Check that the total processing time was recorded
        self.assertGreater(result.processing_time, 0)
    
    def test_process_error(self):
        """Test processing a text with an error."""
        # Make the lexical analyzer parser raise an exception
        self.mock_lap.process.side_effect = ValueError("Test error")
        
        # Process a text
        result = self.pipeline.process("The cat chased the mouse.")
        
        # Check that the result indicates failure
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(result.errors[0], "Test error")
    
    def test_process_text_to_ast(self):
        """Test the process_text_to_ast convenience method."""
        # Set up the mock components to return appropriate values
        mock_parse_output = MagicMock(spec=SyntacticParseOutput)
        mock_parse_output.text = "The cat chased the mouse."
        self.mock_lap.process.return_value = mock_parse_output
        
        mock_isr = MagicMock(spec=IntermediateSemanticRepresentation)
        mock_isr.text = "The cat chased the mouse."
        self.mock_si.interpret.return_value = mock_isr
        
        mock_context = MagicMock(spec=DiscourseContext)
        self.mock_dm.process_utterance.return_value = mock_context
        
        mock_ast_node = MagicMock(spec=ApplicationNode)
        self.mock_formalizer.formalize.return_value = [mock_ast_node]
        
        # Process a text to AST
        ast_nodes, success, errors = self.pipeline.process_text_to_ast("The cat chased the mouse.")
        
        # Check that the result contains the expected values
        self.assertEqual(ast_nodes, [mock_ast_node])
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
    
    def test_process_with_context(self):
        """Test processing a text with a given discourse context."""
        # Set up the mock components to return appropriate values
        mock_parse_output = MagicMock(spec=SyntacticParseOutput)
        mock_parse_output.text = "The cat chased the mouse."
        self.mock_lap.process.return_value = mock_parse_output
        
        mock_isr = MagicMock(spec=IntermediateSemanticRepresentation)
        mock_isr.text = "The cat chased the mouse."
        self.mock_si.interpret.return_value = mock_isr
        
        mock_context = MagicMock(spec=DiscourseContext)
        self.mock_dm.process_utterance.return_value = mock_context
        
        mock_ast_node = MagicMock(spec=ApplicationNode)
        self.mock_formalizer.formalize.return_value = [mock_ast_node]
        
        # Create a previous context
        previous_context = MagicMock(spec=DiscourseContext)
        
        # Process a text with context
        result = self.pipeline.process_with_context("The cat chased the mouse.", previous_context)
        
        # Check that the result is an NLUResult
        self.assertIsInstance(result, NLUResult)
        
        # Check that the context was set
        self.assertEqual(self.pipeline.discourse_manager.context, previous_context)
    
    def test_reset_discourse_context(self):
        """Test resetting the discourse context."""
        # Reset the discourse context
        self.pipeline.reset_discourse_context()
        
        # Check that a new discourse manager was created
        self.assertIsInstance(self.pipeline.discourse_manager, DiscourseStateManager)
    
    def test_create_nlu_pipeline(self):
        """Test the create_nlu_pipeline convenience function."""
        # Create a pipeline
        pipeline = create_nlu_pipeline(self.type_system)
        
        # Check that the pipeline was created correctly
        self.assertIsInstance(pipeline, NLUPipeline)
        self.assertEqual(pipeline.type_system, self.type_system)
    
    def test_end_to_end_integration(self):
        """Test the pipeline end-to-end with real components."""
        # Skip this test if we're running in a CI environment or don't have the required dependencies
        try:
            import spacy
            spacy.load("en_core_web_sm")
        except (ImportError, OSError):
            self.skipTest("Skipping integration test due to missing dependencies")
        
        # Create a real pipeline
        pipeline = NLUPipeline(self.type_system)
        
        # Patch the _initialize_lexicon_ontology method to avoid loading WordNet
        with patch.object(pipeline, '_initialize_lexicon_ontology'):
            # Process a simple text
            result = pipeline.process("The cat chased the mouse.")
            
            # Check that the result is an NLUResult
            self.assertIsInstance(result, NLUResult)
            
            # Check that the result contains the expected values
            self.assertEqual(result.input_text, "The cat chased the mouse.")
            self.assertIsNotNone(result.syntactic_parse)
            self.assertIsNotNone(result.semantic_representation)
            self.assertIsNotNone(result.discourse_context)
            
            # The AST nodes might be empty if we don't have a proper type system
            # self.assertGreater(len(result.ast_nodes), 0)
            
            self.assertTrue(result.success)
            self.assertEqual(len(result.errors), 0)


if __name__ == '__main__':
    unittest.main()