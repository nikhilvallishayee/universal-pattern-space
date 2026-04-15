"""
Knowledge Management Tests for GödelOS Backend

Comprehensive test suite for knowledge management functionality including:
- Knowledge ingestion and processing
- Search engine functionality
- Category management
- Storage and retrieval operations
- Import/export operations
- Analytics and statistics
"""

import asyncio
import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Import the modules to test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.knowledge_management import KnowledgeManagementService, KnowledgeSearchEngine
from backend.knowledge_models import (
    KnowledgeItem, ImportSource, SearchQuery, SearchResult, Category,
    URLImportRequest, FileImportRequest, WikipediaImportRequest, TextImportRequest
)


class TestKnowledgeSearchEngine:
    """Test the knowledge search engine functionality."""
    
    def setup_method(self):
        """Set up search engine for each test."""
        self.search_engine = KnowledgeSearchEngine()
        
        # Add sample knowledge items
        self.sample_items = [
            KnowledgeItem(
                id="item1",
                title="Machine Learning Basics",
                content="Machine learning is a subset of artificial intelligence that focuses on algorithms.",
                knowledge_type="concept",
                source=ImportSource(source_type="manual", source_identifier="test"),
                import_id="test_import",
                categories=["technology", "ai"],
                auto_categories=["computer_science"],
                manual_categories=[],
                quality_score=0.8,
                confidence=0.9,
                validation_status="validated",
                extracted_at=time.time(),
                access_count=5,
                last_accessed=time.time()
            ),
            KnowledgeItem(
                id="item2",
                title="Python Programming",
                content="Python is a high-level programming language known for its simplicity and readability.",
                knowledge_type="fact",
                source=ImportSource(source_type="url", source_identifier="python.org"),
                import_id="test_import",
                categories=["programming", "technology"],
                auto_categories=["languages"],
                manual_categories=["tutorial"],
                quality_score=0.7,
                confidence=0.85,
                validation_status="validated",
                extracted_at=time.time() - 3600,
                access_count=10,
                last_accessed=time.time() - 1800
            ),
            KnowledgeItem(
                id="item3",
                title="Quantum Computing",
                content="Quantum computing uses quantum mechanics to process information in quantum bits.",
                knowledge_type="concept",
                source=ImportSource(source_type="wikipedia", source_identifier="Quantum_computing"),
                import_id="test_import",
                categories=["physics", "technology"],
                auto_categories=["quantum_mechanics"],
                manual_categories=[],
                quality_score=0.9,
                confidence=0.95,
                validation_status="validated",
                extracted_at=time.time() - 7200,
                access_count=3,
                last_accessed=time.time() - 3600
            )
        ]
        
        for item in self.sample_items:
            self.search_engine.add_knowledge_item(item)
    
    def test_add_knowledge_item(self):
        """Test adding knowledge items to the search engine."""
        initial_count = len(self.search_engine.knowledge_store)
        
        new_item = KnowledgeItem(
            id="test_item",
            title="Test Item",
            content="This is a test knowledge item for testing purposes.",
            knowledge_type="fact",
            source=ImportSource(source_type="manual", source_identifier="test_source"),
            import_id="test_import",
            categories=["test"],
            auto_categories=[],
            manual_categories=[],
            quality_score=1.0,
            confidence=1.0,
            validation_status="pending",
            extracted_at=time.time(),
            access_count=0,
            last_accessed=time.time()
        )
        
        self.search_engine.add_knowledge_item(new_item)
        
        assert len(self.search_engine.knowledge_store) == initial_count + 1
        assert "test_item" in self.search_engine.knowledge_store
        
        # Verify indexing
        assert "test" in self.search_engine.search_index
        assert "test_item" in self.search_engine.search_index["test"]
        assert "test_item" in self.search_engine.category_index["test"]
        assert "test_item" in self.search_engine.source_index["manual"]
    
    def test_remove_knowledge_item(self):
        """Test removing knowledge items from the search engine."""
        initial_count = len(self.search_engine.knowledge_store)
        
        self.search_engine.remove_knowledge_item("item1")
        
        assert len(self.search_engine.knowledge_store) == initial_count - 1
        assert "item1" not in self.search_engine.knowledge_store
        
        # Verify removal from indices
        assert "item1" not in self.search_engine.search_index.get("machine", set())
        assert "item1" not in self.search_engine.category_index.get("technology", set())
    
    @pytest.mark.asyncio
    async def test_full_text_search(self):
        """Test full-text search functionality."""
        query = SearchQuery(
            query_text="machine learning artificial intelligence",
            search_type="full_text",
            max_results=10
        )
        
        response = await self.search_engine.search(query)
        
        assert response.total_matches > 0
        assert len(response.results) > 0
        
        # Should find the machine learning item
        result_ids = [result.knowledge_item.id for result in response.results]
        assert "item1" in result_ids
        
        # Verify response structure
        assert response.search_time_ms > 0
        assert isinstance(response.suggestions, list)
        assert isinstance(response.facets, dict)
    
    @pytest.mark.asyncio
    async def test_semantic_search(self):
        """Test semantic search functionality."""
        query = SearchQuery(
            query_text="computer programming code",
            search_type="semantic",
            max_results=10
        )
        
        response = await self.search_engine.search(query)
        
        assert response.total_matches > 0
        # Should find programming-related items through synonym expansion
        result_ids = [result.knowledge_item.id for result in response.results]
        assert "item2" in result_ids
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self):
        """Test hybrid search combining full-text and semantic approaches."""
        query = SearchQuery(
            query_text="quantum mechanics physics",
            search_type="hybrid",
            max_results=10
        )
        
        response = await self.search_engine.search(query)
        
        assert response.total_matches > 0
        result_ids = [result.knowledge_item.id for result in response.results]
        assert "item3" in result_ids
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """Test search with various filters."""
        query = SearchQuery(
            query_text="technology",
            search_type="full_text",
            knowledge_types=["concept"],
            categories=["technology"],
            source_types=["manual"],
            confidence_threshold=0.8,
            max_results=10
        )
        
        response = await self.search_engine.search(query)
        
        # Should only return items matching all filters
        for result in response.results:
            item = result.knowledge_item
            assert item.knowledge_type == "concept"
            assert "technology" in item.categories or "technology" in item.auto_categories
            assert item.source.source_type == "manual"
            assert item.confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_search_relevance_scoring(self):
        """Test search result relevance scoring."""
        query = SearchQuery(
            query_text="programming python",
            search_type="full_text",
            max_results=10
        )
        
        response = await self.search_engine.search(query)
        
        if len(response.results) > 1:
            # Results should be sorted by relevance score
            scores = [result.relevance_score for result in response.results]
            assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_search_snippets(self):
        """Test search result snippet generation."""
        query = SearchQuery(
            query_text="artificial intelligence",
            search_type="full_text",
            include_snippets=True,
            max_results=10
        )
        
        response = await self.search_engine.search(query)
        
        for result in response.results:
            if "artificial" in result.knowledge_item.content.lower():
                assert result.snippet is not None
                assert len(result.snippet) <= 200 + 6  # 200 chars + "..." prefix/suffix
    
    @pytest.mark.asyncio
    async def test_empty_search(self):
        """Test handling of empty search queries."""
        query = SearchQuery(
            query_text="",
            search_type="full_text",
            max_results=10
        )
        
        response = await self.search_engine.search(query)
        
        assert response.total_matches == 0
        assert len(response.results) == 0
        assert response.search_time_ms == 0
    
    def test_extract_search_terms(self):
        """Test search term extraction and filtering."""
        text = "This is a test with the and or but stopwords"
        terms = self.search_engine._extract_search_terms(text)
        
        # Should exclude stop words and short words
        expected_terms = ["test", "stopwords"]
        assert set(terms) == set(expected_terms)
    
    def test_generate_facets(self):
        """Test facet generation for search results."""
        item_ids = ["item1", "item2", "item3"]
        facets = self.search_engine._generate_facets(item_ids)
        
        assert "knowledge_types" in facets
        assert "categories" in facets
        assert "source_types" in facets
        
        # Verify facet counts
        assert facets["knowledge_types"]["concept"] == 2  # item1 and item3
        assert facets["knowledge_types"]["fact"] == 1     # item2
        assert facets["categories"]["technology"] == 3    # all items


class TestKnowledgeManagementService:
    """Test the knowledge management service."""
    
    def setup_method(self):
        """Set up knowledge management service for each test."""
        # Use temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.service = KnowledgeManagementService(storage_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up after each test."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization."""
        await self.service.initialize()
        
        # Service should be initialized with empty state
        assert len(self.service.search_engine.knowledge_store) == 0
        assert len(self.service.categories) == 0
    
    @pytest.mark.asyncio
    async def test_category_management(self):
        """Test category management operations."""
        await self.service.initialize()
        
        # Create test category
        category = Category(
            category_id="test_cat",
            name="Test Category",
            description="A test category",
            color="#FF0000",
            parent_category=None,
            metadata={}
        )
        
        # Test category creation
        success = await self.service.create_category(category)
        assert success is True
        assert "test_cat" in self.service.categories
        
        # Test duplicate category creation
        duplicate_success = await self.service.create_category(category)
        assert duplicate_success is False
        
        # Test category retrieval
        categories = await self.service.get_categories()
        assert len(categories) == 1
        assert categories[0].category_id == "test_cat"
        
        # Test category update
        category.description = "Updated description"
        update_success = await self.service.update_category(category)
        assert update_success is True
        assert self.service.categories["test_cat"].description == "Updated description"
        
        # Test category deletion
        delete_success = await self.service.delete_category("test_cat")
        assert delete_success is True
        assert "test_cat" not in self.service.categories
    
    @pytest.mark.asyncio
    async def test_knowledge_item_operations(self):
        """Test knowledge item CRUD operations."""
        await self.service.initialize()
        
        # Create test knowledge item
        item = KnowledgeItem(
            id="test_item",
            title="Test Knowledge",
            content="This is test knowledge content.",
            knowledge_type="fact",
            source=ImportSource(source_type="manual", source_identifier="test"),
            import_id="test_import",
            categories=["test"],
            auto_categories=[],
            manual_categories=[],
            quality_score=1.0,
            confidence=1.0,
            validation_status="pending",
            extracted_at=time.time(),
            access_count=0,
            last_accessed=time.time()
        )
        
        # Add to search engine
        self.service.search_engine.add_knowledge_item(item)
        
        # Test item retrieval
        retrieved_item = await self.service.get_knowledge_item("test_item")
        assert retrieved_item is not None
        assert retrieved_item.id == "test_item"
        assert retrieved_item.access_count == 1  # Should increment on access
        
        # Test item deletion
        delete_success = await self.service.delete_knowledge_item("test_item")
        assert delete_success is True
        assert "test_item" not in self.service.search_engine.knowledge_store
        
        # Test deleting non-existent item
        delete_fail = await self.service.delete_knowledge_item("nonexistent")
        assert delete_fail is False
    
    @pytest.mark.asyncio
    async def test_categorize_items(self):
        """Test item categorization functionality."""
        await self.service.initialize()
        
        # Create test items
        item1 = KnowledgeItem(
            id="item1",
            title="Item 1",
            content="Content 1",
            knowledge_type="fact",
            source=ImportSource(source_type="manual", source_identifier="test"),
            import_id="test_import",
            categories=["original"],
            auto_categories=[],
            manual_categories=[],
            quality_score=1.0,
            confidence=1.0,
            validation_status="pending",
            extracted_at=time.time(),
            access_count=0,
            last_accessed=time.time()
        )
        
        item2 = KnowledgeItem(
            id="item2",
            title="Item 2",
            content="Content 2",
            knowledge_type="fact",
            source=ImportSource(source_type="manual", source_identifier="test"),
            import_id="test_import",
            categories=["original"],
            auto_categories=[],
            manual_categories=[],
            quality_score=1.0,
            confidence=1.0,
            validation_status="pending",
            extracted_at=time.time(),
            access_count=0,
            last_accessed=time.time()
        )
        
        self.service.search_engine.add_knowledge_item(item1)
        self.service.search_engine.add_knowledge_item(item2)
        
        # Categorize items
        updated_count = await self.service.categorize_items(
            ["item1", "item2"], 
            ["new_category", "another_category"]
        )
        
        assert updated_count == 2
        
        # Verify categories were added
        updated_item1 = self.service.search_engine.knowledge_store["item1"]
        assert "new_category" in updated_item1.categories
        assert "another_category" in updated_item1.categories
    
    @pytest.mark.asyncio
    async def test_knowledge_statistics(self):
        """Test knowledge statistics generation."""
        await self.service.initialize()
        
        # Add sample items with different characteristics
        items = [
            KnowledgeItem(
                id=f"item{i}",
                title=f"Item {i}",
                content=f"Content for item {i}",
                knowledge_type="concept" if i % 2 == 0 else "fact",
                source=ImportSource(
                    source_type="url" if i % 3 == 0 else "manual",
                    source_identifier=f"source{i}"
                ),
                import_id="test_import",
                categories=[f"category{i % 3}"],
                auto_categories=[],
                manual_categories=[],
                quality_score=min(0.5 + (i * 0.05), 1.0),
                confidence=min(0.7 + (i * 0.03), 1.0),
                validation_status="validated",
                extracted_at=time.time() - (i * 3600),  # Different ages
                access_count=i,
                last_accessed=time.time()
            )
            for i in range(10)
        ]
        
        for item in items:
            self.service.search_engine.add_knowledge_item(item)
        
        # Get statistics
        stats = await self.service.get_knowledge_statistics()
        
        assert stats.total_items == 10
        assert "concept" in stats.items_by_type
        assert "fact" in stats.items_by_type
        assert "url" in stats.items_by_source
        assert "manual" in stats.items_by_source
        assert len(stats.items_by_category) > 0
        assert 0.0 <= stats.average_confidence <= 1.0
        assert "low" in stats.quality_distribution
        assert "medium" in stats.quality_distribution
        assert "high" in stats.quality_distribution
        assert len(stats.most_accessed_items) <= 10
        assert stats.total_storage_mb >= 0
        assert stats.index_size_mb >= 0
    
    @pytest.mark.asyncio
    async def test_search_integration(self):
        """Test search integration with the management service."""
        await self.service.initialize()
        
        # Add test item
        item = KnowledgeItem(
            id="search_test",
            title="Search Test Item",
            content="This item is for testing search integration functionality.",
            knowledge_type="fact",
            source=ImportSource(source_type="manual", source_identifier="test"),
            import_id="test_import",
            categories=["search", "test"],
            auto_categories=[],
            manual_categories=[],
            quality_score=1.0,
            confidence=1.0,
            validation_status="validated",
            extracted_at=time.time(),
            access_count=0,
            last_accessed=time.time()
        )
        
        self.service.search_engine.add_knowledge_item(item)
        
        # Test search through service
        query = SearchQuery(
            query_text="search integration",
            search_type="full_text",
            max_results=10
        )
        
        response = await self.service.search_knowledge(query)
        
        assert response.total_matches > 0
        result_ids = [result.knowledge_item.id for result in response.results]
        assert "search_test" in result_ids


class TestKnowledgeIngestion:
    """Test knowledge ingestion and import functionality."""
    
    def setup_method(self):
        """Set up for ingestion tests."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_url_import_request_creation(self):
        """Test URL import request creation."""
        import_source = ImportSource(
            source_type="url",
            source_identifier="https://example.com",
            metadata={"category": "web"}
        )
        
        url_request = URLImportRequest(
            source=import_source,
            url="https://example.com",
            categorization_hints=["web", "example"],
            priority=5
        )
        
        normalized_url = str(url_request.url).rstrip("/")
        assert normalized_url == "https://example.com"
        assert url_request.source.source_type == "url"
        assert "web" in url_request.categorization_hints
        assert url_request.priority == 5
    
    def test_file_import_request_creation(self):
        """Test file import request creation."""
        import_source = ImportSource(
            source_type="file",
            source_identifier="test.txt",
            metadata={"original_filename": "test.txt"}
        )
        
        file_request = FileImportRequest(
            source=import_source,
            filename="test.txt",
            file_type="txt",
            encoding="utf-8",
            categorization_hints=["document"],
            processing_options={},
            priority=5
        )
        
        assert file_request.filename == "test.txt"
        assert file_request.file_type == "txt"
        assert file_request.encoding == "utf-8"
        assert "document" in file_request.categorization_hints
    
    def test_wikipedia_import_request_creation(self):
        """Test Wikipedia import request creation."""
        import_source = ImportSource(
            source_type="wikipedia",
            source_identifier="Machine_learning",
            metadata={"category": "encyclopedia"}
        )
        
        wiki_request = WikipediaImportRequest(
            source=import_source,
            page_title="Machine learning",
            categorization_hints=["ai", "technology"],
            priority=5
        )
        
        assert wiki_request.page_title == "Machine learning"
        assert wiki_request.source.source_type == "wikipedia"
        assert "ai" in wiki_request.categorization_hints
    
    def test_text_import_request_creation(self):
        """Test text import request creation."""
        import_source = ImportSource(
            source_type="text",
            source_identifier="Manual Entry",
            metadata={"category": "manual"}
        )
        
        text_request = TextImportRequest(
            source=import_source,
            content="This is manually entered text content for testing.",
            title="Manual Entry",
            categorization_hints=["manual", "test"],
            priority=5
        )
        
        assert text_request.content == "This is manually entered text content for testing."
        assert text_request.title == "Manual Entry"
        assert text_request.source.source_type == "text"


class TestKnowledgeModelsValidation:
    """Test knowledge models and validation."""
    
    def test_knowledge_item_validation(self):
        """Test KnowledgeItem model validation."""
        # Valid knowledge item
        valid_item = KnowledgeItem(
            id="valid_item",
            title="Valid Item",
            content="This is valid content.",
            knowledge_type="concept",
            source=ImportSource(source_type="manual", source_identifier="test"),
            import_id="test_import",
            categories=["test"],
            auto_categories=[],
            manual_categories=[],
            quality_score=0.8,
            confidence=0.9,
            validation_status="validated",
            extracted_at=time.time(),
            access_count=0,
            last_accessed=time.time()
        )
        
        assert valid_item.id == "valid_item"
        assert valid_item.quality_score == 0.8
        assert valid_item.confidence == 0.9
    
    def test_search_query_validation(self):
        """Test SearchQuery model validation."""
        # Valid search query
        valid_query = SearchQuery(
            query_text="test query",
            search_type="full_text",
            knowledge_types=["concept", "fact"],
            categories=["test"],
            source_types=["manual", "web"],
            confidence_threshold=0.5,
            max_results=20,
            include_snippets=True
        )
        
        assert valid_query.query_text == "test query"
        assert valid_query.search_type == "full_text"
        assert valid_query.max_results == 20
        assert valid_query.include_snippets is True
    
    def test_category_validation(self):
        """Test Category model validation."""
        # Valid category
        valid_category = Category(
            category_id="test_category",
            name="Test Category",
            description="A category for testing",
            color="#FF5733",
            parent_category=None,
            metadata={"created_by": "test"}
        )
        
        assert valid_category.category_id == "test_category"
        assert valid_category.name == "Test Category"
        assert valid_category.color == "#FF5733"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])