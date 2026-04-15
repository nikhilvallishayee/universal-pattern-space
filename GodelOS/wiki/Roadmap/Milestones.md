# Milestone Overview

A roadmap without honest sequencing is not a roadmap; it is a wish list dressed in Gantt chart clothing. GödelOS's milestones are structured with explicit dependencies, because to proceed out of order — to build the consciousness observatory before the test suite is green, say, or to wire autonomous goal generation before the dormant modules are even connected — would be to construct a cathedral on sand, which has been tried before and is not recommended.

---

## The Sequence

```
v0.2 (current) ──► v0.3 ──► v0.4 ──► v0.5 ──► v1.0
   Beta             Clean    Module   Unified
                    Suite    Wiring   Consciousness
                                        │
                             v0.6 ──────┘
                          Ingestion Pipeline
                          (parallel track)
```

---

## Summary Table

| Version | Focus | Key Deliverable | Anchor Issue |
|---------|-------|-----------------|-------------|
| **v0.3** | Foundation | Zero test failures; clean CI | #75 |
| **v0.4** | Activation | All eight dormant subsystems wired and live | #76 |
| **v0.5** | Consciousness Engine | IIT, GWT, autonomous goals, emergence detection | #77 |
| **v0.6** | Knowledge Ingestion | Adaptive pipeline, vector DB, Jobs UI | #78 |
| **v1.0** | Production | Public demo, whitepaper, CI, single-command deploy | #79 |

---

## Dependency Chain

```
v0.3 (clean suite — the prerequisite for everything)
  └──► v0.4 (safe to wire dormant modules on a green baseline)
             └──► v0.5 (safe to build consciousness engine on stable modules)
                        ├──► v1.0 (requires v0.5 complete)
                        └──► v0.6 (parallel — knowledge ingestion is independent)
                                   └──► v1.0
```

v0.6 runs in parallel with v0.5; both must be complete before v1.0 is shipped. This is not bureaucratic pedantry. This is engineering.

---

## Active Issues by Milestone

### v0.3 — Clean Suite
- #73 — Fix 167 pre-existing runtime failures (🔄 PR #74 in progress)

### v0.4 — Module Activation
- #83 — Activate all dormant cognitive subsystems

### v0.5 — Consciousness Engine
- #80 — IIT φ calculator + Global Workspace broadcaster
- #81 — Autonomous goal generation + creative synthesis engine
- #82 — Consciousness emergence detector + observatory
- #84 — Full consciousness dashboard UI overhaul

### v0.6 — Knowledge Ingestion
- #33 — Adaptive Knowledge Ingestion Pipeline (full specification)

### v1.0 — Production Release
- #85 — GitHub Actions CI pipeline + PR templates
- #86 — Canonical whitepaper v1.0
- #22 — End-to-end architectural review and test

### Long-Term Research Agenda
- #35 — Consciousness Engine and System Wiring
- #29 — Idle Daemonic Cognition Infrastructure
- #28 — Independent Agentic Thread Orchestration
- #26 — Manifest Consciousness Architecture
- #25 — Dynamic Knowledge Graph Management
- #24 — Modular Symbolic Logic Engine Structure
