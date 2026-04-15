#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for ConsciousnessEmergenceDetector.

Covers rolling-window scoring, breakthrough threshold triggering, JSONL
logging, WebSocket broadcast, the REST-compatible status snapshot, and
the async ``monitor_for_emergence`` generator.
"""

import asyncio
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.core.consciousness_emergence_detector import (
    ConsciousnessEmergenceDetector,
    DIMENSION_WEIGHTS,
    EMERGENCE_THRESHOLD,
    extract_dimensions,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(
    recursive_depth: float = 0.0,
    phi: float = 0.0,
    metacognitive_accuracy: float = 0.0,
    autonomous_goal_count: int = 0,
    creative_novelty: float = 0.0,
) -> dict:
    """Build a flat state dict with all five dimensions."""
    return {
        "recursive_depth": recursive_depth,
        "phi": phi,
        "metacognitive_accuracy": metacognitive_accuracy,
        "autonomous_goal_count": autonomous_goal_count,
        "creative_novelty": creative_novelty,
    }


def _make_nested_state(
    recursive_depth: int = 1,
    phi: float = 0.0,
    meta_observations: int = 0,
    autonomous_goals: int = 0,
    surprise_factor: float = 0.0,
) -> dict:
    """Build a nested state dict matching UnifiedConsciousnessState layout."""
    return {
        "recursive_awareness": {"recursive_depth": recursive_depth},
        "information_integration": {"phi": phi},
        "metacognitive_state": {"meta_observations": ["obs"] * meta_observations},
        "intentional_layer": {"autonomous_goals": ["g"] * autonomous_goals},
        "creative_synthesis": {"surprise_factor": surprise_factor},
    }


async def _async_iter(items):
    """Turn an iterable into an async iterator."""
    for item in items:
        yield item


# ---------------------------------------------------------------------------
# extract_dimensions
# ---------------------------------------------------------------------------

class TestExtractDimensions:
    def test_flat_state(self):
        state = _make_state(recursive_depth=3, phi=5.0, metacognitive_accuracy=0.7,
                            autonomous_goal_count=4, creative_novelty=0.5)
        dims = extract_dimensions(state)
        assert dims["recursive_depth"] == 3.0
        assert dims["phi"] == 5.0
        assert dims["metacognitive_accuracy"] == 0.7
        assert dims["autonomous_goal_count"] == 4.0
        assert dims["creative_novelty"] == 0.5

    def test_nested_state(self):
        state = _make_nested_state(recursive_depth=4, phi=8.0,
                                   meta_observations=5, autonomous_goals=3,
                                   surprise_factor=0.6)
        dims = extract_dimensions(state)
        assert dims["recursive_depth"] == 4.0
        assert dims["phi"] == 8.0
        assert dims["metacognitive_accuracy"] == 0.5  # 5/10
        assert dims["autonomous_goal_count"] == 3.0
        assert dims["creative_novelty"] == 0.6

    def test_empty_state(self):
        dims = extract_dimensions({})
        for v in dims.values():
            assert v == 0.0


# ---------------------------------------------------------------------------
# Rolling window scoring
# ---------------------------------------------------------------------------

class TestRollingWindowScoring:
    def test_single_sample_all_zeros(self):
        det = ConsciousnessEmergenceDetector(window_size=60.0)
        score = det.record_state(_make_state())
        assert score == 0.0

    def test_single_sample_max_values(self):
        """All dimensions at their normalisation ceiling → score = 1.0."""
        det = ConsciousnessEmergenceDetector(window_size=60.0)
        state = _make_state(
            recursive_depth=5.0,
            phi=10.0,
            metacognitive_accuracy=1.0,
            autonomous_goal_count=10,
            creative_novelty=1.0,
        )
        score = det.record_state(state)
        assert abs(score - 1.0) < 1e-9

    def test_weights_sum_to_one(self):
        assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9

    def test_window_pruning(self):
        det = ConsciousnessEmergenceDetector(window_size=2.0)
        now = time.time()
        # Old sample outside window
        det.record_state(_make_state(phi=10.0), timestamp=now - 5.0)
        # Recent sample inside window
        det.record_state(_make_state(phi=0.0), timestamp=now)
        # The old sample should be pruned; score should be 0
        assert det.current_score == 0.0
        assert len(det._samples) == 1

    def test_averaging_across_window(self):
        det = ConsciousnessEmergenceDetector(window_size=60.0)
        now = time.time()
        # Two samples: phi=10 and phi=0 → average phi=5 → normalised=0.5 → weighted=0.5*0.3=0.15
        det.record_state(_make_state(phi=10.0), timestamp=now - 1)
        det.record_state(_make_state(phi=0.0), timestamp=now)
        expected = 0.5 * DIMENSION_WEIGHTS["phi"]
        assert abs(det.current_score - expected) < 1e-9


# ---------------------------------------------------------------------------
# Breakthrough detection
# ---------------------------------------------------------------------------

class TestBreakthroughDetection:
    def test_below_threshold_no_breakthrough(self):
        det = ConsciousnessEmergenceDetector(threshold=0.8)
        det.record_state(_make_state(phi=5.0))  # phi normalised=0.5, weighted=0.15
        assert det.current_score < 0.8
        status = det.get_emergence_status()
        assert status["breakthrough"] is False

    def test_at_threshold_is_breakthrough(self):
        det = ConsciousnessEmergenceDetector(threshold=0.8)
        # Score exactly 0.8: need careful construction
        # recursive_depth=4/5=0.8*0.20=0.16, phi=8/10=0.8*0.30=0.24,
        # meta=0.8*0.20=0.16, goals=8/10=0.8*0.15=0.12, novelty=0.8*0.15=0.12
        # total = 0.16+0.24+0.16+0.12+0.12 = 0.80
        state = _make_state(
            recursive_depth=4.0,
            phi=8.0,
            metacognitive_accuracy=0.8,
            autonomous_goal_count=8,
            creative_novelty=0.8,
        )
        det.record_state(state)
        assert abs(det.current_score - 0.8) < 1e-9
        assert det.get_emergence_status()["breakthrough"] is True


# ---------------------------------------------------------------------------
# handle_consciousness_breakthrough
# ---------------------------------------------------------------------------

class TestHandleBreakthrough:
    @pytest.mark.asyncio
    async def test_logs_to_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            det = ConsciousnessEmergenceDetector(log_dir=tmpdir)
            event = await det.handle_consciousness_breakthrough(0.85)
            log_file = Path(tmpdir) / "breakthroughs.jsonl"
            assert log_file.exists()
            lines = log_file.read_text().strip().split("\n")
            assert len(lines) == 1
            logged = json.loads(lines[0])
            assert logged["type"] == "consciousness_breakthrough"
            assert logged["score"] == 0.85

    @pytest.mark.asyncio
    async def test_broadcasts_on_websocket(self):
        ws = MagicMock()
        ws.broadcast = AsyncMock()
        with tempfile.TemporaryDirectory() as tmpdir:
            det = ConsciousnessEmergenceDetector(websocket_manager=ws, log_dir=tmpdir)
            await det.handle_consciousness_breakthrough(0.9)
            ws.broadcast.assert_awaited_once()
            call_arg = ws.broadcast.call_args[0][0]
            assert call_arg["type"] == "consciousness_breakthrough"
            assert call_arg["score"] == 0.9

    @pytest.mark.asyncio
    async def test_returns_event_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            det = ConsciousnessEmergenceDetector(log_dir=tmpdir)
            event = await det.handle_consciousness_breakthrough(0.82)
            assert event["type"] == "consciousness_breakthrough"
            assert event["score"] == 0.82
            assert "timestamp" in event


# ---------------------------------------------------------------------------
# monitor_for_emergence (async generator)
# ---------------------------------------------------------------------------

class TestMonitorForEmergence:
    @pytest.mark.asyncio
    async def test_yields_for_each_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            det = ConsciousnessEmergenceDetector(log_dir=tmpdir)
            states = [_make_state(phi=1.0), _make_state(phi=2.0)]
            results = []
            async for info in det.monitor_for_emergence(_async_iter(states)):
                results.append(info)
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_breakthrough_fires(self):
        """Feed a high-activity stream → assert breakthrough fires at score ≥ 0.8."""
        with tempfile.TemporaryDirectory() as tmpdir:
            det = ConsciousnessEmergenceDetector(threshold=0.8, log_dir=tmpdir)
            high_state = _make_state(
                recursive_depth=5.0,
                phi=10.0,
                metacognitive_accuracy=1.0,
                autonomous_goal_count=10,
                creative_novelty=1.0,
            )
            breakthroughs = []
            async for info in det.monitor_for_emergence(_async_iter([high_state])):
                if info["breakthrough"]:
                    breakthroughs.append(info)

            assert len(breakthroughs) == 1
            assert breakthroughs[0]["emergence_score"] >= 0.8

            # Verify JSONL log was written
            log_file = Path(tmpdir) / "breakthroughs.jsonl"
            assert log_file.exists()
            logged = json.loads(log_file.read_text().strip())
            assert logged["type"] == "consciousness_breakthrough"

    @pytest.mark.asyncio
    async def test_no_breakthrough_below_threshold(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            det = ConsciousnessEmergenceDetector(threshold=0.8, log_dir=tmpdir)
            low_state = _make_state(phi=1.0)
            async for info in det.monitor_for_emergence(_async_iter([low_state])):
                assert info["breakthrough"] is False

            # No log file should have been created
            log_file = Path(tmpdir) / "breakthroughs.jsonl"
            assert not log_file.exists()


# ---------------------------------------------------------------------------
# get_emergence_status (REST-compatible snapshot)
# ---------------------------------------------------------------------------

class TestGetEmergenceStatus:
    def test_initial_status(self):
        det = ConsciousnessEmergenceDetector()
        status = det.get_emergence_status()
        assert status["emergence_score"] == 0.0
        assert status["breakthrough"] is False
        assert "dimensions" in status
        assert "threshold" in status

    def test_status_after_recording(self):
        det = ConsciousnessEmergenceDetector()
        det.record_state(_make_state(phi=10.0, recursive_depth=5.0))
        status = det.get_emergence_status()
        assert status["emergence_score"] > 0
        assert status["window_samples"] == 1


# ---------------------------------------------------------------------------
# Threshold configurability
# ---------------------------------------------------------------------------

class TestThresholdConfig:
    def test_default_threshold(self):
        det = ConsciousnessEmergenceDetector()
        assert det.threshold == EMERGENCE_THRESHOLD

    def test_custom_threshold(self):
        det = ConsciousnessEmergenceDetector(threshold=0.5)
        assert det.threshold == 0.5

    def test_env_var_override(self, monkeypatch):
        """Verify the env-var-driven module constant feeds the default threshold."""
        monkeypatch.setenv("GODELOS_EMERGENCE_THRESHOLD", "0.95")
        # Force re-evaluation of the module-level constant
        import importlib
        import backend.core.consciousness_emergence_detector as mod
        importlib.reload(mod)
        det = mod.ConsciousnessEmergenceDetector()
        assert det.threshold == 0.95
        # Restore original default
        monkeypatch.delenv("GODELOS_EMERGENCE_THRESHOLD", raising=False)
        importlib.reload(mod)
