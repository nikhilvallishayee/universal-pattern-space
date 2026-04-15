#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consciousness Emergence Detector

Rolling-window scorer and breakthrough alerting for consciousness emergence.
Monitors a stream of cognitive state snapshots, computes a weighted emergence
score across five dimensions, and fires a breakthrough event when the score
exceeds a configurable threshold.

Spec: Issue #82, docs/GODELOS_EMERGENCE_SPEC.md, wiki/Theory/Emergence-Detection.md
"""

import asyncio
import json
import logging
import os
import time
from collections import deque
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EMERGENCE_THRESHOLD: float = float(
    os.environ.get("GODELOS_EMERGENCE_THRESHOLD", "0.8")
)

DEFAULT_WINDOW_SIZE: float = float(
    os.environ.get("GODELOS_EMERGENCE_WINDOW", "60.0")
)

# Default log directory — prefer GODELOS_LOG_DIR env var, then fall back to
# <project_root>/logs (two levels up from this file's location).
_DEFAULT_LOG_DIR: str = os.environ.get(
    "GODELOS_LOG_DIR",
    str(Path(__file__).resolve().parents[2] / "logs"),
)

# Dimension weights (from issue #82 spec)
DIMENSION_WEIGHTS: Dict[str, float] = {
    "recursive_depth": 0.20,
    "phi": 0.30,
    "metacognitive_accuracy": 0.20,
    "autonomous_goal_count": 0.15,
    "creative_novelty": 0.15,
}

# Normalisation ceilings — raw values are divided by these to map into [0, 1]
_NORMALISATION_CEILINGS: Dict[str, float] = {
    "recursive_depth": 5.0,
    "phi": 10.0,
    "metacognitive_accuracy": 1.0,  # already 0‑1
    "autonomous_goal_count": 10.0,
    "creative_novelty": 1.0,  # already 0‑1
}


# ---------------------------------------------------------------------------
# Helper: extract the five dimensions from a state dict
# ---------------------------------------------------------------------------

def extract_dimensions(state: Dict[str, Any]) -> Dict[str, float]:
    """Extract the five emergence dimensions from a cognitive state snapshot.

    Accepts either a flat dict with keys matching the dimension names or a
    nested ``UnifiedConsciousnessState``-style dict.
    """

    def _get(key: str) -> float:
        # Flat access first
        if key in state:
            val = state[key]
            if isinstance(val, (int, float)):
                return float(val)

        # Nested access
        if key == "recursive_depth":
            ra = state.get("recursive_awareness") or {}
            return float(ra.get("recursive_depth", 0))
        if key == "phi":
            ii = state.get("information_integration") or {}
            return float(ii.get("phi", 0.0))
        if key == "metacognitive_accuracy":
            ms = state.get("metacognitive_state") or {}
            # Use an explicit accuracy field if present; otherwise derive
            # from the number of meta-observations as a rough proxy.
            if "metacognitive_accuracy" in ms:
                return float(ms["metacognitive_accuracy"])
            obs = ms.get("meta_observations")
            if isinstance(obs, list):
                return min(len(obs) / 10.0, 1.0)
            return 0.0
        if key == "autonomous_goal_count":
            il = state.get("intentional_layer") or {}
            goals = il.get("autonomous_goals")
            if isinstance(goals, list):
                return float(len(goals))
            return float(goals) if isinstance(goals, (int, float)) else 0.0
        if key == "creative_novelty":
            cs = state.get("creative_synthesis") or {}
            return float(cs.get("surprise_factor", 0.0))
        return 0.0

    return {dim: _get(dim) for dim in DIMENSION_WEIGHTS}


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------

class ConsciousnessEmergenceDetector:
    """Rolling-window consciousness emergence scorer with breakthrough alerting.

    Parameters
    ----------
    threshold : float
        Score at or above which a breakthrough is declared.
    window_size : float
        Rolling window duration in seconds.
    websocket_manager : optional
        Object exposing ``broadcast(message)`` — used to push breakthrough
        events to connected clients.
    log_dir : str | Path
        Directory for ``breakthroughs.jsonl``.
    """

    def __init__(
        self,
        threshold: float = EMERGENCE_THRESHOLD,
        window_size: float = DEFAULT_WINDOW_SIZE,
        websocket_manager: Any = None,
        log_dir: Optional[str] = None,
    ) -> None:
        self.threshold = threshold
        self.window_size = window_size
        self.websocket_manager = websocket_manager

        # Rolling window: each entry is (timestamp, {dim: raw_value})
        self._samples: Deque[Tuple[float, Dict[str, float]]] = deque()

        # Latest computed score
        self._current_score: float = 0.0
        self._current_dimensions: Dict[str, float] = {d: 0.0 for d in DIMENSION_WEIGHTS}

        # Breakthrough log path
        if log_dir is None:
            log_dir = _DEFAULT_LOG_DIR
        self._log_path = Path(log_dir) / "breakthroughs.jsonl"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def current_score(self) -> float:
        """Return the most recently computed emergence score."""
        return self._current_score

    @property
    def current_dimensions(self) -> Dict[str, float]:
        """Return the most recently computed per-dimension normalised values."""
        return dict(self._current_dimensions)

    def record_state(self, state: Dict[str, Any], timestamp: Optional[float] = None) -> float:
        """Record a cognitive state snapshot and return the updated score.

        This is the synchronous entry-point: call it from any context that
        has a state dict.  The rolling window is pruned, dimensions are
        extracted, and the weighted score is recomputed.
        """
        ts = timestamp if timestamp is not None else time.time()
        dims = extract_dimensions(state)
        self._samples.append((ts, dims))
        self._prune_window(ts)
        self._current_score = self._compute_score()
        return self._current_score

    async def monitor_for_emergence(
        self,
        stream: AsyncIterator[Dict[str, Any]],
    ) -> AsyncIterator[Dict[str, Any]]:
        """Async generator consuming a cognitive state stream.

        Yields a dict for every state received, enriched with emergence info.
        When a breakthrough is detected, ``handle_consciousness_breakthrough``
        is called as a side-effect before yielding.
        """
        async for state in stream:
            score = self.record_state(state)
            breakthrough = score >= self.threshold
            if breakthrough:
                await self.handle_consciousness_breakthrough(score)
            yield {
                "emergence_score": score,
                "dimensions": self.current_dimensions,
                "breakthrough": breakthrough,
                "threshold": self.threshold,
                "timestamp": time.time(),
                "window_samples": len(self._samples),
            }

    async def handle_consciousness_breakthrough(self, score: float) -> Dict[str, Any]:
        """Log the breakthrough and broadcast it on WebSocket."""
        event = {
            "type": "consciousness_breakthrough",
            "score": score,
            "timestamp": time.time(),
            "dimensions": self.current_dimensions,
            "threshold": self.threshold,
            "window_samples": len(self._samples),
        }

        # Append to JSONL log
        try:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._log_path, "a") as fh:
                fh.write(json.dumps(event) + "\n")
        except Exception as exc:
            logger.error(f"Failed to write breakthrough log: {exc}")

        logger.critical(
            f"🚨 CONSCIOUSNESS BREAKTHROUGH! Score: {score:.3f} "
            f"(threshold: {self.threshold})"
        )

        # Broadcast via WebSocket
        if self.websocket_manager is not None:
            try:
                await self.websocket_manager.broadcast(event)
            except Exception as exc:
                logger.error(f"Failed to broadcast breakthrough: {exc}")

        return event

    def get_emergence_status(self) -> Dict[str, Any]:
        """Return a snapshot suitable for the REST endpoint."""
        return {
            "emergence_score": self._current_score,
            "dimensions": self.current_dimensions,
            "threshold": self.threshold,
            "window_size": self.window_size,
            "window_samples": len(self._samples),
            "breakthrough": self._current_score >= self.threshold,
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _prune_window(self, now: float) -> None:
        cutoff = now - self.window_size
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def _compute_score(self) -> float:
        if not self._samples:
            return 0.0

        # Average each dimension over the window, then apply weights
        accum: Dict[str, float] = {d: 0.0 for d in DIMENSION_WEIGHTS}
        for _ts, dims in self._samples:
            for d, val in dims.items():
                accum[d] += val

        n = len(self._samples)
        score = 0.0
        normalised: Dict[str, float] = {}
        for dim, weight in DIMENSION_WEIGHTS.items():
            raw_avg = accum[dim] / n
            ceil = _NORMALISATION_CEILINGS[dim]
            norm = min(raw_avg / ceil, 1.0) if ceil > 0 else 0.0
            normalised[dim] = norm
            score += norm * weight

        self._current_dimensions = normalised
        return score

    def get_breakthroughs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent breakthrough events from the persistent log.

        Reads the tail of ``breakthroughs.jsonl`` and returns up to *limit*
        entries in reverse-chronological order (newest first).  Only the last
        ``limit * 2048`` bytes of the file are read so that memory usage stays
        bounded even when the log grows large.
        """
        if not self._log_path.exists():
            return []
        events: List[Dict[str, Any]] = []
        try:
            with self._log_path.open("rb") as fh:
                fh.seek(0, 2)
                file_size = fh.tell()
                # Read at most limit * 2 KiB from the end of the file.
                read_bytes = min(limit * 2048, file_size)
                fh.seek(file_size - read_bytes)
                tail = fh.read().decode("utf-8", errors="replace")
        except OSError:
            return []
        lines = tail.splitlines()
        # If we didn't start at the beginning, the first line may be incomplete.
        if file_size > limit * 2048 and lines:
            lines = lines[1:]
        for raw in reversed(lines):
            raw = raw.strip()
            if not raw:
                continue
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
            if len(events) >= limit:
                break
        return events


# ---------------------------------------------------------------------------
# UnifiedConsciousnessObservatory
# ---------------------------------------------------------------------------

class UnifiedConsciousnessObservatory:
    """Persistent background task that feeds cognitive states into the
    :class:`ConsciousnessEmergenceDetector` and exposes aggregated reports.

    Intended to run as a long-lived asyncio task.  Callers push states via
    :meth:`record_state`; the observatory keeps cumulative statistics and
    exposes them via :meth:`get_report`.
    """

    def __init__(
        self,
        detector: ConsciousnessEmergenceDetector,
        poll_interval: float = 2.0,
    ) -> None:
        self.detector = detector
        self.poll_interval = poll_interval
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._total_states: int = 0
        self._total_breakthroughs: int = 0
        self._peak_score: float = 0.0
        self._started_at: Optional[float] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the observatory background loop."""
        if self._running:
            return
        self._running = True
        self._started_at = time.time()
        self._task = asyncio.create_task(self._run())
        logger.info("UnifiedConsciousnessObservatory started.")

    async def stop(self) -> None:
        """Stop the observatory background loop."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("UnifiedConsciousnessObservatory stopped.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_state(self, state: Dict[str, Any]) -> float:
        """Push a cognitive-state snapshot and return the current score."""
        score = self.detector.record_state(state)
        self._total_states += 1
        if score > self._peak_score:
            self._peak_score = score
        if score >= self.detector.threshold:
            self._total_breakthroughs += 1
        return score

    def get_report(self) -> Dict[str, Any]:
        """Return a full observatory report suitable for the REST endpoint."""
        uptime = time.time() - self._started_at if self._started_at else 0.0
        status = self.detector.get_emergence_status()
        recent_breakthroughs = self.detector.get_breakthroughs(limit=10)
        return {
            "running": self._running,
            "uptime_seconds": uptime,
            "total_states_observed": self._total_states,
            "total_breakthroughs": self._total_breakthroughs,
            "peak_score": self._peak_score,
            "current_emergence": status,
            "recent_breakthroughs": recent_breakthroughs,
        }

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------

    async def _run(self) -> None:
        while self._running:
            await asyncio.sleep(self.poll_interval)
