"""
Unit tests for the NlpProcessor.
"""

import pytest
from unittest.mock import MagicMock, patch

from godelOS.knowledge_extraction.nlp_processor import NlpProcessor

@pytest.fixture
def mock_spacy_model():
    """Fixture for a mock spaCy model."""
    mock_nlp = MagicMock()
    
    # Mock Doc, Span, and Token objects
    mock_doc = MagicMock()
    mock_span = MagicMock()
    mock_span.text = "Apple"
    mock_span.label_ = "ORG"
    mock_span.start_char = 0
    mock_span.end_char = 5
    
    mock_span2 = MagicMock()
    mock_span2.text = "U.K."
    mock_span2.label_ = "GPE"
    mock_span2.start_char = 24
    mock_span2.end_char = 28

    mock_sent = MagicMock()
    mock_sent.start_char = 0
    mock_sent.end_char = 50
    mock_sent.text = "Apple is looking at buying U.K. startup for $1 billion"

    mock_doc.ents = [mock_span, mock_span2]
    mock_doc.sents = [mock_sent]
    
    mock_nlp.return_value = mock_doc
    return mock_nlp

@pytest.fixture
def mock_relation_extractor():
    """Fixture for a mock relation extraction pipeline."""
    mock_pipeline = MagicMock()
    mock_pipeline.return_value = {'score': 0.9, 'answer': 'is looking at buying'}
    return mock_pipeline

@patch('spacy.load')
@patch('transformers.pipeline')
async def test_nlp_processor(mock_pipeline, mock_spacy_load):
    """Test the NlpProcessor."""
    mock_spacy_load.return_value = mock_spacy_model()()
    mock_pipeline.return_value = mock_relation_extractor()

    processor = NlpProcessor()
    
    text = "Apple is looking at buying U.K. startup for $1 billion"
    result = await processor.process(text)

    # Assertions
    assert "entities" in result
    assert "relationships" in result
    
    assert len(result['entities']) == 2
    assert result['entities'][0]['text'] == "Apple"
    assert result['entities'][1]['text'] == "U.K."

    assert len(result['relationships']) == 1
    assert result['relationships'][0]['source']['text'] == "Apple"
    assert result['relationships'][0]['target']['text'] == "U.K."
    assert result['relationships'][0]['relation'] == "is looking at buying"