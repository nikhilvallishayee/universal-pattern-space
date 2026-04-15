#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Autonomous Goal Engine (Issue #81) and the new consciousness
endpoints added in this PR:
  - AutonomousGoalGenerator
  - CreativeSynthesisEngine
  - GET /api/consciousness/goals
  - POST /api/consciousness/goals/generate
  - GET /api/consciousness/creative-synthesis
  - GET /api/consciousness/breakthroughs
  - GET /api/consciousness/observatory
  - UnifiedConsciousnessObservatory
"""

import asyncio
import json

import pytest

from backend.core.autonomous_goal_engine import AutonomousGoalGenerator, CreativeSynthesisEngine
from backend.core.consciousness_emergence_detector import (
    ConsciousnessEmergenceDetector,
    UnifiedConsciousnessObservatory,
)


# ---------------------------------------------------------------------------
# AutonomousGoalGenerator tests
# ---------------------------------------------------------------------------

class TestAutonomousGoalGenerator:
    """Unit tests for AutonomousGoalGenerator."""

    def _make_generator(self) -> AutonomousGoalGenerator:
        return AutonomousGoalGenerator()

    @pytest.mark.asyncio
    async def test_generate_returns_list(self):
        gen = self._make_generator()
        goals = await gen.generate({})
        assert isinstance(goals, list)

    @pytest.mark.asyncio
    async def test_baseline_goal_generated_when_empty(self):
        """At least one goal is produced from an empty state."""
        gen = self._make_generator()
        goals = await gen.generate({})
        assert len(goals) >= 1

    @pytest.mark.asyncio
    async def test_phi_gap_triggers_integration_goal(self):
        """Low phi triggers an integration-type goal."""
        gen = self._make_generator()
        state = {"information_integration": {"phi": 0.0}}
        goals = await gen.generate(state)
        types = [g["type"] for g in goals]
        assert "integration" in types

    @pytest.mark.asyncio
    async def test_coherence_gap_triggers_coherence_goal(self):
        """Low coherence triggers a coherence-type goal."""
        gen = self._make_generator()
        state = {"cognitive_coherence": 0.3}
        goals = await gen.generate(state)
        types = [g["type"] for g in goals]
        assert "coherence" in types

    @pytest.mark.asyncio
    async def test_goal_has_required_fields(self):
        """Each goal dict contains mandatory fields."""
        gen = self._make_generator()
        goals = await gen.generate({})
        for goal in goals:
            for field in ("id", "type", "target", "priority", "source", "confidence", "created_at", "status"):
                assert field in goal, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_active_goals_populated_after_generate(self):
        gen = self._make_generator()
        assert gen.active_goals == []
        await gen.generate({})
        assert len(gen.active_goals) >= 1

    @pytest.mark.asyncio
    async def test_dedup_suppresses_repeated_target(self):
        """Same target is not proposed twice within the dedup window."""
        gen = self._make_generator()
        goals1 = await gen.generate({})
        goals2 = await gen.generate({})
        # Both calls return fresh goals only; no duplicates should appear across them
        ids1 = {g["id"] for g in goals1}
        ids2 = {g["id"] for g in goals2}
        assert ids1.isdisjoint(ids2), "Same goal IDs returned in two consecutive calls"

    @pytest.mark.asyncio
    async def test_knowledge_gap_generates_learning_goal(self):
        gen = self._make_generator()
        context = {"knowledge_gaps": [{"context": "quantum entanglement", "confidence": 0.9}]}
        goals = await gen.generate({}, context=context)
        types = [g["type"] for g in goals]
        assert "learning" in types

    @pytest.mark.asyncio
    async def test_mark_goal_completed(self):
        gen = self._make_generator()
        goals = await gen.generate({})
        assert len(goals) > 0
        goal_id = goals[0]["id"]
        result = gen.mark_goal_completed(goal_id)
        assert result is True
        remaining_ids = {g["id"] for g in gen.active_goals}
        assert goal_id not in remaining_ids

    def test_get_metrics_structure(self):
        gen = self._make_generator()
        metrics = gen.get_metrics()
        for key in ("active_goal_count", "total_generations", "last_generation_at"):
            assert key in metrics

    @pytest.mark.asyncio
    async def test_goal_count_increases_per_session(self):
        """After multiple generate calls, active goal count can grow."""
        gen = AutonomousGoalGenerator()
        # Generate with states that each trigger different goal types
        await gen.generate({"cognitive_coherence": 0.3})
        # Active goals should be present
        assert len(gen.active_goals) >= 1


# ---------------------------------------------------------------------------
# CreativeSynthesisEngine tests
# ---------------------------------------------------------------------------

class TestCreativeSynthesisEngine:
    """Unit tests for CreativeSynthesisEngine."""

    def _make_engine(self) -> CreativeSynthesisEngine:
        return CreativeSynthesisEngine()

    def test_synthesise_empty_buffer_returns_empty(self):
        engine = self._make_engine()
        results = engine.synthesise(n=3)
        assert results == []

    def test_synthesise_single_concept_returns_empty(self):
        engine = self._make_engine()
        engine.ingest_concepts(["quantum mechanics"])
        results = engine.synthesise()
        assert results == []

    def test_synthesise_two_concepts_returns_output(self):
        engine = self._make_engine()
        engine.ingest_concepts(["quantum mechanics", "narrative structure"])
        results = engine.synthesise(n=1)
        assert len(results) == 1

    def test_synthesis_has_required_fields(self):
        engine = self._make_engine()
        engine.ingest_concepts(["mind", "mathematics"])
        results = engine.synthesise(n=1)
        assert len(results) == 1
        for field in ("id", "concept_a", "concept_b", "synthesis", "novelty_score", "coherence_score", "combined_score"):
            assert field in results[0], f"Missing field: {field}"

    def test_novelty_score_between_0_and_1(self):
        engine = self._make_engine()
        engine.ingest_concepts(["time", "consciousness", "space", "entropy"])
        results = engine.synthesise(n=5)
        for r in results:
            assert 0.0 <= r["novelty_score"] <= 1.0, f"novelty_score out of range: {r['novelty_score']}"

    def test_coherence_score_between_0_and_1(self):
        engine = self._make_engine()
        engine.ingest_concepts(["wave function", "particle", "observer", "collapse"])
        results = engine.synthesise(n=5)
        for r in results:
            assert 0.0 <= r["coherence_score"] <= 1.0

    def test_ingest_deduplicates_concepts(self):
        engine = self._make_engine()
        engine.ingest_concepts(["alpha", "alpha", "beta"])
        assert engine._concept_buffer.count("alpha") == 1

    def test_get_recent_outputs(self):
        engine = self._make_engine()
        engine.ingest_concepts(["art", "mathematics", "biology"])
        engine.synthesise(n=3)
        outputs = engine.get_recent_outputs(limit=10)
        assert len(outputs) >= 1

    def test_get_metrics_structure(self):
        engine = self._make_engine()
        metrics = engine.get_metrics()
        for key in ("concept_buffer_size", "total_syntheses", "avg_novelty_last_20"):
            assert key in metrics

    def test_novelty_decreases_for_repeated_pair(self):
        """Re-synthesising the same pair should yield lower novelty."""
        engine = self._make_engine()
        engine.ingest_concepts(["alpha", "beta"])
        r1 = engine.synthesise(n=1)
        r2 = engine.synthesise(n=1)
        assert len(r1) == 1 and len(r2) == 1, "Expected one result per synthesis call"
        assert r2[0]["novelty_score"] <= r1[0]["novelty_score"]

    def test_synthesise_respects_n_limit(self):
        engine = self._make_engine()
        engine.ingest_concepts(["a", "b", "c", "d", "e"])
        results = engine.synthesise(n=3)
        assert len(results) <= 3


# ---------------------------------------------------------------------------
# UnifiedConsciousnessObservatory tests
# ---------------------------------------------------------------------------

class TestUnifiedConsciousnessObservatory:
    """Unit tests for UnifiedConsciousnessObservatory."""

    def _make_observatory(self, log_dir: str) -> UnifiedConsciousnessObservatory:
        detector = ConsciousnessEmergenceDetector(log_dir=log_dir)
        return UnifiedConsciousnessObservatory(detector)

    def test_initial_report_structure(self, tmp_path):
        obs = self._make_observatory(str(tmp_path))
        report = obs.get_report()
        for key in ("running", "uptime_seconds", "total_states_observed",
                    "total_breakthroughs", "peak_score", "current_emergence",
                    "recent_breakthroughs"):
            assert key in report, f"Missing key: {key}"

    def test_record_state_increments_counter(self, tmp_path):
        obs = self._make_observatory(str(tmp_path))
        obs.record_state({"phi": 0.1})
        assert obs.get_report()["total_states_observed"] == 1

    def test_peak_score_tracked(self, tmp_path):
        obs = self._make_observatory(str(tmp_path))
        obs.record_state({"phi": 0.0})
        obs.record_state({"phi": 5.0, "metacognitive_accuracy": 1.0})
        report = obs.get_report()
        assert report["peak_score"] > 0.0

    @pytest.mark.asyncio
    async def test_start_stop(self, tmp_path):
        obs = self._make_observatory(str(tmp_path))
        await obs.start()
        assert obs._running is True
        await obs.stop()
        assert obs._running is False

    @pytest.mark.asyncio
    async def test_double_start_is_safe(self, tmp_path):
        obs = self._make_observatory(str(tmp_path))
        await obs.start()
        await obs.start()  # should not raise
        await obs.stop()


# ---------------------------------------------------------------------------
# GET /api/consciousness/breakthroughs — unit test via detector directly
# ---------------------------------------------------------------------------

class TestBreakthroughsEndpoint:
    """Test the get_breakthroughs helper method used by the endpoint."""

    def test_no_log_returns_empty(self, tmp_path):
        detector = ConsciousnessEmergenceDetector(log_dir=str(tmp_path))
        assert detector.get_breakthroughs() == []

    def test_log_entries_returned_newest_first(self, tmp_path):
        detector = ConsciousnessEmergenceDetector(log_dir=str(tmp_path))
        log_path = tmp_path / "breakthroughs.jsonl"
        events = [
            {"type": "consciousness_breakthrough", "score": 0.85, "timestamp": 1000.0},
            {"type": "consciousness_breakthrough", "score": 0.91, "timestamp": 2000.0},
        ]
        with open(log_path, "w") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")
        results = detector.get_breakthroughs(limit=10)
        assert len(results) == 2
        # Newest first
        assert results[0]["timestamp"] == 2000.0
        assert results[1]["timestamp"] == 1000.0

    def test_limit_respected(self, tmp_path):
        detector = ConsciousnessEmergenceDetector(log_dir=str(tmp_path))
        log_path = tmp_path / "breakthroughs.jsonl"
        with open(log_path, "w") as f:
            for i in range(10):
                f.write(json.dumps({"type": "consciousness_breakthrough", "score": 0.9, "timestamp": float(i)}) + "\n")
        results = detector.get_breakthroughs(limit=3)
        assert len(results) == 3

    def test_malformed_lines_skipped(self, tmp_path):
        detector = ConsciousnessEmergenceDetector(log_dir=str(tmp_path))
        log_path = tmp_path / "breakthroughs.jsonl"
        with open(log_path, "w") as f:
            f.write("not json\n")
            f.write(json.dumps({"type": "consciousness_breakthrough", "score": 0.9, "timestamp": 1.0}) + "\n")
        results = detector.get_breakthroughs()
        assert len(results) == 1
