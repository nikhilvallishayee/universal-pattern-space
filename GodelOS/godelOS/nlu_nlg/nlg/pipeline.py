"""
NLG Pipeline for GödelOS.

This module provides the central NLGPipeline class that coordinates the flow of data
through the various components of the NLG pipeline, from AST nodes to natural
language text.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union, cast
from dataclasses import dataclass, field
import logging
import time

from godelOS.core_kr.ast.nodes import AST_Node
from godelOS.core_kr.type_system.manager import TypeSystemManager

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


@dataclass
class NLGResult:
    """
    The result of the NLG pipeline processing.
    
    Contains the outputs of each stage of the pipeline, as well as the final
    natural language text representing the input AST nodes.
    """
    input_ast_nodes: List[AST_Node]
    message_specification: Optional[MessageSpecification] = None
    sentence_plans: List[SentencePlan] = field(default_factory=list)
    output_text: str = ""
    discourse_context: Optional[DiscourseContext] = None
    
    # Timing information
    processing_time: float = 0.0
    component_times: Dict[str, float] = field(default_factory=dict)
    
    # Error information
    success: bool = True
    errors: List[str] = field(default_factory=list)


class NLGPipeline:
    """
    Natural Language Generation Pipeline.
    
    This class coordinates the flow of data through the various components of the
    NLG pipeline, from AST nodes to natural language text.
    """
    
    def __init__(self, type_system: TypeSystemManager,
                discourse_manager: Optional[DiscourseStateManager] = None):
        """
        Initialize the NLG pipeline.
        
        Args:
            type_system: The type system manager for type validation and inference
            discourse_manager: Optional discourse state manager for context-aware generation
        """
        self.type_system = type_system
        self.logger = logging.getLogger(__name__)
        
        # Initialize the pipeline components
        self.content_planner = ContentPlanner(type_system)
        self.sentence_generator = SentenceGenerator()
        self.surface_realizer = SurfaceRealizer()
        self.discourse_manager = discourse_manager or DiscourseStateManager()
    
    def process(self, ast_nodes: List[AST_Node]) -> NLGResult:
        """
        Process AST nodes through the NLG pipeline.
        
        Args:
            ast_nodes: The AST nodes representing the formal logical content
            
        Returns:
            An NLGResult containing the outputs of each stage of the pipeline
        """
        # Create the result object
        result = NLGResult(input_ast_nodes=ast_nodes)
        
        # Record the start time
        start_time = time.time()
        
        try:
            # Step 1: Content Planning
            cp_start = time.time()
            context = {"discourse_context": getattr(self.discourse_manager, 'context', None)}
            message_spec = self.content_planner.plan_content(ast_nodes, context)
            cp_end = time.time()
            result.component_times["content_planning"] = cp_end - cp_start
            result.message_specification = message_spec
            
            # Step 2: Sentence Generation
            sg_start = time.time()
            sentence_plans = self.sentence_generator.generate_sentence_plans(message_spec, context)
            sg_end = time.time()
            result.component_times["sentence_generation"] = sg_end - sg_start
            result.sentence_plans = sentence_plans
            
            # Step 3: Surface Realization
            sr_start = time.time()
            output_text = self.surface_realizer.realize_text(sentence_plans, context)
            sr_end = time.time()
            result.component_times["surface_realization"] = sr_end - sr_start
            result.output_text = output_text
            
            # Record the discourse context
            result.discourse_context = getattr(self.discourse_manager, 'context', None)
            
            # Record the success
            result.success = True
        except Exception as e:
            # Record the error
            result.success = False
            result.errors.append(str(e))
            self.logger.error(f"Error processing AST nodes: {str(e)}", exc_info=True)
        
        # Record the total processing time
        end_time = time.time()
        result.processing_time = end_time - start_time
        
        return result
    
    def process_ast_to_text(self, ast_nodes: List[AST_Node]) -> Tuple[str, bool, List[str]]:
        """
        Process AST nodes to natural language text.
        
        This is a convenience method that returns just the output text and error information.
        
        Args:
            ast_nodes: The AST nodes representing the formal logical content
            
        Returns:
            A tuple containing:
            - The output text
            - A boolean indicating whether the processing was successful
            - A list of error messages if the processing was not successful
        """
        result = self.process(ast_nodes)
        return result.output_text, result.success, result.errors
    
    def process_with_context(self, ast_nodes: List[AST_Node], 
                           previous_context: Optional[DiscourseContext] = None) -> NLGResult:
        """
        Process AST nodes with a given discourse context.
        
        This method allows for processing AST nodes in the context of a previous conversation.
        
        Args:
            ast_nodes: The AST nodes representing the formal logical content
            previous_context: Optional previous discourse context
            
        Returns:
            An NLGResult containing the outputs of each stage of the pipeline
        """
        # If a previous context is provided, use it
        if previous_context:
            self.discourse_manager.context = previous_context
        
        # Process the AST nodes
        return self.process(ast_nodes)
    
    def reset_discourse_context(self) -> None:
        """Reset the discourse context to a fresh state."""
        self.discourse_manager = DiscourseStateManager()


def create_nlg_pipeline(type_system: TypeSystemManager,
                       discourse_manager: Optional[DiscourseStateManager] = None) -> NLGPipeline:
    """
    Create an NLG pipeline with the given type system.
    
    This is a convenience function that creates an NLG pipeline with default
    components.
    
    Args:
        type_system: The type system manager for type validation and inference
        discourse_manager: Optional discourse state manager for context-aware generation
        
    Returns:
        A new NLGPipeline instance
    """
    return NLGPipeline(type_system, discourse_manager)