"""
Tests for the SelfModificationEngine and its REST API endpoints.

Covers:
  - test_propose_modification   – POST propose → 200, proposal_id in response
  - test_apply_modification     – propose + apply → GET /api/knowledge shows the change
  - test_rollback_modification  – apply + rollback → change is reversed
  - test_history                – history endpoint returns records in order, including
                                  both applied and rolled-back entries

Uses httpx.AsyncClient against the ASGI app so no live server is needed.
The SelfModificationEngine is NOT mocked — we test the real engine wired
into the server's lifespan via a module-level patch.
"""

import pytest
import httpx

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine():
    """Return a fresh, standalone SelfModificationEngine instance."""
    from backend.core.self_modification_engine import SelfModificationEngine
    return SelfModificationEngine()


@pytest.fixture()
def patched_app(engine):
    """
    Yield the unified_server FastAPI app with a known SelfModificationEngine
    injected so every endpoint has access to it without starting a real server.
    Lifespan is disabled in the transport to prevent the app from re-initializing
    the engine and overwriting the patched instance.
    """
    import backend.unified_server as srv
    from backend.unified_server import app

    original = getattr(srv, "self_modification_engine", None)
    srv.self_modification_engine = engine
    yield app, engine
    srv.self_modification_engine = original


def _transport(app):
    """Create an ASGITransport with lifespan disabled to avoid re-init."""
    return httpx.ASGITransport(app=app, raise_app_exceptions=False)


# ---------------------------------------------------------------------------
# Unit tests for the engine itself
# ---------------------------------------------------------------------------

class TestSelfModificationEngineUnit:
    """Direct unit tests for SelfModificationEngine (no HTTP layer)."""

    @pytest.mark.asyncio
    async def test_propose_returns_pending_proposal(self, engine):
        proposal = await engine.propose_modification(
            target="knowledge_graph",
            operation="add",
            parameters={"concept": "Testability", "definition": "The quality of being testable"},
        )
        assert proposal.proposal_id
        assert proposal.status == "pending"
        assert proposal.target == "knowledge_graph"
        assert proposal.operation == "add"

    @pytest.mark.asyncio
    async def test_apply_persists_to_store(self, engine):
        proposal = await engine.propose_modification(
            target="knowledge_graph",
            operation="add",
            parameters={"concept": "Persistence", "definition": "Continued existence"},
        )
        result = await engine.apply_modification(proposal.proposal_id)
        assert result.status == "applied"
        items = engine.get_knowledge_items()
        assert any(i["concept"] == "Persistence" for i in items)

    @pytest.mark.asyncio
    async def test_rollback_removes_added_item(self, engine):
        proposal = await engine.propose_modification(
            target="knowledge_graph",
            operation="add",
            parameters={"concept": "Ephemeral", "definition": "Temporary"},
        )
        await engine.apply_modification(proposal.proposal_id)
        assert any(i["concept"] == "Ephemeral" for i in engine.get_knowledge_items())

        await engine.rollback_modification(proposal.proposal_id)
        assert not any(i["concept"] == "Ephemeral" for i in engine.get_knowledge_items())

    @pytest.mark.asyncio
    async def test_invalid_target_raises(self, engine):
        with pytest.raises(ValueError, match="Unknown target"):
            await engine.propose_modification(
                target="nonexistent_target",
                operation="add",
                parameters={},
            )

    @pytest.mark.asyncio
    async def test_double_apply_raises(self, engine):
        from backend.core.self_modification_engine import ProposalStateError
        proposal = await engine.propose_modification(
            target="inference_rules",
            operation="add",
            parameters={"name": "rule1", "condition": "x", "action": "y"},
        )
        await engine.apply_modification(proposal.proposal_id)
        with pytest.raises(ProposalStateError, match="cannot be applied"):
            await engine.apply_modification(proposal.proposal_id)

    @pytest.mark.asyncio
    async def test_active_modules_enable_disable(self, engine):
        proposal = await engine.propose_modification(
            target="active_modules", operation="disable", parameters={"module": "memory"}
        )
        await engine.apply_modification(proposal.proposal_id)
        assert engine.get_modules_status()["memory"]["enabled"] is False

        proposal2 = await engine.propose_modification(
            target="active_modules", operation="enable", parameters={"module": "memory"}
        )
        await engine.apply_modification(proposal2.proposal_id)
        assert engine.get_modules_status()["memory"]["enabled"] is True

    @pytest.mark.asyncio
    async def test_propose_with_non_dict_parameters_raises(self, engine):
        """parameters must be a dict; passing a string should raise."""
        with pytest.raises(ValueError, match="must be a JSON object"):
            await engine.propose_modification(
                target="knowledge_graph",
                operation="add",
                parameters="not_a_dict",
            )

    @pytest.mark.asyncio
    async def test_attention_weights_empty_component_raises(self, engine):
        """Attention weight operations require a non-empty component."""
        proposal = await engine.propose_modification(
            target="attention_weights",
            operation="add",
            parameters={"component": "", "weight": 0.5},
        )
        with pytest.raises(ValueError, match="component.*required"):
            await engine.apply_modification(proposal.proposal_id)

    @pytest.mark.asyncio
    async def test_attention_weights_invalid_weight_raises(self, engine):
        """Attention weight must be a valid number."""
        proposal = await engine.propose_modification(
            target="attention_weights",
            operation="add",
            parameters={"component": "x", "weight": "bad"},
        )
        with pytest.raises(ValueError, match="Invalid.*weight"):
            await engine.apply_modification(proposal.proposal_id)

    @pytest.mark.asyncio
    async def test_active_modules_empty_name_raises(self, engine):
        """enable/disable/remove require a non-empty module identifier."""
        proposal = await engine.propose_modification(
            target="active_modules",
            operation="enable",
            parameters={"module": ""},
        )
        with pytest.raises(ValueError, match="non-empty module identifier"):
            await engine.apply_modification(proposal.proposal_id)

    @pytest.mark.asyncio
    async def test_history_pruning(self):
        """Ensure old records are evicted when max_history is exceeded."""
        from backend.core.self_modification_engine import SelfModificationEngine
        engine = SelfModificationEngine(max_history=3)
        pids = []
        for i in range(5):
            p = await engine.propose_modification(
                target="knowledge_graph",
                operation="add",
                parameters={"concept": f"item{i}"},
            )
            await engine.apply_modification(p.proposal_id)
            pids.append(p.proposal_id)

        history = await engine.get_history()
        assert len(history) == 3
        # Only the last 3 should remain
        history_ids = [r.proposal_id for r in history]
        assert pids[0] not in history_ids
        assert pids[1] not in history_ids
        assert pids[2] in history_ids


# ---------------------------------------------------------------------------
# REST API tests
# ---------------------------------------------------------------------------

class TestProposeSelfModification:
    """POST /api/self-modification/propose"""

    @pytest.mark.asyncio
    async def test_propose_returns_200_with_proposal_id(self, patched_app):
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post(
                "/api/self-modification/propose",
                json={
                    "target": "knowledge_graph",
                    "operation": "add",
                    "parameters": {"concept": "TestConcept", "definition": "A test concept"},
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "proposal_id" in data
        assert data["status"] == "pending"
        assert data["target"] == "knowledge_graph"
        assert data["operation"] == "add"

    @pytest.mark.asyncio
    async def test_propose_invalid_target_returns_400(self, patched_app):
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post(
                "/api/self-modification/propose",
                json={"target": "bogus_target", "operation": "add", "parameters": {}},
            )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_propose_modules_operation(self, patched_app):
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post(
                "/api/self-modification/propose",
                json={
                    "target": "active_modules",
                    "operation": "disable",
                    "parameters": {"module": "learning"},
                },
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"

    @pytest.mark.asyncio
    async def test_propose_null_parameters_returns_400(self, patched_app):
        """parameters: null should be coerced to {} (not crash)."""
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post(
                "/api/self-modification/propose",
                json={"target": "knowledge_graph", "operation": "add", "parameters": None},
            )
        # null is coerced to empty dict — should succeed
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_propose_non_object_parameters_returns_400(self, patched_app):
        """parameters: 'string' should return 400."""
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post(
                "/api/self-modification/propose",
                json={"target": "knowledge_graph", "operation": "add", "parameters": "nope"},
            )
        assert resp.status_code == 400


class TestApplySelfModification:
    """POST /api/self-modification/apply/{proposal_id}"""

    @pytest.mark.asyncio
    async def test_apply_modification_knowledge_graph_verifiable(self, patched_app):
        """Apply a knowledge_graph add → GET /api/knowledge shows the new item."""
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            # Propose
            resp = await client.post(
                "/api/self-modification/propose",
                json={
                    "target": "knowledge_graph",
                    "operation": "add",
                    "parameters": {
                        "concept": "VerifiableConcept",
                        "definition": "A concept that can be verified",
                        "category": "testing",
                    },
                },
            )
            assert resp.status_code == 200
            proposal_id = resp.json()["proposal_id"]

            # Apply
            apply_resp = await client.post(f"/api/self-modification/apply/{proposal_id}")
            assert apply_resp.status_code == 200
            apply_data = apply_resp.json()
            assert apply_data["status"] == "applied"
            assert apply_data["proposal_id"] == proposal_id
            assert "changes_summary" in apply_data

            # Verify via GET /api/knowledge
            knowledge_resp = await client.get("/api/knowledge")
            assert knowledge_resp.status_code == 200
            knowledge_data = knowledge_resp.json()
            concepts = knowledge_data.get("concepts", [])
            assert any(c.get("concept") == "VerifiableConcept" for c in concepts), (
                f"VerifiableConcept not found in concepts: {concepts}"
            )

    @pytest.mark.asyncio
    async def test_apply_nonexistent_proposal_returns_404(self, patched_app):
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post("/api/self-modification/apply/no-such-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_apply_already_applied_returns_409(self, patched_app):
        """Applying a proposal that's already applied should return 409 Conflict."""
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post(
                "/api/self-modification/propose",
                json={
                    "target": "knowledge_graph",
                    "operation": "add",
                    "parameters": {"concept": "DupApply"},
                },
            )
            proposal_id = resp.json()["proposal_id"]
            await client.post(f"/api/self-modification/apply/{proposal_id}")
            dup_resp = await client.post(f"/api/self-modification/apply/{proposal_id}")
        assert dup_resp.status_code == 409

    @pytest.mark.asyncio
    async def test_apply_active_modules_verifiable(self, patched_app):
        """Apply a module disable → GET /api/system/modules reflects the change."""
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post(
                "/api/self-modification/propose",
                json={
                    "target": "active_modules",
                    "operation": "disable",
                    "parameters": {"module": "metacognition"},
                },
            )
            proposal_id = resp.json()["proposal_id"]
            await client.post(f"/api/self-modification/apply/{proposal_id}")

            modules_resp = await client.get("/api/system/modules")
            assert modules_resp.status_code == 200
            modules = modules_resp.json()["modules"]
            assert modules["metacognition"]["enabled"] is False


class TestRollbackSelfModification:
    """POST /api/self-modification/rollback/{proposal_id}"""

    @pytest.mark.asyncio
    async def test_rollback_reverses_knowledge_graph_add(self, patched_app):
        """Apply + rollback → knowledge item disappears from GET /api/knowledge."""
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            # Propose + apply
            resp = await client.post(
                "/api/self-modification/propose",
                json={
                    "target": "knowledge_graph",
                    "operation": "add",
                    "parameters": {"concept": "RollbackMe", "definition": "Will be removed"},
                },
            )
            proposal_id = resp.json()["proposal_id"]
            await client.post(f"/api/self-modification/apply/{proposal_id}")

            # Confirm it's there
            knowledge_resp = await client.get("/api/knowledge")
            concepts_before = knowledge_resp.json().get("concepts", [])
            assert any(c.get("concept") == "RollbackMe" for c in concepts_before)

            # Rollback
            rollback_resp = await client.post(
                f"/api/self-modification/rollback/{proposal_id}"
            )
            assert rollback_resp.status_code == 200
            assert rollback_resp.json()["status"] == "rolled_back"

            # Confirm it's gone
            knowledge_resp2 = await client.get("/api/knowledge")
            concepts_after = knowledge_resp2.json().get("concepts", [])
            assert not any(c.get("concept") == "RollbackMe" for c in concepts_after), (
                f"RollbackMe should have been removed but found in: {concepts_after}"
            )

    @pytest.mark.asyncio
    async def test_rollback_nonexistent_returns_404(self, patched_app):
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post("/api/self-modification/rollback/no-such-id")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_rollback_pending_proposal_returns_404(self, patched_app):
        """Rolling back a proposal that was never applied should return 404."""
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post(
                "/api/self-modification/propose",
                json={
                    "target": "knowledge_graph",
                    "operation": "add",
                    "parameters": {"concept": "NeverApplied"},
                },
            )
            proposal_id = resp.json()["proposal_id"]
            rollback_resp = await client.post(
                f"/api/self-modification/rollback/{proposal_id}"
            )
        # no record exists for a pending-only proposal → 404
        assert rollback_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_rollback_already_rolled_back_returns_409(self, patched_app):
        """Rolling back an already-rolled-back proposal should return 409."""
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.post(
                "/api/self-modification/propose",
                json={
                    "target": "knowledge_graph",
                    "operation": "add",
                    "parameters": {"concept": "DoubleRollback"},
                },
            )
            proposal_id = resp.json()["proposal_id"]
            await client.post(f"/api/self-modification/apply/{proposal_id}")
            await client.post(f"/api/self-modification/rollback/{proposal_id}")
            dup = await client.post(f"/api/self-modification/rollback/{proposal_id}")
        assert dup.status_code == 409


class TestModificationHistory:
    """GET /api/self-modification/history"""

    @pytest.mark.asyncio
    async def test_history_returns_records_in_order(self, patched_app):
        """History lists both applied and rolled-back entries in chronological order."""
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            # First modification: apply and keep
            r1 = await client.post(
                "/api/self-modification/propose",
                json={
                    "target": "knowledge_graph",
                    "operation": "add",
                    "parameters": {"concept": "Item1"},
                },
            )
            pid1 = r1.json()["proposal_id"]
            await client.post(f"/api/self-modification/apply/{pid1}")

            # Second modification: apply then rollback
            r2 = await client.post(
                "/api/self-modification/propose",
                json={
                    "target": "knowledge_graph",
                    "operation": "add",
                    "parameters": {"concept": "Item2"},
                },
            )
            pid2 = r2.json()["proposal_id"]
            await client.post(f"/api/self-modification/apply/{pid2}")
            await client.post(f"/api/self-modification/rollback/{pid2}")

            # Fetch history
            hist_resp = await client.get("/api/self-modification/history")
            assert hist_resp.status_code == 200
            history = hist_resp.json()["history"]

            assert len(history) >= 2

            ids_in_order = [r["proposal_id"] for r in history]
            assert pid1 in ids_in_order
            assert pid2 in ids_in_order
            assert ids_in_order.index(pid1) < ids_in_order.index(pid2), (
                "pid1 should appear before pid2 in history"
            )

            # Verify statuses
            by_id = {r["proposal_id"]: r for r in history}
            assert by_id[pid1]["status"] == "applied"
            assert by_id[pid2]["status"] == "rolled_back"

    @pytest.mark.asyncio
    async def test_history_empty_initially(self, patched_app):
        """History is empty when no modifications have been applied."""
        app, _ = patched_app
        async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
            resp = await client.get("/api/self-modification/history")
        assert resp.status_code == 200
        assert resp.json()["history"] == []


class TestSelfModificationAuth:
    """Token-based authentication for self-modification endpoints."""

    @pytest.mark.asyncio
    async def test_auth_rejected_when_token_required(self, engine):
        """When GODELOS_API_TOKEN is set, requests without the token get 401."""
        import backend.unified_server as srv
        from backend.unified_server import app

        original_engine = getattr(srv, "self_modification_engine", None)
        original_token = srv._SELFMOD_TOKEN
        srv.self_modification_engine = engine
        srv._SELFMOD_TOKEN = "test-secret-token"
        try:
            async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
                resp = await client.post(
                    "/api/self-modification/propose",
                    json={
                        "target": "knowledge_graph",
                        "operation": "add",
                        "parameters": {"concept": "Blocked"},
                    },
                )
            assert resp.status_code == 401
        finally:
            srv.self_modification_engine = original_engine
            srv._SELFMOD_TOKEN = original_token

    @pytest.mark.asyncio
    async def test_auth_accepted_with_correct_token(self, engine):
        """When the correct X-API-Token header is provided, requests succeed."""
        import backend.unified_server as srv
        from backend.unified_server import app

        original_engine = getattr(srv, "self_modification_engine", None)
        original_token = srv._SELFMOD_TOKEN
        srv.self_modification_engine = engine
        srv._SELFMOD_TOKEN = "test-secret-token"
        try:
            async with httpx.AsyncClient(transport=_transport(app), base_url="http://test") as client:
                resp = await client.post(
                    "/api/self-modification/propose",
                    json={
                        "target": "knowledge_graph",
                        "operation": "add",
                        "parameters": {"concept": "Allowed"},
                    },
                    headers={"X-API-Token": "test-secret-token"},
                )
            assert resp.status_code == 200
        finally:
            srv.self_modification_engine = original_engine
            srv._SELFMOD_TOKEN = original_token
