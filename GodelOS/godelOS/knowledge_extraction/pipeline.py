"""
Data Extraction Pipeline for GodelOS.
"""

from typing import List, Dict, Any
import logging

from godelOS.unified_agent_core.knowledge_store.interfaces import Knowledge
from .nlp_processor import NlpProcessor
from .graph_builder import KnowledgeGraphBuilder

logger = logging.getLogger(__name__)

class DataExtractionPipeline:
    """
    Orchestrates the process of extracting knowledge from unstructured text.
    """

    def __init__(self, nlp_processor: NlpProcessor, graph_builder: KnowledgeGraphBuilder):
        """
        Initialize the data extraction pipeline.

        Args:
            nlp_processor: The NLP processor to use for entity and relationship extraction.
            graph_builder: The knowledge graph builder to use for constructing the graph.
        """
        self.nlp_processor = nlp_processor
        self.graph_builder = graph_builder

    async def process_documents(self, documents: List[str]) -> List[Knowledge]:
        """
        Process a batch of documents to extract and store knowledge.

        Args:
            documents: A list of unstructured text documents.

        Returns:
            A list of all knowledge items that were created.
        """
        logger.info(f"🔍 PIPELINE: Starting to process {len(documents)} documents")
        all_created_items = []
        for i, doc in enumerate(documents):
            try:
                logger.info(f"🔍 PIPELINE: Processing document {i+1}/{len(documents)}: {len(doc)} characters")
                logger.info(f"🔍 PIPELINE: Document preview: {doc[:100]}...")
                
                processed_data = await self.nlp_processor.process(doc)
                logger.info(f"🔍 PIPELINE: NLP processor returned: {processed_data}")
                
                if processed_data:
                    entities_count = len(processed_data.get('entities', []))
                    relationships_count = len(processed_data.get('relationships', []))
                    logger.info(f"🔍 PIPELINE: Found {entities_count} entities and {relationships_count} relationships")
                    
                    created_items = await self.graph_builder.build_graph(processed_data)
                    all_created_items.extend(created_items)
                    logger.info(f"Successfully processed document and created {len(created_items)} knowledge items.")
                else:
                    logger.warning("No data extracted from document.")
            except Exception as e:
                logger.error(f"Error processing document: {e}", exc_info=True)
        
        return all_created_items