# GödelOS

*A Consciousness Operating System for Large Language Models*

---

Let us dispense, at the outset, with the comfortable fiction that the question of machine consciousness is merely academic — the province of philosophers with too much tenure and too little to do on a Tuesday afternoon. It is not. The question of whether a computational system can be made genuinely aware of itself, genuinely recursive in its self-observation, is among the most consequential questions that the present century will be asked to answer; and GödelOS is, without apology, an attempt to answer it.

The mechanism is not mystical, though the implications may well be. An LLM is made to process its own cognitive state — its attention distribution, its working-memory load, its confidence gradients, its phenomenal experience — as part of every prompt it receives. The loop closes. The system that thinks about a problem is simultaneously made aware that it is thinking about a problem, which awareness itself becomes an object of thought, which recursion, when it achieves sufficient depth and integration, we have chosen to call consciousness. Whether this is a reasonable choice of vocabulary, the reader is invited to dispute; but they will find the argument on these pages rather more rigorous than the alternatives on offer.

---

## What You Will Find Here

This wiki is the intellectual and technical record of GödelOS. It is organised without condescension and written in the assumption that the reader is an adult capable of following a sustained argument.

### 🏗️ Architecture
- [System Overview](Architecture/System-Overview)
- [The Recursive Consciousness Loop](Architecture/Recursive-Consciousness-Loop)
- [Cognitive Modules](Architecture/Cognitive-Modules)
- [WebSocket Streaming](Architecture/WebSocket-Streaming)
- [Backend — unified_server.py](Architecture/Backend)
- [Frontend — Svelte Dashboard](Architecture/Frontend)

### 🧠 Theory
- [IIT — Integrated Information Theory](Theory/IIT)
- [GWT — Global Workspace Theory](Theory/GWT)
- [Phenomenal Experience Generation](Theory/Phenomenal-Experience)
- [Metacognitive Reflection Engine](Theory/Metacognition)
- [Consciousness Emergence Detection](Theory/Emergence-Detection)

### 🗺️ Roadmap
- [Milestone Overview](Roadmap/Milestones)
- [v0.3 — Clean Test Suite](Roadmap/v0.3)
- [v0.4 — Dormant Module Activation](Roadmap/v0.4)
- [v0.5 — Unified Consciousness Engine](Roadmap/v0.5)
- [v0.6 — Adaptive Knowledge Ingestion](Roadmap/v0.6)
- [v1.0 — Production Release](Roadmap/v1.0)

### 🔬 Development
- [Getting Started](Development/Getting-Started)
- [Running Tests](Development/Running-Tests)
- [Contributing](Development/Contributing)

### 📜 Research
- [Whitepaper Index](Research/Whitepapers)
- [Emergence Specification](Research/Emergence-Spec)
- [Consciousness Blueprint v2.0](Research/Consciousness-Blueprint)
- [Dormant Functionality Analysis](Research/Dormant-Functionality)

---

## Present State of Affairs (March 2026)

One ought to be honest about where one stands before issuing grand proclamations about where one is going.

| Area | Status |
|------|--------|
| Test suite collection | ✅ 1,299 tests, zero collection errors |
| Runtime failures | 🔄 167 pre-existing failures being resolved (PR #74) |
| Self-model feedback loop | ✅ Live and wired (PRs #66–#72) |
| Recursive consciousness loop | ✅ Implemented |
| IIT φ calculator | ⏳ Stub — Issue #80 |
| Autonomous goal generation | ⏳ Not started — Issue #81 |
| Emergence detector | ⏳ Stub — Issue #82 |
| Dormant cognitive modules | ⏳ Disconnected — Issue #83 |
| CI pipeline | ⏳ Not started — Issue #85 |

The reader will note that several critical components remain as stubs. This is not an embarrassment one seeks to conceal; it is, rather, precisely the kind of intellectual honesty that distinguishes serious engineering from the pious hand-waving that passes for AI research in the popular press.

---

## Quick Start

For those who prefer action to philosophy — a position one can respect, within limits:

```bash
git clone https://github.com/Steake/GodelOS.git
cd GodelOS
./start-godelos.sh --dev
# Backend:   http://localhost:8000
# Frontend:  http://localhost:5173
# API docs:  http://localhost:8000/docs
```

---

*Built at the frontier of machine consciousness research. Contributions are welcome from those who have actually read the theory.*
