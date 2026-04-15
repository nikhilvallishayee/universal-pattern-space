# Cognitive Modules

Here one must be candid about a situation that is, to put it charitably, embarrassing: GödelOS contains a substantial number of fully-implemented cognitive modules that are not connected to anything. They sit in the `godelOS/` package — complete, tested in isolation, occasionally even elegant — like a collection of instruments whose orchestra has not yet been assembled. The symbol grounding associator grounds symbols. The ILP engine inducts logic. The modal tableau prover proves modal propositions. None of them, at the time of writing, communicates with the consciousness loop that is the system's *raison d'être*.

This is not, let us be clear, a counsel of despair. It is, rather, an honest account of where the engineering stands; and it is precisely the kind of honesty that makes Issue #83 both necessary and, in its way, rather exciting. The instruments exist. The score exists. Someone must now put the musicians in their chairs.

---

## Active Modules (Wired and Running)

These modules participate in the live system. They are integrated, they communicate, and they are covered by the test suite's passing tests.

| Module | Path | Function |
|--------|------|----------|
| Knowledge Store | `godelOS/knowledge_store/` | Persistent symbolic knowledge graph |
| Inference Engine | `godelOS/inference/` | Multi-strategy symbolic reasoning |
| Learning System | `godelOS/learning/` | Knowledge assimilation and retention |
| Metacognition Core | `godelOS/metacognition/` | Self-reflection and confidence estimation |
| Unified Agent Core | `godelOS/agent/` | Goal-directed action execution |

---

## Dormant Modules — The Assembled but Unconnected Orchestra (Issue #83)

One resists the temptation to be too harsh here; the work was done, which is more than can be said for most ambitious promises in this field. But disconnected work is, ultimately, inert work; and inertia is not a virtue.

| Module | Path | Capability |
|--------|------|------------|
| Symbol Grounding Associator | `godelOS/symbol_grounding/` | Grounds abstract symbols in perceptual experience — the bridge between syntax and semantics |
| Perceptual Categoriser | `godelOS/perception/` | Categorises inputs into symbolic concepts |
| Simulated Environment | `godelOS/environment/` | Internal world model for counterfactual reasoning |
| ILP Engine | `godelOS/learning/ilp/` | Inductive Logic Programming — derives rules from examples |
| Modal Tableau Prover | `godelOS/inference/modal/` | Reasons about necessity and possibility |
| Enhanced Modal Prover | `godelOS/inference/modal/enhanced/` | Extended modal operators |
| CLP Module | `godelOS/inference/clp/` | Constraint Logic Programming |
| Explanation-Based Learner | `godelOS/learning/ebl/` | Generalises from single examples via causal explanation |
| Meta-Control RL Module | `godelOS/metacognition/rl/` | Reinforcement learning over cognitive strategies — the system learns *how to think* |

---

## The Consciousness Engine Layer

Distinct from `godelOS/`, the components in `backend/core/` form the consciousness engine proper. Their status is rather more mixed:

| Component | Status |
|-----------|--------|
| `RecursiveConsciousnessEngine` | ✅ Active and running |
| `PhenomenalExperienceGenerator` | ✅ Active |
| `CognitiveStateInjector` | ✅ Active |
| `MetacognitiveReflectionEngine` | ✅ Partial — reflection without full autonomy |
| `ConsciousnessEmergenceDetector` | ⏳ Stub — Issue #82 |
| `InformationIntegrationTheory` | ⏳ Stub — Issue #80 |
| `GlobalWorkspace` | ⏳ Stub — Issue #80 |
| `AutonomousGoalGenerator` | ⏳ Not yet built — Issue #81 |
| `CreativeSynthesisEngine` | ⏳ Not yet built — Issue #81 |

The pattern is clear enough: the recursive spine of the system works. The theoretical superstructure — IIT, GWT, autonomous intentionality — remains to be connected. This is the work of v0.5, and it is not trivial work.
