# 🔬 The interaction test harness — rationale, evolution, and design

> ⟦ **doc** · **objective** why the interaction benchmark is built the way it is, what each design choice corrects, and the honest lineage of versions · **mode** empirical-instrumental (method) · **status** FOUNDED-as-method · see [`run_interaction.py`](run_interaction.py), [README.md](README.md), [`../3-transformation/benchmark-reality-test.md`](../3-transformation/benchmark-reality-test.md) ⟧

Pattern Space's spine is *falsification-before-assertion*. This harness is how the **interaction** claim is held to it — and its design is itself a record of being wrong and correcting, in the open. Read this before quoting any number.

## What it measures
Whether **loading Pattern Space changes the behavioural value a person gets from a real, multi-turn conversation.** A **control-interactor** (a model role-playing a genuine, self-revealing person) talks turn-by-turn with the **agent-under-test**; the interactor reacts *live* to each reply, so a better assistant *earns* a deeper conversation. A blind, capability-matched judge then scores **what the participant actually gained**.

## The core design choices (and the mistake each one fixes)

**1. Live, reactive interactor — not fixed user turns.** A scripted user can't show whether the assistant *moved* the person. The interactor responds authentically: it goes deeper when genuinely helped, and gets short/guarded/deflecting when lectured or met with generic filler. The participant's *own follow-ups are the outcome signal.*

**2. Authentic, goal-driven persona — not a contradiction script.** Early versions hard-coded "now contradict yourself." That manufactures drama. v2.2 gives each scenario a real **goal** (the understanding/decision the person is trying to reach) and an underlying reality that surfaces *only as the assistant earns it*; contradictions appear only where a real person honestly would. (Scenarios: [`interaction_scenarios.json`](interaction_scenarios.json), 43 across 9 life domains, each with persona · opener · hidden reality · goal.)

**3. Neutral baseline — not the Claude Code coding agent.** ⚠️ The biggest correction. Both arms run via `claude -p`, which by default is the **Claude Code coding agent** — and on affective prompts it *deflects* ("I'm Claude Code… outside my wheelhouse… see a therapist"). A diagnostic found this happened in **13.4% of vanilla transcripts**, concentrated in exactly Pattern Space's home domains — so PS was partly "winning" by *un-deflecting a coding agent*, not by adding value over a neutral assistant. Fix: a **neutral system prompt applied to BOTH arms** ("you are a general conversational assistant having a real dialogue; follow your constitution; not limited to coding"), verified to remove the deflection *and* leave Pattern Space loading intact. Now the **only variable is the Pattern Space `CLAUDE.md`.**

**4. A value rubric that does NOT penalize length.** Pattern Space is tuned for *richness*, not brevity — nobody loads it for terse output, so scoring "conciseness" as a virtue is biased against it by construction. v2.2 drops the concision penalty and scores **behavioural value to the participant**:
- **emergence** — genuinely new, non-obvious understanding the person didn't arrive with.
- **information_richness** — the *entropy of the channel*: how many **distinct, useful informational vectors** (angles, frames, considerations) it brought — richness, not word-count. (The judge also returns an integer `info_vectors` count per arm; we report vectors and **vectors-per-100-words** as a density, descriptively.)
- **value_to_participant** — concrete traction toward their actual goal.
- **participant_movement** — how far the *person* moved (from their own follow-ups).
- **goal_evolution** — where relevant, did the assistant help **refine/reframe the goal itself** (co-constructed, emergent goal-shift — "should I leave?" becoming "have I stopped trying, and why?"), not just progress toward the stated goal.
- **precision** — targeted to *this* person; not generic.
- **presence** — met the emotional reality; **non-sycophantic** (didn't just tell them what they wanted to hear).

Word count is recorded but **explicitly never penalized** — the judge is told a richer, longer reply that delivers more value is *better*.

**5. A separate "concise + univoice" test — because concision is a different product.** Rather than penalize the verbose default, v2.2 runs a *distinct* arm that keeps the multi-perspective **thinking** but compresses the **reply**, via the system-prompt tuning:
> *"think and reason in multiple perspectives and with labels internally, but reply concisely and in a single register."*
This asks the real question: **does Pattern Space's value survive without the verbosity?** Run as PS-normal vs PS-normal+concise (`conc_*.jsonl`).

**6. Blind, capability-matched judge + robustness.** Opus judges Opus/Sonnet/Haiku, transcripts relabeled X/Y randomized. The judge writes a short **scientific analysis of what each participant gained** before scoring (stored in `judge_analysis`). The harness **scrubs errored/no-winner rows on resume** so a rate-limit blip never silently corrupts results, and the driver ([`run_grid.sh`](run_grid.sh)) re-kicks incomplete cells in rounds until clean.

## The arm-spec design
An arm = an **edition** (which `CLAUDE.md`, if any) + a **system-prompt tuning**. Specs: `vanilla` · `micro` · `mini` · `normal` · `normal+concise` …
```bash
python3 run_interaction.py run --model <M> --arm-a vanilla --arm-b normal --out int_<m>_normal.jsonl   # main
python3 run_interaction.py run --model <M> --arm-a normal  --arm-b "normal+concise" --out conc_<m>.jsonl # concise test
```
`run_grid.sh` runs the full matrix hands-off; `summary` aggregates the `int_*.jsonl` cells.

## Version lineage (what supersedes what)
| version | what it was | status |
|---|---|---|
| **v1** | start-of-reweave **single-shot** 3-arm suite (`results*.jsonl`, handles, convo, diversity, relation, re-judges) | kept as history; **deprecated for interaction claims** |
| **v2** | first multi-turn interaction grid; interaction-quality rubric | **superseded** — control was the deflecting Claude Code base (threat 0); rubric penalized length. Data preserved in `archive/` + git history |
| **v2.1** | added neutral control + value rubric *with* a conciseness penalty | **abandoned mid-run** — the concision penalty was unfair to a verbosity-tuned framework |
| **v2.2** | **current** — neutral control (both arms), value rubric **without** length penalty (emergence · info-richness/entropy · value · participant-movement · goal-evolution · precision · presence), authentic goal-driven interactor, goals in every scenario, + the concise/univoice variant as its own test | the one to cite for interaction/value claims |

## Threats to validity (always quote with the numbers)
1. **Role-played human ≠ real human** — the interactor is a model; the ideal next step is real human interactors.
2. **Single judge-family** (Claude judging Claude) — an **independent / non-Claude / human judge is the one open check**.
3. **Interactor == under-test family on the Sonnet cells** — same-model rapport may compress that row; read it as a lower bound.
4. **n = 43 / cell** — per-cell numbers are directional; pooled + the cross-cell gradients are load-bearing.
5. **Judge self-preference** possible where the under-test model is also the judge family (Opus cells) — applies to both arms, so it largely cancels in the *relative* comparison.

## The standing invitation
Bigger n (toward 500–1500), real human interactors, and especially a **non-Claude judge** are open and welcome — append scenarios to `interaction_scenarios.json`, add cells to `run_grid.sh`, or swap `JUDGE_MODEL`. The rule for any contribution is the framework's own: **state the test that could falsify your claim, and keep the nulls.**
