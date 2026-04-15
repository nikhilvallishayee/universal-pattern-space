"""
Integration tests for dormant module activation (Issue #76).

Tests cover:
  - GET /api/system/dormant-modules returns the correct schema for all 8 modules
  - DormantModuleManager initializes and ticks without errors
  - WebSocket broadcast is attempted on each tick
  - The manager correctly reports active/inactive status from CognitivePipeline
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.dormant_module_manager import (
    DORMANT_MODULE_NAMES,
    DormantModuleManager,
    ModuleRecord,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_pipeline(active_names: Optional[List[str]] = None):
    """Build a minimal CognitivePipeline mock.

    If *active_names* is None all 8 modules are considered active.
    """
    if active_names is None:
        active_names = list(DORMANT_MODULE_NAMES)

    statuses = {
        name: {"status": "active" if name in active_names else "error", "error": None}
        for name in DORMANT_MODULE_NAMES
    }

    instances: Dict[str, Any] = {}
    for name in active_names:
        inst = MagicMock()
        # Configure lightweight tick-method return values
        inst.learn_groundings_from_buffer.return_value = None
        inst.process_perceptual_input.return_value = set()
        inst.tick.return_value = None
        inst.capabilities = {"modal_logic": True}
        inst.get_state_features.return_value = [0.0] * 8
        inst.grounding_links = {}
        inst.experience_buffer = []
        inst.solver_registry = {}
        inst.action_space = []
        inst.exploration_rate = 0.1
        world_state = MagicMock()
        world_state.time = 0.0
        world_state.objects = {}
        world_state.agents = {}
        inst.world_state = world_state
        object_tracker = MagicMock()
        object_tracker.tracked_objects = {}
        inst.object_tracker = object_tracker
        instances[name] = inst

    pipeline = MagicMock()
    pipeline.get_subsystem_status.return_value = statuses
    pipeline.get_instance.side_effect = lambda name: instances.get(name)
    return pipeline


def _make_mock_integration(active_names: Optional[List[str]] = None):
    integration = MagicMock()
    integration.cognitive_pipeline = _make_mock_pipeline(active_names)
    return integration


def _make_mock_ws_manager():
    ws = MagicMock()
    ws.broadcast_cognitive_update = AsyncMock(return_value=None)
    ws.broadcast = AsyncMock(return_value=None)
    return ws


# ---------------------------------------------------------------------------
# Unit tests — DormantModuleManager
# ---------------------------------------------------------------------------

class TestDormantModuleManagerInit:
    def test_all_modules_active_when_pipeline_has_all(self):
        mgr = DormantModuleManager()
        integration = _make_mock_integration()
        mgr.initialize(integration)
        status = mgr.get_module_status()
        assert len(status) == len(DORMANT_MODULE_NAMES)
        active = [s for s in status if s["active"]]
        assert len(active) == len(DORMANT_MODULE_NAMES)

    def test_inactive_when_no_pipeline(self):
        mgr = DormantModuleManager()
        integration = MagicMock()
        integration.cognitive_pipeline = None
        mgr.initialize(integration)
        status = mgr.get_module_status()
        assert all(not s["active"] for s in status)

    def test_partial_activation(self):
        active = ["symbol_grounding_associator", "ilp_engine"]
        mgr = DormantModuleManager()
        mgr.initialize(_make_mock_integration(active))
        status = {s["module_name"]: s for s in mgr.get_module_status()}
        assert status["symbol_grounding_associator"]["active"] is True
        assert status["ilp_engine"]["active"] is True
        assert status["modal_tableau_prover"]["active"] is False

    def test_correct_module_names_returned(self):
        mgr = DormantModuleManager()
        mgr.initialize(_make_mock_integration())
        names = [s["module_name"] for s in mgr.get_module_status()]
        assert set(names) == set(DORMANT_MODULE_NAMES)


class TestDormantModuleManagerTick:
    @pytest.mark.asyncio
    async def test_tick_updates_last_tick(self):
        mgr = DormantModuleManager()
        mgr.initialize(_make_mock_integration())
        assert all(r.last_tick is None for r in mgr._records.values())
        await mgr.tick()
        active_records = [r for r in mgr._records.values() if r.active]
        assert all(r.last_tick is not None for r in active_records)

    @pytest.mark.asyncio
    async def test_tick_increments_tick_count(self):
        mgr = DormantModuleManager()
        mgr.initialize(_make_mock_integration())
        await mgr.tick()
        for r in mgr._records.values():
            if r.active:
                assert r.tick_count == 1
        await mgr.tick()
        for r in mgr._records.values():
            if r.active:
                assert r.tick_count == 2

    @pytest.mark.asyncio
    async def test_tick_broadcasts_websocket_event(self):
        ws = _make_mock_ws_manager()
        mgr = DormantModuleManager()
        mgr.initialize(_make_mock_integration(), ws)
        await mgr.tick()
        # broadcast_cognitive_update should have been called once
        ws.broadcast_cognitive_update.assert_awaited_once()
        call_args = ws.broadcast_cognitive_update.call_args[0][0]
        assert call_args["type"] == "module_state_update"
        assert "modules" in call_args
        assert len(call_args["modules"]) == len(DORMANT_MODULE_NAMES)

    @pytest.mark.asyncio
    async def test_tick_returns_all_module_states(self):
        mgr = DormantModuleManager()
        mgr.initialize(_make_mock_integration())
        results = await mgr.tick()
        assert len(results) == len(DORMANT_MODULE_NAMES)
        for item in results:
            assert "module_name" in item
            assert "active" in item
            assert "last_tick" in item

    @pytest.mark.asyncio
    async def test_tick_does_not_raise_on_uninitialized_manager(self):
        mgr = DormantModuleManager()
        # Not initialized
        results = await mgr.tick()
        assert results == []

    @pytest.mark.asyncio
    async def test_tick_is_resilient_to_module_errors(self):
        """A module whose tick handler throws should not abort the overall tick."""
        mgr = DormantModuleManager()
        integration = _make_mock_integration()
        bad_instance = MagicMock()
        bad_instance.learn_groundings_from_buffer.side_effect = RuntimeError("boom")
        bad_instance.grounding_links = {}
        bad_instance.experience_buffer = []
        integration.cognitive_pipeline.get_instance.side_effect = (
            lambda name: bad_instance if name == "symbol_grounding_associator"
            else _make_mock_pipeline().get_instance(name)
        )
        mgr.initialize(integration)
        # Should not raise
        results = await mgr.tick()
        assert len(results) == len(DORMANT_MODULE_NAMES)


class TestModuleRecord:
    def test_as_dict_structure(self):
        record = ModuleRecord("ilp_engine")
        d = record.as_dict()
        assert d["module_name"] == "ilp_engine"
        assert d["active"] is False
        assert d["last_tick"] is None
        assert d["tick_count"] == 0
        assert d["last_output"] is None
        assert d["error"] is None

    def test_as_dict_with_last_tick(self):
        record = ModuleRecord("modal_tableau_prover")
        record.active = True
        record.last_tick = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        d = record.as_dict()
        assert d["last_tick"] == "2024-01-01T12:00:00+00:00"


# ---------------------------------------------------------------------------
# REST endpoint tests — GET /api/system/dormant-modules
# ---------------------------------------------------------------------------

class TestModulesEndpoint:
    """Tests for GET /api/system/dormant-modules using TestClient."""

    def setup_method(self):
        """Import app and patch global dormant_module_manager."""
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

    def _get_test_client(self, mock_mgr):
        """Return a FastAPI TestClient with dormant_module_manager patched."""
        from fastapi.testclient import TestClient
        import backend.unified_server as us
        us.dormant_module_manager = mock_mgr
        return TestClient(us.app)

    def _make_active_manager(self):
        mgr = DormantModuleManager()
        mgr.initialize(_make_mock_integration())
        return mgr

    def test_returns_200(self):
        from fastapi.testclient import TestClient
        import backend.unified_server as us
        original = us.dormant_module_manager
        try:
            us.dormant_module_manager = self._make_active_manager()
            client = TestClient(us.app)
            response = client.get("/api/system/dormant-modules")
            assert response.status_code == 200
        finally:
            us.dormant_module_manager = original

    def test_response_has_modules_list(self):
        from fastapi.testclient import TestClient
        import backend.unified_server as us
        original = us.dormant_module_manager
        try:
            us.dormant_module_manager = self._make_active_manager()
            client = TestClient(us.app)
            data = client.get("/api/system/dormant-modules").json()
            assert "modules" in data
            assert isinstance(data["modules"], list)
        finally:
            us.dormant_module_manager = original

    def test_all_eight_modules_present(self):
        from fastapi.testclient import TestClient
        import backend.unified_server as us
        original = us.dormant_module_manager
        try:
            us.dormant_module_manager = self._make_active_manager()
            client = TestClient(us.app)
            data = client.get("/api/system/dormant-modules").json()
            names = {m["module_name"] for m in data["modules"]}
            assert names == set(DORMANT_MODULE_NAMES)
        finally:
            us.dormant_module_manager = original

    def test_active_true_when_manager_active(self):
        from fastapi.testclient import TestClient
        import backend.unified_server as us
        original = us.dormant_module_manager
        try:
            us.dormant_module_manager = self._make_active_manager()
            client = TestClient(us.app)
            data = client.get("/api/system/dormant-modules").json()
            for m in data["modules"]:
                assert m["active"] is True, f"Module {m['module_name']} not active"
        finally:
            us.dormant_module_manager = original

    def test_schema_fields_present(self):
        from fastapi.testclient import TestClient
        import backend.unified_server as us
        original = us.dormant_module_manager
        try:
            us.dormant_module_manager = self._make_active_manager()
            client = TestClient(us.app)
            data = client.get("/api/system/dormant-modules").json()
            required_fields = {"module_name", "active", "last_tick", "tick_count", "last_output", "error"}
            for m in data["modules"]:
                assert required_fields.issubset(set(m.keys())), (
                    f"Module {m.get('module_name')} missing fields: "
                    f"{required_fields - set(m.keys())}"
                )
        finally:
            us.dormant_module_manager = original

    def test_fallback_when_manager_none(self):
        from fastapi.testclient import TestClient
        import backend.unified_server as us
        original_mgr = us.dormant_module_manager
        original_gi = us.godelos_integration
        try:
            us.dormant_module_manager = None
            us.godelos_integration = None
            client = TestClient(us.app)
            response = client.get("/api/system/dormant-modules")
            assert response.status_code == 200
            data = response.json()
            assert "modules" in data
            assert len(data["modules"]) == len(DORMANT_MODULE_NAMES)
        finally:
            us.dormant_module_manager = original_mgr
            us.godelos_integration = original_gi


# ---------------------------------------------------------------------------
# Active-after-tick test
# ---------------------------------------------------------------------------

class TestActiveAfterTick:
    """Assert active:true AND at least one WS event emitted within a tick cycle."""

    @pytest.mark.asyncio
    async def test_all_modules_active_and_ws_event_emitted(self):
        ws = _make_mock_ws_manager()
        mgr = DormantModuleManager()
        mgr.initialize(_make_mock_integration(), ws)

        # Tick once
        results = await mgr.tick()

        # All modules report active:true
        for r in results:
            assert r["active"] is True, f"Module {r['module_name']} not active after tick"

        # At least one WS broadcast was emitted
        ws.broadcast_cognitive_update.assert_awaited()

        # The WS event contains module state data
        ws_payload = ws.broadcast_cognitive_update.call_args[0][0]
        assert ws_payload["type"] == "module_state_update"
        active_in_event = [m for m in ws_payload["modules"] if m["active"]]
        assert len(active_in_event) == len(DORMANT_MODULE_NAMES)

    @pytest.mark.asyncio
    async def test_last_tick_is_set_after_tick(self):
        mgr = DormantModuleManager()
        mgr.initialize(_make_mock_integration())
        await mgr.tick()
        for r in mgr._records.values():
            if r.active:
                assert r.last_tick is not None
                # Should be a recent timestamp
                diff = (datetime.now(tz=timezone.utc) - r.last_tick).total_seconds()
                assert diff < 5.0


# ---------------------------------------------------------------------------
# Individual module tick handler tests
# ---------------------------------------------------------------------------

class TestModuleTickHandlers:
    """Verify that each individual tick handler returns a dict."""

    def setup_method(self):
        self.mgr = DormantModuleManager()

    def _mock_sga(self):
        inst = MagicMock()
        inst.learn_groundings_from_buffer.return_value = None
        inst.grounding_links = {"visual": [1, 2]}
        inst.experience_buffer = [1, 2, 3]
        return inst

    def test_symbol_grounding_associator_handler(self):
        result = self.mgr._tick_symbol_grounding_associator(self._mock_sga())
        assert "grounding_link_count" in result
        assert result["experience_buffer_size"] == 3

    def test_perceptual_categorizer_handler(self):
        inst = MagicMock()
        inst.process_perceptual_input.return_value = set()
        ot = MagicMock()
        ot.tracked_objects = {"a": 1, "b": 2}
        inst.object_tracker = ot
        result = self.mgr._tick_perceptual_categorizer(inst)
        assert result["object_tracker_count"] == 2

    def test_simulated_environment_handler(self):
        inst = MagicMock()
        ws = MagicMock()
        ws.time = 1.5
        ws.objects = {"o1": 1}
        ws.agents = {}
        inst.world_state = ws
        result = self.mgr._tick_simulated_environment(inst)
        assert result["world_time"] == 1.5
        assert result["object_count"] == 1

    def test_ilp_engine_handler(self):
        inst = MagicMock()
        bias = MagicMock()
        bias.max_clause_length = 5
        inst.language_bias = bias
        result = self.mgr._tick_ilp_engine(inst)
        assert result["ready"] is True
        assert result["max_clause_length"] == 5

    def test_modal_tableau_prover_handler(self):
        inst = MagicMock()
        inst.capabilities = {"modal_logic": True}
        result = self.mgr._tick_modal_tableau_prover(inst)
        assert result["ready"] is True

    def test_clp_module_handler(self):
        inst = MagicMock()
        inst.capabilities = {"constraint_solving": True}
        inst.solver_registry = {"fd": 1}
        result = self.mgr._tick_clp_module(inst)
        assert result["solver_count"] == 1
        assert result["ready"] is True

    def test_explanation_based_learner_handler(self):
        inst = MagicMock()
        config = MagicMock()
        config.max_unfolding_depth = 3
        inst.config = config
        result = self.mgr._tick_explanation_based_learner(inst)
        assert result["ready"] is True
        assert result["max_unfolding_depth"] == 3

    def test_meta_control_rl_handler(self):
        inst = MagicMock()
        inst.get_state_features.return_value = [0.1, 0.2, 0.3]
        inst.action_space = ["a", "b"]
        inst.exploration_rate = 0.05
        result = self.mgr._tick_meta_control_rl(inst)
        assert result["state_dim"] == 3
        assert result["action_space_size"] == 2
        assert result["exploration_rate"] == 0.05
        assert result["ready"] is True
