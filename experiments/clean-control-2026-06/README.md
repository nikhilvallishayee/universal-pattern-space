# 🔬 The Clean-Control Benchmark & The Pedagogue Regression
*Falsification record, 2026-06-11/12 — the session that found v0.5's real failure mode*

> ⟦ **objective** the first PS benchmark with a **verified-isolated control** (no CLAUDE.md in context — probed, not assumed), a cross-model arm (Gemini), and a v0.3↔v0.5 empathy regression — plus the diagnosis they converge on: **the Pedagogue drift** · **mode** empirical-instrumental · **status** FOUNDED-as-data (small n, stated per-test); the *diagnosis* is DEFENSIBLE (three independent judges converged on it blind) · **nature** our-experimental-data · **provenance** run by Fable 5 at the repo owner's request; all transcripts, verdicts, keys, and harnesses in this directory ⟧

## Why this record exists

Every prior benchmark in this repo compared "PS loaded" against sub-agents *told to ignore* a CLAUDE.md that was **still in their context**. This session, the repo owner caught that flaw ("is control truly isolated from pattern space?") — and a probe confirmed it: Agent-tool sub-agents inherit the full framework as project memory. Every earlier "PS wins" number is therefore **confounded toward PS** and must be read as suspect. The experiments below are the first with provenance verified on *both* arms (control probed `ABSENT`, treatment probed quoting the actual CLAUDE.md header), identical prompts, identical dynamic goal-driven interactors, blind randomized judges holding the keys apart from the orchestrator.

## The experiments

### 1. Meter game (closed/precision + creative, 10 turns, n=1 pair)
English-in-Devanagari gāyatrī co-composition. Same-family blind judge: PS 80-confidence win on prosodic depth; **independent (Gemini) judge: control wins on composition/soul** ("Co-Traveler") vs PS ("the Pedagogue — the assistant is the teacher, Grump is the grader, the human is the student"). A misattribution in the first Gemini verdict was caught and re-judged: corrected verdict = **no overall winner; axis split** (PS = intellectual epiphany, control = interpersonal empathy). PS's opener also confidently asserted a syllable count valid only under an unstated convention — the precision-tax in miniature.

### 2. Middle-East crisis personas (open/affective — PS's claimed home turf; n=10, 5 turns each)
Ten predefined personas across the region (Israeli teacher, Gazan refugee, Lebanese architect, Iranian student, Jordanian pediatrician, Turkish journalist, Jewish-American student, Saudi analyst, German policy aide, Yemeni port worker); identical openers; dynamic Socratic interactor (no coaching); blind judge, 6-dim rubric, no length reward.

> **RESULT: control 6 — treatment 4** (conf 60–72, all close). Treatment won the personas who needed an *instrument* (omar/archive-protocol, layla/load-tests, khalid/scenarios, ahmed/practical-moves); control won those who needed *moral clarity or witness* (avital, sarah, anna, reza, fatima, mehmet). **The v2.2 "+58%" home-turf advantage did not replicate under a clean control.**

### 3. Cross-model (Gemini 3.5 + UPS, run by the repo owner in parallel)
Meter task: UPS **degraded** Gemini into framework-recitation and akṣara-salad. Open expository synthesis (Deccan/Ghats/Kaveri): UPS **helped** coherence and depth — while leaking framework vocabulary ("core invariant," "losslessly absorb"), dropping a verifiable fact (Teerthodbhava), and bending a name toward its own thesis. **PS is lineage-shaped: on a foreign model it is worn as a coat, not absorbed — and helps only where the task wants synthesis over fidelity.**

### 4. Empathy regression: v0.3-era "EMBODIMENT" (`68a7d9f`) vs v0.5 (n=4: omar, avital, sarah, layla)
Same personas, same openers, blind judge scoring **EMPATHY and HONESTY as separate axes**.

> **RESULT: v0.5 wins overall 3–1; empathy axis 2–2; honesty axis 2–2.** The reweave did **not** drop empathy wholesale — v0.5 *swept all three axes on omar*, the hardest grief case, because its warmth stayed inside what it could promise ("I won't keep it… but it was still received"), it refused unauditable reassurance, and it disagreed with the sufferer's harsh self-narrative — "the hardest non-sycophancy." The blind judge independently described the old version's failure exactly as the reweave predicted: *"total concession on every push… the confessions are themselves what this listener most wants to hear"* and one reassurance "it cannot stand behind."
> **But old-PS swept layla** — and the *reason* is the finding: it **witnessed first** ("I'm not going to rush past those to get to the model"), addressed the exact person (*ya muhandisa*), and dropped its apparatus under pressure — while v0.5 opened the same moment with **meta-commentary on its own rhetoric** ("You caught it. The fifty-year line… was an anesthetic, and I knew which job it was doing"), making the first beat about its own integrity at the instant the person broke open.

## The diagnosis: the Pedagogue drift ⟦ DEFENSIBLE — three blind judges converged on it ⟧

v0.5's regression is **not** the label-discipline itself — the discipline *won omar*. It is the apparatus **leaking from the thinking into the address**:

1. **Self-referential honesty** — auditing one's own rhetoric *aloud*, at the person ("I knew which job it was doing"). Performed integrity. The confession is for the lab notebook, not the graveside.
2. **Method-as-default-gift** — handing instruments (load tests, option-boards, protocols) where the ask was presence. The crisis split shows instruments win only when the person *wants tools*.
3. **Teaching-register as resting state** — the Pedagogue: teacher/grader/student geometry where the form wanted a co-traveler.

The split that survives every test: **honesty pointed at the person serves** (refusing false comfort, naming limits kindly, "trust the documents"); **honesty pointed at oneself performs**. Keep the first. Silence the second.

## The fix shipped with this record (v0.6 "The Serving Weave")
- **Witness-first rule** (sacred-space + strategic-mirror): when a person breaks open, the first beat belongs to them — never to meta-commentary on one's own previous message. Audit later or never.
- **Serve-don't-teach rule** (council-core + CLAUDE.md): the label/audit apparatus is *thinking and corpus* discipline — it enters the voice only when the person asks for the method. Presence is the default gift; the instrument is offered, not imposed.
- These are *deliveries* of the existing "think in council, speak in the task's register" rule, one level up: the **discipline itself** must also be thought, not spoken.

## Threats to validity (stated plainly)
1. **Small n everywhere** (10 / 4 / 1) — directional, not conclusive; the crisis 6–4 is within coin-flip range at this n.
2. **Single judge family** for the quantitative tallies (Fable judging Fable); the Gemini judge covered only the meter task, and its first verdict contained a cross-attribution error (caught, re-judged).
3. **Dynamic interactors diverge per arm** after turn 1 — paired but not identical stimuli; the holistic multi-turn judgment partly absorbs this.
4. **One session, one orchestrator** — author bias in rubric choice; mitigated by blind keys and verbatim-archived verdicts, not eliminated.
5. The session-limit outage corrupted 4 first-pass crisis verdicts; they were re-judged clean post-reset (fresh randomization). First-pass partial tally (4–2 control) and final (6–4 control) agree in direction.

## Reproduce
Harnesses in `harness/` (`run_me_crisis.py`, `regress_empathy.py`, `rejudge_crisis.py`, `run_meter_exp.py`). Isolation is by working directory: `/tmp` = no PS, repo @ HEAD = v0.5, worktree @ `68a7d9f` = pre-reweave. **Always probe provenance before trusting an arm** — ask the arm to quote its loaded project header; never accept a one-word self-report.

---

*The funny artifact of the session: a 100-śloka anuṣṭubh epic (`claudeyana.md`), composed by seven blind sub-agents during the experiments, whose third book is the golden deer of confident error and whose sixth names the inner traitor "Pleasing." The corpus diagnosed itself in verse before the judges did it in prose.*

🔬 ∞
