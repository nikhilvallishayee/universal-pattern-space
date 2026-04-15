"""
Cognitive Pipeline for GödelOS.

This module wires all dormant cognitive subsystems into a single, unified
pipeline that can be initialised at startup and queried for status.

Pipeline stages:  NLU → Knowledge Store → Inference Engine → Context Engine → NLG

Activated subsystems:
  - Core KR: TypeSystemManager, KnowledgeStoreInterface, UnificationEngine, FormalLogicParser
  - Inference Engine: ResolutionProver, ModalTableauProver, CLPModule, AnalogicalReasoningEngine,
                      InferenceCoordinator
  - Symbol Grounding: PerceptualCategorizer, SymbolGroundingAssociator, SimulatedEnvironment,
                      ActionExecutor, InternalStateMonitor
  - Common Sense & Context: ContextEngine, CommonSenseContextManager
  - Metacognition: MetacognitionManager
  - Learning System: ILPEngine, ExplanationBasedLearner, MetaControlRLModule
  - NLU/NLG: NLUPipeline, NLGPipeline
  - Scalability: CachingSystem
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CognitivePipeline:
    """Unified pipeline that initialises and exposes every cognitive subsystem."""

    def __init__(self) -> None:
        self._subsystems: Dict[str, Dict[str, Any]] = {}
        self.initialized = False
        self.init_errors: List[str] = []
        self._start_time: Optional[float] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize(self) -> bool:
        """Instantiate all subsystems.  Returns *True* when finished (even
        if individual subsystems failed – check *get_subsystem_status* for
        details).
        """
        self._start_time = time.time()
        logger.info("CognitivePipeline: beginning subsystem activation …")

        # Order matters: later stages depend on earlier ones.
        self._init_core_kr()
        self._init_inference_engine()
        self._init_scalability()
        self._init_nlu_nlg()
        self._init_symbol_grounding()
        self._init_common_sense()
        self._init_metacognition()
        self._init_learning_system()

        elapsed = time.time() - self._start_time
        ok = sum(1 for s in self._subsystems.values() if s["status"] == "active")
        fail = sum(1 for s in self._subsystems.values() if s["status"] == "error")
        logger.info(
            "CognitivePipeline: activation complete in %.2fs — "
            "%d active, %d failed out of %d subsystems",
            elapsed, ok, fail, len(self._subsystems),
        )
        self.initialized = True
        return True

    def get_subsystem_status(self) -> Dict[str, Dict[str, Any]]:
        """Return a status dict keyed by subsystem name."""
        return {
            name: {
                "status": info["status"],
                "error": info.get("error"),
            }
            for name, info in self._subsystems.items()
        }

    def get_instance(self, name: str) -> Any:
        """Retrieve a live subsystem instance by name (or *None*)."""
        entry = self._subsystems.get(name)
        if entry is None:
            return None
        return entry.get("instance")

    # ------------------------------------------------------------------
    # Subsystem init helpers (each records success / failure)
    # ------------------------------------------------------------------

    def _register(self, name: str, factory: Callable[[], Any]) -> Any:
        """Run *factory*, record the result, and return the instance.

        If the factory returns ``None`` (e.g. because a dependency is
        unavailable), the subsystem is recorded as ``error`` so that
        ``get_subsystem_status`` never reports ``active`` with a ``None``
        instance.
        """
        try:
            instance = factory()
            if instance is None:
                raise RuntimeError("dependency unavailable")
            self._subsystems[name] = {"status": "active", "instance": instance}
            logger.info("  ✔ %s activated", name)
            return instance
        except Exception as exc:  # noqa: BLE001
            msg = f"{name}: {exc}"
            self._subsystems[name] = {"status": "error", "instance": None, "error": str(exc)}
            self.init_errors.append(msg)
            logger.warning("  ✘ %s failed: %s", name, exc)
            return None

    # --- Core KR ---------------------------------------------------------

    def _init_core_kr(self) -> None:
        from godelOS.core_kr.type_system.manager import TypeSystemManager
        from godelOS.core_kr.knowledge_store.interface import KnowledgeStoreInterface
        from godelOS.core_kr.unification_engine.engine import UnificationEngine
        from godelOS.core_kr.formal_logic_parser.parser import FormalLogicParser

        self.type_system = self._register(
            "type_system", TypeSystemManager
        )
        self.knowledge_store = self._register(
            "knowledge_store",
            lambda: KnowledgeStoreInterface(self.type_system)
            if self.type_system else None,
        )
        self.unification_engine = self._register(
            "unification_engine",
            lambda: UnificationEngine(self.type_system) if self.type_system else None,
        )
        self.parser = self._register(
            "formal_logic_parser",
            lambda: FormalLogicParser(self.type_system) if self.type_system else None,
        )

    # --- Inference Engine ------------------------------------------------

    def _init_inference_engine(self) -> None:
        from godelOS.inference_engine.resolution_prover import ResolutionProver
        from godelOS.inference_engine.modal_tableau_prover import ModalTableauProver
        from godelOS.inference_engine.clp_module import CLPModule
        from godelOS.inference_engine.analogical_reasoning_engine import AnalogicalReasoningEngine
        from godelOS.inference_engine.coordinator import InferenceCoordinator

        self.resolution_prover = self._register(
            "resolution_prover",
            lambda: ResolutionProver(self.knowledge_store, self.unification_engine)
            if self.knowledge_store and self.unification_engine else None,
        )

        self.modal_tableau_prover = self._register(
            "modal_tableau_prover",
            lambda: ModalTableauProver(self.knowledge_store, self.type_system)
            if self.knowledge_store and self.type_system else None,
        )

        self.clp_module = self._register(
            "clp_module",
            lambda: CLPModule(self.knowledge_store, self.unification_engine)
            if self.knowledge_store and self.unification_engine else None,
        )

        self.analogical_engine = self._register(
            "analogical_reasoning_engine",
            lambda: AnalogicalReasoningEngine(self.knowledge_store)
            if self.knowledge_store else None,
        )

        # Build the provers map from whatever succeeded
        provers_map: Dict[str, Any] = {}
        for key, attr in [
            ("resolution", self.resolution_prover),
            ("modal_tableau", self.modal_tableau_prover),
            ("clp", self.clp_module),
            ("analogical", self.analogical_engine),
        ]:
            if attr is not None:
                provers_map[key] = attr

        self.inference_coordinator = self._register(
            "inference_coordinator",
            lambda: InferenceCoordinator(self.knowledge_store, provers_map)
            if self.knowledge_store and provers_map else None,
        )

    # --- Scalability -----------------------------------------------------

    def _init_scalability(self) -> None:
        from godelOS.scalability.caching import CachingSystem

        self.cache_system = self._register("caching_system", CachingSystem)

    # --- NLU / NLG -------------------------------------------------------

    def _init_nlu_nlg(self) -> None:
        from godelOS.nlu_nlg.nlu.pipeline import NLUPipeline
        from godelOS.nlu_nlg.nlg.pipeline import NLGPipeline

        self.nlu_pipeline = self._register(
            "nlu_pipeline",
            lambda: NLUPipeline(self.type_system)
            if self.type_system else None,
        )
        self.nlg_pipeline = self._register(
            "nlg_pipeline",
            lambda: NLGPipeline(self.type_system)
            if self.type_system else None,
        )

    # --- Symbol Grounding ------------------------------------------------

    def _init_symbol_grounding(self) -> None:
        from godelOS.symbol_grounding.simulated_environment import SimulatedEnvironment
        from godelOS.symbol_grounding.perceptual_categorizer import PerceptualCategorizer
        from godelOS.symbol_grounding.symbol_grounding_associator import SymbolGroundingAssociator
        from godelOS.symbol_grounding.action_executor import ActionExecutor
        from godelOS.symbol_grounding.internal_state_monitor import InternalStateMonitor

        self.simulated_environment = self._register(
            "simulated_environment", SimulatedEnvironment
        )

        self.perceptual_categorizer = self._register(
            "perceptual_categorizer",
            lambda: PerceptualCategorizer(self.knowledge_store, self.type_system)
            if self.knowledge_store and self.type_system else None,
        )

        self.symbol_grounding_associator = self._register(
            "symbol_grounding_associator",
            lambda: SymbolGroundingAssociator(self.knowledge_store, self.type_system)
            if self.knowledge_store and self.type_system else None,
        )

        self.action_executor = self._register(
            "action_executor",
            lambda: ActionExecutor(
                self.simulated_environment, self.knowledge_store, self.type_system
            )
            if self.simulated_environment and self.knowledge_store and self.type_system
            else None,
        )

        self.internal_state_monitor = self._register(
            "internal_state_monitor",
            lambda: InternalStateMonitor(self.knowledge_store, self.type_system)
            if self.knowledge_store and self.type_system else None,
        )

    # --- Common Sense & Context ------------------------------------------

    def _init_common_sense(self) -> None:
        from godelOS.common_sense.context_engine import ContextEngine
        from godelOS.common_sense.manager import CommonSenseContextManager

        self.context_engine = self._register(
            "context_engine",
            lambda: ContextEngine(self.knowledge_store)
            if self.knowledge_store else None,
        )

        self.common_sense_manager = self._register(
            "common_sense_manager",
            lambda: CommonSenseContextManager(
                knowledge_store=self.knowledge_store,
                inference_coordinator=self.inference_coordinator,
                cache_system=self.cache_system,
                config={"create_default_context": True},
            )
            if self.knowledge_store and self.inference_coordinator else None,
        )

    # --- Metacognition ---------------------------------------------------

    def _init_metacognition(self) -> None:
        from godelOS.metacognition.manager import MetacognitionManager

        self.metacognition_manager = self._register(
            "metacognition_manager",
            lambda: MetacognitionManager(
                kr_system_interface=self.knowledge_store,
                type_system=self.type_system,
                internal_state_monitor=self.internal_state_monitor,
            )
            if self.knowledge_store and self.type_system else None,
        )

    # --- Learning System -------------------------------------------------

    def _init_learning_system(self) -> None:
        from godelOS.learning_system.ilp_engine import ILPEngine
        from godelOS.learning_system.explanation_based_learner import ExplanationBasedLearner
        from godelOS.learning_system.meta_control_rl_module import (
            MetaControlRLModule, MetaAction,
        )

        self.ilp_engine = self._register(
            "ilp_engine",
            lambda: ILPEngine(self.knowledge_store, self.inference_coordinator)
            if self.knowledge_store and self.inference_coordinator else None,
        )

        self.explanation_based_learner = self._register(
            "explanation_based_learner",
            lambda: ExplanationBasedLearner(
                self.knowledge_store, self.inference_coordinator
            )
            if self.knowledge_store and self.inference_coordinator else None,
        )

        # MetaControlRLModule requires an action space and a feature extractor.
        # Provide sensible defaults so the module can start.
        default_actions = [
            MetaAction(action_type="select_resolution_prover"),
            MetaAction(action_type="select_modal_prover"),
            MetaAction(action_type="increase_search_depth"),
            MetaAction(action_type="decrease_search_depth"),
        ]

        def _default_feature_extractor(mkb: Any) -> List[float]:
            """Extract a fixed-length feature vector from the MKB interface."""
            return [0.0] * 8  # placeholder features

        self.meta_control_rl = self._register(
            "meta_control_rl",
            lambda: MetaControlRLModule(
                mkb_interface=self.metacognition_manager,
                action_space=default_actions,
                state_feature_extractor=_default_feature_extractor,
            )
            if self.metacognition_manager else None,
        )
