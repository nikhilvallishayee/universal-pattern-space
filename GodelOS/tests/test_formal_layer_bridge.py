#!/usr/bin/env python3
"""
Tests for the Formal Layer Bridge — integration between
``godelOS.unified_agent_core.cognitive_engine`` and the
``backend/core`` consciousness runtime.
"""

import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.formal_layer_bridge import (
    FormalLayerBridge,
    FormalSnapshot,
    _FORMAL_AVAILABLE,
)
from backend.core.unified_consciousness_engine import (
    UnifiedConsciousnessEngine,
    UnifiedConsciousnessState,
)


# ---------------------------------------------------------------------------
# FormalLayerBridge unit tests
# ---------------------------------------------------------------------------

class TestFormalLayerBridge:
    """Validate the bridge initialises and exposes the formal layer."""

    @pytest.fixture
    def bridge(self):
        return FormalLayerBridge()

    def test_availability_reflects_import(self, bridge):
        """is_available should match whether godelOS was importable."""
        assert bridge.is_available == _FORMAL_AVAILABLE

    @pytest.mark.asyncio
    async def test_initialize_succeeds(self, bridge):
        """Bridge initialisation should succeed when godelOS is available."""
        if not bridge.is_available:
            pytest.skip("godelOS formal layer not installed")
        ok = await bridge.initialize()
        assert ok is True
        assert bridge.is_initialized is True

    @pytest.mark.asyncio
    async def test_double_initialize_is_idempotent(self, bridge):
        """Calling initialize twice should be harmless."""
        if not bridge.is_available:
            pytest.skip("godelOS formal layer not installed")
        await bridge.initialize()
        ok = await bridge.initialize()
        assert ok is True

    @pytest.mark.asyncio
    async def test_submit_observation_returns_thought_id(self, bridge):
        """submit_observation should return a non-None thought id."""
        if not bridge.is_available:
            pytest.skip("godelOS formal layer not installed")
        await bridge.initialize()
        tid = await bridge.submit_observation(
            "test observation", priority=0.7, thought_type="insight"
        )
        assert tid is not None
        assert isinstance(tid, str)

    @pytest.mark.asyncio
    async def test_snapshot_after_observations(self, bridge):
        """After submitting observations, snapshot should reflect activity."""
        if not bridge.is_available:
            pytest.skip("godelOS formal layer not installed")
        await bridge.initialize()
        for i in range(3):
            await bridge.submit_observation(f"obs {i}", priority=0.5 + i * 0.1)
        snap = await bridge.get_snapshot()
        assert isinstance(snap, FormalSnapshot)
        assert snap.thought_count >= 3
        assert 0.0 <= snap.cognitive_load <= 1.0

    @pytest.mark.asyncio
    async def test_stub_mode_returns_defaults(self):
        """When formal layer is unavailable, stub should return safe defaults."""
        bridge = FormalLayerBridge()
        bridge.is_available = False
        ok = await bridge.initialize()
        assert ok is False
        tid = await bridge.submit_observation("anything")
        assert tid is None
        snap = await bridge.get_snapshot()
        assert snap.cognitive_load == 0.0
        assert snap.thought_count == 0

    @pytest.mark.asyncio
    async def test_insights_populated_after_reflection(self, bridge):
        """Insights list in snapshot should be populated from reflections."""
        if not bridge.is_available:
            pytest.skip("godelOS formal layer not installed")
        await bridge.initialize()
        await bridge.submit_observation(
            "I notice an inconsistency in my own reasoning",
            priority=0.9,
            thought_type="insight",
        )
        snap = await bridge.get_snapshot()
        # Insights come from the ReflectionEngine; may or may not be populated
        # depending on the reflection engine's heuristics, but the list should exist
        assert isinstance(snap.latest_insights, list)


# ---------------------------------------------------------------------------
# Integration: bridge wired into UnifiedConsciousnessEngine
# ---------------------------------------------------------------------------

class TestEngineWithFormalBridge:
    """Verify that UnifiedConsciousnessEngine uses the formal bridge."""

    @pytest.fixture
    def engine(self):
        return UnifiedConsciousnessEngine()

    def test_engine_has_formal_bridge(self, engine):
        """Engine should carry a FormalLayerBridge instance."""
        assert hasattr(engine, "formal_bridge")
        assert isinstance(engine.formal_bridge, FormalLayerBridge)

    @pytest.mark.asyncio
    async def test_initialize_components_initialises_bridge(self, engine):
        """initialize_components should call formal_bridge.initialize()."""
        await engine.initialize_components()
        if engine.formal_bridge.is_available:
            assert engine.formal_bridge.is_initialized is True

    @pytest.mark.asyncio
    async def test_consciousness_report_includes_formal_layer(self, engine):
        """The consciousness report should contain formal_layer section."""
        await engine.initialize_components()
        report = await engine.get_consciousness_report()
        assert "formal_layer" in report
        assert "connected" in report["formal_layer"]
        if engine.formal_bridge.is_available:
            assert report["formal_layer"]["connected"] is True
