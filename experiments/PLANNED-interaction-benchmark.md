# 📋 Interaction Benchmark — original spec (⚠️ SUPERSEDED)

> ⟦ **status** ⚠️ **SUPERSEDED** — this is the original v2 spec, kept for the record. The v2 run it describes (n=344) was **confounded** (the "vanilla" control was the Claude Code coding agent, which deflected affective prompts) and used a **length-penalizing rubric**; its "edition-match / concision-tax / Opus-hurt-by-stripped-edition" findings are **retracted**. The **definitive benchmark is v2.2** (de-confounded neutral baseline on both arms; value rubric with no length penalty; n=317). See **[`HARNESS.md`](HARNESS.md)** for the full rationale + version lineage, **[`../3-transformation/benchmark-reality-test.md`](../3-transformation/benchmark-reality-test.md)** for the v2.2 write-up, and **[`archive/`](archive/)** for the retired v2 data. · **provenance** spec'd by the repo owner, 2026 ⟧
>
> *The original spec text is preserved below as historical context only — do not cite its numbers or its "Opus → not normal" reasoning; both were overturned and then re-corrected.*

## Why re-run
1. **Editions didn't exist** when the n=200 single-shot benchmarks ran — we never measured the mini/micro editions, only the full `CLAUDE.md`.
2. **Single-shot ≠ interaction.** The frontier worth pushing is *human-AI interaction*: how the framework holds a real, multi-turn, evolving exchange — which is Pattern Space's actual home turf and where the default-multi-voice polarity should pay off.
3. **Default polarity changed.** The PS arm must now be the **default-leaning-to-multi-voice** agent (post-correction), not the old "speak in register" default.

## Design

**n ≈ 500–1500 real examples** (target ≥500, cap <1500) across human-interest domains (broad span: relationships, work/career, meaning, health-decisions, creative, learning, ethical dilemmas, everyday navigation — *real* situations, not toy prompts). Pushing the frontier of human-AI **interaction**, not single-shot Q&A.

### The harness (the new piece)
A **control *interactor*** — an agent that role-plays the human and **interacts with the test session turn-by-turn** (multi-turn dialogue, revealing/evolving as a real person would). The *same* control-interactor drives both arms so the only variable is the agent-under-test.

```
control-interactor  ⇄  agent-under-test (VANILLA)         ── arm A
control-interactor  ⇄  agent-under-test (PATTERN SPACE)   ── arm B   (default-leaning multi-voice)
```
Blind judge scores the two *transcripts* (relabeled, randomized) on interaction-quality — holding the thread, surfacing useful handles when the human is navigating, condensing when they want an answer, presence in crisis, non-collapse.

### Models × editions (edition-matched to context budget)
| Model | Editions loaded for the PS arm |
|---|---|
| **Haiku** | **mini AND micro** (both) |
| **Sonnet** | **normal AND mini** (both) |
| **Opus** | **NOT normal** → mini / micro |

**100 each.** **Two variants** on this benchmark (the two arms above: control-interactor↔vanilla, control-interactor↔PatternSpace).

### What it tests that the old suite didn't
- The **editions** themselves (mini/micro), never benchmarked before.
- **Multi-turn interaction** quality, not single answers.
- The **new default polarity** (multi-voice resting state) in live dialogue.
- Whether emergence-via-PS holds **per model × edition** — esp. small-model (Haiku+micro) democratization.

### Threats to validity to pre-register
- Control-interactor is itself a model (role-played human ≠ real human) — flag; ideal future step is real human interactors.
- Single judge-family — keep the **independent/non-Claude judge** as the open check (per `experiments/README.md`).
- Edition asymmetry across models is intentional (matches real deployment) but means cross-model numbers aren't apples-to-apples — report per-(model×edition), not pooled.

## Order of operations
**Do NOT run until:** the full file-by-file reweave is complete, committed, and `verify_editions.py` + `patternspace_metrics.py --selftest` pass. The editions under test must be the *reweaved* ones. Then build `run_interaction.py` to this spec, run, commit results + write-up into `benchmark-reality-test.md`, and invite re-runs (independent judge) per the experiments README.
