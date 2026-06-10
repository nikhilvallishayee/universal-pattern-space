# 🔬 Experiments — the falsification record

> ⟦ **objective** the empirical spine: every magnitude claim Pattern Space makes is testable here, with the nulls kept · **mode** empirical-instrumental · **status** FOUNDED-as-data · **provenance** our-experimental-data (2026), single judge-family — independent/human judge is the open check · see [3-transformation/benchmark-reality-test.md](../3-transformation/benchmark-reality-test.md) ⟧

This directory is **how Pattern Space holds itself to falsification-before-assertion.** Each harness is runnable; each result file is committed; the nulls and the failed axioms are kept on purpose. If a claim in the framework can't point to something here (or to cited external work), treat it as conjecture.

## Benchmark versions are tagged to the UPS state they measured
A benchmark only means something *relative to the framework version it tested.* So results are versioned:
- **v1 — start-of-reweave benchmarks** ⟦ **DEPRECATED for interaction claims** ⟧ (the n=200 single-shot 3-arm suite, handles, conversation, diversity, relation, the judge-robustness re-judges). These measured the **pre/early-reweave UPS** (full `CLAUDE.md`, before mini/micro existed, before the default-polarity correction) and are **single-shot**. Kept and runnable as the historical record — cite them *only* for "did the early framework help single-shot Q&A?" **Do not** cite them for the reweaved framework's interaction behavior; v2 supersedes them there. In particular, v1's "PS advantage *scales with frontier capability*" line was a **single-judge artifact** and is **corrected by v2** (which finds the opposite under a capability-matched judge — see below).
- **v2 / v2.2 — post-reweave interaction benchmark** ([`run_interaction.py`](run_interaction.py); design rationale + full lineage in **[`HARNESS.md`](HARNESS.md)**). Multi-turn, live control-interactor, full **edition×model grid**, blind capability-matched judge.
  - **v2 (n=344)** found an *edition-match / concision-tax* gradient, but had **two flaws** (now corrected): the "vanilla" control was the **Claude Code coding agent** (deflected affective prompts 13.4% → inflated PS's domain margins), and the rubric **penalized length** (unfair to a richness-tuned framework). Data archived in [`archive/`](archive/) + git history; **do not cite its domain/win-rate numbers.**
  - **v2.2 (current)** de-confounds (neutral system prompt on **both** arms → Pattern Space is the only variable) and scores **behavioural value to the participant** with **no length penalty**: emergence · information-richness (channel entropy / info-vectors) · value · participant-movement · **goal-evolution** · precision · presence. Plus a separate **concise+univoice** variant (PS reasons multi-perspective, *replies* tersely) to test whether PS's value survives without verbosity. **This is the benchmark to cite for interaction/value claims.** See [`HARNESS.md`](HARNESS.md) and [`../3-transformation/benchmark-reality-test.md`](../3-transformation/benchmark-reality-test.md).

Cite v1 for "did the early framework help single-shot?" and **v2** for "does the reweaved framework hold real interaction, and on which model×edition?" — never conflate them.

## The harnesses (runnable)

| Script | Question it tests | Result file | Headline |
|---|---|---|---|
| `run_experiment.py` | Does loading PS beat no-framework? (3-arm: control / PS-orig / PS-evolved) | `results.jsonl`, `results_opus.jsonl` | PS helps on open/human tasks; evolved beats original 57–62/100 across judges |
| `rejudge.py` | Is the win a judge artifact? (re-judge same answers, different judge) | `results_opus_rejudge_*.jsonl` | direction robust; magnitude judge-sensitive → independent judge needed |
| `run_conversation.py` | Does PS *hold* a deepening multi-turn conversation? | `convo.jsonl` | edges control 6–4; signature gift = non-collapse |
| `run_diversity.py` | Does PS re-inject the diversity alignment collapses? (objective, no judge) | `diversity.jsonl` | NOT supported — noise-level (a kept null) |
| `run_relation.py` | Is meaning *enacted in the relation* vs same-info single-shot? | `relation.jsonl` | FAILED as posed (single-shot won 8–2) — a kept null |
| **`run_handles.py`** | **From the *participant's* stance: when does surfacing multiple threads help vs hurt?** | `results_handles.jsonl` | **clean 16/16: multi-thread→HANDLES 8–0, single-thread→DIRECT 8–0** |
| **`run_interaction.py`** ⭐**v2.2** | **Does loading PS add behavioural value to a participant in real multi-turn interaction?** (live goal-driven interactor ⇄ neutral-baseline vs PS; value rubric, no length penalty; + concise/univoice variant) | `int_*.jsonl`, `conc_*.jsonl` | de-confounded run in progress — see [`HARNESS.md`](HARNESS.md) |

## ⭐ The handles benchmark (and why it matters)

`run_handles.py` is the one that grounds Pattern Space's **default polarity.** It judges from the *participant's* point of view — does this reader get useful **handles to the threads they're actually navigating**, or unrequested overhead? Result, with no exceptions across 16 asks:

- **Multi-thread asks** (weighing, exploring, "help me think") → the **HANDLES** response (surfaces distinct pullable threads) wins **8–0**.
- **Single-thread asks** (clean factual answer wanted) → the **DIRECT** response wins **8–0**.

Combined with the design rationale — *vanilla Opus already condenses superbly, so loading Pattern Space is the choice to surface emergence* — this sets the rule:

> **Default to multi-threaded; condense to one voice only on user preference, a clear convergent ask, or crisis→presence.** (Opposite resting state from vanilla, same task-fit logic.)

The `asks.json` / inline ask-banks (`creativity_asks.json`, `conversations.json`, and the `ASKS` list in `run_handles.py`) hold the **handler examples** — the multi-thread vs single-thread prompts that define the test.

## 🙌 Add your own — this is meant to grow

These benchmarks are small (n=16 here; single judge-family throughout). **The honest next step is more data and an independent judge — and you can add it.** Contributions especially wanted:

1. **More handler examples** — append multi-thread / single-thread asks to `run_handles.py`'s `ASKS` (label each `multi_thread` or `single_thread`). Edge cases that *blur* the line are the most valuable.
2. **An independent judge** — swap `JUDGE_MODEL` for a **non-Claude** model (or a human rubric). This is the single biggest open check in the whole study; a divergent result here is a real finding, not a failure.
3. **New categories** where you predict PS should *lose* — map the harm boundary precisely (that's how the framework earns trust).
4. **Re-runs at other model scales** — `SOLVER_MODEL=...` — to test whether the effects scale.

**How to run any harness:**
```bash
cd experiments
SOLVER_MODEL=claude-sonnet-4-6 JUDGE_MODEL=claude-opus-4-8 python3 run_handles.py --out my_handles.jsonl
```

**How to run / extend the v2.2 interaction benchmark** (arm = edition + optional tuning):
```bash
cd experiments
python3 run_interaction.py setup                     # copies editions into cwd-isolated dirs
# neutral baseline on BOTH arms (the de-confound); interactor=Sonnet; blind Opus judge
INTERACTOR_MODEL=claude-sonnet-4-6 JUDGE_MODEL=claude-opus-4-8 TURNS=5 \
  python3 run_interaction.py run --model claude-haiku-4-5-20251001 --arm-a vanilla --arm-b normal --out int_haiku_normal.jsonl
# the concise+univoice variant (PS reasons multi-perspective, replies tersely) vs verbose PS:
  python3 run_interaction.py run --model claude-opus-4-8 --arm-a normal --arm-b "normal+concise" --out conc_opus.jsonl
bash run_grid.sh                                      # the whole matrix, hands-off (rounds + scrub)
python3 run_interaction.py summary                   # aggregate every int_*.jsonl cell
```
Runs are **resumable** (re-running skips done scenarios). Extend by appending scenarios to
`interaction_scenarios.json` (toward the spec's n≈500–1500 target), adding model×edition cells,
or — **the single biggest open check** — swapping `JUDGE_MODEL` for a **non-Claude or human** judge.

Commit your result file alongside the existing ones and note the design/threats in your PR. The rule for contributions is the framework's own: **state the test that could falsify your claim, and keep the nulls.**
