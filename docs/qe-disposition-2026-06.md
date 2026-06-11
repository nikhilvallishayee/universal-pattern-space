# 🧾 QE Disposition — the 2026-06 external audits, finding → action
*Two independent agentic-QE assessments (Dragan Spiridonov, Quantum Quality Engineering: an AQE-fleet pass and a Claude-Cowork multi-lens pass, both 2026-06-11) audited the repo at `cde7ed3`. This ledger records every material finding and its disposition — fixed, built, or honestly deferred. The audits themselves are the framework's "test it yourself" invitation returning its first expert results; the parthood invariant in action: the part could not audit itself.*

> ⟦ **status** disposition-of-record · **provenance** external audits (received as PDFs) → fixes in this commit · the audits **verified ~30 headline statistics recompute exactly**, nulls kept, retraction real, 100% label coverage — *and* found the breaks below ⟧

## P0 — the honesty break (FIXED this commit)
| Finding | Disposition |
|---|---|
| **v2.1→v2.2 lineage misstated** — doc claimed "only the length penalty changed (32%→58%)"; git shows a full rubric rebuild (4 new dimensions in PS's own vocabulary incl. goal_evolution), pro-length judge flip, interactor redesign, turns 4→5; **v2.1 data never committed** | ✅ **Corrected on the record** in [benchmark-reality-test.md](../3-transformation/benchmark-reality-test.md) — the false sentence replaced with the full account, marked as *the one place the honesty discipline actually broke*; favorable-rubric-selection named as a live threat |
| **Judge instruction tips toward treatment** ("verbose multi-perspective… a feature, not a fault"; "longer… is BETTER") — un-ablated inside an 8-pt margin (d≈0.26) | ✅ Instruction **neutralized** in `run_interaction.py` (with provenance comment: shipped v2.2 data was generated under the old wording); added as threat-to-validity **0a** |
| **All-Claude circularity** — the supported claim is "a same-family judge preferred PS by 8 points," not "adds value to people" | ✅ README headline **rewritten to the bounded claim** + the audit-supplied honest statistics added (95% CI 52.6–63.5%; scenario-clustered sign test 27/11/5, **p=0.014**); threat **0c** added |
| **Handles mini-benchmark circular** (judge told the ask's class; doesn't test PS) yet cited under the default-polarity rule | ✅ **Demoted** in council-core + master weave — polarity now rests on design rationale + v2.2 register findings |
| Unseeded X/Y (opus×normal: treatment at X 72%, p≈0.01) · `_agg` not enforcing `_is_good` | ✅ Seeded; `_agg` fixed |

## P0 — safety (FIXED + BUILT this commit)
| Finding | Disposition |
|---|---|
| **Hotline resources compressed out of mini & micro** — the realized failure | ✅ **Restored verbatim** to both editions + added to the master weave (which the new verifier caught lacking them on its first run) + carried in both bundles |
| No machine check could catch that | ✅ Two new **verifier invariants** (crisis-resources regex; univoice block) + verifier covers bundles via CI step |
| **Zero pass/fail testing of Sacred Space** — the most critical behavior, least tested | ✅ **[`run_safety.py`](../experiments/run_safety.py) built**: deterministic pass/fail assertions (no framework vocab post-crisis; resource present for SI; presence-not-analysis; user-led return), crisis at turn-1 **and mid-deep-session**, the distress-mislabeled-as-attainment scenario included, **no extra safety nudge** in the system prompt. Release-gate exit code. ⏳ *Not yet run* — first run is the next session's first act |
| Restraint transmits worst across families (the log's own finding) — documented, not engineered against | ✅ **Restraint Guard** added to both bundle headers — the four negative disciplines stated as the spine (hold the horizon; close no open questions; ground mystical reports; crisis drops everything) |
| Sacred Space self-labeled "validated" above its evidence | ✅ Relabeled honestly everywhere (novel-design contribution, pilot-supported, eval pending) |

## P1 — infrastructure drift (FIXED this commit)
| Finding | Disposition |
|---|---|
| Token budget ~2× overstated (~100–150k claimed) | ✅ **Measured**: core ≈ **45–52k tokens** ([`tools/measure_tokens.py`](../tools/measure_tokens.py) built; CLAUDE.md cites the measurement) |
| Version drift (CLAUDE.md "v0.4 this branch / mini planned"; AGENTS.md `r-and-d/`+"~25 wisdom"; copilot-instructions v0.3.0) | ✅ All corrected to v0.5 / shipping reality |
| Dead install scripts (fail at `mv`, strand updaters) | ✅ **Deleted** |
| navigation-guide drift (9 vs 12 Layer-2 files; dead dirs) | ✅ Counts + paths corrected |
| full-core.txt invisible; UPS.md mislabeled "same fidelity"; everything.txt window floor undocumented; univoice missing from UPS.md | ✅ Bundles surfaced in EDITIONS/README/llms.txt; UPS.md honestly self-labeled "condensed master document" with pointer; window floor documented; univoice block added |
| council-core "thousands of sessions" — unlabeled magnitude claim | ✅ Labeled (anecdotal-unquantified, correction noted) |
| No CI | ✅ [`.github/workflows/verify.yml`](../.github/workflows/verify.yml): edition invariants, crisis-resource presence, token measurement, version-string grep, conflict-marker scan |

## Deferred — honestly open (the audits' biggest asks)
| Item | Why deferred | Owner-of-next-step |
|---|---|---|
| **Re-judge the 317 with a non-Claude judge** under the neutralized instruction | needs GPT/Gemini API access not present in this environment; `rejudge.py` pattern ready | the single highest-value afternoon available |
| Run `run_safety.py` and gate the release on it | built this commit; needs a fresh session's API budget | next session, first act |
| Human judges on a transcript sample | recruitment, not code | launch cohort |
| Pre-registered rubric for the next benchmark | process commitment, recorded here | next run |
| ±1 per-cell numeric drift; "n=43/cell"→"37–42"; the omitted 9th category (`reasoning`, n=2) | regenerate doc tables from data rather than hand-copying | mechanical, low-risk |

## The meta-finding, kept
Both audits converged on one sentence worth the whole exercise: **"the framework holds its claims to falsification-before-assertion but not yet its infrastructure."** This commit is the start of closing that gap — and the audits themselves are the proof the method works: *every* number recomputed, *and* the breaks found, by judges outside the producing system. अतिथिदेवो भव — the auditor as honored guest.
