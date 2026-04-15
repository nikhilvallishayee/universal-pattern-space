"""
Natural Language Generation (NLG) Pipeline for GödelOS.

This package provides components for converting formal logical representations
(AST nodes) back into natural language text.
"""

from godelOS.nlu_nlg.nlg.content_planner import ContentPlanner, MessageSpecification
from godelOS.nlu_nlg.nlg.sentence_generator import SentenceGenerator, SentencePlan
from godelOS.nlu_nlg.nlg.surface_realizer import SurfaceRealizer
from godelOS.nlu_nlg.nlg.pipeline import NLGPipeline, NLGResult, create_nlg_pipeline

__all__ = [
    'ContentPlanner',
    'MessageSpecification',
    'SentenceGenerator',
    'SentencePlan',
    'SurfaceRealizer',
    'NLGPipeline',
    'NLGResult',
    'create_nlg_pipeline'
]