"""
Integration tests: frontend payloads → backend schema validation → no 422 errors.

These tests import the FastAPI ``app`` from unified_server.py and use the
Starlette/HTTPX ``TestClient`` to send the **exact** JSON payloads that the
Svelte frontend (``svelte-frontend/src/utils/api.js``) sends.  Every
assertion confirms that the request is accepted (no 422 Unprocessable Entity).

The tests run **in-process** — no live backend required.
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# All tests run in-process — no backend server required.
# ---------------------------------------------------------------------------
pytestmark = [pytest.mark.integration, pytest.mark.standalone]

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client():
    """Create a TestClient bound to the unified FastAPI app."""
    from backend.unified_server import app
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# POST /api/query — frontend sends {query, context, stream}
# ---------------------------------------------------------------------------


class TestQueryEndpoint:
    """Ensure the /api/query endpoint accepts the exact frontend payload."""

    def test_query_frontend_payload(self, client):
        """Frontend sends query + context + stream; no 422."""
        resp = client.post("/api/query", json={
            "query": "What is consciousness?",
            "context": {"source": "user_interface"},
            "stream": False,
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"

    def test_query_minimal(self, client):
        """Minimal payload — just the query string."""
        resp = client.post("/api/query", json={"query": "hello"})
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"


# ---------------------------------------------------------------------------
# POST /api/knowledge — frontend sends concept/content/definition/title/category
# ---------------------------------------------------------------------------


class TestAddKnowledge:
    """Ensure /api/knowledge accepts various frontend payload shapes."""

    def test_add_knowledge_concept(self, client):
        resp = client.post("/api/knowledge", json={
            "concept": "Neural network",
            "definition": "A computing system inspired by biological neural networks",
            "category": "technology",
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"

    def test_add_knowledge_content(self, client):
        resp = client.post("/api/knowledge", json={
            "content": "The sky is blue",
            "title": "Sky colour",
            "category": "science",
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"

    def test_add_knowledge_empty_category(self, client):
        resp = client.post("/api/knowledge", json={
            "content": "test item",
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"


# ---------------------------------------------------------------------------
# POST /api/knowledge/import/wikipedia — frontend sends {title}
# ---------------------------------------------------------------------------


class TestWikipediaImport:
    """Ensure /api/knowledge/import/wikipedia accepts {title}."""

    def test_wikipedia_title_field(self, client):
        """Frontend sends ``title``, not ``page_title``."""
        resp = client.post("/api/knowledge/import/wikipedia", json={
            "title": "Artificial intelligence",
        })
        # 503 is acceptable (service not available); 422 is not.
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"

    def test_wikipedia_topic_alias(self, client):
        resp = client.post("/api/knowledge/import/wikipedia", json={
            "topic": "Machine learning",
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"


# ---------------------------------------------------------------------------
# POST /api/knowledge/import/url — frontend sends {url, category}
# ---------------------------------------------------------------------------


class TestURLImport:
    """Ensure /api/knowledge/import/url accepts {url, category}."""

    def test_url_import_frontend_payload(self, client):
        resp = client.post("/api/knowledge/import/url", json={
            "url": "https://example.com",
            "category": "web",
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"

    def test_url_import_with_extras(self, client):
        """Include all optional schema fields."""
        resp = client.post("/api/knowledge/import/url", json={
            "url": "https://example.com",
            "category": "web",
            "max_depth": 2,
            "follow_links": True,
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"


# ---------------------------------------------------------------------------
# POST /api/knowledge/import/text — frontend sends {content, title, category}
# ---------------------------------------------------------------------------


class TestTextImport:
    """Ensure /api/knowledge/import/text accepts {content, title, category}."""

    def test_text_import_frontend_payload(self, client):
        resp = client.post("/api/knowledge/import/text", json={
            "content": "Some text content for import",
            "title": "Manual Text Input",
            "category": "document",
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"

    def test_text_import_minimal(self, client):
        resp = client.post("/api/knowledge/import/text", json={
            "content": "Minimal text",
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"


# ---------------------------------------------------------------------------
# POST /api/knowledge/import/batch — frontend sends {sources: [...]}
# ---------------------------------------------------------------------------


class TestBatchImport:
    """Ensure /api/knowledge/import/batch accepts {sources}."""

    def test_batch_import_frontend_payload(self, client):
        resp = client.post("/api/knowledge/import/batch", json={
            "sources": [
                {"type": "url", "url": "https://example.com"},
                {"type": "text", "content": "inline text"},
            ],
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"

    def test_batch_import_empty(self, client):
        resp = client.post("/api/knowledge/import/batch", json={
            "sources": [],
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"


# ---------------------------------------------------------------------------
# POST /api/enhanced-cognitive/query — frontend sends {query, context}
# ---------------------------------------------------------------------------


class TestEnhancedCognitiveQuery:
    """Ensure /api/enhanced-cognitive/query accepts {query, context}."""

    def test_enhanced_query_frontend_payload(self, client):
        resp = client.post("/api/enhanced-cognitive/query", json={
            "query": "Explain consciousness",
            "context": "user_interface",
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"

    def test_enhanced_query_dict_context(self, client):
        """Context may also be a dict."""
        resp = client.post("/api/enhanced-cognitive/query", json={
            "query": "Explain consciousness",
            "context": {"source": "user_interface"},
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"


# ---------------------------------------------------------------------------
# POST /api/transparency/provenance/query — frontend sends extended fields
# ---------------------------------------------------------------------------


class TestProvenanceQuery:
    """Ensure provenance query accepts the full frontend payload."""

    def test_provenance_query_frontend_payload(self, client):
        resp = client.post("/api/transparency/provenance/query", json={
            "target_id": "default",
            "query_type": "backward_trace",
            "max_depth": 5,
            "time_window_start": None,
            "time_window_end": None,
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"

    def test_provenance_query_minimal(self, client):
        resp = client.post("/api/transparency/provenance/query", json={
            "target_id": "item_1",
            "query_type": "backward_trace",
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"


# ---------------------------------------------------------------------------
# POST /api/transparency/provenance/snapshot — frontend sends {}
# ---------------------------------------------------------------------------


class TestProvenanceSnapshot:
    """Ensure provenance snapshot accepts an empty body (frontend pattern)."""

    def test_snapshot_empty_body(self, client):
        """Frontend sends ``{}``; description defaults to empty string."""
        resp = client.post("/api/transparency/provenance/snapshot", json={})
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"

    def test_snapshot_with_description(self, client):
        resp = client.post("/api/transparency/provenance/snapshot", json={
            "description": "Manual snapshot",
            "include_quality_metrics": True,
        })
        assert resp.status_code != 422, f"422 from field mismatch: {resp.text}"
