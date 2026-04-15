#!/usr/bin/env python3
"""
Grounding Coherence Daemon for GodelOS

Monitors contradiction validation scores from the consciousness engine's
self-model validator and raises alerts when the mean contradiction score
exceeds a configurable threshold.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from backend.core.agentic_daemon_system import (
    AgenticDaemon,
    DaemonTask,
    DaemonType,
)

logger = logging.getLogger(__name__)

# ── Tunables ──────────────────────────────────────────────────────────

_WINDOW_SIZE = 10       # number of recent validations to evaluate
_ALERT_THRESHOLD = 0.4  # mean contradiction score that triggers an alert


class GroundingCoherenceDaemon(AgenticDaemon):
    """Daemon that watches contradiction validation scores and fires alerts
    when the rolling mean exceeds the configured threshold."""

    def __init__(
        self,
        cognitive_manager=None,
        knowledge_pipeline=None,
        websocket_manager=None,
        consciousness_engine=None,
    ):
        super().__init__(
            daemon_type=DaemonType.GROUNDING_COHERENCE,
            name="Grounding Coherence Daemon",
            cognitive_manager=cognitive_manager,
            knowledge_pipeline=knowledge_pipeline,
            websocket_manager=websocket_manager,
        )
        self.consciousness_engine = consciousness_engine
        self.sleep_interval = 60  # Check every 60 seconds

    # ── lifecycle ─────────────────────────────────────────────────────

    async def _initialize(self) -> None:
        """Initialize daemon-specific components."""
        logger.info(
            "Grounding Coherence Daemon initialised – "
            f"window={_WINDOW_SIZE}, threshold={_ALERT_THRESHOLD}"
        )

    # ── task generation ───────────────────────────────────────────────

    async def _generate_autonomous_tasks(self) -> List[DaemonTask]:
        """Evaluate recent contradiction validations and generate an alert
        task when the windowed mean exceeds the threshold."""
        tasks: List[DaemonTask] = []

        # Guard: need a consciousness engine with a self-model validator
        validator = self._get_validator()
        if validator is None:
            return tasks

        history = validator.validation_history
        if len(history) < _WINDOW_SIZE:
            return tasks

        window = history[-_WINDOW_SIZE:]
        window_mean = sum(r.contradiction_score for r in window) / _WINDOW_SIZE

        if window_mean > _ALERT_THRESHOLD:
            stats = {
                "window_size": _WINDOW_SIZE,
                "window_mean": round(window_mean, 4),
                "threshold": _ALERT_THRESHOLD,
                "max_score": round(
                    max(r.contradiction_score for r in window), 4
                ),
                "min_score": round(
                    min(r.contradiction_score for r in window), 4
                ),
            }
            task = DaemonTask(
                type="grounding_alert",
                description=(
                    f"Grounding coherence alert: mean contradiction "
                    f"{window_mean:.4f} > {_ALERT_THRESHOLD}"
                ),
                priority=9,
                parameters=stats,
            )
            tasks.append(task)

        return tasks

    # ── task execution ────────────────────────────────────────────────

    async def _execute_task(self, task: DaemonTask) -> Dict[str, Any]:
        """Execute a grounding alert task: log and broadcast via WebSocket."""
        try:
            if task.type == "grounding_alert":
                logger.warning(
                    "🚨 Grounding coherence alert – %s", task.description
                )

                if self.websocket_manager:
                    await self.websocket_manager.broadcast_cognitive_update({
                        "type": "grounding_coherence_alert",
                        "timestamp": datetime.now().isoformat(),
                        "data": task.parameters,
                    })

                return {"status": "completed", "discoveries_made": 1}

            return {"status": "completed", "message": "Unknown task type"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ── helpers ───────────────────────────────────────────────────────

    def _get_validator(self):
        """Return the SelfModelValidator from the consciousness engine, or
        ``None`` if unavailable."""
        engine = self.consciousness_engine
        if engine is not None and hasattr(engine, "self_model_validator"):
            return engine.self_model_validator
        return None
