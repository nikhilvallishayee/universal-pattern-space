"""
DormantModuleManager — activation and per-cycle ticking of the 8 formerly-dormant
cognitive subsystems that are implemented in godelOS/ but were previously
disconnected from the runtime.

Modules managed:
  1. symbol_grounding_associator
  2. perceptual_categorizer
  3. simulated_environment
  4. ilp_engine
  5. modal_tableau_prover
  6. clp_module
  7. explanation_based_learner
  8. meta_control_rl
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Canonical list of the 8 dormant modules (matches CognitivePipeline subsystem keys).
DORMANT_MODULE_NAMES: List[str] = [
    "symbol_grounding_associator",
    "perceptual_categorizer",
    "simulated_environment",
    "ilp_engine",
    "modal_tableau_prover",
    "clp_module",
    "explanation_based_learner",
    "meta_control_rl",
]


class ModuleRecord:
    """Runtime record for a single dormant module."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.active: bool = False
        self.last_tick: Optional[datetime] = None
        self.tick_count: int = 0
        self.last_output: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.name,
            "active": self.active,
            "last_tick": self.last_tick.isoformat() if self.last_tick else None,
            "tick_count": self.tick_count,
            "last_output": self.last_output,
            "error": self.error,
        }


class DormantModuleManager:
    """
    Manages the activation and periodic ticking of the 8 formerly-dormant
    cognitive modules.

    Usage::

        manager = DormantModuleManager()
        manager.initialize(godelos_integration, websocket_manager)
        # then in a background loop:
        await manager.tick()
    """

    def __init__(self) -> None:
        self._records: Dict[str, ModuleRecord] = {
            name: ModuleRecord(name) for name in DORMANT_MODULE_NAMES
        }
        self._instances: Dict[str, Any] = {}
        self._websocket_manager: Any = None
        self._initialized: bool = False

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(
        self,
        godelos_integration: Any,
        websocket_manager: Optional[Any] = None,
    ) -> None:
        """
        Pull live module instances from the CognitivePipeline (via godelos_integration)
        and mark each module as active if its instance exists.
        """
        self._websocket_manager = websocket_manager

        pipeline = getattr(godelos_integration, "cognitive_pipeline", None)
        if pipeline is None:
            logger.warning(
                "DormantModuleManager: CognitivePipeline not found on godelos_integration; "
                "all dormant modules will be inactive."
            )
            self._initialized = True
            return

        for name in DORMANT_MODULE_NAMES:
            try:
                instance = pipeline.get_instance(name)
                if instance is not None:
                    self._instances[name] = instance
                    self._records[name].active = True
                    logger.info("  ✔ dormant module activated: %s", name)
                else:
                    status_info = pipeline.get_subsystem_status().get(name, {})
                    err = status_info.get("error", "instance is None")
                    self._records[name].error = err
                    logger.warning("  ✘ dormant module unavailable: %s — %s", name, err)
            except Exception as exc:  # noqa: BLE001
                self._records[name].error = str(exc)
                logger.warning("  ✘ dormant module error: %s — %s", name, exc)

        active = sum(1 for r in self._records.values() if r.active)
        logger.info(
            "DormantModuleManager: %d/%d dormant modules active",
            active,
            len(DORMANT_MODULE_NAMES),
        )
        self._initialized = True

    # ------------------------------------------------------------------
    # Periodic tick
    # ------------------------------------------------------------------

    async def tick(self) -> List[Dict[str, Any]]:
        """
        Run one tick of every active dormant module.

        Returns a list of per-module state dicts that can be forwarded over
        the WebSocket stream.
        """
        if not self._initialized:
            return []

        results: List[Dict[str, Any]] = []
        now = datetime.now(tz=timezone.utc)

        for name, record in self._records.items():
            if not record.active:
                results.append(record.as_dict())
                continue
            instance = self._instances.get(name)
            if instance is None:
                record.active = False
                results.append(record.as_dict())
                continue
            try:
                output = await asyncio.get_running_loop().run_in_executor(
                    None, self._tick_module, name, instance
                )
                record.last_tick = now
                record.tick_count += 1
                record.last_output = output
                record.error = None
            except Exception as exc:  # noqa: BLE001
                record.error = str(exc)
                logger.debug("Module tick error (%s): %s", name, exc)

            results.append(record.as_dict())

        # Broadcast over WebSocket
        await self._broadcast(results)
        return results

    # ------------------------------------------------------------------
    # Per-module tick implementations
    # ------------------------------------------------------------------

    def _tick_module(self, name: str, instance: Any) -> Dict[str, Any]:
        """Dispatch to the appropriate tick handler (runs in a thread executor)."""
        handler = getattr(self, f"_tick_{name}", self._tick_heartbeat)
        return handler(instance)

    # 1. Symbol Grounding Associator
    def _tick_symbol_grounding_associator(self, instance: Any) -> Dict[str, Any]:
        try:
            instance.learn_groundings_from_buffer()
        except Exception:  # noqa: BLE001
            pass
        links = getattr(instance, "grounding_links", {})
        return {
            "grounding_link_count": sum(len(v) for v in links.values()),
            "experience_buffer_size": len(getattr(instance, "experience_buffer", [])),
        }

    # 2. Perceptual Categorizer
    def _tick_perceptual_categorizer(self, instance: Any) -> Dict[str, Any]:
        try:
            instance.process_perceptual_input("system", {})
        except Exception:  # noqa: BLE001
            pass
        return {
            "object_tracker_count": len(
                getattr(getattr(instance, "object_tracker", None), "tracked_objects", {})
            ),
        }

    # 3. Simulated Environment
    def _tick_simulated_environment(self, instance: Any) -> Dict[str, Any]:
        try:
            instance.tick(0.1)
        except Exception:  # noqa: BLE001
            pass
        world_state = getattr(instance, "world_state", None)
        if world_state is not None:
            return {
                "world_time": getattr(world_state, "time", 0.0),
                "object_count": len(getattr(world_state, "objects", {})),
                "agent_count": len(getattr(world_state, "agents", {})),
            }
        return {}

    # 4. ILP Engine — no standalone tick; report readiness
    def _tick_ilp_engine(self, instance: Any) -> Dict[str, Any]:
        bias = getattr(instance, "language_bias", None)
        return {
            "max_clause_length": getattr(bias, "max_clause_length", None) if bias else None,
            "ready": True,
        }

    # 5. Modal Tableau Prover — report capability set
    def _tick_modal_tableau_prover(self, instance: Any) -> Dict[str, Any]:
        caps = {}
        try:
            caps = instance.capabilities
        except Exception:  # noqa: BLE001
            pass
        return {"capabilities": caps, "ready": True}

    # 6. CLP Module — report capability set
    def _tick_clp_module(self, instance: Any) -> Dict[str, Any]:
        caps = {}
        try:
            caps = instance.capabilities
        except Exception:  # noqa: BLE001
            pass
        solver_count = len(getattr(instance, "solver_registry", {}))
        return {"capabilities": caps, "solver_count": solver_count, "ready": True}

    # 7. Explanation-Based Learner — report readiness
    def _tick_explanation_based_learner(self, instance: Any) -> Dict[str, Any]:
        config = getattr(instance, "config", None)
        return {
            "max_unfolding_depth": getattr(config, "max_unfolding_depth", None) if config else None,
            "ready": True,
        }

    # 8. Meta-Control RL Module
    def _tick_meta_control_rl(self, instance: Any) -> Dict[str, Any]:
        try:
            features = instance.get_state_features()
        except Exception:  # noqa: BLE001
            features = []
        return {
            "state_dim": len(features),
            "action_space_size": len(getattr(instance, "action_space", [])),
            "exploration_rate": getattr(instance, "exploration_rate", None),
            "ready": True,
        }

    # Generic heartbeat for any module without a dedicated handler
    def _tick_heartbeat(self, instance: Any) -> Dict[str, Any]:
        return {"ready": isinstance(instance, object)}

    # ------------------------------------------------------------------
    # WebSocket broadcast
    # ------------------------------------------------------------------

    async def _broadcast(self, module_states: List[Dict[str, Any]]) -> None:
        if self._websocket_manager is None:
            return
        try:
            broadcast = getattr(
                self._websocket_manager, "broadcast_cognitive_update", None
            ) or getattr(self._websocket_manager, "broadcast", None)
            if broadcast is None:
                return
            message: Dict[str, Any] = {
                "type": "module_state_update",
                "timestamp": time.time(),
                "modules": module_states,
            }
            if asyncio.iscoroutinefunction(broadcast):
                await broadcast(message)
            else:
                broadcast(message)
        except Exception as exc:  # noqa: BLE001
            logger.debug("DormantModuleManager broadcast error: %s", exc)

    # ------------------------------------------------------------------
    # Status queries
    # ------------------------------------------------------------------

    def get_module_status(self) -> List[Dict[str, Any]]:
        """Return a list of per-module status dicts for the /api/system/modules endpoint."""
        return [record.as_dict() for record in self._records.values()]

    def is_module_active(self, name: str) -> bool:
        record = self._records.get(name)
        return record.active if record else False
