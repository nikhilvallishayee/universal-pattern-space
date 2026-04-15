"""
Unit tests for the KnowledgeGraphBuilder.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from godelOS.knowledge_extraction.graph_builder import KnowledgeGraphBuilder
from godelOS.unified_agent_core.knowledge_store.interfaces import Fact, Relationship

@pytest.fixture
def mock_knowledge_store():
    """Fixture for a mock UnifiedKnowledgeStore."""
    mock_store = AsyncMock()
    mock_store.store_knowledge = AsyncMock()
    return mock_store

@pytest.mark.asyncio
async def test_knowledge_graph_builder(mock_knowledge_store):
    """Test the KnowledgeGraphBuilder."""
    builder = KnowledgeGraphBuilder(knowledge_store=mock_knowledge_store)

    processed_data = {
        "entities": [
            {"text": "Apple", "label": "ORG"},
            {"text": "U.K.", "label": "GPE"}
        ],
        "relationships": [
            {
                "source": {"text": "Apple", "label": "ORG"},
                "target": {"text": "U.K.", "label": "GPE"},
                "relation": "is looking at buying",
                "sentence": "Apple is looking at buying U.K. startup for $1 billion"
            }
        ]
    }

    created_items = await builder.build_graph(processed_data)

    # Assertions
    assert mock_knowledge_store.store_knowledge.call_count == 3
    
    # Check that 2 Facts and 1 Relationship were created
    fact_calls = [
        call for call in mock_knowledge_store.store_knowledge.call_args_list
        if isinstance(call.args[0], Fact)
    ]
    relationship_calls = [
        call for call in mock_knowledge_store.store_knowledge.call_args_list
        if isinstance(call.args[0], Relationship)
    ]

    assert len(fact_calls) == 2
    assert len(relationship_calls) == 1

    # Check the content of the created items
    assert fact_calls[0].args[0].content['text'] == "Apple"
    assert fact_calls[1].args[0].content['text'] == "U.K."
    
    relationship = relationship_calls[0].args[0]
    assert relationship.relation_type == "is looking at buying"
    assert relationship.content['sentence'] == "Apple is looking at buying U.K. startup for $1 billion"