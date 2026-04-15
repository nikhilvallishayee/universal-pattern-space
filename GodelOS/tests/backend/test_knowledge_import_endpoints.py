"""
Tests for all 6 knowledge import endpoints on the unified server.

Exercises the routes via httpx.AsyncClient against the ASGI app so no live
server is required.  The KnowledgeIngestionService is mocked at the module
level so that we test the HTTP layer in isolation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# We need to mock the ingestion service *before* importing the app because the
# module-level import in unified_server.py captures the global reference.  The
# fixtures below take care of this via monkeypatching.


def _make_mock_service():
    """Create a fully mocked KnowledgeIngestionService."""
    svc = MagicMock()
    svc.import_from_url = AsyncMock(return_value="url_import_001")
    svc.import_from_text = AsyncMock(return_value="text_import_001")
    svc.import_from_file = AsyncMock(return_value="file_import_001")
    svc.cancel_import = AsyncMock(return_value=True)
    svc.get_import_progress = AsyncMock(return_value=MagicMock(
        import_id="progress_001",
        status="processing",
        progress_percentage=42.0,
        started_at=1000000.0,
        completed_at=None,
        error_message=None,
        error=None,
        filename="test.txt",
    ))
    return svc


@pytest.fixture()
def patched_app():
    """
    Yield the unified_server FastAPI ``app`` with KnowledgeIngestionService
    stubbed out so the endpoints never touch real I/O.
    """
    mock_svc = _make_mock_service()

    with (
        patch("backend.unified_server.KNOWLEDGE_SERVICES_AVAILABLE", True),
        patch("backend.unified_server.knowledge_ingestion_service", mock_svc),
    ):
        from backend.unified_server import app
        yield app, mock_svc


@pytest.fixture()
def patched_app_no_service():
    """Yield the app with ingestion service unavailable (503 path)."""
    with (
        patch("backend.unified_server.KNOWLEDGE_SERVICES_AVAILABLE", False),
        patch("backend.unified_server.knowledge_ingestion_service", None),
    ):
        from backend.unified_server import app
        yield app


# ---------------------------------------------------------------------------
# Tests — happy paths
# ---------------------------------------------------------------------------


class TestKnowledgeImportURL:
    """POST /api/knowledge/import/url"""

    @pytest.mark.asyncio
    async def test_url_import_returns_200(self, patched_app):
        app, mock_svc = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/knowledge/import/url", json={
                "url": "https://example.com/article",
            })
        assert resp.status_code == 200
        body = resp.json()
        assert body["import_id"] == "url_import_001"
        assert body["status"] == "queued"
        mock_svc.import_from_url.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_url_import_missing_url(self, patched_app):
        app, _ = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/knowledge/import/url", json={})
        # URLImportSchema requires 'url'; Pydantic rejects with 422
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_url_import_service_unavailable(self, patched_app_no_service):
        app = patched_app_no_service
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/knowledge/import/url", json={
                "url": "https://example.com",
            })
        assert resp.status_code == 503


class TestKnowledgeImportText:
    """POST /api/knowledge/import/text"""

    @pytest.mark.asyncio
    async def test_text_import_returns_200(self, patched_app):
        app, mock_svc = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/knowledge/import/text", json={
                "content": "The sky is blue because of Rayleigh scattering.",
                "title": "Sky Color",
            })
        assert resp.status_code == 200
        body = resp.json()
        assert body["import_id"] == "text_import_001"
        assert body["status"] == "queued"
        assert body["content_length"] == len("The sky is blue because of Rayleigh scattering.")
        mock_svc.import_from_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_text_import_missing_content(self, patched_app):
        app, _ = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/knowledge/import/text", json={
                "title": "No content",
            })
        # TextImportSchema requires 'content'; Pydantic rejects with 422
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_text_import_service_unavailable(self, patched_app_no_service):
        app = patched_app_no_service
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/knowledge/import/text", json={
                "content": "test",
            })
        assert resp.status_code == 503


class TestKnowledgeImportFile:
    """POST /api/knowledge/import/file"""

    @pytest.mark.asyncio
    async def test_file_import_returns_200(self, patched_app):
        app, mock_svc = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/api/knowledge/import/file",
                files={"file": ("notes.txt", b"Hello world content", "text/plain")},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["import_id"] == "file_import_001"
        assert body["status"] == "started"
        assert body["filename"] == "notes.txt"
        mock_svc.import_from_file.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_file_import_pdf(self, patched_app):
        app, mock_svc = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/api/knowledge/import/file",
                files={"file": ("doc.pdf", b"%PDF-fake", "application/pdf")},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "started"

    @pytest.mark.asyncio
    async def test_file_import_service_unavailable(self, patched_app_no_service):
        app = patched_app_no_service
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/api/knowledge/import/file",
                files={"file": ("test.txt", b"x", "text/plain")},
            )
        assert resp.status_code == 503


class TestKnowledgeImportStatus:
    """GET /api/knowledge/import/status/{job_id}"""

    @pytest.mark.asyncio
    async def test_status_returns_200(self, patched_app):
        app, mock_svc = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/knowledge/import/status/progress_001")
        assert resp.status_code == 200
        body = resp.json()
        assert body["import_id"] == "progress_001"
        assert "status" in body

    @pytest.mark.asyncio
    async def test_status_not_found(self, patched_app):
        """When the job doesn't exist we still get 200 with status=not_found."""
        app, mock_svc = patched_app
        mock_svc.get_import_progress = AsyncMock(return_value=None)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/knowledge/import/status/nonexistent")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_progress_endpoint_also_works(self, patched_app):
        """The original /progress/ path should still work."""
        app, _ = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/knowledge/import/progress/progress_001")
        assert resp.status_code == 200


class TestKnowledgeImportBatch:
    """POST /api/knowledge/import/batch"""

    @pytest.mark.asyncio
    async def test_batch_import_returns_200(self, patched_app):
        app, mock_svc = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/knowledge/import/batch", json={
                "sources": [
                    {"type": "text", "content": "Fact one", "title": "F1"},
                    {"type": "text", "content": "Fact two", "title": "F2"},
                ],
            })
        assert resp.status_code == 200
        body = resp.json()
        assert body["batch_size"] == 2
        assert len(body["import_ids"]) == 2
        assert body["status"] == "queued"
        # Each text source should call import_from_text once
        assert mock_svc.import_from_text.await_count == 2

    @pytest.mark.asyncio
    async def test_batch_import_empty_sources(self, patched_app):
        app, _ = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/knowledge/import/batch", json={"sources": []})
        assert resp.status_code == 200
        body = resp.json()
        assert body["batch_size"] == 0
        assert body["status"] == "completed"

    @pytest.mark.asyncio
    async def test_batch_import_url_type(self, patched_app):
        app, mock_svc = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/api/knowledge/import/batch", json={
                "sources": [
                    {"type": "url", "url": "https://example.com/page"},
                ],
            })
        assert resp.status_code == 200
        body = resp.json()
        assert body["batch_size"] == 1
        mock_svc.import_from_url.assert_awaited_once()


class TestKnowledgeImportCancel:
    """DELETE /api/knowledge/import/cancel/{job_id}"""

    @pytest.mark.asyncio
    async def test_cancel_returns_200(self, patched_app):
        app, mock_svc = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.delete("/api/knowledge/import/cancel/some-job-id")
        assert resp.status_code == 200
        body = resp.json()
        assert body["import_id"] == "some-job-id"
        assert body["status"] == "cancelled"
        mock_svc.cancel_import.assert_awaited_once_with("some-job-id")

    @pytest.mark.asyncio
    async def test_cancel_not_found(self, patched_app):
        app, mock_svc = patched_app
        mock_svc.cancel_import = AsyncMock(return_value=False)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.delete("/api/knowledge/import/cancel/nonexistent")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_delete_endpoint_also_works(self, patched_app):
        """The original DELETE /api/knowledge/import/{id} path should still work."""
        app, mock_svc = patched_app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.delete("/api/knowledge/import/job-42")
        assert resp.status_code == 200
        body = resp.json()
        assert body["import_id"] == "job-42"
