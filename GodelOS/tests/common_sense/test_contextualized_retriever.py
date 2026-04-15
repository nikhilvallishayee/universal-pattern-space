"""
Test cases for the Contextualized Retriever component.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

from godelOS.common_sense.contextualized_retriever import (
    ContextualizedRetriever,
    ContextRelevanceStrategy,
    RetrievalResult
)
from godelOS.common_sense.context_engine import ContextType


class TestContextualizedRetriever(unittest.TestCase):
    """Test cases for the ContextualizedRetriever class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocked dependencies
        self.knowledge_store = Mock()
        self.context_engine = Mock()
        self.cache_system = Mock()
        
        # Create the retriever
        self.retriever = ContextualizedRetriever(
            knowledge_store=self.knowledge_store,
            context_engine=self.context_engine,
            cache_system=self.cache_system,
            default_relevance_strategy=ContextRelevanceStrategy.WEIGHTED,
            max_results=10,
            min_confidence=0.0,
            min_relevance=0.0
        )
    
    def test_initialization(self):
        """Test initialization of the retriever."""
        self.assertEqual(self.retriever.knowledge_store, self.knowledge_store)
        self.assertEqual(self.retriever.context_engine, self.context_engine)
        self.assertEqual(self.retriever.cache_system, self.cache_system)
        self.assertEqual(self.retriever.default_relevance_strategy, ContextRelevanceStrategy.WEIGHTED)
        self.assertEqual(self.retriever.max_results, 10)
        self.assertEqual(self.retriever.min_confidence, 0.0)
        self.assertEqual(self.retriever.min_relevance, 0.0)
        
        # Check that default relevance weights are set
        self.assertIn("exact_match", self.retriever.relevance_weights)
        self.assertIn("semantic_similarity", self.retriever.relevance_weights)
        self.assertIn("temporal_recency", self.retriever.relevance_weights)
        self.assertIn("hierarchical", self.retriever.relevance_weights)
        
        # Check that custom relevance functions are registered
        self.assertIn("exact_match", self.retriever.custom_relevance_functions)
        self.assertIn("semantic_similarity", self.retriever.custom_relevance_functions)
        self.assertIn("temporal_recency", self.retriever.custom_relevance_functions)
        self.assertIn("hierarchical", self.retriever.custom_relevance_functions)
    
    def test_retrieve_with_cache_hit(self):
        """Test retrieving with a cache hit."""
        # Mock the cache to return a hit
        cached_data = [
            {
                "content": "Cached content",
                "source": "cache",
                "confidence": 0.9,
                "context_relevance": 0.8,
                "metadata": {"cached": True},
                "timestamp": time.time()
            }
        ]
        self.cache_system.get.return_value = cached_data
        
        # Call retrieve
        results = self.retriever.retrieve("test query")
        
        # Check that the cache was checked
        self.cache_system.get.assert_called_once()
        
        # Check that the results were returned from cache
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Cached content")
        self.assertEqual(results[0].source, "cache")
        self.assertEqual(results[0].confidence, 0.9)
        self.assertEqual(results[0].context_relevance, 0.8)
        self.assertEqual(results[0].metadata, {"cached": True})
        
        # Check that the knowledge store was not queried
        self.knowledge_store.search_text.assert_not_called()
    
    def test_retrieve_with_cache_miss(self):
        """Test retrieving with a cache miss."""
        # Mock the cache to return a miss
        self.cache_system.get.return_value = None
        
        # Mock the context engine
        mock_context = Mock()
        self.context_engine.get_active_context.return_value = mock_context
        
        # Mock the knowledge store
        self.knowledge_store.search_text.return_value = [
            {
                "content": "Test content",
                "score": 0.9
            }
        ]
        
        # Mock the _apply_context_relevance method
        with patch.object(self.retriever, '_apply_context_relevance') as mock_apply:
            mock_apply.return_value = [
                RetrievalResult(
                    content="Test content",
                    source="knowledge_store",
                    confidence=0.9,
                    context_relevance=0.8
                )
            ]
            
            # Call retrieve
            results = self.retriever.retrieve("test query")
            
            # Check that the cache was checked
            self.cache_system.get.assert_called_once()
            
            # Check that the knowledge store was queried
            self.knowledge_store.search_text.assert_called_once()
            
            # Check that context relevance was applied
            mock_apply.assert_called_once()
            
            # Check that the results were returned
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].content, "Test content")
            self.assertEqual(results[0].source, "knowledge_store")
            self.assertEqual(results[0].confidence, 0.9)
            self.assertEqual(results[0].context_relevance, 0.8)
            
            # Check that the results were cached
            self.cache_system.set.assert_called_once()
    
    def test_retrieve_with_ambiguity_resolution(self):
        """Test retrieving with ambiguity resolution."""
        # Mock the retrieve method
        with patch.object(self.retriever, 'retrieve') as mock_retrieve:
            mock_retrieve.return_value = [
                RetrievalResult(
                    content="Ambiguous result 1",
                    source="knowledge_store",
                    confidence=0.8,
                    context_relevance=0.7
                ),
                RetrievalResult(
                    content="Ambiguous result 2",
                    source="knowledge_store",
                    confidence=0.7,
                    context_relevance=0.8
                )
            ]
            
            # Mock the _disambiguate_results method
            with patch.object(self.retriever, '_disambiguate_results') as mock_disambiguate:
                mock_disambiguate.return_value = [
                    RetrievalResult(
                        content="Disambiguated result",
                        source="knowledge_store",
                        confidence=0.9,
                        context_relevance=0.9
                    )
                ]
                
                # Call retrieve_with_ambiguity_resolution
                results = self.retriever.retrieve_with_ambiguity_resolution("ambiguous query")
                
                # Check that retrieve was called
                mock_retrieve.assert_called_once_with(
                    query="ambiguous query",
                    context_id=None,
                    relevance_strategy=ContextRelevanceStrategy.WEIGHTED,
                    max_results=5,
                    min_confidence=0.0,
                    min_relevance=0.0
                )
                
                # Check that disambiguate was called
                mock_disambiguate.assert_called_once()
                
                # Check that the results were returned
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].content, "Disambiguated result")
    
    def test_retrieve_with_context_sensitivity(self):
        """Test retrieving with context sensitivity."""
        # Create a mock retriever
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = [
            RetrievalResult(
                content="Sensitive result",
                source="knowledge_store",
                confidence=0.9,
                context_relevance=0.9
            )
        ]
        
        # Mock the ContextualizedRetriever constructor
        with patch('godelOS.common_sense.contextualized_retriever.ContextualizedRetriever') as mock_class:
            mock_class.return_value = mock_retriever
            
            # Call retrieve_with_context_sensitivity
            results = self.retriever.retrieve_with_context_sensitivity(
                query="sensitive query",
                context_id="test_context",
                sensitivity_level=0.7
            )
            
            # Check that a new retriever was created with adjusted weights
            mock_class.assert_called_once()
            
            # Check that retrieve was called on the new retriever
            mock_retriever.retrieve.assert_called_once_with("sensitive query", "test_context")
            
            # Check that the results were returned
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].content, "Sensitive result")
    
    def test_register_custom_relevance_function(self):
        """Test registering a custom relevance function."""
        # Define a custom relevance function
        def custom_relevance(result, context):
            return 0.5
        
        # Register the function
        self.retriever.register_custom_relevance_function("custom", custom_relevance)
        
        # Check that the function was registered
        self.assertIn("custom", self.retriever.custom_relevance_functions)
        self.assertEqual(self.retriever.custom_relevance_functions["custom"], custom_relevance)
    
    def test_get_context(self):
        """Test getting a context."""
        # Mock the context engine
        mock_context = Mock()
        self.context_engine.get_context.return_value = mock_context
        self.context_engine.get_active_context.return_value = Mock()
        
        # Get a specific context
        context = self.retriever._get_context("test_context")
        
        # Check that the context engine was called
        self.context_engine.get_context.assert_called_once_with("test_context")
        
        # Check that the context was returned
        self.assertEqual(context, mock_context)
        
        # Get the active context
        context = self.retriever._get_context()
        
        # Check that the context engine was called
        self.context_engine.get_active_context.assert_called_once()
    
    def test_generate_cache_key(self):
        """Test generating a cache key."""
        # Mock the context engine
        self.context_engine.active_context_id = "active_context"
        
        # Generate a cache key
        key = self.retriever._generate_cache_key(
            query="test query",
            context_id="test_context",
            relevance_strategy=ContextRelevanceStrategy.WEIGHTED,
            filters={"type": "test"}
        )
        
        # Check that the key contains the expected components
        self.assertIn("query:test query", key)
        self.assertIn("context:test_context", key)
        self.assertIn("strategy:WEIGHTED", key)
        self.assertIn("filters:type:test", key)
        
        # Generate a key without a context ID
        key = self.retriever._generate_cache_key(
            query="test query",
            context_id=None,
            relevance_strategy=ContextRelevanceStrategy.WEIGHTED,
            filters=None
        )
        
        # Check that the key uses the active context ID
        self.assertIn("context:active_context", key)
    
    def test_retrieval_result(self):
        """Test the RetrievalResult class."""
        # Create a result
        result = RetrievalResult(
            content="Test content",
            source="test_source",
            confidence=0.9,
            context_relevance=0.8,
            metadata={"test": True}
        )
        
        # Check the properties
        self.assertEqual(result.content, "Test content")
        self.assertEqual(result.source, "test_source")
        self.assertEqual(result.confidence, 0.9)
        self.assertEqual(result.context_relevance, 0.8)
        self.assertEqual(result.metadata, {"test": True})
        
        # Check the overall score
        self.assertEqual(result.overall_score(), 0.9 * 0.8)
        
        # Check the dictionary representation
        result_dict = result.to_dict()
        self.assertEqual(result_dict["content"], "Test content")
        self.assertEqual(result_dict["source"], "test_source")
        self.assertEqual(result_dict["confidence"], 0.9)
        self.assertEqual(result_dict["context_relevance"], 0.8)
        self.assertEqual(result_dict["metadata"], {"test": True})
        self.assertEqual(result_dict["overall_score"], 0.9 * 0.8)


if __name__ == '__main__':
    unittest.main()