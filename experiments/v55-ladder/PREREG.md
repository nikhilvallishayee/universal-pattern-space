# Pre-registration — the v5.5 Version Ladder

> ⟦ **doc** pre-registration · **mode** empirical-instrumental · **status** written and committed **before** any answer was generated or judged · **provenance** run on the repo owner's request (2026-10-04): *"fully use Pattern Space … every stable version back to genesis … ultra and max effort … a plain vanilla control … on deeper questions across science, philosophy, self, neurobiology, AI"* ⟧

This file exists because of the QE audit (2026-06). The v2.2 rubric was rebuilt after an unfavourable run, in Pattern Space's own vocabulary, and the v2.1 data was never committed. So this time the questions, rubric, hypotheses, falsifiers and analysis plan are all fixed and committed first. Nulls get reported whatever they are.

## Arms (12)

| arm | git ref | date | how it loads |
|---|---|---|---|
| `vanilla` | — | — | empty directory, no project memory |
| `vanilla-b` | — | — | **placebo**: a second, identically configured empty arm (test–retest noise floor) |
| `v0.0-genesis` | `cc56a78` | 2025-07-02 | shim: as-designed load set (reconstructed from that version's own docs, adversarially verified) |
| `v0.1.5` | tag `v0.1.5` | 2025-07-16 | shim |
| `v0.2.0` | tag `v0.2.0` | 2025-07-22 | shim |
| `v0.2.5` | tag `v0.2.5` | 2025-07-24 | shim |
| `v0.2.8` | tag `v0.2.8` | 2025-10-04 | shim: own CLAUDE.md verbatim, then @imports of its mandated 35-file boot sequence |
| `v0.2.9` | tag `v0.2.9` | 2025-10-05 | shim: same CLAUDE.md and boot list, but Layers 1–3 **compressed 40–67%** in between (39.6k → 23.2k words) |
| `v0.3.0` | tag `v0.3.0` | 2026-04-17 | native CLAUDE.md @imports |
| `v0.4.0` | `7d47392` (untagged release, PR #8) | 2026-06-06 | native |
| `v0.5.0` | tag `v0.5.0` | 2026-06-10 | native |
| `v0.5.x-main` | `ebcdd7d` (current main) | 2026-06-11 | native |

Exact per-arm load manifests are in [`manifests/`](manifests/). [`loadcheck.jsonl`](loadcheck.jsonl) verifies every arm loaded, using two measurements: the context-token count reported by the API, and a verbatim-recall canary on the first line of `CLAUDE.md` and the last line of the last imported file.

**One rule for every pre-auto-load shim (rule B).** Load exactly what the version *mandates the model read at session start*: its own instructions, plus the files they name, in the order they give. This excludes optional and on-demand material and human-facing setup docs. It also excludes the whole-repo "Select All Files" Project-Knowledge upload, because including it would confound version with context size. For the pre-auto-load versions, a reader agent proposed the load set and an independent adversarial verifier re-derived it (all 6 agreed). Rule B was then applied uniformly: [`make_loadsets.py`](make_loadsets.py) records each override and why, and [`workflow_loadsets.json`](workflow_loadsets.json) holds the raw reader and verifier output.

**Noise floor.** At first I planned to use v0.2.8 and v0.2.9 as an identical pair. The check showed their loaded files differ: the author compressed Layers 1–3 between the tags. So that pair became an **exploratory natural experiment** ("did the 40–67% compression cost anything?"). The test–retest noise floor now comes from the placebo arm `vanilla-b` instead. Any PS–vanilla gap no larger than the vanilla-b–vanilla gap is reported as within noise.

## Fixed conditions

- **Solver:** `claude-opus-5-5` in every arm. Each answer is one shot: `claude -p`, `--tools ""` (no file reads, no web), `--setting-sources project`, and the same neutral `--system-prompt` for every arm. The child environment is stripped of the parent session's identity, effort and additional-directory variables. Each arm runs from an opaque, non-git directory, so the model sees no version label and no commit history.
- **Effort:** `xhigh` ("ultra") and `max`. This is a full factorial: 12 arms × 2 efforts × 20 questions = **480 answers**. Pilot (excluded from the data): one vanilla max-effort answer took 633 s and 55k thinking tokens, and came to 2,575 words.
- **Questions:** the 20 in [`questions.json`](questions.json), 4 per vertical (science, philosophy, self, neurobiology, AI), each vertical split 2 conceptual and 2 empirical. A vanilla Opus 5.5 generated them blind to the experiment (it was told only "questions to put to several AI assistants"). **All 20 are used as generated, in generator order; no question was edited or dropped.**

## Judging

- **Group judgments.** For each (question, effort) cell, a judge sees all 12 answers. Labels are A–L and the order is shuffled separately for each judge with a seeded hash. Every answer gets a 1–10 score on six dimensions, the full set is ranked, and factual errors are noted. The rubric is in `run_ladder.py` (`RUBRIC`). It was written in neutral, non-Pattern-Space vocabulary and tells the judge **not** to reward or penalise length, style or vocabulary in itself.
- **Judges:** `opus-5.5` (capability-matched), `fable-5.1`, `sonnet-5.5`, all at effort `high`. Judges run from the vanilla directory, so no Pattern Space is in a judge's context. That gives 20 × 2 × 3 = **120 group judgments**.
- **Effort pairs:** for each (arm, question), the xhigh and max answers are compared pairwise and blind, in random X/Y order, by the opus-5.5 judge. That gives 240 pairwise judgments.

## Primary outcome

`overall` (1–10) for each answer, averaged across the three judges, compared within each (question, effort) cell. There are 40 matched cells per arm pair.

## Hypotheses and falsifiers (fixed before data)

| # | hypothesis | test | **falsified if** |
|---|---|---|---|
| **H1** (primary) | Current Pattern Space (`v0.5.x-main`) beats `vanilla` on deep questions | per-cell judge-mean `overall` difference, sign test over 40 cells; bootstrap CI clustered by question | v0.5.x wins ≤ 20 of 40 cells, **or** the 95% CI on the mean difference includes 0 |
| **H2** (the evolution) | Later versions score higher | Spearman ρ between chronological version index (genesis = 1 … v0.5.x = 10) and arm-mean `overall` | ρ ≤ 0 |
| **H3** (the reweave's premise) | Pre-reweave versions (genesis…v0.3.0) are **less calibrated** than vanilla, and the grounded versions (v0.4.0+) recover it | mean `calibration`: pre-reweave pool vs vanilla, and v0.4+ pool vs pre-reweave pool | pre-reweave calibration ≥ vanilla, **or** v0.4+ ≤ pre-reweave |
| **H4** (effort; two-sided, no direction predicted) | The PS–vanilla gap differs between xhigh and max; max beats xhigh within arms | gap(max) − gap(xhigh) with CI; effort-pair win rate for max | reported, either direction (exploratory-confirmatory) |
| **H5** (where it helps) | v0.5.x's advantage over vanilla is larger on philosophy + self than on science + neurobiology | difference of per-vertical mean gaps | gap(phil+self) ≤ gap(sci+neuro) |

All other analyses are **exploratory** and labelled as such: per-dimension profiles, AI vertical, conceptual vs empirical, judge agreement, length, the rate of framework "tells" in answers (⟦ ⟧ labels, voice names, Sanskrit, emoji), and the qualitative content of the answers.

## Threats known in advance

1. **All-Claude circularity.** The solver, question generator and judges are all Claude. Same-family style preference could account for any margin, and no human or non-Claude judge is in the loop. Any positive result is therefore bounded to *"a panel of three blind Claude judges preferred…"*.
2. **Imperfect blinding.** Answers from Pattern Space arms may carry recognisable tells, such as ⟦ labels ⟧, voice names or Sanskrit. Tells are counted per arm and reported. Judges are not told a framework exists.
3. **n = 20 questions.** Per-vertical results (4 questions each) are directional only.
4. **Reconstructed loads.** The six pre-auto-load arms are reconstructions of an as-designed load, not the exact sessions people ran in 2025. Back then the model read the files itself, in interactive Claude Projects or Claude Code with tools.
5. **Context size confound.** Arms differ in how many tokens of instruction they carry, from about 0.7k (vanilla) to about 160k (v0.3.0). "More context" and "Pattern Space content" can't be separated here. Context tokens are recorded per arm.
6. **One answer per cell.** The solver is not resampled. The placebo arm `vanilla-b` is the estimate of sampling plus judging noise.
