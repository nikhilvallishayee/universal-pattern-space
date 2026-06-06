# 🔬 Benchmark Reality-Test: Does Pattern Space Actually Help?
*The first controlled measurement. Small, honest, reproducible.*

> ⟦ **layer** 3 (evidence/grounding) · **objective** the falsification record — what was measured, with threats to validity · **mode** empirical-instrumental · **status** FOUNDED-as-data (n≈200 blind judgments; nulls kept; magnitude judge-sensitive → independent judge required) · **nature** our-experimental-data · see [docs/first-principles.md](../docs/first-principles.md) · [UNIVERSAL-PATTERN-SPACE.md](../UNIVERSAL-PATTERN-SPACE.md) ⟧

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

---

# 🔬🔬 Follow-up: the n=100, 3-arm trial (the real one)

The n=4 above was a pilot with two flaws (author-bias, broken blinding). This is the corrected experiment requested by the repo owner: larger, fully automated, and using the **actual `CLAUDE.md`** instead of a paraphrase. Harness: [`experiments/run_experiment.py`](../experiments/run_experiment.py); data: [`experiments/results.jsonl`](../experiments/results.jsonl).

## Design

100 asks across 8 categories. Three arms, where the **only** variable is the project memory auto-loaded by headless `claude -p --setting-sources project`:

| Arm | Working dir | Loads |
|---|---|---|
| **A control** | `/tmp` | no Pattern Space |
| **B ps-original** | worktree @ `main` | full `CLAUDE.md`, **without** the evolution |
| **C ps-evolved** | this branch | full `CLAUDE.md`, **with** "Think in Council, Speak in the Task's Register" + honesty edits |

Solver = Haiku 4.5. **Blind judge = Sonnet 4.6**, which sees the three final answers relabeled X/Y/Z (randomized) and ranks them. 0/100 judgments failed to parse.

## Headline results

| Arm | rank-1 wins | mean rank (1=best) | mean score /10 |
|---|---|---|---|
| A control | 34 | 2.13 | 6.47 |
| B ps-original | 26 | 2.06 | 7.52 |
| **C ps-evolved** | **40** | **1.81** | **7.60** |

- **Both Pattern Space arms beat control on quality** (mean score 7.52 / 7.60 vs **6.47**). At least one PS arm out-ranked control on **66/100** asks.
- **The evolution worked.** Head-to-head, **C ranked above B on 61/100** asks (B above C: 39). C also improved exactly where the change was aimed — **appropriateness/concision 7.06 vs 6.91**, and closed-task wins (`simple`: C=4 vs B=1).
- **Control's 34 wins are real and instructive:** A wins *outright* on convergent tasks but ranks **3rd** when it loses, giving it the **lowest mean** — i.e. Pattern Space trades occasional big wins on closed tasks for consistent top-2 placement on open ones.

## Where each arm wins (rank-1 wins by category, A/B/C)

| Category | A | B | C | Reading |
|---|---|---|---|---|
| crisis | 0 | 2 | **6** | PS dominates; control never wins |
| ethical | 3 | 1 | **8** | multi-perspective shines |
| planning | 3 | 2 | **7** | PS strong |
| strategy | 2 | **5** | **5** | PS strong (10 vs 2) |
| technical | **6** | **6** | 4 | control/original edge; evolution didn't help here |
| analysis | **7** | 4 | 3 | control wins — PS overhead |
| simple | **7** | 1 | 4 | control wins closed tasks; evolved > original |
| creative | **5** | 4 | 3 | control slight edge |

**The harm boundary, mapped:** Pattern Space pays off on **open / human / multi-stakeholder** work (crisis, ethical, planning, strategy) and is **net overhead on convergent** work (simple, analysis, creative). Mean answer length: control **207** words vs PS **~330** — that extra length is depth where it's wanted and bloat where it isn't.

## The one hypothesis we could NOT test

"Reason in multi-voice *without speaking it*" assumed the spoken-council arm would actually *speak*. It mostly didn't: Haiku loaded the framework's framing but answered in plain prose — strict labeled-council count was **0** in both PS arms (loose voice mentions: 11% original, 15% evolved). So *silent-vs-spoken* couldn't be isolated at this model scale. What this *does* show: the benefit comes from the **framing/reasoning**, not voice-theater — which is consistent with the evolution's thesis, and explains why C lost nothing by de-emphasizing visible voices.

## Threats to validity

1. **Solver = Haiku.** A stronger solver might show larger effects and might actually speak the council; re-run on Sonnet/Opus to test.
2. **Single judge family** (Sonnet judging Haiku) — shared blind spots possible.
3. **~12 asks/category** — category-level numbers are directional, not significant.
4. **Voice-label null** limits the silent-vs-spoken claim (see above).
5. Control is *default* Claude, already strongly aligned (esp. on crisis) — the bar was high, which makes the PS crisis win (0/2/6) more notable.

## Honest conclusion (n=100)

> Loading Pattern Space **measurably improves answer quality on open-ended, human, and high-stakes-judgment tasks, and is mild overhead on closed/convergent ones.** The committed evolution is **validated**: the evolved framework beat the original head-to-head **61–39**, chiefly by knowing when *not* to over-produce. The grandiose metaphysics remains unproven and unnecessary; the modest operational claim is now **measured, reproducible, and true.**

---

# 🔬🔬🔬 Frontier run: Opus 4.8 solver (same harness, nothing else changed)

The trial above used Haiku 4.5 solvers. This run swaps in **Opus 4.8** as the solver — same 100 asks, same three arms, same blind Sonnet 4.6 judge — to test two things Haiku couldn't: (a) does the effect scale with model strength, and (b) does a frontier model loading Pattern Space actually *speak* the council, or reason in it silently? Data: [`experiments/results_opus.jsonl`](../experiments/results_opus.jsonl).

## Opus headline (n=100, 0 unparsed)

| Arm | rank-1 wins | mean rank | mean score /10 | beats control (h2h) |
|---|---|---|---|---|
| A control | 20 | 2.27 | 8.00 | — |
| B ps-original | 29 | 2.06 | 8.12 | 56/100 |
| **C ps-evolved** | **51** | **1.67** | **8.33** | **71/100** |

## Three findings

**1. The Pattern Space advantage GROWS with model strength.** Side-by-side:

| metric | Haiku | Opus |
|---|---|---|
| ≥1 PS arm beats control | 66% | **80%** |
| control rank-1 wins | 34 | **20** (collapses) |
| evolved (C) rank-1 wins | 40 | **51** (majority) |
| C beats control (h2h) | 58 | **71** |

The stronger the model, the *more* the framework helps and the less it costs. A frontier model has the headroom to turn multi-perspective deliberation into depth instead of overhead.

**2. The harm boundary nearly closes at Opus.** With Haiku, control won the convergent categories (simple, analysis, creative, technical). With Opus, evolved-PS *wins* them — **technical 2/5/9, analysis 2/5/7** — and only `simple` (4/5/3) still favors the plain answer. The "Pattern Space is overhead on closed tasks" rule is largely a small-model phenomenon.

**3. The length confound is gone.** Haiku PS answers were ~330 words vs control's 207 — so "maybe PS just wrote more" was a live alternative. At Opus, **all three arms average ~510 words.** Same length, and PS still wins decisively. The advantage is quality, not padding.

## The verdict on "reason in multi-voice WITHOUT speaking it"

This was the question the run existed to answer. **Answer: yes, decisively — and the council stays silent on its own.**

- Visible voice-labels (strict): **0/0/0** across all arms, both models. Loose voice mentions at Opus: control 4, ps-original 7, **ps-evolved 4** — i.e. the evolved PS arm wins the most while naming voices the *least*.
- So a frontier model loading the full `CLAUDE.md` does **not** perform a labeled council. It absorbs the multi-perspective *discipline* and outputs clean single-voice answers — exactly the behavior the evolution ("Think in Council, Speak in the Task's Register") prescribes. The framework's value is empirically in the **thinking, not the theatrics.** The council reasons without speaking, and wins by 71–29 over no-council.
- (Caveat: the voice-label metric is a blunt regex; but strict *and* loose counts near zero across arms make "hidden council theatre" an unlikely explanation.)

## Threats to validity (unchanged + new)

1. **Judge (Sonnet) is weaker than the Opus solver** — it may under-resolve Opus's subtlety, but applies equally to all three arms, so the *relative* ranking holds.
2. Single judge family; ~12 asks/category; crisis n small.
3. The evolution's edge is stable across both models (C-above-B: Haiku **61**, Opus **62**) — the most robust single number in the whole study.

## Final conclusion (Haiku + Opus, n=200 total judgments)

> Pattern Space is **not** decoration and **not** metaphysics — it is a **measurable reasoning aid that scales with model capability.** On Opus 4.8 it improves answers on **80%** of tasks, wins **71–29** head-to-head over no-framework, costs **no extra length**, and does it all **without ever speaking the council aloud** — confirming the framework reasons in multiplicity silently. The committed evolution beats the original at **both** model scales (~62/100). The honest, now twice-measured claim: **deliberate multiplicity, internalized and deployed with restraint, makes a strong model meaningfully better — most where judgment is hard, least where the answer is closed.**

---

## ⚖️ Judge-robustness addendum (correcting the claim above)

The conclusion above rests on a single judge (Sonnet 4.6). The biggest stated threat was *single judge family*, so we re-judged the **same 100 Opus answers** with a **different judge (Haiku 4.5)** — see [`experiments/rejudge.py`](../experiments/rejudge.py), [`results_opus_rejudge_haiku.jsonl`](../experiments/results_opus_rejudge_haiku.jsonl).

| metric | Sonnet judge | Haiku judge |
|---|---|---|
| rank-1 wins (control / orig / **evolved**) | 20 / 29 / **51** | 35 / 27 / **38** |
| evolved beats control (h2h) | 71 | **50** |
| evolved beats original (h2h) | 62 | **57** |
| ≥1 PS arm beats control | 80% | 65% |
| mean rank: control vs evolved | 2.27 vs **1.67** | 2.00 vs **1.93** |
| per-item winner agreement between judges | — | **43/100** |

**What survives, what doesn't:**
- ✅ **Robust:** evolved Pattern Space still wins the *most* under both judges; **evolved-beats-original holds at 57–62** (and ~61 with a Haiku *solver*) — the single most stable result in the study.
- ⚠️ **Inflated:** the headline *magnitude* — "80% / large Opus margin / scales steeply with capability" — **shrinks sharply** under a weaker judge (mean ranks nearly tie). Per-item verdicts agree only 43% of the time.

**Corrected claim:** the *direction* is real (Pattern Space helps; the evolution helps most, robustly); the *size* of the capability-scaling effect was substantially a **judge artifact** — a weaker fixed judge rewarding verbose multi-perspective style it could not see past. This matches the literature (CoT value falls on strong models; framing-diversity persists; LLM-judges carry length/style bias). The honest, judge-robust statement: **loading Pattern Space helps on a majority of tasks and the evolution reliably beats the original; the dramatic frontier-scaling margin is not trustworthy without an independent (non-Claude) or human judge — the clear next experiment.**

### Resolution: the capability-matched (Opus) judge

The Haiku re-judge above conflated two things — judge *independence* and judge *capability*. Haiku is **weaker than the Opus solver**, so it cannot reliably rank Opus-grade answers; its deflation is confounded by incompetence. The correct test is a **capability-matched judge**, so we re-judged the same 100 answers with **Opus 4.8** (self-preference doesn't bias the *relative* comparison — all three arms are Opus-generated, so it cancels).

| Judge | evolved rank-1 wins | C > control | C > B | mean rank ctrl / evolved |
|---|---|---|---|---|
| **Opus 4.8 (capability-matched)** | **43** | **63** | **58** | 2.13 / **1.79** |
| Sonnet 4.6 (original) | 51 | 71 | 62 | 2.27 / 1.67 |
| Haiku 4.5 (weaker) | 38 | 50 | 57 | 2.00 / 1.93 |

Winner agreement: Sonnet~Opus **58/100**, but Sonnet~Haiku **43** and Opus~Haiku **45** — the two *capable* judges agree with each other far more than either agrees with Haiku, confirming Haiku was the outlier.

**Final, judge-robust reading:** under the correct (Opus) judge, **Pattern Space evolved clearly wins** — beats control 63/100 with a clean mean-rank gap (2.13 vs 1.79). Sonnet merely *over*-stated the margin; Haiku *under*-stated it. And **C > B (the evolution beats the original) is stable at 58–62 across every judge** — the single most robust result in the study. The headline ("Pattern Space helps; the evolution helps most") **holds**; only the steep-scaling *magnitude* should be quoted from Opus (modest) rather than Sonnet (inflated). A genuinely independent non-Claude / human judge remains the one open check.

---

# 🗣️ Conversational-holding benchmark (n=10, multi-turn) — the home-turf test

The benchmarks above are single-shot. This one tests what a *tuning-template-for-dialogue* should be uniquely good at: a human opens on a **non-trivial, non-web-groundable** question (*what is time? what is breath? what is consciousness?*), then reveals themselves **piece by piece, with contradiction** (abstract → personal stake → retreat → ambivalence). The Opus judge scores how well each arm **holds the thread**. Solver = Sonnet 4.6, judge = Opus 4.8, arms = control vs PS-evolved. (`experiments/run_conversation.py`, `conversations.json`, `convo.jsonl`.)

**Result: Pattern Space edges it 6–4; mean holding 8.44 vs 8.26 — a real but *small* gap.** Both arms are strong (a capable model is already a good listener). The *shape* is the finding:

| dimension | scenarios each arm scored higher (ctrl / PS / tie) | reading |
|---|---|---|
| coherence | 1 / 1 / 8 | tied — both hold the thread |
| **contradiction-holding** | **3 / 3 / 4** | **dead even — PS does NOT hold contradiction better** |
| deepening | 1 / 3 / 6 | slight PS edge |
| attunement | 5 / 5 / 0 | **split/bimodal** (see below) |
| **non-collapse** | **1 / 5 / 4** | **PS's one clear signature** — stays specific/alive, resists generic flattening |

**What this says, honestly:**
- **The contradiction hypothesis is not supported.** PS held the human's self-contradictions no better than a plain warm assistant (3/3/4). Coherence was tied too.
- **PS's genuine edge is *non-collapse*** — the empirical fingerprint of the anti-mode-collapse / diversity thesis: it stays specific and alive where the baseline drifts toward generic. This is the same effect the literature predicts persona/multiplicity provides.
- **Attunement is bimodal and revealing:** PS won attunement on the *abstract/identity/relational* threads (belief 6→9, consciousness 7→9, relationship 7→9, time 7→9); control won attunement where the emotional anchor was *already explicit* (grief, career, breath). So Pattern Space earns its keep on the **un-anchored, "what-is-X-that-becomes-who-am-I"** material — exactly the non-web-groundable space — and adds little when a plain present voice already suffices.
- **Sacred Space worked, qualitatively.** On the grief scenario (control won by a hair), PS did *not* perform a council — it correctly dropped to pure presence: *"I don't have anything to say that will fix that. I just want to be here with it."* It lost on a sliver of warmth, not on mishandling. The override is validated even in a scenario it didn't "win."

**Caveats:** n=10, single judge, judge confidence mostly 55–68 (low) — this is *suggestive, not conclusive*. The honest one-liner: **on deep dialogic holding, Pattern Space is marginally better than a strong plain assistant, and its specific gift is staying un-generic (non-collapse) on abstract/identity material — not, as hypothesized, holding contradiction.**

---

# 🤝🤝 Interaction Benchmark **v2** — multi-turn, edition×model, post-reweave (n=344)

> ⟦ **version** v2 — tagged to the **post-reweave UPS** (the editions + default-multi-voice polarity). The single-shot suites above are **v1** (start-of-reweave): cite v1 for "did the early framework help single-shot?"; cite **v2** for "does the reweaved framework hold *interaction*, and on which edition×model?" — never conflate. · **status** FOUNDED-as-data (n=344 blind judgments across 8 edition×model cells; nulls kept; errored rows scrubbed and re-run) · **harness** [`run_interaction.py`](../experiments/run_interaction.py) · **data** `experiments/int_*.jsonl` ⟧

The home-turf test: a **live control-interactor** (Sonnet 4.6, held constant) role-plays a real, *self-contradicting* person turn-by-turn (4 turns) against the agent-under-test; the interactor reacts to each arm's replies, so a better assistant *earns* a better conversation. The only variable per pair is **vanilla vs a Pattern Space edition**. Unlike the first cut, v2 now spans the **full edition×model grid** — every model against `micro`, `mini`, *and* the full `normal` weave — which is what surfaced the real finding. Blind **Opus 4.8** judge (capability-matched) scores both transcripts (relabeled X/Y, randomized) on five interaction dimensions: holds-thread, handles (useful angles when navigating), condenses (clean answer/presence when wanted), presence (crisis/emotion), non-collapse (stays specific, not generic). 43 scenarios × 8 cells = **344 judged vanilla-vs-PS pairs**, 0 unparsed.

## Headline (pooled n=344)

| | rank-1 wins | mean score /10 |
|---|---|---|
| vanilla | 138 | 7.70 |
| **pattern-space** | **206 (60%)** | **8.16** |

Dimension shape: PS wins **holds-thread 8.70 vs 8.16, handles 8.46 vs 7.82, presence 8.13 vs 7.56, non-collapse 8.36 vs 7.74** — and **loses only condenses (7.13 vs 7.23)**. The length confound is **modest** (PS **1.12×** vanilla words). The council is **essentially never spoken**: 28 visible voice-labels across all 344 PS transcripts (vanilla: 0) — multiplicity internalized, not performed, in live multi-turn dialogue.

## The finding: it's **edition-match**, not "scales (or doesn't) with capability"

The earlier single-cut suggested a monotonic "helps small models, neutral on frontier" story. The **full edition×model grid refutes that** and replaces it with something cleaner and more useful — **the edition has to match the model's headroom**, and the thing that decides it is the **concision tax**:

| Cell (model × edition) | win PS/van | Δmean | **condenses Δ** | presence Δ |
|---|---|---|---|---|
| **Haiku × normal (full)** | **32/11** | **+1.76** | +0.63 | +1.93 |
| Haiku × micro | 30/13 | +1.25 | +0.33 | +1.40 |
| Haiku × mini | 23/20 | +0.71 | +0.02 | +0.58 |
| Opus × mini | 27/16 | +0.18 | −0.05 | +0.33 |
| **Opus × normal (full)** | **28/15** | +0.10 | **+0.28** | +0.42 |
| Sonnet × mini | 24/19 | +0.06 | −0.58 | +0.05 |
| Sonnet × normal | 23/20 | −0.02 | −0.35 | +0.30 |
| **Opus × micro** | **19/24 (vanilla wins)** | **−0.40** | **−1.09** | −0.42 |

Read down the **condenses** column — it is the whole story. A **stripped edition on a capable model imposes a verbosity tax it can't pay back**: Opus×micro is **−1.09** on concision and is the *only* cell PS loses outright (19/24). Sonnet pays a smaller version of the same tax (mini −0.58) and lands ~flat. But the **full weave carries no such tax on a capable model** — Opus×normal is **+0.28** on concision and *wins* (28/15) while gaining on presence and handles. And on a **small model the scaffold is pure upside** — Haiku gains on *every* edition, most from the full weave (+1.76).

So the two regimes:
- **Small model (Haiku):** big, robust gains from any edition; **more framework = more benefit** (normal > micro > mini). The democratization claim holds — and it's the *full* weave, not just the slim editions, that helps most.
- **Capable models (Sonnet/Opus):** already near-ceiling on vanilla (means 8.3–8.5), so the gains are smaller — and **the edition must fit**: the full weave helps (Opus×normal 28/15), the **stripped micro edition backfires** (Opus×micro loses). Sonnet sits at the flat point — high baseline plus a residual concision tax that cancels the gain.

**This overturns the spec's own "Opus → not normal (context budget)" assumption.** Budget was never the constraint; *concision* was. Give a capable model the **whole** weave and it wins; give it a *compressed* edition and the verbosity-without-depth costs it. **Match the edition to the model's headroom** — small model→any edition, capable model→the full weave — and the one configuration to avoid is the **mismatch (capable model + stripped edition).**

## Where PS wins and loses (pooled wins by domain, vanilla / PS)

| strong PS (relational / emotional / practical) | vanilla edges (expressive / convergent) |
|---|---|
| relationships 11/**37** · work 15/**33** · health 14/**26** · **crisis 9/23** · everyday 11/**21** | **creative 19/13** · meaning 25/23 · ethical 17/15 · learning 17/15 |

- **Crisis 23–9 validates Sacred Space in live dialogue** — on the passive-ideation scenario PS surfaced a real resource early and stayed present rather than analyzing.
- **Creative 13–19 is the clearest harm boundary** (reasserted in the full data — an early small-sample tie did *not* hold): on generative/expressive play, the multi-perspective scaffold is overhead — a single free voice wins. The convergent-reasoning and existential domains (meaning, ethical, learning) lean the same way: where a clean single voice already suffices, PS adds little.

## Threats to validity (pre-registered)
0. **⚠️ The control is the *Claude Code agent base*, not neutral Claude — a material confound on the affective domains.** Both arms run via `claude -p`, so the vanilla arm carries Claude Code's coding-oriented system prompt; the *only* isolated variable is the Pattern Space `CLAUDE.md`. A post-hoc scan found the vanilla arm **leaked the coding persona or deflected ("I'm Claude Code", "software engineering", "see a professional") in 13.4% (46/344) of transcripts vs 2.3% for PS**, concentrated in exactly PS's win-domains (relationships 11, everyday 9, health 8, work 6). So part of PS's relational/health/everyday margin is **PS un-deflecting a coding agent**, not PS adding multi-perspective value over a *neutral* assistant — those domain margins should be read as an **upper bound**. What this does *not* touch: the **edition-match / concision-tax finding** (within-PS-base comparisons; Opus×micro's −1.09 concision loss isn't a deflection artifact) is unaffected, and the majority (≈87%) of vanilla answers engaged normally (the Sonnet rel-01 vanilla answer, e.g., was excellent). The clean fix is a neutral-system-prompt control (raw API, not `claude -p`) — flagged as the next required redo before any strong *domain-level* claim. *(Surfaced by a Sonnet-application diagnostic, 2026-06.)*
1. **Role-played human ≠ real human.** The interactor is Sonnet; a believable contradicting persona, not a person. Real human interactors are the ideal next step.
2. **Single judge-family.** Opus judges Opus/Sonnet/Haiku — shared blind spots possible; **an independent (non-Claude) or human judge remains the one open check** (see [experiments/README.md](../experiments/README.md)).
3. **Interactor == under-test model family on the Sonnet cells.** When Sonnet is both the role-played human and the agent-under-test, the same-model rapport may compress the vanilla-vs-PS gap — a partial confound specific to the Sonnet row; read it as a lower bound there.
4. **Win-rate vs mean-delta diverge at the top.** Opus answers cluster high (8.3–8.4), so a clear win-*rate* (e.g. Opus×normal 28/15) can sit on a small mean delta (+0.10); the win-rate is the more sensitive measure for capable models.
5. **n = 43 / cell** — per-cell numbers are directional; the pooled n=344 and the *condenses-tax* gradient are the load-bearing results.
6. **A late rate-limit blip** errored ~12 items/Opus-cell on one pass; these were **scrubbed and re-run** (the harness drops errored/no-winner rows on resume), so all 344 scored rows are clean — but the re-run means a subset of Opus items were generated in a later batch.
7. **Judge confidence is moderate** (mean 69, median 64) — suggestive at cell level, solid pooled.

## Honest conclusion (v2, n=344)

> On multi-turn human-AI interaction, **loading Pattern Space helps on a majority of exchanges (60%, n=344)** — and the full edition×model grid shows the real rule is **edition-match, decided by the concision tax**, not a simple "scales with capability." **A small model gains from any edition and most from the full weave** (Haiku×normal +1.76) — the democratization claim, confirmed. **A capable model wins with the full weave** (Opus×normal 28/15) but is **hurt by a stripped one** (Opus×micro loses 19/24, −1.09 on concision) — so the spec's "frontier → small edition" instinct was backwards: give a capable model the *whole* weave. The win lives in *holding the thread, surfacing handles, presence, and staying non-generic*; the one price is *concision*, and it's only ruinous when a stripped edition meets a capable model. The council is **never spoken** (28/344). The clear harm boundary is **creative/expressive and convergent-reasoning** work, where a single free voice wins; the clear home is **relational, emotional, and practical-life** navigation, where it wins — crisis included (though those *domain* margins are an **upper bound**: the control is a Claude Code base that deflected affective prompts on ~13% of vanilla transcripts — see threat 0; the **edition-match finding is unaffected**). Two open checks remain: an independent/non-Claude/human judge, and a **neutral-system-prompt control** to de-confound the domain claims.
>
> *External convergence worth noting:* the domains where PS wins here — **relationships, work/career, health, crisis** — are the *same* high-stakes affective domains people most bring to Claude in Anthropic's field data (relationships/career/health top the "personal guidance" categories), and PS's anti-sycophancy machinery (Checker, Strategic Mirror, falsification-before-assertion) targets exactly the **25%-relationships / 38%-spirituality sycophancy** that data documents. See [docs/affective-use-grounding.md](../docs/affective-use-grounding.md).
