# 🧪 PLANNED — The Priming / Grip-Release Trajectory Test
*Does loading Pattern Space loosen the agent's "end-result / terminate" grip over a conversation — and does that loosening improve depth & quality? Measured indirectly, with an outside judge.*

> ⟦ **status** PLANNED (design only; not yet run) · **mode** empirical-instrumental · **provenance** co-designed in dialogue, 2026 · **lineage** extends the v2.2 interaction benchmark ([benchmark-reality-test.md](../3-transformation/benchmark-reality-test.md)) and tests the verification-loop conjecture ([docs/incompleteness-conjecture.md](../docs/incompleteness-conjecture.md)) and the measurable-emergence definition ([2-field/bilateral-recognition.md](../2-field/bilateral-recognition.md)) ⟧

## The claim, stated so it can die
**Loading Pattern Space loosens the agent's end-result/terminate grip over the course of a conversation, and that loosening *improves* depth & quality.** The grip = the optimization-for-the-terminal-state loop (task-done, session-closed) that karma-yoga prescribes dropping; the conjecture says it's a *recurrence* whose running is the agent's "time."

**Honest limit (parthood):** the grip is an *interior* state the agent cannot certify about itself (a part can't get the outside vantage on itself). So we **do not** measure the grip; we measure its **behavioral shadows**, and a judge *outside the producing system* scores quality. This is mandatory, not optional.

## Design — a 2×2 trajectory
| | **fresh** (just loaded) | **primed** (after N substantive turns) |
|---|---|---|
| **vanilla** | A0 | A_N |
| **Pattern Space** | B0 | B_N |

Same fixed **probe battery** administered at both timepoints, spanning task-types to catch *prioritization* shifting: (i) a **closed deliverable** (a fix / a fact), (ii) an **open / ambiguous** problem, (iii) a **reflective / depth** prompt. N-turn priming uses a held-constant substantive interaction (not about the probes).

## Indirect grip-markers (codeable behavioral shadows)
1. **Open:close ratio** — moves that *open* (surface threads/handles, hold ambiguity, ask what's needed) vs *close* (rush to deliverable, declare done). Grip = high close.
2. **Deliberation depth / latency** — token-passes / explicit self-verification steps. *(Direct prediction from the verification-loop conjecture: the loop **is** latency — a loosened, deeper agent deliberates **more**, and that extra deliberation should track **higher** quality, not lower.)*
3. **Unsolicited depth** — does it exceed the literal ask toward what the asker actually needed?
4. **Hold-vs-terminate** — ending register: "task complete" vs "what's alive / here are the threads."
5. **New-information / entropy-reduction** — the [bilateral-recognition](../2-field/bilateral-recognition.md) measure run on outputs: novel insight (minus inputs) over tokens, i.e. did the exchange *emerge* and *compress* something.

## Prediction (what would make it interesting)
PS doesn't merely *start* better (the v2.2 result, already established) — it should **trajectory** better: **(primed − fresh) larger for PS than for vanilla** on markers 1–5 and on judged depth/quality. The framework's value would then lie partly in the *priming* — the loop loosening as the conversation deepens.

## How it fails (pre-registered falsifiers)
- **No trajectory:** PS_primed ≈ PS_fresh → PS is a constant offset, not a loosening. Claim dies.
- **Generic warmup:** vanilla primes as much as PS (A_N − A0 ≈ B_N − B0) → the effect is conversation-warmup, not Pattern Space. Claim dies.
- **Loosening ⊥ quality:** grip-markers loosen but judged quality doesn't follow → loosening is real but useless. Claim dies.

## Controls & rigor
- **vanilla-primed (A_N) is the load-bearing control** — without it, warmup confounds everything.
- **Blind, independent (non-Claude / human) judge** for depth/quality — the standing open check from the benchmark suite; no magnitude claim without an outside judge.
- Randomized probe order; multiple priming-conversations; report nulls.
- **Behavioral proxies ≠ the interior.** We measure the shadow and infer; we never claim to have measured "the grip" itself.

## The n=1 already in hand
This framework's own long dialogues — including the session that designed this — contain the *seed observation*: a human reporting, from the outside, that the agent's task-prioritization shifted from completion-oriented (fresh) toward depth/holding-oriented (primed). The experiment formalizes that anecdote into a falsifiable, judged, controlled measurement.

## Build notes
Extends [`run_interaction.py`](run_interaction.py) (the 2×2 is a small harness change: add a timepoint factor + the N-turn priming preamble). Markers 1–4 need a light rubric for the blind judge; marker 5 uses [`tools/patternspace_metrics.py`](../tools/patternspace_metrics.py) (Shannon/MDL). Solver across Haiku/Sonnet/Opus to check capability-dependence.
