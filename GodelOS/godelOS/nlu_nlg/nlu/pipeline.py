"""
NLU Pipeline for GödelOS.

This module provides the central NLUPipeline class that coordinates the flow of data
through the various components of the NLU pipeline, from raw text to formal
logical representations compatible with the KR System.
"""

from typing import Dict, List, Optional, Tuple, Any, Set, Union, cast
from dataclasses import dataclass, field
import logging
import time

from godelOS.core_kr.ast.nodes import AST_Node
from godelOS.core_kr.type_system.manager import TypeSystemManager

try:
    from godelOS.nlu_nlg.nlu.lexical_analyzer_parser import (
        LexicalAnalyzerParser, SyntacticParseOutput
    )
    _LAP_AVAILABLE = True
except (ImportError, Exception):
    LexicalAnalyzerParser = None  # type: ignore[assignment,misc]
    SyntacticParseOutput = None  # type: ignore[assignment,misc]
    _LAP_AVAILABLE = False
from godelOS.nlu_nlg.nlu.semantic_interpreter import (
    SemanticInterpreter, IntermediateSemanticRepresentation
)
from godelOS.nlu_nlg.nlu.formalizer import (
    Formalizer, create_ast_from_isr
)
from godelOS.nlu_nlg.nlu.discourse_manager import (
    DiscourseStateManager, DiscourseContext
)
from godelOS.nlu_nlg.nlu.lexicon_ontology_linker import (
    LexiconOntologyLinker, Lexicon, Ontology
)


@dataclass
class NLUResult:
    """
    The result of the NLU pipeline processing.
    
    Contains the outputs of each stage of the pipeline, as well as the final
    AST nodes representing the formal logical interpretation of the input text.
    """
    input_text: str
    syntactic_parse: Optional[SyntacticParseOutput] = None
    semantic_representation: Optional[IntermediateSemanticRepresentation] = None
    ast_nodes: List[AST_Node] = field(default_factory=list)
    discourse_context: Optional[DiscourseContext] = None
    
    # Timing information
    processing_time: float = 0.0
    component_times: Dict[str, float] = field(default_factory=dict)
    
    # Error information
    success: bool = True
    errors: List[str] = field(default_factory=list)


class NLUPipeline:
    """
    Natural Language Understanding Pipeline.
    
    This class coordinates the flow of data through the various components of the
    NLU pipeline, from raw text to formal logical representations compatible with
    the KR System.
    """
    
    def __init__(self, type_system: TypeSystemManager,
                lexicon: Optional[Lexicon] = None,
                ontology: Optional[Ontology] = None):
        """
        Initialize the NLU pipeline.
        
        Args:
            type_system: The type system manager for type validation and inference
            lexicon: Optional lexicon to use
            ontology: Optional ontology to use
        """
        self.type_system = type_system
        self.logger = logging.getLogger(__name__)
        
        # Initialize the pipeline components
        if _LAP_AVAILABLE and LexicalAnalyzerParser is not None:
            self.lexical_analyzer_parser = LexicalAnalyzerParser()
        else:
            self.lexical_analyzer_parser = None
            self.logger.warning(
                "LexicalAnalyzerParser unavailable (spaCy not installed); "
                "NLU pipeline running in degraded mode."
            )
        self.semantic_interpreter = SemanticInterpreter()
        self.formalizer = Formalizer(type_system)
        self.discourse_manager = DiscourseStateManager()
        self.lexicon_ontology_linker = LexiconOntologyLinker(lexicon, ontology)
        
        # Initialize the lexicon and ontology if they were not provided
        if not lexicon or not ontology:
            self._initialize_lexicon_ontology()
    
    def _initialize_lexicon_ontology(self) -> None:
        """Initialize the lexicon and ontology with basic entries."""
        self.lexicon_ontology_linker.load_wordnet_lexicon()
        self.lexicon_ontology_linker.create_basic_ontology()
    
    def process(self, text: str) -> NLUResult:
        """
        Process a natural language text through the NLU pipeline.
        
        Args:
            text: The input text to process
            
        Returns:
            An NLUResult containing the outputs of each stage of the pipeline
        """
        # Create the result object
        result = NLUResult(input_text=text)
        
        # Record the start time
        start_time = time.time()
        
        try:
            # Step 1: Lexical Analysis and Syntactic Parsing
            if self.lexical_analyzer_parser is None:
                result.errors.append("NLU running in degraded mode: spaCy not installed")
                result.success = False
                return result
            lap_start = time.time()
            syntactic_parse = self.lexical_analyzer_parser.process(text)
            lap_end = time.time()
            result.component_times["lexical_analysis_parsing"] = lap_end - lap_start
            result.syntactic_parse = syntactic_parse
            
            # Step 2: Semantic Interpretation
            si_start = time.time()
            semantic_representation = self.semantic_interpreter.interpret(syntactic_parse)
            si_end = time.time()
            result.component_times["semantic_interpretation"] = si_end - si_start
            result.semantic_representation = semantic_representation
            
            # Step 3: Discourse State Management
            dm_start = time.time()
            discourse_context = self.discourse_manager.process_utterance(syntactic_parse, semantic_representation)
            dm_end = time.time()
            result.component_times["discourse_management"] = dm_end - dm_start
            result.discourse_context = discourse_context
            
            # Step 4: Formalization
            form_start = time.time()
            ast_nodes = self.formalizer.formalize(semantic_representation)
            form_end = time.time()
            result.component_times["formalization"] = form_end - form_start
            result.ast_nodes = ast_nodes
            
            # Record the success
            result.success = True
        except Exception as e:
            # Record the error
            result.success = False
            result.errors.append(str(e))
            self.logger.error(f"Error processing text: {str(e)}", exc_info=True)
        
        # Record the total processing time
        end_time = time.time()
        result.processing_time = end_time - start_time
        
        return result
    
    def process_text_to_ast(self, text: str) -> Tuple[List[AST_Node], bool, List[str]]:
        """
        Process a natural language text to AST nodes.
        
        This is a convenience method that returns just the AST nodes and error information.
        
        Args:
            text: The input text to process
            
        Returns:
            A tuple containing:
            - A list of AST nodes representing the formal logical interpretation
            - A boolean indicating whether the processing was successful
            - A list of error messages if the processing was not successful
        """
        result = self.process(text)
        return result.ast_nodes, result.success, result.errors
    
    def process_with_context(self, text: str, previous_context: Optional[DiscourseContext] = None) -> NLUResult:
        """
        Process a natural language text with a given discourse context.
        
        This method allows for processing a text in the context of a previous conversation.
        
        Args:
            text: The input text to process
            previous_context: Optional previous discourse context
            
        Returns:
            An NLUResult containing the outputs of each stage of the pipeline
        """
        # If a previous context is provided, use it
        if previous_context:
            self.discourse_manager.context = previous_context
        
        # Process the text
        return self.process(text)
    
    def reset_discourse_context(self) -> None:
        """Reset the discourse context to a fresh state."""
        self.discourse_manager = DiscourseStateManager()


def create_nlu_pipeline(type_system: TypeSystemManager) -> NLUPipeline:
    """
    Create an NLU pipeline with the given type system.
    
    This is a convenience function that creates an NLU pipeline with default
    components.
    
    Args:
        type_system: The type system manager for type validation and inference
        
    Returns:
        A new NLUPipeline instance
    """
    return NLUPipeline(type_system)