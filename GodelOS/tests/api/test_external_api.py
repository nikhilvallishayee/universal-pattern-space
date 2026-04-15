"""
Tests for the External API (``backend.api.external_api``).

Covers REST endpoints (query, knowledge, status, context) and the WebSocket
``/events`` endpoint, including Bearer-token authentication.
"""

import importlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Direct-import helper: load external_api.py without triggering the heavy
# ``backend.api.__init__`` import chain (which pulls in modules that may
# have pre-existing issues unrelated to the external API).
# ---------------------------------------------------------------------------

_MODULE_PATH = Path(__file__).resolve().parents[2] / "backend" / "api" / "external_api.py"


def _load_module(token: str = ""):
    """(Re-)load external_api with the given token env-var value."""
    env = {**os.environ, "GODELOS_API_TOKEN": token}
    with patch.dict(os.environ, env):
        spec = importlib.util.spec_from_file_location(
            "backend.api.external_api", str(_MODULE_PATH)
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["backend.api.external_api"] = mod
        spec.loader.exec_module(mod)
    return mod


def _make_app(*, token: str = ""):
    """Return a ``(FastAPI, module)`` tuple with the external API router."""
    mod = _load_module(token)
    app = FastAPI()
    app.include_router(mod.router)
    # Wire fallback dependencies (no live GödelOS integration).
    mod.configure(
        godelos_integration=None,
        websocket_manager=None,
        cognitive_state={"processing_load": 0.5, "active_queries": 0},
        startup_time=time.time(),
        tool_based_llm=None,
    )
    return app, mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def unauthenticated_client():
    """Client for an app with authentication *disabled* (no token env var)."""
    app, _mod = _make_app(token="")
    return TestClient(app)


@pytest.fixture()
def unauthenticated_mod():
    """Module reference matching the unauthenticated_client app."""
    _app, mod = _make_app(token="")
    return mod


@pytest.fixture()
def authenticated_client():
    """Client for an app with authentication *enabled*."""
    app, _mod = _make_app(token="test-secret-token")
    return TestClient(app, headers={"Authorization": "Bearer test-secret-token"})


@pytest.fixture()
def bad_token_client():
    """Client that provides the wrong Bearer token."""
    app, _mod = _make_app(token="test-secret-token")
    return TestClient(app, headers={"Authorization": "Bearer wrong-token"})


# ===================================================================
# REST endpoint tests — no authentication
# ===================================================================

class TestQueryEndpoint:
    """POST /api/v1/external/query"""

    def test_basic_query(self, unauthenticated_client):
        resp = unauthenticated_client.post(
            "/api/v1/external/query",
            json={"query": "What is consciousness?"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "response" in body
        assert body["inference_time_ms"] is not None
        assert isinstance(body["inference_time_ms"], (int, float))

    def test_query_with_context(self, unauthenticated_client):
        resp = unauthenticated_client.post(
            "/api/v1/external/query",
            json={"query": "Tell me more", "context": {"topic": "AI"}},
        )
        assert resp.status_code == 200

    def test_query_missing_field(self, unauthenticated_client):
        resp = unauthenticated_client.post(
            "/api/v1/external/query",
            json={},
        )
        assert resp.status_code == 422  # Pydantic validation error

    def test_query_with_godelos_integration(self):
        """Test query when godelos_integration is available."""
        app, mod = _make_app(token="")
        client = TestClient(app)

        mock_integration = MagicMock()
        mock_integration.process_query = AsyncMock(return_value={
            "response": "Consciousness is a complex phenomenon.",
            "confidence": 0.85,
            "reasoning_trace": ["Step 1: Retrieve knowledge", "Step 2: Reason"],
            "sources": ["knowledge_base"],
        })
        mod._godelos_integration = mock_integration

        try:
            resp = client.post(
                "/api/v1/external/query",
                json={"query": "What is consciousness?", "include_reasoning": True},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["response"] == "Consciousness is a complex phenomenon."
            assert body["confidence"] == 0.85
            assert body["reasoning_trace"] is not None
        finally:
            mod._godelos_integration = None


class TestKnowledgeEndpoint:
    """POST /api/v1/external/knowledge"""

    def test_ingest_knowledge(self, unauthenticated_client):
        resp = unauthenticated_client.post(
            "/api/v1/external/knowledge",
            json={"content": "The sky is blue", "knowledge_type": "fact"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["knowledge_id"] is not None

    def test_ingest_knowledge_with_metadata(self, unauthenticated_client):
        resp = unauthenticated_client.post(
            "/api/v1/external/knowledge",
            json={
                "content": "Water boils at 100°C",
                "knowledge_type": "fact",
                "context_id": "SCIENCE",
                "metadata": {"source": "textbook"},
            },
        )
        assert resp.status_code == 200

    def test_ingest_knowledge_missing_content(self, unauthenticated_client):
        resp = unauthenticated_client.post(
            "/api/v1/external/knowledge",
            json={"knowledge_type": "fact"},
        )
        assert resp.status_code == 422


class TestStatusEndpoint:
    """GET /api/v1/external/status"""

    def test_status(self, unauthenticated_client):
        resp = unauthenticated_client.get("/api/v1/external/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["system"] == "GodelOS"
        assert body["status"] == "operational"
        assert "components" in body
        assert "uptime_seconds" in body
        assert "timestamp" in body

    def test_status_components(self, unauthenticated_client):
        resp = unauthenticated_client.get("/api/v1/external/status")
        body = resp.json()
        components = body["components"]
        assert "cognitive_engine" in components
        assert "knowledge_base" in components
        assert "websocket_streaming" in components
        assert "llm_integration" in components


class TestContextEndpoint:
    """GET /api/v1/external/context"""

    def test_context_fallback(self, unauthenticated_client):
        resp = unauthenticated_client.get("/api/v1/external/context")
        assert resp.status_code == 200
        body = resp.json()
        assert "active_context" in body
        assert "timestamp" in body

    def test_context_with_integration(self):
        """Test context when godelos_integration is available."""
        app, mod = _make_app(token="")
        client = TestClient(app)

        mock_integration = MagicMock()
        mock_integration.get_cognitive_state = AsyncMock(return_value={
            "processing_load": 0.7,
            "attention_focus": {"primary": "Testing"},
        })
        mod._godelos_integration = mock_integration

        try:
            resp = client.get("/api/v1/external/context")
            assert resp.status_code == 200
            body = resp.json()
            assert body["active_context"]["processing_load"] == 0.7
        finally:
            mod._godelos_integration = None


# ===================================================================
# Authentication tests
# ===================================================================

class TestAuthentication:
    """Bearer-token authentication across all endpoints."""

    def test_authenticated_query(self, authenticated_client):
        resp = authenticated_client.post(
            "/api/v1/external/query",
            json={"query": "Hello"},
        )
        assert resp.status_code == 200

    def test_bad_token_query(self, bad_token_client):
        resp = bad_token_client.post(
            "/api/v1/external/query",
            json={"query": "Hello"},
        )
        assert resp.status_code == 401

    def test_missing_token_when_required(self):
        """Request without token when auth is enabled should be rejected."""
        app, _mod = _make_app(token="required-token")
        client = TestClient(app)  # no Authorization header
        resp = client.post(
            "/api/v1/external/query",
            json={"query": "Hello"},
        )
        assert resp.status_code == 401

    def test_authenticated_status(self, authenticated_client):
        resp = authenticated_client.get("/api/v1/external/status")
        assert resp.status_code == 200

    def test_bad_token_status(self, bad_token_client):
        resp = bad_token_client.get("/api/v1/external/status")
        assert resp.status_code == 401

    def test_authenticated_context(self, authenticated_client):
        resp = authenticated_client.get("/api/v1/external/context")
        assert resp.status_code == 200

    def test_authenticated_knowledge(self, authenticated_client):
        resp = authenticated_client.post(
            "/api/v1/external/knowledge",
            json={"content": "Test knowledge"},
        )
        assert resp.status_code == 200


# ===================================================================
# WebSocket /events tests
# ===================================================================

class TestEventsWebSocket:
    """WS /api/v1/external/events"""

    def test_websocket_connect_and_initial_state(self, unauthenticated_client):
        with unauthenticated_client.websocket_connect("/api/v1/external/events") as ws:
            msg = json.loads(ws.receive_text())
            assert msg["type"] == "initial_state"
            assert "timestamp" in msg

    def test_websocket_ping_pong(self, unauthenticated_client):
        with unauthenticated_client.websocket_connect("/api/v1/external/events") as ws:
            _ = ws.receive_text()  # initial_state
            ws.send_text(json.dumps({"type": "ping"}))
            msg = json.loads(ws.receive_text())
            assert msg["type"] == "pong"
            assert "timestamp" in msg

    def test_websocket_subscribe(self, unauthenticated_client):
        with unauthenticated_client.websocket_connect("/api/v1/external/events") as ws:
            _ = ws.receive_text()  # initial_state
            ws.send_text(json.dumps({
                "type": "subscribe",
                "event_types": ["consciousness_update", "cognitive_event"],
            }))
            msg = json.loads(ws.receive_text())
            assert msg["type"] == "subscription_confirmed"
            assert "consciousness_update" in msg["event_types"]

    def test_websocket_request_state(self, unauthenticated_client):
        with unauthenticated_client.websocket_connect("/api/v1/external/events") as ws:
            _ = ws.receive_text()  # initial_state
            ws.send_text(json.dumps({"type": "request_state"}))
            msg = json.loads(ws.receive_text())
            assert msg["type"] == "state_update"
            assert "data" in msg

    def test_websocket_invalid_json(self, unauthenticated_client):
        with unauthenticated_client.websocket_connect("/api/v1/external/events") as ws:
            _ = ws.receive_text()  # initial_state
            ws.send_text("not-json{{{")
            msg = json.loads(ws.receive_text())
            assert msg["type"] == "error"

    def test_websocket_auth_required(self):
        """WebSocket should reject connection when token is required but missing."""
        app, _mod = _make_app(token="ws-secret")
        client = TestClient(app)
        # No token query param → should close immediately.
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/external/events") as ws:
                ws.receive_text()

    def test_websocket_auth_valid_token(self):
        """WebSocket should accept connection with correct token query param."""
        app, _mod = _make_app(token="ws-secret")
        client = TestClient(app)
        with client.websocket_connect("/api/v1/external/events?token=ws-secret") as ws:
            msg = json.loads(ws.receive_text())
            assert msg["type"] == "initial_state"


# ===================================================================
# OpenAPI schema presence test
# ===================================================================

class TestOpenAPISpec:
    """Verify the external endpoints appear in the auto-generated OpenAPI schema."""

    def test_openapi_includes_external_endpoints(self, unauthenticated_client):
        resp = unauthenticated_client.get("/openapi.json")
        assert resp.status_code == 200
        spec = resp.json()
        paths = spec.get("paths", {})
        assert "/api/v1/external/query" in paths
        assert "/api/v1/external/knowledge" in paths
        assert "/api/v1/external/status" in paths
        assert "/api/v1/external/context" in paths
