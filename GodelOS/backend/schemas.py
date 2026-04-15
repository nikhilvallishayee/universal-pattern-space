# -*- coding: utf-8 -*-
"""
Shared API Schema Definitions for GodelOS

Canonical Pydantic v2 request/response models that define the contract
between the Svelte frontend and the FastAPI backend.  Import these into
route handlers (unified_server.py, transparency_endpoints.py, etc.) so
that validation is consistent on both sides.

Every model listed here corresponds to a frontend ``fetch()`` call in
``svelte-frontend/src/utils/api.js`` and its matching backend handler.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# POST /api/query
# ---------------------------------------------------------------------------

class QueryRequestSchema(BaseModel):
    """Canonical request for ``POST /api/query``.

    The frontend may include ``stream`` (currently unused); accepting it
    prevents 422 errors without changing backend behaviour.
    """

    query: str = Field(..., description="Natural language query to process")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for the query"
    )
    include_reasoning: bool = Field(
        False, description="Whether to include reasoning steps in response"
    )
    stream: bool = Field(
        False, description="Reserved for future streaming support"
    )


# ---------------------------------------------------------------------------
# POST /api/knowledge  (simple / frontend-friendly)
# ---------------------------------------------------------------------------

class AddKnowledgeSchema(BaseModel):
    """Canonical request for ``POST /api/knowledge``."""

    concept: Optional[str] = Field(None, description="Concept name")
    content: Optional[str] = Field(None, description="Knowledge content")
    definition: Optional[str] = Field(None, description="Definition text")
    title: Optional[str] = Field(None, description="Title for the knowledge")
    category: Optional[str] = Field(
        "general", description="Category for the knowledge"
    )
    knowledge_type: Optional[str] = Field(
        "concept", description="Type of knowledge (fact, rule, concept)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata"
    )


# ---------------------------------------------------------------------------
# POST /api/knowledge/import/wikipedia
# ---------------------------------------------------------------------------

class WikipediaImportSchema(BaseModel):
    """Canonical request for ``POST /api/knowledge/import/wikipedia``.

    The frontend sends ``title``; the backend maps this to the underlying
    ``WikipediaImportRequest.page_title``.
    """

    title: Optional[str] = Field(None, description="Wikipedia article title")
    topic: Optional[str] = Field(
        None, description="Alias for title (legacy support)"
    )
    language: str = Field("en", description="Wikipedia language edition")
    include_references: bool = Field(
        True, description="Whether to include reference links"
    )
    section_filter: List[str] = Field(
        default_factory=list, description="Specific sections to import"
    )


# ---------------------------------------------------------------------------
# POST /api/knowledge/import/url
# ---------------------------------------------------------------------------

class URLImportSchema(BaseModel):
    """Canonical request for ``POST /api/knowledge/import/url``."""

    url: str = Field(..., description="URL to scrape and import")
    category: Optional[str] = Field(
        None, description="Category hint for imported content"
    )
    max_depth: int = Field(1, ge=1, le=3, description="Max crawling depth")
    follow_links: bool = Field(
        False, description="Whether to follow internal links"
    )
    content_selectors: List[str] = Field(
        default_factory=list,
        description="CSS selectors for content extraction",
    )


# ---------------------------------------------------------------------------
# POST /api/knowledge/import/text
# ---------------------------------------------------------------------------

class TextImportSchema(BaseModel):
    """Canonical request for ``POST /api/knowledge/import/text``."""

    content: str = Field(..., description="Text content to import")
    title: str = Field(
        "Manual Text Input", description="Title for the imported content"
    )
    category: Optional[str] = Field(
        None, description="Category hint for imported content"
    )
    format_type: str = Field(
        "plain", description="Text format type (plain, markdown, html)"
    )


# ---------------------------------------------------------------------------
# POST /api/knowledge/import/batch
# ---------------------------------------------------------------------------

class BatchImportSchema(BaseModel):
    """Canonical request for ``POST /api/knowledge/import/batch``.

    The frontend sends ``sources``; the formal ``BatchImportRequest`` model
    uses ``import_requests``.  This schema normalises the field name.
    """

    sources: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of import source descriptors"
    )


# ---------------------------------------------------------------------------
# POST /api/enhanced-cognitive/query
# ---------------------------------------------------------------------------

class EnhancedCognitiveQuerySchema(BaseModel):
    """Canonical request for ``POST /api/enhanced-cognitive/query``."""

    query: str = Field(..., description="Natural language query")
    context: Optional[Any] = Field(
        None, description="Context (string identifier or dict)"
    )
    reasoning_trace: bool = Field(
        False, description="Whether to include a reasoning trace"
    )


# ---------------------------------------------------------------------------
# POST /api/transparency/provenance/query
# ---------------------------------------------------------------------------

class ProvenanceQuerySchema(BaseModel):
    """Canonical request for ``POST /api/transparency/provenance/query``.

    Superset of the original ``ProvenanceQuery`` — includes the
    ``max_depth`` / ``time_window_*`` fields sent by the frontend.
    """

    target_id: str = Field("default", description="Target item ID")
    query_type: str = Field(
        "backward_trace", description="Type of provenance query"
    )
    max_depth: int = Field(5, ge=1, description="Max trace depth")
    time_window_start: Optional[float] = Field(
        None, description="Start of time window (unix timestamp)"
    )
    time_window_end: Optional[float] = Field(
        None, description="End of time window (unix timestamp)"
    )
    include_derivation_chain: bool = Field(
        True, description="Whether to include full derivation chain"
    )


# ---------------------------------------------------------------------------
# POST /api/transparency/provenance/snapshot
# ---------------------------------------------------------------------------

class ProvenanceSnapshotSchema(BaseModel):
    """Canonical request for ``POST /api/transparency/provenance/snapshot``.

    The frontend sends an empty ``{}``; ``description`` therefore defaults
    to an empty string to avoid a 422.
    """

    description: str = Field(
        "", description="Snapshot description (optional)"
    )
    include_quality_metrics: bool = Field(
        True, description="Whether to include quality metrics"
    )
