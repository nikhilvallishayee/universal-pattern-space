"""
Unit tests for the NLG Pipeline module.
"""

import unittest
from unittest.mock import patch, MagicMock
import time

from godelOS.core_kr.ast.nodes import (
    AST_Node, ConstantNode, VariableNode, ApplicationNode
)
from godelOS.core_kr.type_system.manager import TypeSystemManager
from godelOS.core_kr.type_system.types import AtomicType

from godelOS.nlu_nlg.nlg.content_planner import (
    ContentPlanner, MessageSpecification
)
from godelOS.nlu_nlg.nlg.sentence_generator import (
    SentenceGenerator, SentencePlan
)
from godelOS.nlu_nlg.nlg.surface_realizer import (
    SurfaceRealizer
)
from godelOS.nlu_nlg.nlu.discourse_manager import (
    DiscourseStateManager, DiscourseContext
)
from godelOS.nlu_nlg.nlg.pipeline import (
    NLGPipeline, NLGResult, create_nlg_pipeline
)


class TestNLGPipeline(unittest.TestCase):
    """Test cases for the NLGPipeline class."""
    
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
        self.mock_cp = MagicMock(spec=ContentPlanner)
        self.mock_sg = MagicMock(spec=SentenceGenerator)
        self.mock_sr = MagicMock(spec=SurfaceRealizer)
        self.mock_dm = MagicMock(spec=DiscourseStateManager)
        
        # Create the pipeline with mocked components
        self.pipeline = NLGPipeline(self.type_system, self.mock_dm)
        self.pipeline.content_planner = self.mock_cp
        self.pipeline.sentence_generator = self.mock_sg
        self.pipeline.surface_realizer = self.mock_sr
    
    def test_process_success(self):
        """Test processing AST nodes successfully."""
        # Create a test AST node
        ast_node = MagicMock(spec=ApplicationNode)
        
        # Set up the mock components to return appropriate values
        mock_message_spec = MagicMock(spec=MessageSpecification)
        self.mock_cp.plan_content.return_value = mock_message_spec
        
        mock_sentence_plan = MagicMock(spec=SentencePlan)
        self.mock_sg.generate_sentence_plans.return_value = [mock_sentence_plan]
        
        self.mock_sr.realize_text.return_value = "The cat chases the mouse."
        
        mock_context = MagicMock(spec=DiscourseContext)
        self.mock_dm.context = mock_context
        
        # Process AST nodes
        result = self.pipeline.process([ast_node])
        
        # Check that the result is an NLGResult
        self.assertIsInstance(result, NLGResult)
        
        # Check that the result contains the expected values
        self.assertEqual(result.input_ast_nodes, [ast_node])
        self.assertEqual(result.message_specification, mock_message_spec)
        self.assertEqual(result.sentence_plans, [mock_sentence_plan])
        self.assertEqual(result.output_text, "The cat chases the mouse.")
        self.assertEqual(result.discourse_context, mock_context)
        self.assertTrue(result.success)
        self.assertEqual(len(result.errors), 0)
        
        # Check that the component times were recorded
        self.assertGreater(len(result.component_times), 0)
        self.assertIn("content_planning", result.component_times)
        self.assertIn("sentence_generation", result.component_times)
        self.assertIn("surface_realization", result.component_times)
        
        # Check that the total processing time was recorded
        self.assertGreater(result.processing_time, 0)
    
    def test_process_error(self):
        """Test processing AST nodes with an error."""
        # Create a test AST node
        ast_node = MagicMock(spec=ApplicationNode)
        
        # Make the content planner raise an exception
        self.mock_cp.plan_content.side_effect = ValueError("Test error")
        
        # Process AST nodes
        result = self.pipeline.process([ast_node])
        
        # Check that the result indicates failure
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(result.errors[0], "Test error")
    
    def test_process_ast_to_text(self):
        """Test the process_ast_to_text convenience method."""
        # Create a test AST node
        ast_node = MagicMock(spec=ApplicationNode)
        
        # Set up the mock components to return appropriate values
        mock_message_spec = MagicMock(spec=MessageSpecification)
        self.mock_cp.plan_content.return_value = mock_message_spec
        
        mock_sentence_plan = MagicMock(spec=SentencePlan)
        self.mock_sg.generate_sentence_plans.return_value = [mock_sentence_plan]
        
        self.mock_sr.realize_text.return_value = "The cat chases the mouse."
        
        # Process AST nodes to text
        text, success, errors = self.pipeline.process_ast_to_text([ast_node])
        
        # Check that the result contains the expected values
        self.assertEqual(text, "The cat chases the mouse.")
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
    
    def test_process_with_context(self):
        """Test processing AST nodes with a given discourse context."""
        # Create a test AST node
        ast_node = MagicMock(spec=ApplicationNode)
        
        # Set up the mock components to return appropriate values
        mock_message_spec = MagicMock(spec=MessageSpecification)
        self.mock_cp.plan_content.return_value = mock_message_spec
        
        mock_sentence_plan = MagicMock(spec=SentencePlan)
        self.mock_sg.generate_sentence_plans.return_value = [mock_sentence_plan]
        
        self.mock_sr.realize_text.return_value = "The cat chases the mouse."
        
        # Create a previous context
        previous_context = MagicMock(spec=DiscourseContext)
        
        # Process AST nodes with context
        result = self.pipeline.process_with_context([ast_node], previous_context)
        
        # Check that the result is an NLGResult
        self.assertIsInstance(result, NLGResult)
        
        # Check that the context was set
        self.assertEqual(self.pipeline.discourse_manager.context, previous_context)
    
    def test_reset_discourse_context(self):
        """Test resetting the discourse context."""
        # Reset the discourse context
        self.pipeline.reset_discourse_context()
        
        # Check that a new discourse manager was created
        self.assertIsInstance(self.pipeline.discourse_manager, DiscourseStateManager)
        self.assertIsNot(self.pipeline.discourse_manager, self.mock_dm)
    
    def test_create_nlg_pipeline(self):
        """Test the create_nlg_pipeline convenience function."""
        # Create a pipeline
        pipeline = create_nlg_pipeline(self.type_system)
        
        # Check that the pipeline was created correctly
        self.assertIsInstance(pipeline, NLGPipeline)
        self.assertEqual(pipeline.type_system, self.type_system)
    
    def test_end_to_end_integration(self):
        """Test the pipeline end-to-end with real components."""
        # Skip this test if we're running in a CI environment or don't have the required dependencies
        # This is just a placeholder for a real integration test
        self.skipTest("Skipping integration test for now")
        
        # Create a real pipeline
        pipeline = NLGPipeline(self.type_system)
        
        # Create a simple AST node
        operator = ConstantNode(
            name="chase",
            type_ref=self.entity_type,
            value=None
        )
        
        arg1 = ConstantNode(
            name="cat",
            type_ref=self.entity_type,
            value=None
        )
        
        arg2 = ConstantNode(
            name="mouse",
            type_ref=self.entity_type,
            value=None
        )
        
        application_node = ApplicationNode(
            operator=operator,
            arguments=[arg1, arg2],
            type_ref=self.proposition_type
        )
        
        # Process the AST node
        result = pipeline.process([application_node])
        
        # Check that the result is an NLGResult
        self.assertIsInstance(result, NLGResult)
        
        # Check that the result contains the expected values
        self.assertEqual(result.input_ast_nodes, [application_node])
        self.assertIsNotNone(result.message_specification)
        self.assertGreater(len(result.sentence_plans), 0)
        self.assertIsNotNone(result.output_text)
        self.assertIsNotNone(result.discourse_context)
        self.assertTrue(result.success)
        self.assertEqual(len(result.errors), 0)


if __name__ == '__main__':
    unittest.main()