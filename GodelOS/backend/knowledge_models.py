"""
Knowledge Ingestion Data Models

Defines Pydantic models for the comprehensive knowledge ingestion system,
including import operations, search queries, categorization, and analytics.
"""

from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
import time


class ImportSource(BaseModel):
    """Model for import source information."""
    source_type: Literal["url", "file", "wikipedia", "text", "batch", "manual"] = Field(..., description="Type of import source")
    source_identifier: str = Field(..., description="URL, filename, Wikipedia title, or identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Source-specific metadata")


class ImportRequest(BaseModel):
    """Base model for knowledge import requests."""
    source: ImportSource = Field(..., description="Import source information")
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Processing configuration")
    categorization_hints: Optional[List[str]] = Field(default_factory=list, description="Suggested categories")
    priority: int = Field(default=5, ge=1, le=10, description="Import priority (1-10)")


class URLImportRequest(ImportRequest):
    """Request model for URL-based knowledge import."""
    url: HttpUrl = Field(..., description="URL to scrape and import")
    max_depth: int = Field(default=1, ge=1, le=3, description="Maximum crawling depth")
    follow_links: bool = Field(default=False, description="Whether to follow internal links")
    content_selectors: Optional[List[str]] = Field(default_factory=list, description="CSS selectors for content extraction")


class FileImportRequest(ImportRequest):
    """Request model for file-based knowledge import."""
    filename: str = Field(..., description="Name of the uploaded file")
    file_type: Literal["pdf", "txt", "json", "csv", "docx"] = Field(..., description="Type of file being imported")
    encoding: Optional[str] = Field(default="utf-8", description="File encoding")
    parse_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="File-specific parsing options")


class WikipediaImportRequest(ImportRequest):
    """Request model for Wikipedia-based knowledge import."""
    page_title: str = Field(..., description="Wikipedia page title to import")
    language: str = Field(default="en", description="Wikipedia language edition")
    include_references: bool = Field(default=True, description="Whether to include reference links")
    section_filter: Optional[List[str]] = Field(default_factory=list, description="Specific sections to import")


class TextImportRequest(ImportRequest):
    """Request model for manual text import."""
    content: str = Field(..., description="Text content to import")
    title: Optional[str] = Field(None, description="Title for the imported content")
    format_type: Literal["plain", "markdown", "html"] = Field(default="plain", description="Text format type")


class BatchImportRequest(BaseModel):
    """Request model for batch import operations."""
    import_requests: List[ImportRequest] = Field(..., description="List of import requests to process")
    batch_name: Optional[str] = Field(None, description="Name for this batch import")
    parallel_processing: bool = Field(default=True, description="Whether to process imports in parallel")
    max_concurrent: int = Field(default=5, ge=1, le=20, description="Maximum concurrent import operations")


class ImportProgress(BaseModel):
    """Model for tracking import operation progress."""
    import_id: str = Field(..., description="Unique identifier for the import operation")
    status: Literal["queued", "processing", "completed", "failed", "cancelled"] = Field(..., description="Current import status")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Progress percentage (0-100)")
    current_step: str = Field(..., description="Current processing step description")
    total_steps: int = Field(..., description="Total number of processing steps")
    completed_steps: int = Field(..., description="Number of completed steps")
    started_at: float = Field(..., description="Timestamp when import started")
    estimated_completion: Optional[float] = Field(None, description="Estimated completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if import failed")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings during import")


class ContentChunk(BaseModel):
    """Model for processed content chunks."""
    chunk_id: str = Field(..., description="Unique identifier for the content chunk")
    content: str = Field(..., description="Chunk content")
    chunk_type: Literal["paragraph", "section", "table", "list", "code", "metadata"] = Field(..., description="Type of content chunk")
    position: int = Field(..., description="Position within the source document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk-specific metadata")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in chunk extraction quality")


class KnowledgeItem(BaseModel):
    """Enhanced model for knowledge items with ingestion metadata."""
    id: str = Field(..., description="Unique identifier for the knowledge item")
    content: str = Field(..., description="Knowledge content")
    knowledge_type: Literal["fact", "rule", "concept", "procedure", "example"] = Field(..., description="Type of knowledge")
    title: Optional[str] = Field(None, description="Title or summary of the knowledge")
    
    # Source and provenance
    source: ImportSource = Field(..., description="Original source of this knowledge")
    import_id: str = Field(..., description="ID of the import operation that created this item")
    extracted_at: float = Field(default_factory=time.time, description="Timestamp when knowledge was extracted")
    
    # Content structure
    chunks: List[ContentChunk] = Field(default_factory=list, description="Content chunks that make up this knowledge")
    relationships: List[str] = Field(default_factory=list, description="IDs of related knowledge items")
    
    # Quality and validation
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in knowledge quality")
    validation_status: Literal["pending", "validated", "rejected", "needs_review"] = Field(default="pending", description="Validation status")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Automated quality assessment score")
    
    # Categorization and organization
    categories: List[str] = Field(default_factory=list, description="Knowledge categories/tags")
    auto_categories: List[str] = Field(default_factory=list, description="Automatically assigned categories")
    manual_categories: List[str] = Field(default_factory=list, description="Manually assigned categories")
    
    # Usage and analytics
    access_count: int = Field(default=0, description="Number of times this knowledge has been accessed")
    last_accessed: Optional[float] = Field(None, description="Timestamp of last access")
    usage_context: List[str] = Field(default_factory=list, description="Contexts where this knowledge has been used")
    
    # Metadata and annotations
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    annotations: List[str] = Field(default_factory=list, description="Human annotations and notes")


class SearchQuery(BaseModel):
    """Model for knowledge base search queries."""
    query_text: str = Field(..., description="Search query text")
    search_type: Literal["full_text", "semantic", "hybrid"] = Field(default="hybrid", description="Type of search to perform")
    
    # Filters
    knowledge_types: Optional[List[str]] = Field(default_factory=list, description="Filter by knowledge types")
    categories: Optional[List[str]] = Field(default_factory=list, description="Filter by categories")
    source_types: Optional[List[str]] = Field(default_factory=list, description="Filter by source types")
    date_range: Optional[Dict[str, float]] = Field(None, description="Date range filter (start/end timestamps)")
    confidence_threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum confidence threshold")
    
    # Search options
    max_results: int = Field(default=50, ge=1, le=1000, description="Maximum number of results to return")
    include_snippets: bool = Field(default=True, description="Whether to include content snippets")
    highlight_terms: bool = Field(default=True, description="Whether to highlight search terms")
    include_related: bool = Field(default=False, description="Whether to include related knowledge items")


class SearchResult(BaseModel):
    """Model for individual search results."""
    knowledge_item: KnowledgeItem = Field(..., description="The matching knowledge item")
    relevance_score: float = Field(..., ge=0.0, description="Relevance score for this result")
    snippet: Optional[str] = Field(None, description="Content snippet with highlighted terms")
    matched_chunks: List[str] = Field(default_factory=list, description="IDs of chunks that matched the query")
    explanation: Optional[str] = Field(None, description="Explanation of why this item matched")


class SearchResponse(BaseModel):
    """Response model for search operations."""
    query: SearchQuery = Field(..., description="Original search query")
    results: List[SearchResult] = Field(default_factory=list, description="Search results")
    total_matches: int = Field(..., description="Total number of matching items")
    search_time_ms: float = Field(..., description="Time taken to perform search in milliseconds")
    suggestions: List[str] = Field(default_factory=list, description="Query suggestions for refinement")
    facets: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Faceted search results")


class Category(BaseModel):
    """Model for knowledge categorization."""
    category_id: str = Field(..., description="Unique identifier for the category")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    parent_category: Optional[str] = Field(None, description="Parent category ID for hierarchical organization")
    color: Optional[str] = Field(None, description="Color code for UI display")
    icon: Optional[str] = Field(None, description="Icon identifier for UI display")
    knowledge_count: int = Field(default=0, description="Number of knowledge items in this category")
    auto_assignment_rules: List[str] = Field(default_factory=list, description="Rules for automatic category assignment")
    created_at: float = Field(default_factory=time.time, description="Timestamp when category was created")


class KnowledgeStatistics(BaseModel):
    """Model for knowledge base analytics and statistics."""
    total_items: int = Field(..., description="Total number of knowledge items")
    items_by_type: Dict[str, int] = Field(default_factory=dict, description="Count of items by knowledge type")
    items_by_source: Dict[str, int] = Field(default_factory=dict, description="Count of items by source type")
    items_by_category: Dict[str, int] = Field(default_factory=dict, description="Count of items by category")
    
    # Quality metrics
    average_confidence: float = Field(..., description="Average confidence score across all items")
    quality_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of quality scores")
    validation_status_counts: Dict[str, int] = Field(default_factory=dict, description="Count by validation status")
    
    # Usage metrics
    most_accessed_items: List[str] = Field(default_factory=list, description="IDs of most frequently accessed items")
    access_patterns: Dict[str, int] = Field(default_factory=dict, description="Access patterns over time")
    popular_categories: List[str] = Field(default_factory=list, description="Most popular categories")
    
    # Import metrics
    recent_imports: int = Field(..., description="Number of imports in the last 24 hours")
    import_success_rate: float = Field(..., description="Success rate of import operations")
    average_import_time: float = Field(..., description="Average time per import operation")
    
    # Storage and performance
    total_storage_mb: float = Field(..., description="Total storage used by knowledge base in MB")
    index_size_mb: float = Field(..., description="Size of search indexes in MB")
    last_updated: float = Field(default_factory=time.time, description="Timestamp of last statistics update")


class BulkOperation(BaseModel):
    """Model for bulk operations on knowledge items."""
    operation_id: str = Field(..., description="Unique identifier for the bulk operation")
    operation_type: Literal["delete", "categorize", "export", "validate", "update"] = Field(..., description="Type of bulk operation")
    item_ids: List[str] = Field(..., description="IDs of knowledge items to operate on")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific parameters")
    status: Literal["queued", "processing", "completed", "failed"] = Field(default="queued", description="Operation status")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    results: Optional[Dict[str, Any]] = Field(None, description="Operation results")
    started_at: Optional[float] = Field(None, description="Timestamp when operation started")
    completed_at: Optional[float] = Field(None, description="Timestamp when operation completed")


class ExportRequest(BaseModel):
    """Request model for knowledge base export."""
    export_format: Literal["json", "csv", "xml", "rdf", "markdown"] = Field(..., description="Export format")
    filter_criteria: Optional[SearchQuery] = Field(None, description="Criteria for filtering items to export")
    include_metadata: bool = Field(default=True, description="Whether to include metadata in export")
    include_relationships: bool = Field(default=True, description="Whether to include relationship information")
    compression: Optional[Literal["zip", "gzip"]] = Field(None, description="Compression format for export file")


class ImportStatistics(BaseModel):
    """Model for import operation statistics."""
    import_id: str = Field(..., description="Import operation identifier")
    source_info: ImportSource = Field(..., description="Source information")
    
    # Processing results
    total_content_size: int = Field(..., description="Total size of imported content in bytes")
    chunks_extracted: int = Field(..., description="Number of content chunks extracted")
    knowledge_items_created: int = Field(..., description="Number of knowledge items created")
    duplicates_detected: int = Field(..., description="Number of duplicate items detected")
    validation_failures: int = Field(..., description="Number of items that failed validation")
    
    # Performance metrics
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    extraction_time_ms: float = Field(..., description="Time spent on content extraction")
    validation_time_ms: float = Field(..., description="Time spent on validation")
    indexing_time_ms: float = Field(..., description="Time spent on search indexing")
    
    # Quality metrics
    average_confidence: float = Field(..., description="Average confidence of imported items")
    quality_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of quality scores")
    categories_assigned: List[str] = Field(default_factory=list, description="Categories assigned to imported items")
    
    # Error tracking
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings during import")
    errors: List[str] = Field(default_factory=list, description="Errors encountered during import")
    
    completed_at: float = Field(default_factory=time.time, description="Timestamp when import completed")