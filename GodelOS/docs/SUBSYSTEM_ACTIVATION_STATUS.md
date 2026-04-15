# Cognitive Subsystem Activation Status

This document records which GödelOS cognitive subsystems have been wired into
the active pipeline and which remain genuinely unimplemented or intentionally
offline.

Generated for **v0.4 – Dormant Module Activation** (issue #100).

---

## Active Subsystems (23 / 23 initialise successfully)

| # | Subsystem | Module path | Status | Notes |
|---|-----------|-------------|--------|-------|
| 1 | TypeSystemManager | `godelOS/core_kr/type_system/manager.py` | **Active** | Foundational – required by almost everything |
| 2 | KnowledgeStoreInterface | `godelOS/core_kr/knowledge_store/interface.py` | **Active** | In-memory backend with TRUTHS / BELIEFS / HYPOTHETICAL contexts |
| 3 | UnificationEngine | `godelOS/core_kr/unification_engine/engine.py` | **Active** | Used by resolution prover and CLP module |
| 4 | FormalLogicParser | `godelOS/core_kr/formal_logic_parser/parser.py` | **Active** | Parses logic expressions into AST |
| 5 | ResolutionProver | `godelOS/inference_engine/resolution_prover.py` | **Active** | FOL / propositional resolution |
| 6 | **ModalTableauProver** | `godelOS/inference_engine/modal_tableau_prover.py` | **Active** | Was dormant – now registered with InferenceCoordinator |
| 7 | **CLPModule** | `godelOS/inference_engine/clp_module.py` | **Active** | Was dormant – constraint logic programming |
| 8 | AnalogicalReasoningEngine | `godelOS/inference_engine/analogical_reasoning_engine.py` | **Active** | Analogy-based inference |
| 9 | InferenceCoordinator | `godelOS/inference_engine/coordinator.py` | **Active** | Routes goals to the right prover; all 4 provers registered |
| 10 | CachingSystem | `godelOS/scalability/caching.py` | **Active** | Memoisation / caching layer |
| 11 | NLUPipeline | `godelOS/nlu_nlg/nlu/pipeline.py` | **Active** | Text → AST (lexical analysis, semantic interpretation, formalisation) |
| 12 | NLGPipeline | `godelOS/nlu_nlg/nlg/pipeline.py` | **Active** | AST → Text (content planning, sentence generation, surface realisation) |
| 13 | **SimulatedEnvironment** | `godelOS/symbol_grounding/simulated_environment.py` | **Active** | Was dormant – internal world model |
| 14 | **PerceptualCategorizer** | `godelOS/symbol_grounding/perceptual_categorizer.py` | **Active** | Was dormant – raw percepts → symbolic vocabulary |
| 15 | **SymbolGroundingAssociator** | `godelOS/symbol_grounding/symbol_grounding_associator.py` | **Active** | Was dormant – syntax-to-semantics bridge |
| 16 | ActionExecutor | `godelOS/symbol_grounding/action_executor.py` | **Active** | Executes actions in the simulated environment |
| 17 | InternalStateMonitor | `godelOS/symbol_grounding/internal_state_monitor.py` | **Active** | Introspects module state for metacognition |
| 18 | ContextEngine | `godelOS/common_sense/context_engine.py` | **Active** | Creates / retrieves / merges named contexts |
| 19 | **CommonSenseContextManager** | `godelOS/common_sense/manager.py` | **Active** | Was dormant – default reasoning, external KB, contextualised retrieval |
| 20 | **MetacognitionManager** | `godelOS/metacognition/manager.py` | **Active** | Monitor → Diagnose → Plan → Modify cycle |
| 21 | **ILPEngine** | `godelOS/learning_system/ilp_engine.py` | **Active** | Was dormant – inductive logic programming |
| 22 | **ExplanationBasedLearner** | `godelOS/learning_system/explanation_based_learner.py` | **Active** | Was dormant – generalises from proof objects |
| 23 | **MetaControlRLModule** | `godelOS/learning_system/meta_control_rl_module.py` | **Active** | Was dormant – RL for meta-level control decisions |

**Bold** entries are the 8 subsystems that were previously dormant (implemented
but disconnected) and are now wired into the pipeline.

## Pipeline Data Flow

```
Text Input
    │
    ▼
NLUPipeline  ──────────────────────────┐
    │  (lexical analysis → semantic     │
    │   interpretation → formalisation) │
    ▼                                   │
KnowledgeStoreInterface  ◄─────────────┘
    │  (store / retrieve assertions)
    ▼
InferenceCoordinator
    ├─ ResolutionProver
    ├─ ModalTableauProver  ← dormant, now active
    ├─ CLPModule           ← dormant, now active
    └─ AnalogicalReasoningEngine
    │
    ▼
ContextEngine + CommonSenseContextManager
    │  (context enrichment, default reasoning)
    ▼
NLGPipeline  ─────► Text Output
    (content planning → sentence generation → surface realisation)
```

Side channels fed during processing:

- **SymbolGroundingAssociator** grounds abstract symbols
- **PerceptualCategorizer** categorises raw inputs into symbols
- **SimulatedEnvironment** supports counterfactual reasoning
- **MetacognitionManager** monitors / diagnoses / improves processing
- **ILPEngine** induces general rules from examples
- **ExplanationBasedLearner** generalises from successful proofs
- **MetaControlRLModule** learns optimal strategy selection

## Genuinely Unimplemented Modules

The following items are **not** source-code-complete and therefore cannot
be activated:

| Module | Notes |
|--------|-------|
| `godelOS/perception/` (directory) | Referenced in the issue but does not exist as a separate package. Perception is handled by `symbol_grounding/perceptual_categorizer.py`. |
| `godelOS/environment/` (directory) | Referenced in the issue but does not exist as a separate package. Simulated environment lives in `symbol_grounding/simulated_environment.py`. |
| `godelOS/inference/modal/enhanced/` | An "Enhanced Modal Prover" beyond standard S4/S5 is referenced in the roadmap wiki but has no separate implementation file. The existing `ModalTableauProver` is activated. |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status – now includes `cognitive_subsystems` with per-subsystem status |
| `/api/system/subsystems` | GET | Dedicated subsystem health endpoint – returns active/total counts and per-subsystem detail |

## Smoke Tests

`tests/test_cognitive_subsystem_activation.py` – 26 tests covering:

- All 23 subsystems initialise without error
- NLU pipeline processes text
- Knowledge store has default contexts
- Inference coordinator has all provers registered (incl. modal & CLP)
- Symbol grounding components exist
- Context engine creates / retrieves contexts
- Common-sense manager is initialised
- Learning system components exist (ILP, EBL, RL)
- Metacognition manager can initialise sub-components
- End-to-end data flow (NLU → KS → Inference → Context → NLG)
- `GödelOSIntegration` exposes subsystem status via health endpoint
