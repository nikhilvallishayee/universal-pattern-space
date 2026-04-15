#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autonomous Goal Engine — Issue #81

Implements:
  - AutonomousGoalGenerator: monitors cognitive state gaps and proposes goals
    without external prompting, wired into the recursive prompt construction.
  - CreativeSynthesisEngine: novel concept combination with aesthetic scoring.

These are higher-level orchestrators that build on the existing
GoalManagementSystem (backend/goal_management_system.py).
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data models (plain dicts — kept lightweight to avoid circular imports)
# ---------------------------------------------------------------------------

# Goal schema:
#   id: str          — UUID
#   type: str        — "learning" | "coherence" | "integration" | "exploration" | "self_improvement"
#   target: str      — human-readable description
#   priority: str    — "critical" | "high" | "medium" | "low"
#   source: str      — what triggered the goal
#   confidence: float
#   created_at: float
#   status: str      — "pending" | "active" | "completed" | "abandoned"
#   novelty_score: float  — for creatively synthesised goals


# ---------------------------------------------------------------------------
# AutonomousGoalGenerator
# ---------------------------------------------------------------------------

class AutonomousGoalGenerator:
    """Generates goals autonomously by monitoring the cognitive state stream.

    The generator maintains a rolling window of recent cognitive states and
    identifies gaps or opportunities that warrant new goal proposals.  Goals
    are de-duplicated by semantic hash so the same objective is not
    re-proposed within ``dedup_window`` seconds.

    Usage::

        generator = AutonomousGoalGenerator()
        goals = await generator.generate(cognitive_state)
        # goals is a list of goal-dicts
    """

    # How long (seconds) to suppress re-proposing a goal with the same target
    DEDUP_WINDOW: float = 120.0

    # Thresholds that trigger specific goal types
    _LOW_COHERENCE_THRESHOLD: float = 0.65
    _LOW_PHI_THRESHOLD: float = 0.5
    _LOW_METACOGNITIVE_THRESHOLD: float = 0.5

    def __init__(self) -> None:
        self._active_goals: List[Dict[str, Any]] = []
        # (target_hash, created_at) pairs for dedup
        self._recent_targets: Deque[Tuple[str, float]] = deque(maxlen=64)
        self._generation_count: int = 0
        self._last_generation_at: Optional[float] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def active_goals(self) -> List[Dict[str, Any]]:
        """Return a copy of the currently active goal list."""
        return list(self._active_goals)

    async def generate(
        self,
        cognitive_state: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate goals based on the provided cognitive state snapshot.

        Parameters
        ----------
        cognitive_state:
            Snapshot from UnifiedConsciousnessEngine / CognitiveManager.
        context:
            Optional extra context (knowledge gaps, recent queries, etc.).

        Returns
        -------
        list[dict]
            Newly proposed goals (may be empty if none are needed).
        """
        self._generation_count += 1
        self._last_generation_at = time.time()
        self._prune_recent_targets()

        new_goals: List[Dict[str, Any]] = []

        # 1. Phi-gap → deepen integration
        phi = self._extract_phi(cognitive_state)
        if phi < self._LOW_PHI_THRESHOLD:
            new_goals.append(self._make_goal(
                goal_type="integration",
                target="increase information integration (phi) through cross-domain synthesis",
                source="phi_monitor",
                confidence=0.85,
                priority="high",
                novelty_score=0.4,
            ))

        # 2. Coherence gap → improve reasoning consistency
        coherence = self._extract_coherence(cognitive_state)
        if coherence < self._LOW_COHERENCE_THRESHOLD:
            new_goals.append(self._make_goal(
                goal_type="coherence",
                target=f"restore cognitive coherence (current: {coherence:.2f})",
                source="coherence_monitor",
                confidence=0.9,
                priority="critical" if coherence < 0.4 else "high",
                novelty_score=0.2,
            ))

        # 3. Metacognitive blind spots → self-reflection
        meta_accuracy = self._extract_metacognitive_accuracy(cognitive_state)
        if meta_accuracy < self._LOW_METACOGNITIVE_THRESHOLD:
            new_goals.append(self._make_goal(
                goal_type="self_improvement",
                target="improve metacognitive accuracy via deeper self-reflection",
                source="metacognitive_monitor",
                confidence=0.75,
                priority="medium",
                novelty_score=0.5,
            ))

        # 4. Knowledge gaps from context
        if context:
            for gap in (context.get("knowledge_gaps") or [])[:3]:
                topic = gap.get("context", "") or gap.get("topic", "") or str(gap)
                new_goals.append(self._make_goal(
                    goal_type="learning",
                    target=f"fill knowledge gap: {topic[:120]}",
                    source="knowledge_gap_detector",
                    confidence=gap.get("confidence", 0.7),
                    priority="medium",
                    novelty_score=0.6,
                ))

        # 5. Baseline exploration goal if nothing else was generated
        if not new_goals and not self._active_goals:
            new_goals.append(self._make_goal(
                goal_type="exploration",
                target="explore novel conceptual connections in active knowledge domains",
                source="baseline_explorer",
                confidence=0.6,
                priority="low",
                novelty_score=0.7,
            ))

        # Deduplicate against recent targets
        fresh: List[Dict[str, Any]] = []
        for goal in new_goals:
            key = goal["target"][:80]
            if not self._is_recent(key):
                self._mark_recent(key)
                fresh.append(goal)

        # Merge into active goals (cap at 10)
        self._active_goals = (self._active_goals + fresh)[: 10]
        return fresh

    def get_metrics(self) -> Dict[str, Any]:
        """Return generator health metrics."""
        return {
            "active_goal_count": len(self._active_goals),
            "total_generations": self._generation_count,
            "last_generation_at": self._last_generation_at,
        }

    def mark_goal_completed(self, goal_id: str) -> bool:
        """Mark a goal as completed and remove it from the active list."""
        for i, g in enumerate(self._active_goals):
            if g["id"] == goal_id:
                g["status"] = "completed"
                self._active_goals.pop(i)
                return True
        return False

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _make_goal(
        self,
        *,
        goal_type: str,
        target: str,
        source: str,
        confidence: float,
        priority: str,
        novelty_score: float,
    ) -> Dict[str, Any]:
        return {
            "id": str(uuid.uuid4()),
            "type": goal_type,
            "target": target,
            "priority": priority,
            "source": source,
            "confidence": confidence,
            "created_at": time.time(),
            "status": "pending",
            "novelty_score": novelty_score,
        }

    @staticmethod
    def _extract_phi(state: Dict[str, Any]) -> float:
        for path in (
            ("information_integration", "phi"),
            ("phi",),
        ):
            obj = state
            for key in path:
                if not isinstance(obj, dict):
                    break
                obj = obj.get(key, None)
                if obj is None:
                    break
            if isinstance(obj, (int, float)):
                # Normalise: phi > 5 → 1.0
                return min(float(obj) / 5.0, 1.0)
        return 0.5  # neutral when unavailable

    @staticmethod
    def _extract_coherence(state: Dict[str, Any]) -> float:
        for key in ("cognitive_coherence", "coherence", "integration_level"):
            val = state.get(key)
            if isinstance(val, (int, float)):
                return float(val)
        return 0.7  # neutral

    @staticmethod
    def _extract_metacognitive_accuracy(state: Dict[str, Any]) -> float:
        for path in (
            ("metacognitive_monitor", "accuracy"),
            ("metacognitive_accuracy",),
        ):
            obj = state
            for key in path:
                if not isinstance(obj, dict):
                    break
                obj = obj.get(key, None)
                if obj is None:
                    break
            if isinstance(obj, (int, float)):
                return float(obj)
        return 0.5

    def _is_recent(self, key: str) -> bool:
        cutoff = time.time() - self.DEDUP_WINDOW
        return any(k == key and ts >= cutoff for k, ts in self._recent_targets)

    def _mark_recent(self, key: str) -> None:
        self._recent_targets.append((key, time.time()))

    def _prune_recent_targets(self) -> None:
        cutoff = time.time() - self.DEDUP_WINDOW
        while self._recent_targets and self._recent_targets[0][1] < cutoff:
            self._recent_targets.popleft()


# ---------------------------------------------------------------------------
# CreativeSynthesisEngine
# ---------------------------------------------------------------------------

class CreativeSynthesisEngine:
    """Combines concepts from the active knowledge store to produce novel ideas.

    The engine maintains a short-term concept buffer fed by recent cognitive
    states and queries.  On each ``synthesise()`` call it attempts to form
    new combinations and scores them on novelty (distance from seen pairs)
    and coherence (a simple overlap heuristic).

    Usage::

        engine = CreativeSynthesisEngine()
        engine.ingest_concepts(["quantum mechanics", "narrative structure"])
        outputs = engine.synthesise(n=3)
        # Each output: {"id", "concept_a", "concept_b", "synthesis", "novelty_score", "coherence_score", "combined_score"}
    """

    # How many concept-pair results to keep in history (for novelty scoring)
    _HISTORY_SIZE: int = 200

    # Novelty penalty for re-synthesising the same pair
    _REPEAT_PENALTY: float = 0.5

    def __init__(self) -> None:
        self._concept_buffer: List[str] = []
        self._seen_pairs: Deque[Tuple[str, str]] = deque(maxlen=self._HISTORY_SIZE)
        self._output_history: List[Dict[str, Any]] = []
        self._synthesis_count: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest_concepts(self, concepts: List[str]) -> None:
        """Add concepts to the internal buffer (deduplicates, caps at 50)."""
        for c in concepts:
            c = c.strip()
            if c and c not in self._concept_buffer:
                self._concept_buffer.append(c)
        self._concept_buffer = self._concept_buffer[-50:]

    def synthesise(self, n: int = 5) -> List[Dict[str, Any]]:
        """Generate up to *n* creative concept-pair syntheses.

        Returns a list of synthesis dicts with novelty and coherence scores.
        """
        if len(self._concept_buffer) < 2:
            return []

        candidates: List[Dict[str, Any]] = []
        concepts = list(self._concept_buffer)

        for i in range(min(len(concepts), 15)):
            for j in range(i + 1, min(len(concepts), 15)):
                a, b = concepts[i], concepts[j]
                novelty = self._score_novelty(a, b)
                coherence = self._score_coherence(a, b)
                combined = 0.6 * novelty + 0.4 * coherence
                candidates.append({
                    "id": str(uuid.uuid4()),
                    "concept_a": a,
                    "concept_b": b,
                    "synthesis": self._describe_synthesis(a, b),
                    "novelty_score": round(novelty, 3),
                    "coherence_score": round(coherence, 3),
                    "combined_score": round(combined, 3),
                    "created_at": time.time(),
                })

        # Sort by combined score descending and take top-n
        candidates.sort(key=lambda x: x["combined_score"], reverse=True)
        results = candidates[:n]

        # Record pairs so future calls know they've been seen
        for r in results:
            self._seen_pairs.append((r["concept_a"], r["concept_b"]))

        self._output_history.extend(results)
        self._output_history = self._output_history[-self._HISTORY_SIZE:]
        self._synthesis_count += len(results)
        return results

    def get_recent_outputs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent synthesis outputs."""
        return list(reversed(self._output_history[-limit:]))

    def get_metrics(self) -> Dict[str, Any]:
        """Return engine health metrics."""
        recent = self._output_history[-20:]
        avg_novelty = (
            sum(o["novelty_score"] for o in recent) / len(recent)
            if recent else 0.0
        )
        return {
            "concept_buffer_size": len(self._concept_buffer),
            "total_syntheses": self._synthesis_count,
            "avg_novelty_last_20": round(avg_novelty, 3),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _score_novelty(self, a: str, b: str) -> float:
        """Score novelty as inverse frequency of the pair in history."""
        pair = (a, b)
        reverse_pair = (b, a)
        occurrences = sum(1 for p in self._seen_pairs if p == pair or p == reverse_pair)
        base = 1.0 / (1.0 + occurrences)
        # Bonus for semantically distant tokens (approximated by word-overlap)
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        overlap = len(words_a & words_b) / max(len(words_a | words_b), 1)
        distance_bonus = (1.0 - overlap) * 0.3
        return min(base + distance_bonus, 1.0)

    @staticmethod
    def _score_coherence(a: str, b: str) -> float:
        """Rough coherence: concepts sharing abstract domain tags score higher."""
        _DOMAIN_TAGS: List[List[str]] = [
            ["quantum", "physics", "wave", "particle", "entangle"],
            ["mind", "cognitive", "conscious", "awareness", "thought"],
            ["math", "number", "equation", "proof", "theorem"],
            ["art", "creative", "aesthetic", "beauty", "narrative"],
            ["system", "network", "complex", "emergent", "adaptive"],
            ["time", "temporal", "history", "evolution", "change"],
        ]
        a_lower, b_lower = a.lower(), b.lower()
        any_partial = False
        for domain in _DOMAIN_TAGS:
            a_match = any(t in a_lower for t in domain)
            b_match = any(t in b_lower for t in domain)
            if a_match and b_match:
                return 0.8  # same domain → coherent
            if a_match or b_match:
                any_partial = True  # remember partial domain overlap
        if any_partial:
            return 0.5  # at least one partial domain overlap
        return 0.4  # no domain overlap → cross-domain (coherence lower, novelty higher)

    @staticmethod
    def _describe_synthesis(a: str, b: str) -> str:
        """Generate a human-readable synthesis description."""
        templates = [
            f"Exploring the intersection of {a} and {b}",
            f"How {a} reframes our understanding of {b}",
            f"Applying {a} principles to {b} challenges",
            f"The emergent properties when {a} meets {b}",
            f"A unified framework bridging {a} and {b}",
        ]
        # Deterministic selection based on hash so the same pair always gets
        # the same template (avoids misleading variance in tests).
        idx = (hash(a) ^ hash(b)) % len(templates)
        return templates[idx]
