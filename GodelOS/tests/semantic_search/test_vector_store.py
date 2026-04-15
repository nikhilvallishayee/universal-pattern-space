"""
Unit tests for the VectorStore.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from godelOS.semantic_search.vector_store import VectorStore

@pytest.fixture
def mock_sentence_transformer():
    """Fixture for a mock SentenceTransformer model."""
    mock_model = MagicMock()
    mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    return mock_model

@pytest.fixture
def mock_faiss_index():
    """Fixture for a mock FAISS index."""
    mock_index = MagicMock()
    mock_index.ntotal = 2
    mock_index.search.return_value = (np.array([[0.1, 0.2]]), np.array([[0, 1]]))
    return mock_index

@patch('faiss.IndexFlatL2')
@patch('sentence_transformers.SentenceTransformer')
def test_vector_store(mock_transformer, mock_faiss):
    """Test the VectorStore."""
    mock_transformer.return_value = mock_sentence_transformer()
    mock_faiss.return_value = mock_faiss_index()

    store = VectorStore(dimension=3)

    # Test adding items
    items = [("id1", "text1"), ("id2", "text2")]
    store.add_items(items)
    
    mock_transformer.return_value.encode.assert_called_with(["text1", "text2"], convert_to_tensor=False)
    mock_faiss.return_value.add.assert_called_once()
    assert store.id_map == ["id1", "id2"]

    # Test searching
    results = store.search("query", k=2)
    
    mock_transformer.return_value.encode.assert_called_with(["query"], convert_to_tensor=False)
    mock_faiss.return_value.search.assert_called_once()
    
    assert len(results) == 2
    assert results[0][0] == "id1"
    assert results[1][0] == "id2"