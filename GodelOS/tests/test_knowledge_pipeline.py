"""
Integration test for the knowledge extraction and query pipeline.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from godelOS.knowledge_extraction.pipeline import DataExtractionPipeline
from godelOS.knowledge_extraction.nlp_processor import NlpProcessor
from godelOS.knowledge_extraction.graph_builder import KnowledgeGraphBuilder
from godelOS.semantic_search.query_engine import QueryEngine
from godelOS.semantic_search.vector_store import VectorStore
from godelOS.unified_agent_core.knowledge_store.store import UnifiedKnowledgeStore

@pytest.mark.asyncio
async def test_full_pipeline():
    """
    Tests the full data extraction and query pipeline.
    """
    # 1. Setup
    # We'll use a real (but in-memory) knowledge store
    knowledge_store = UnifiedKnowledgeStore()
    await knowledge_store.initialize()

    # We'll use real NLP and graph building components
    # Note: This will be slow as it downloads models on the first run
    nlp_processor = NlpProcessor()
    graph_builder = KnowledgeGraphBuilder(knowledge_store)
    pipeline = DataExtractionPipeline(nlp_processor, graph_builder)

    # We'll use a real vector store and query engine
    vector_store = VectorStore()
    query_engine = QueryEngine(vector_store, knowledge_store)

    # 2. Data Extraction
    document = "Apple, the tech giant, is based in Cupertino. Tim Cook is the CEO of Apple."
    created_items = await pipeline.process_documents([document])
    
    assert len(created_items) > 0

    # 3. Vector Store Population
    items_to_index = []
    for item in created_items:
        if hasattr(item, 'content') and isinstance(item.content, dict) and 'text' in item.content:
            items_to_index.append((item.id, item.content['text']))
        elif hasattr(item, 'content') and isinstance(item.content, dict) and 'sentence' in item.content:
             items_to_index.append((item.id, item.content['sentence']))

    vector_store.add_items(items_to_index)

    # 4. Querying
    query_text = "Who is the CEO of Apple?"
    query_result = await query_engine.query(query_text)

    assert query_result.total_items > 0
    
    # Check if the retrieved results are relevant
    found_ceo = False
    for item in query_result.items:
        if "Tim Cook" in str(item.content):
            found_ceo = True
            break
    
    assert found_ceo, "The query should have returned information about Tim Cook."