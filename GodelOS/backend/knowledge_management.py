"""
Knowledge Management Service

Provides comprehensive knowledge base management including search, categorization,
analytics, and bulk operations for the ingested knowledge items.
"""

import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, Counter
from pathlib import Path

import aiofiles

from .knowledge_models import (
    SearchQuery, SearchResult, SearchResponse, Category, KnowledgeStatistics,
    BulkOperation, ExportRequest, KnowledgeItem, ImportStatistics
)

logger = logging.getLogger(__name__)


class KnowledgeSearchEngine:
    """Search engine for knowledge base queries."""
    
    def __init__(self):
        self.knowledge_store: Dict[str, KnowledgeItem] = {}
        self.search_index: Dict[str, Set[str]] = defaultdict(set)  # term -> knowledge_item_ids
        self.category_index: Dict[str, Set[str]] = defaultdict(set)  # category -> knowledge_item_ids
        self.source_index: Dict[str, Set[str]] = defaultdict(set)  # source_type -> knowledge_item_ids
    
    def add_knowledge_item(self, item: KnowledgeItem):
        """Add a knowledge item to the search index."""
        self.knowledge_store[item.id] = item
        
        # Index content terms
        terms = self._extract_search_terms(item.content)
        for term in terms:
            self.search_index[term].add(item.id)
        
        # Index title terms
        if item.title:
            title_terms = self._extract_search_terms(item.title)
            for term in title_terms:
                self.search_index[term].add(item.id)
        
        # Index categories
        all_categories = item.categories + item.auto_categories
        for category in all_categories:
            self.category_index[category.lower()].add(item.id)
        
        # Index source type
        self.source_index[item.source.source_type].add(item.id)
        
        logger.debug(f"Added knowledge item to search index: {item.id}")
    
    def remove_knowledge_item(self, item_id: str):
        """Remove a knowledge item from the search index."""
        if item_id not in self.knowledge_store:
            return
        
        item = self.knowledge_store[item_id]
        
        # Remove from content index
        terms = self._extract_search_terms(item.content)
        for term in terms:
            self.search_index[term].discard(item_id)
            if not self.search_index[term]:
                del self.search_index[term]
        
        # Remove from title index
        if item.title:
            title_terms = self._extract_search_terms(item.title)
            for term in title_terms:
                self.search_index[term].discard(item_id)
                if not self.search_index[term]:
                    del self.search_index[term]
        
        # Remove from category index
        all_categories = item.categories + item.auto_categories
        for category in all_categories:
            self.category_index[category.lower()].discard(item_id)
            if not self.category_index[category.lower()]:
                del self.category_index[category.lower()]
        
        # Remove from source index
        self.source_index[item.source.source_type].discard(item_id)
        if not self.source_index[item.source.source_type]:
            del self.source_index[item.source.source_type]
        
        # Remove from knowledge store
        del self.knowledge_store[item_id]
        
        logger.debug(f"Removed knowledge item from search index: {item_id}")
    
    async def search(self, query: SearchQuery) -> SearchResponse:
        """Perform a search query on the knowledge base."""
        start_time = time.time()
        
        # Extract search terms
        search_terms = self._extract_search_terms(query.query_text)
        
        if not search_terms:
            return SearchResponse(
                query=query,
                results=[],
                total_matches=0,
                search_time_ms=0,
                suggestions=[],
                facets={}
            )
        
        # Find matching items
        if query.search_type == "full_text":
            matching_items = await self._full_text_search(search_terms, query)
        elif query.search_type == "semantic":
            matching_items = await self._semantic_search(search_terms, query)
        else:  # hybrid
            matching_items = await self._hybrid_search(search_terms, query)
        
        # Apply filters
        filtered_items = self._apply_filters(matching_items, query)
        
        # Sort by relevance
        sorted_items = self._sort_by_relevance(filtered_items, search_terms, query)
        
        # Limit results
        limited_items = sorted_items[:query.max_results]
        
        # Create search results
        results = []
        for item_id, score in limited_items:
            item = self.knowledge_store[item_id]
            snippet = self._generate_snippet(item, search_terms) if query.include_snippets else None
            
            result = SearchResult(
                knowledge_item=item,
                relevance_score=score,
                snippet=snippet,
                matched_chunks=[],  # Could be enhanced to track which chunks matched
                explanation=f"Matched {len([t for t in search_terms if t in item.content.lower()])} search terms"
            )
            results.append(result)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(search_terms, query)
        
        # Generate facets
        facets = self._generate_facets(filtered_items)
        
        search_time_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=query,
            results=results,
            total_matches=len(filtered_items),
            search_time_ms=search_time_ms,
            suggestions=suggestions,
            facets=facets
        )
    
    def _extract_search_terms(self, text: str) -> List[str]:
        """Extract search terms from text."""
        if not text:
            return []
        
        # Convert to lowercase and extract words
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        
        # Filter out common stop words and short words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        terms = [word for word in words if len(word) > 2 and word not in stop_words]
        return terms
    
    async def _full_text_search(self, search_terms: List[str], query: SearchQuery) -> List[str]:
        """Perform full-text search."""
        matching_items = set()
        
        for term in search_terms:
            if term in self.search_index:
                matching_items.update(self.search_index[term])
        
        return list(matching_items)
    
    async def _semantic_search(self, search_terms: List[str], query: SearchQuery) -> List[str]:
        """Perform semantic search (simplified version)."""
        # In a full implementation, this would use embeddings and vector similarity
        # For now, we'll use enhanced keyword matching with synonyms and related terms
        
        matching_items = set()
        
        # Expand search terms with simple synonyms
        expanded_terms = search_terms.copy()
        synonym_map = {
            'computer': ['machine', 'system', 'device'],
            'software': ['program', 'application', 'code'],
            'data': ['information', 'content', 'facts'],
            'algorithm': ['method', 'procedure', 'process'],
            'network': ['connection', 'link', 'communication']
        }
        
        for term in search_terms:
            if term in synonym_map:
                expanded_terms.extend(synonym_map[term])
        
        # Search with expanded terms
        for term in expanded_terms:
            if term in self.search_index:
                matching_items.update(self.search_index[term])
        
        return list(matching_items)
    
    async def _hybrid_search(self, search_terms: List[str], query: SearchQuery) -> List[str]:
        """Perform hybrid search combining full-text and semantic approaches."""
        full_text_results = set(await self._full_text_search(search_terms, query))
        semantic_results = set(await self._semantic_search(search_terms, query))
        
        # Combine results, giving preference to items that appear in both
        all_results = full_text_results.union(semantic_results)
        return list(all_results)
    
    def _apply_filters(self, item_ids: List[str], query: SearchQuery) -> List[str]:
        """Apply filters to search results."""
        filtered_ids = []
        
        for item_id in item_ids:
            if item_id not in self.knowledge_store:
                continue
            
            item = self.knowledge_store[item_id]
            
            # Knowledge type filter
            if query.knowledge_types and item.knowledge_type not in query.knowledge_types:
                continue
            
            # Category filter
            if query.categories:
                item_categories = set(item.categories + item.auto_categories)
                query_categories = set(query.categories)
                if not item_categories.intersection(query_categories):
                    continue
            
            # Source type filter
            if query.source_types and item.source.source_type not in query.source_types:
                continue
            
            # Date range filter
            if query.date_range:
                start_date = query.date_range.get('start')
                end_date = query.date_range.get('end')
                if start_date and item.extracted_at < start_date:
                    continue
                if end_date and item.extracted_at > end_date:
                    continue
            
            # Confidence threshold filter
            if item.confidence < query.confidence_threshold:
                continue
            
            filtered_ids.append(item_id)
        
        return filtered_ids
    
    def _sort_by_relevance(self, item_ids: List[str], search_terms: List[str], query: SearchQuery) -> List[Tuple[str, float]]:
        """Sort items by relevance score."""
        scored_items = []
        
        for item_id in item_ids:
            if item_id not in self.knowledge_store:
                continue
            
            item = self.knowledge_store[item_id]
            score = self._calculate_relevance_score(item, search_terms, query)
            scored_items.append((item_id, score))
        
        # Sort by score (descending)
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return scored_items
    
    def _calculate_relevance_score(self, item: KnowledgeItem, search_terms: List[str], query: SearchQuery) -> float:
        """Calculate relevance score for an item."""
        score = 0.0
        
        content_lower = item.content.lower()
        title_lower = item.title.lower() if item.title else ""
        
        # Term frequency in content
        for term in search_terms:
            content_matches = content_lower.count(term)
            title_matches = title_lower.count(term)
            
            # Weight title matches higher
            score += content_matches * 1.0 + title_matches * 2.0
        
        # Boost based on item quality
        score *= (1.0 + item.confidence)
        score *= (1.0 + item.quality_score)
        
        # Boost recent items slightly
        age_days = (time.time() - item.extracted_at) / (24 * 3600)
        if age_days < 30:  # Items less than 30 days old
            score *= 1.1
        
        # Boost items with more access
        if item.access_count > 0:
            score *= (1.0 + min(item.access_count / 100.0, 0.5))
        
        return score
    
    def _generate_snippet(self, item: KnowledgeItem, search_terms: List[str]) -> str:
        """Generate a content snippet with highlighted search terms."""
        content = item.content
        if len(content) <= 200:
            return content
        
        # Find the best snippet location (where most search terms appear)
        best_start = 0
        best_score = 0
        
        for start in range(0, len(content) - 200, 50):
            snippet = content[start:start + 200].lower()
            score = sum(snippet.count(term) for term in search_terms)
            if score > best_score:
                best_score = score
                best_start = start
        
        # Extract snippet
        snippet = content[best_start:best_start + 200]
        
        # Add ellipsis if needed
        if best_start > 0:
            snippet = "..." + snippet
        if best_start + 200 < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _generate_suggestions(self, search_terms: List[str], query: SearchQuery) -> List[str]:
        """Generate search suggestions."""
        suggestions = []
        
        # Suggest related terms based on co-occurrence
        related_terms = set()
        for term in search_terms:
            if term in self.search_index:
                for item_id in list(self.search_index[term])[:10]:  # Limit for performance
                    if item_id in self.knowledge_store:
                        item = self.knowledge_store[item_id]
                        item_terms = self._extract_search_terms(item.content)
                        related_terms.update(item_terms[:5])  # Top 5 terms from each item
        
        # Remove original search terms
        related_terms -= set(search_terms)
        
        # Convert to suggestions
        suggestions = [f"{query.query_text} {term}" for term in list(related_terms)[:3]]
        
        return suggestions
    
    def _generate_facets(self, item_ids: List[str]) -> Dict[str, Dict[str, int]]:
        """Generate faceted search results."""
        facets = {
            'knowledge_types': defaultdict(int),
            'categories': defaultdict(int),
            'source_types': defaultdict(int)
        }
        
        for item_id in item_ids:
            if item_id not in self.knowledge_store:
                continue
            
            item = self.knowledge_store[item_id]
            
            # Knowledge type facet
            facets['knowledge_types'][item.knowledge_type] += 1
            
            # Category facets
            for category in item.categories + item.auto_categories:
                facets['categories'][category] += 1
            
            # Source type facet
            facets['source_types'][item.source.source_type] += 1
        
        # Convert defaultdicts to regular dicts and limit results
        return {
            facet_name: dict(sorted(facet_data.items(), key=lambda x: x[1], reverse=True)[:10])
            for facet_name, facet_data in facets.items()
        }


class KnowledgeManagementService:
    """Main service for knowledge base management operations."""
    
    def __init__(self, storage_path: str = "./knowledge_storage"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.search_engine = KnowledgeSearchEngine()
        self.categories: Dict[str, Category] = {}
        self.bulk_operations: Dict[str, BulkOperation] = {}
    
    async def initialize(self):
        """Initialize the knowledge management service."""
        logger.info("Initializing Knowledge Management Service...")
        
        # Load categories
        await self._load_categories()
        
        # Load knowledge items into search engine
        await self._load_knowledge_items()
        
        logger.info("Knowledge Management Service initialized successfully")
    
    async def search_knowledge(self, query: SearchQuery) -> SearchResponse:
        """Search the knowledge base."""
        return await self.search_engine.search(query)
    
    async def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """Get a specific knowledge item by ID."""
        item = self.search_engine.knowledge_store.get(item_id)
        if item:
            # Update access statistics
            item.access_count += 1
            item.last_accessed = time.time()
            await self._save_knowledge_item(item)
        return item
    
    async def delete_knowledge_item(self, item_id: str) -> bool:
        """Delete a knowledge item."""
        if item_id in self.search_engine.knowledge_store:
            self.search_engine.remove_knowledge_item(item_id)
            
            # Delete file
            item_file = self.storage_path / f"{item_id}.json"
            try:
                item_file.unlink()
            except FileNotFoundError:
                pass
            
            logger.info(f"Deleted knowledge item: {item_id}")
            return True
        return False
    
    async def get_categories(self) -> List[Category]:
        """Get all knowledge categories."""
        return list(self.categories.values())
    
    async def create_category(self, category: Category) -> bool:
        """Create a new knowledge category."""
        if category.category_id in self.categories:
            return False
        
        self.categories[category.category_id] = category
        await self._save_categories()
        
        logger.info(f"Created category: {category.name}")
        return True
    
    async def update_category(self, category: Category) -> bool:
        """Update an existing category."""
        if category.category_id not in self.categories:
            return False
        
        self.categories[category.category_id] = category
        await self._save_categories()
        
        logger.info(f"Updated category: {category.name}")
        return True
    
    async def delete_category(self, category_id: str) -> bool:
        """Delete a category."""
        if category_id in self.categories:
            del self.categories[category_id]
            await self._save_categories()
            
            logger.info(f"Deleted category: {category_id}")
            return True
        return False
    
    async def categorize_items(self, item_ids: List[str], categories: List[str]) -> int:
        """Add categories to knowledge items."""
        updated_count = 0
        
        for item_id in item_ids:
            if item_id in self.search_engine.knowledge_store:
                item = self.search_engine.knowledge_store[item_id]
                
                # Add new categories
                for category in categories:
                    if category not in item.manual_categories:
                        item.manual_categories.append(category)
                        item.categories.append(category)
                
                await self._save_knowledge_item(item)
                updated_count += 1
        
        logger.info(f"Categorized {updated_count} knowledge items")
        return updated_count
    
    async def get_knowledge_statistics(self) -> KnowledgeStatistics:
        """Get comprehensive knowledge base statistics."""
        items = list(self.search_engine.knowledge_store.values())
        
        if not items:
            return KnowledgeStatistics(
                total_items=0,
                average_confidence=0.0,
                recent_imports=0,
                import_success_rate=1.0,
                average_import_time=0.0,
                total_storage_mb=0.0,
                index_size_mb=0.0
            )
        
        # Basic counts
        total_items = len(items)
        items_by_type = Counter(item.knowledge_type for item in items)
        items_by_source = Counter(item.source.source_type for item in items)
        
        # Category counts
        all_categories = []
        for item in items:
            all_categories.extend(item.categories + item.auto_categories)
        items_by_category = Counter(all_categories)
        
        # Quality metrics
        average_confidence = sum(item.confidence for item in items) / total_items
        quality_ranges = {'low': 0, 'medium': 0, 'high': 0}
        validation_status_counts = Counter(item.validation_status for item in items)
        
        for item in items:
            if item.quality_score < 0.4:
                quality_ranges['low'] += 1
            elif item.quality_score < 0.7:
                quality_ranges['medium'] += 1
            else:
                quality_ranges['high'] += 1
        
        # Usage metrics
        most_accessed = sorted(items, key=lambda x: x.access_count, reverse=True)[:10]
        most_accessed_items = [item.id for item in most_accessed]
        
        # Recent imports (last 24 hours)
        recent_cutoff = time.time() - (24 * 3600)
        recent_imports = sum(1 for item in items if item.extracted_at > recent_cutoff)
        
        # Storage metrics
        total_storage_mb = sum(len(item.content.encode()) for item in items) / (1024 * 1024)
        index_size_mb = len(str(self.search_engine.search_index).encode()) / (1024 * 1024)
        
        return KnowledgeStatistics(
            total_items=total_items,
            items_by_type=dict(items_by_type),
            items_by_source=dict(items_by_source),
            items_by_category=dict(items_by_category),
            average_confidence=average_confidence,
            quality_distribution=quality_ranges,
            validation_status_counts=dict(validation_status_counts),
            most_accessed_items=most_accessed_items,
            access_patterns={},  # Could be enhanced with time-based access patterns
            popular_categories=list(dict(items_by_category.most_common(10)).keys()),
            recent_imports=recent_imports,
            import_success_rate=1.0,  # Would need to track from import service
            average_import_time=0.0,  # Would need to track from import service
            total_storage_mb=total_storage_mb,
            index_size_mb=index_size_mb
        )
    
    async def _load_categories(self):
        """Load categories from storage."""
        categories_file = self.storage_path / "categories.json"
        if categories_file.exists():
            try:
                async with aiofiles.open(categories_file, 'r') as f:
                    categories_data = json.loads(await f.read())
                    for cat_data in categories_data:
                        category = Category(**cat_data)
                        self.categories[category.category_id] = category
                logger.info(f"Loaded {len(self.categories)} categories")
            except Exception as e:
                logger.error(f"Error loading categories: {e}")
    
    async def _save_categories(self):
        """Save categories to storage."""
        categories_file = self.storage_path / "categories.json"
        try:
            categories_data = [cat.model_dump() for cat in self.categories.values()]
            async with aiofiles.open(categories_file, 'w') as f:
                await f.write(json.dumps(categories_data, indent=2))
        except Exception as e:
            logger.error(f"Error saving categories: {e}")
    
    async def _load_knowledge_items(self):
        """Load knowledge items into the search engine."""
        for item_file in self.storage_path.glob("*.json"):
            if item_file.name in ["categories.json"] or item_file.name.startswith("temp_"):
                continue
            
            try:
                async with aiofiles.open(item_file, 'r') as f:
                    item_data = json.loads(await f.read())
                    knowledge_item = KnowledgeItem(**item_data)
                    self.search_engine.add_knowledge_item(knowledge_item)
            except Exception as e:
                logger.warning(f"Failed to load knowledge item {item_file}: {e}")
        
        logger.info(f"Loaded {len(self.search_engine.knowledge_store)} knowledge items into search engine")
    
    async def _save_knowledge_item(self, item: KnowledgeItem):
        """Save a knowledge item to storage."""
        item_file = self.storage_path / f"{item.id}.json"
        try:
            async with aiofiles.open(item_file, 'w') as f:
                await f.write(item.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Error saving knowledge item {item.id}: {e}")


# Global instance
knowledge_management_service = KnowledgeManagementService()