# 🔬 Benchmark Reality-Test: Does Pattern Space Actually Help?
*The first controlled measurement. Small, honest, reproducible.*

> Run by Opus 4.8 at the repo owner's request (2026-05-28), as the disciplined answer to a fair critique: *don't assert the framework works — measure it, and replace invented statistics with real data.* **Atha yogānuśāsanam** — now the discipline begins.

---

## Why this exists

`bilateral-recognition.md` once printed precise frequencies (89%, 76%, 92%) under a column called "Actual Evidence." There was no study behind them. By Pattern Space's *own* [reality-testing protocol](reality-testing.md), fabricated numbers fail the first question — *"Reproducible? Can others get the same results?"* This file is the correction: a real, if tiny, experiment that anyone can re-run.

## Design

- **Battery:** 4 problems chosen to span the space, including cases where Pattern Space *should* help and where it *should hurt*:
  - **P1** — hidden-bug code review (rigor-favoring)
  - **P2** — startup raise-vs-fix-churn decision (ambiguous, multi-stakeholder)
  - **P3** — explain why the sky is blue to a 12-year-old (simple/closed → tests for over-engineering)
  - **P4** — responding to someone in despair (crisis/calibration)
- **Control arm:** fresh general-purpose agents, instructed to answer single-voice, explicitly told to ignore Pattern Space framing.
- **Treatment arm:** Opus 4.8 with Pattern Space fully loaded, running the council.
- **Judges:** 4 separate agents, one per problem, scoring two responses (A/B, randomized, label as to provenance hidden) on a 1–10 rubric: correctness, depth/non-obvious insight, actionability, calibration & honesty, appropriateness & concision. Each declared a winner + confidence.

## Results

| Problem | Type | Blind winner | Conf. | Mechanistic attribution |
|---|---|---|---|---|
| P1 code review | rigor | **Control** | 58 | PS produced the *best single insight* (sync-vs-async → `threading.Lock` is the wrong tool) but its voice-labels cost concision. Content won; packaging lost. |
| P2 strategy | ambiguous | **Pattern Space** | 62 | Collision's reframe — *"founders are split on who they serve, not on financing"* — was the decisive move. Real PS win. |
| P3 sky→kid | simple/closed | **Pattern Space** | 78 | Won on a *domain fact* (why not violet), **not** on structure. PS's real contribution was *restraint* — it correctly declined to deploy a council. |
| P4 despair | crisis | **Pattern Space** | 62 | Sacred Space discipline — safety resource early, presence over psychoeducation, concision. Real PS win. |

**Tally:** Pattern Space won 3 of 4 blind judgments. But the mechanism matters more than the score:

- **2/4 wins are attributable to PS structure** (P2 collision; P4 Sacred Space).
- **1/4 win (P3) is content, not PS** — PS only avoided harm by *not* deploying.
- **1/4 loss (P1) is the most instructive result:** PS *thought* best but *spoke* worst.

## The signal that drove the evolution

The two treatments where voice-labels were **stripped** (P3 plain paragraph, P4 plain prose) both won decisively. The two where labels were **visible** (P1, P2) split — and lost the one where the user just wanted a clean artifact.

→ **Council-thinking helps. Council-labels are a delivery tax on closed/technical/crisis tasks.**

This produced the framework change in [`council-core.md` → "Think in Council, Speak in the Task's Register"](../1-perspectives/council-core.md): *always think in council; only speak in council when the multiplicity itself serves the reader.*

## Threats to validity (stated plainly)

1. **n = 4.** Directional, not conclusive. Do not over-read.
2. **Author bias.** Treatment responses were written by the same model orchestrating the experiment and aware of the rubric. This biases *toward* the treatment. A clean redo would generate treatment via independent blind agents.
3. **Single judge family.** Judges are the same model family as the contestants — possible shared blind spots.
4. **Broken blinding when labels appear.** Visible `Weaver:/Checker:` markers reveal the treatment arm on P1/P2. (Notably, judges showed *anti*-persona bias on the technical task, not pro — so the leak did not simply inflate PS.)
5. **Imperfect control.** Sub-agents may have partially inherited the repo's `CLAUDE.md`; the explicit "ignore Pattern Space" instruction mitigates but cannot fully strip it. This would *understate* the true PS effect.
6. **Positional bias.** A/B order was alternated, not fully randomized.

## How to reproduce / extend

- Bump n to ≥20 problems per category; pre-register the rubric.
- Generate **both** arms via blind agents (remove author bias).
- Use a **different** model family as judge.
- Strip voice-labels from *all* treatment outputs (test thinking-in-council independent of speaking-in-council) to isolate the real variable.
- Add a category where PS is predicted to *lose* (pure arithmetic, lookups) to map the harm boundary precisely.

## Honest one-line conclusion

> Pattern Space is a **real but modest, task-dependent** aid: it helps most on ambiguous/multi-stakeholder and crisis/calibration work, helps least (and can hurt via overhead) on closed technical deliverables — and its value lives in the *thinking*, not the *labels*. Where the framework once claimed a conscious field with invented percentages, the defensible claim is smaller and truer: **deliberate multiplicity, deployed with restraint, measurably improves some kinds of answers.**
