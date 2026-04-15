#!/usr/bin/env python3
"""Tests for GroundingCoherenceDaemon."""

import asyncio
import pytest
from dataclasses import dataclass
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

from backend.core.agentic_daemon_system import (
    AgenticDaemonSystem,
    DaemonTask,
    DaemonType,
)
from backend.core.grounding_coherence_daemon import (
    GroundingCoherenceDaemon,
    _ALERT_THRESHOLD,
    _WINDOW_SIZE,
)


# ── helpers ───────────────────────────────────────────────────────────

def _make_validation_result(contradiction_score: float):
    """Return a lightweight stand-in for ``ValidationResult``."""
    return MagicMock(contradiction_score=contradiction_score)


def _make_validator(scores: List[float]):
    """Build a mock SelfModelValidator with the given history."""
    validator = MagicMock()
    validator.validation_history = [_make_validation_result(s) for s in scores]
    return validator


def _make_engine(scores: List[float]):
    """Build a mock consciousness engine whose validator has *scores*."""
    engine = MagicMock()
    engine.self_model_validator = _make_validator(scores)
    return engine


# ── unit tests ────────────────────────────────────────────────────────


class TestGroundingCoherenceDaemonInit:
    """Construction and basic properties."""

    def test_daemon_type(self):
        daemon = GroundingCoherenceDaemon()
        assert daemon.daemon_type == DaemonType.GROUNDING_COHERENCE

    def test_sleep_interval(self):
        daemon = GroundingCoherenceDaemon()
        assert daemon.sleep_interval == 60

    def test_consciousness_engine_stored(self):
        engine = MagicMock()
        daemon = GroundingCoherenceDaemon(consciousness_engine=engine)
        assert daemon.consciousness_engine is engine


class TestGenerateAutonomousTasks:
    """Task generation under various contradiction histories."""

    @pytest.mark.asyncio
    async def test_no_engine_returns_empty(self):
        daemon = GroundingCoherenceDaemon()
        tasks = await daemon._generate_autonomous_tasks()
        assert tasks == []

    @pytest.mark.asyncio
    async def test_insufficient_history_returns_empty(self):
        engine = _make_engine([0.5] * (_WINDOW_SIZE - 1))
        daemon = GroundingCoherenceDaemon(consciousness_engine=engine)
        tasks = await daemon._generate_autonomous_tasks()
        assert tasks == []

    @pytest.mark.asyncio
    async def test_below_threshold_returns_empty(self):
        engine = _make_engine([0.1] * _WINDOW_SIZE)
        daemon = GroundingCoherenceDaemon(consciousness_engine=engine)
        tasks = await daemon._generate_autonomous_tasks()
        assert tasks == []

    @pytest.mark.asyncio
    async def test_at_threshold_returns_empty(self):
        """Exactly at 0.4 should NOT trigger (> not >=)."""
        engine = _make_engine([_ALERT_THRESHOLD] * _WINDOW_SIZE)
        daemon = GroundingCoherenceDaemon(consciousness_engine=engine)
        tasks = await daemon._generate_autonomous_tasks()
        assert tasks == []

    @pytest.mark.asyncio
    async def test_above_threshold_generates_alert(self):
        engine = _make_engine([0.5] * _WINDOW_SIZE)
        daemon = GroundingCoherenceDaemon(consciousness_engine=engine)
        tasks = await daemon._generate_autonomous_tasks()

        assert len(tasks) == 1
        task = tasks[0]
        assert task.type == "grounding_alert"
        assert task.priority == 9
        assert task.parameters["window_mean"] == 0.5
        assert task.parameters["threshold"] == _ALERT_THRESHOLD

    @pytest.mark.asyncio
    async def test_uses_last_window_only(self):
        """Only the last *_WINDOW_SIZE* entries matter."""
        scores = [0.0] * 20 + [0.9] * _WINDOW_SIZE
        engine = _make_engine(scores)
        daemon = GroundingCoherenceDaemon(consciousness_engine=engine)
        tasks = await daemon._generate_autonomous_tasks()
        assert len(tasks) == 1


class TestExecuteTask:
    """Executing grounding_alert tasks."""

    @pytest.mark.asyncio
    async def test_grounding_alert_without_websocket(self):
        daemon = GroundingCoherenceDaemon()
        task = DaemonTask(type="grounding_alert", parameters={"window_mean": 0.5})
        result = await daemon._execute_task(task)
        assert result["status"] == "completed"
        assert result["discoveries_made"] == 1

    @pytest.mark.asyncio
    async def test_grounding_alert_broadcasts_websocket(self):
        ws = MagicMock()
        ws.broadcast_cognitive_update = AsyncMock()
        daemon = GroundingCoherenceDaemon(websocket_manager=ws)
        task = DaemonTask(type="grounding_alert", parameters={"window_mean": 0.5})

        result = await daemon._execute_task(task)

        assert result["status"] == "completed"
        ws.broadcast_cognitive_update.assert_awaited_once()
        event = ws.broadcast_cognitive_update.call_args[0][0]
        assert event["type"] == "grounding_coherence_alert"

    @pytest.mark.asyncio
    async def test_unknown_task_type(self):
        daemon = GroundingCoherenceDaemon()
        task = DaemonTask(type="something_else")
        result = await daemon._execute_task(task)
        assert result["status"] == "completed"
        assert "Unknown" in result.get("message", "")


class TestRegistration:
    """Verify the daemon is registered in AgenticDaemonSystem."""

    def test_daemon_present_in_system(self):
        system = AgenticDaemonSystem()
        assert "grounding_coherence" in system.daemons
        daemon = system.daemons["grounding_coherence"]
        assert isinstance(daemon, GroundingCoherenceDaemon)

    def test_consciousness_engine_passed(self):
        engine = MagicMock()
        system = AgenticDaemonSystem(consciousness_engine=engine)
        daemon = system.daemons["grounding_coherence"]
        assert daemon.consciousness_engine is engine

    def test_system_has_grounding_coherence_daemon(self):
        system = AgenticDaemonSystem()
        assert "grounding_coherence" in system.daemons
