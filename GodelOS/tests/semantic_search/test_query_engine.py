"""
Unit tests for the QueryEngine.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from godelOS.semantic_search.query_engine import QueryEngine
from godelOS.unified_agent_core.knowledge_store.interfaces import Fact, QueryResult

@pytest.fixture
def mock_vector_store():
    """Fixture for a mock VectorStore."""
    mock_store = MagicMock()
    mock_store.search.return_value = [("fact1", 0.1), ("fact2", 0.2)]
    return mock_store

@pytest.fixture
def mock_knowledge_store():
    """Fixture for a mock UnifiedKnowledgeStore."""
    mock_store = AsyncMock()
    
    async def retrieve_knowledge(item_id, memory_types=None):
        if item_id == "fact1":
            return Fact(id="fact1", content={"text": "fact 1 content"})
        if item_id == "fact2":
            return Fact(id="fact2", content={"text": "fact 2 content"})
        return None
        
    mock_store.retrieve_knowledge = AsyncMock(side_effect=retrieve_knowledge)
    return mock_store

@pytest.mark.asyncio
async def test_query_engine(mock_vector_store, mock_knowledge_store):
    """Test the QueryEngine."""
    engine = QueryEngine(vector_store=mock_vector_store, knowledge_store=mock_knowledge_store)

    query_text = "some query"
    result = await engine.query(query_text, k=2)

    # Assertions
    mock_vector_store.search.assert_called_once_with(query_text, k=2)
    
    assert isinstance(result, QueryResult)
    assert result.total_items == 2
    
    assert result.items[0].id == "fact1"
    assert result.items[1].id == "fact2"