"""
Formal Layer Bridge — connects the godelOS symbolic layer to the
backend/core consciousness runtime.

The bridge lazily initialises the formal CognitiveEngine
(ThoughtStream + ReflectionEngine + MetacognitiveMonitor) from the
``godelOS.unified_agent_core.cognitive_engine`` package and exposes a
narrow API that the consciousness loop, phenomenal experience generator,
and backend metacognitive monitor can call.

If the godelOS package is not available (e.g. in a reduced deployment)
the bridge degrades gracefully to a no-op stub that returns neutral
defaults.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

_MAX_INSIGHTS_PER_REFLECTION = 3  # cap insights harvested per reflection
_SNAPSHOT_THOUGHT_LIMIT = 50       # cap thought retrieval for counting

# ---------- lazy import flag ---------------------------------------------------
_FORMAL_AVAILABLE = True
try:
    from godelOS.unified_agent_core.cognitive_engine.interfaces import (
        Thought,
        Reflection,
        CognitiveContext,
    )
    from godelOS.unified_agent_core.cognitive_engine.thought_stream import (
        ThoughtStream,
    )
    from godelOS.unified_agent_core.cognitive_engine.reflection_engine import (
        ReflectionEngine,
    )
    from godelOS.unified_agent_core.cognitive_engine.metacognitive_monitor import (
        MetacognitiveMonitor as FormalMetacognitiveMonitor,
    )
except ImportError:
    _FORMAL_AVAILABLE = False
    logger.warning(
        "godelOS formal layer not available — FormalLayerBridge will operate "
        "in stub mode"
    )


@dataclass
class FormalSnapshot:
    """Snapshot of metrics produced by the formal cognitive pipeline."""
    cognitive_load: float = 0.0            # [0, 1]
    attention_allocation: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    thought_count: int = 0
    reflection_count: int = 0
    latest_insights: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class FormalLayerBridge:
    """
    Thin adapter between the ``backend/core`` consciousness runtime and the
    fully-implemented formal symbolic layer in ``godelOS/``.

    Public API used by the consciousness loop:

    *  ``await submit_observation(text, priority, metadata)``
       – feeds a consciousness-loop observation into the formal
         ThoughtStream; returns the Thought id.
    *  ``await get_snapshot() -> FormalSnapshot``
       – returns the latest formal-layer metrics (cognitive load,
         attention, performance, insights).
    *  ``is_available`` – True when the godelOS package was imported.
    """

    def __init__(self) -> None:
        self.is_available: bool = _FORMAL_AVAILABLE
        self._thought_stream: Optional[Any] = None
        self._reflection_engine: Optional[Any] = None
        self._metacognitive_monitor: Optional[Any] = None
        self._initialised = False
        self._lock = asyncio.Lock()

    @property
    def is_initialized(self) -> bool:
        """Whether the formal layer components have been successfully created."""
        return self._initialised

    async def initialize(self) -> bool:
        """Create the formal-layer components. Safe to call repeatedly."""
        if self._initialised:
            return True
        if not self.is_available:
            logger.info("FormalLayerBridge: stub mode (godelOS not available)")
            return False
        async with self._lock:
            if self._initialised:
                return True
            try:
                self._thought_stream = ThoughtStream(
                    max_capacity=500,
                    forgetting_threshold=0.2,
                    retention_period=3600,
                )
                self._reflection_engine = ReflectionEngine()
                self._metacognitive_monitor = FormalMetacognitiveMonitor()
                self._initialised = True
                logger.info(
                    "✅ FormalLayerBridge initialised "
                    "(ThoughtStream + ReflectionEngine + MetacognitiveMonitor)"
                )
                return True
            except Exception as exc:
                logger.error(f"FormalLayerBridge init failed: {exc}")
                self.is_available = False
                return False

    # ── public API ────────────────────────────────────────────────────

    async def submit_observation(
        self,
        content: str,
        priority: float = 0.5,
        thought_type: str = "insight",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Submit a consciousness-loop observation as a ``Thought`` and
        trigger reflection + metacognitive update.

        Returns the Thought id, or ``None`` in stub mode.
        """
        if not self._initialised:
            return None
        try:
            thought = Thought(
                content=content,
                type=thought_type,
                priority=priority,
                metadata=metadata or {},
            )
            await self._thought_stream.add_thought(thought, priority=priority)

            # Build a lightweight cognitive context
            priority_thoughts = await self._thought_stream.get_priority_thoughts(
                max_thoughts=5
            )
            context = CognitiveContext(
                active_thoughts=[t.id for t in priority_thoughts],
                attention_focus=content[:80],
                cognitive_load=await self._metacognitive_monitor.get_cognitive_load(),
            )

            # Attempt reflection — the formal ReflectionEngine may raise
            # due to pre-existing nested-method bugs; tolerate gracefully.
            reflection = None
            try:
                reflection = await self._reflection_engine.reflect(thought, context)
            except Exception as exc:
                logger.debug(f"Reflection skipped (non-fatal): {exc}")

            # Update metacognitive monitor with the thought+reflection
            try:
                await self._metacognitive_monitor.update_state(
                    thought, reflection, context
                )
            except Exception as exc:
                logger.debug(f"Metacognitive update skipped (non-fatal): {exc}")

            return thought.id
        except Exception as exc:
            logger.warning(f"FormalLayerBridge.submit_observation failed: {exc}")
            return None

    async def get_snapshot(self) -> FormalSnapshot:
        """Return current formal-layer metrics as a ``FormalSnapshot``."""
        if not self._initialised:
            return FormalSnapshot()
        try:
            load = await self._metacognitive_monitor.get_cognitive_load()
            attention = await self._metacognitive_monitor.get_attention_allocation()
            summary = await self._metacognitive_monitor.get_cognitive_state_summary()

            # Collect insights from the most-recent reflections
            latest_insights: List[str] = []
            priority_thoughts = await self._thought_stream.get_priority_thoughts(
                max_thoughts=3
            )
            for t in priority_thoughts:
                reflections = await self._reflection_engine.get_reflections_for_thought(
                    t.id
                )
                for r in reflections[-1:]:
                    latest_insights.extend(r.insights[:_MAX_INSIGHTS_PER_REFLECTION])

            return FormalSnapshot(
                cognitive_load=load,
                attention_allocation=attention,
                performance_metrics=summary.get("performance_metrics", {}),
                thought_count=len(
                    await self._thought_stream.get_priority_thoughts(
                        max_thoughts=_SNAPSHOT_THOUGHT_LIMIT
                    )
                ),
                reflection_count=summary.get("reflections_created", 0),
                latest_insights=latest_insights[-5:],
            )
        except Exception as exc:
            logger.warning(f"FormalLayerBridge.get_snapshot failed: {exc}")
            return FormalSnapshot()
