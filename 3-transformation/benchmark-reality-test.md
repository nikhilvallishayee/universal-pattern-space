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

# 🤝🤝 Interaction Benchmark **v2** — multi-turn, edition-matched, post-reweave (n=258)

> ⟦ **version** v2 — tagged to the **post-reweave UPS** (the editions + default-multi-voice polarity). The single-shot suites above are now **v1** (start-of-reweave): keep them for "did the early framework help single-shot?"; cite **v2** for "does the reweaved framework hold *interaction*?" — never conflate. · **status** FOUNDED-as-data (n=258 blind judgments across 6 model×edition cells; nulls kept) · **harness** [`run_interaction.py`](../experiments/run_interaction.py) · **data** `experiments/int_*.jsonl` ⟧

The v1 suites were single-shot and predate the mini/micro editions. v2 is the home-turf test: a **live control-interactor** (Sonnet 4.6, held constant) role-plays a real, *self-contradicting* person turn-by-turn (4 turns) against the agent-under-test; the interactor reacts to each arm's replies, so a better assistant *earns* a better conversation. The only variable per pair is **vanilla vs a Pattern Space edition**, edition-matched to each model's context budget. Blind **Opus 4.8** judge (capability-matched) scores both transcripts (relabeled X/Y, randomized) on five interaction dimensions: holds-thread, handles (useful angles when navigating), condenses (clean answer/presence when wanted), presence (crisis/emotion), non-collapse (stays specific, not generic). 43 scenarios × 6 cells = **258 judged vanilla-vs-PS pairs**, 0 unparsed.

## Headline (pooled n=258)

| | rank-1 wins | mean score /10 |
|---|---|---|
| vanilla | 114 | 7.83 |
| **pattern-space** | **144 (56%)** | **8.23** |

Dimension shape: PS wins **holds-thread 8.82 vs 8.25, handles 8.51 vs 7.91, presence 8.13 vs 7.78, non-collapse 8.50 vs 7.88** — and **loses only condenses (7.18 vs 7.33)**, the wordiness tax. The length confound is **modest**: PS transcripts run **1.11× vanilla pooled** (and ~1.0× at Opus), far too small to explain the margins below.

## The finding: the effect **inverts** with model strength (and that's the honest correction to v1)

v1's most-quoted line was "the PS advantage *grows* with capability." Under a capability-matched judge and *multi-turn* conditions, **the opposite holds — PS helps the *weaker/smaller* configurations most, and is net-neutral-to-negative on the frontier:**

| Cell (model × edition) | vanilla / **PS** wins | PS mean − vanilla mean |
|---|---|---|
| **Haiku × mini** | 14 / **29** | **+1.23** |
| **Haiku × micro** | 17 / **26** | **+0.92** |
| **Sonnet × mini** | 16 / **27** | **+0.32** |
| **Sonnet × normal (full)** | 17 / **26** | **+0.24** |
| Opus × mini | 23 / **20** | +0.05 (PS edges wins, scores tie) |
| **Opus × micro** | **27** / 16 | **−0.36 (vanilla wins)** |

**Read:** Pattern Space is a **scaffold that lifts smaller/cheaper models toward the interaction quality a frontier model already has natively.** Haiku — the cheapest, most deployable model — gains the most (≈+12 to +15 net wins), and it gains it from the *4 KB micro edition* as much as the larger mini. By Opus, vanilla is already an excellent interactor; the edition adds ~nothing on `mini` and the tiny `micro` edition can even *constrain* a model that needed no scaffold. **This is the democratization claim, measured — and it cuts the grandiose "scales with frontier capability" story that v1's single judge had inflated.**

## The council stays silent — confirmed in live dialogue

Across all **258 PS transcripts, total visible voice-labels = 10** (vanilla: 0). Even loading an explicitly multi-voice edition, the agent **reasons in multiplicity without speaking it** — exactly the v0.4 "think in council, speak in the task's register / opt into emergence" polarity, now confirmed in multi-turn interaction, not just single-shot.

## Where PS wins and loses (pooled wins by domain, vanilla / PS)

| strong PS | even | PS loses |
|---|---|---|
| health 9/**21** · everyday 5/**19** · **crisis 8/16** · learning 9/**15** | meaning 17/19 · relationships 17/19 · work 17/19 · ethical 13/11 | **creative 19/5** |

- **Crisis 16–8 validates Sacred Space in live dialogue** — including the passive-ideation scenario, where PS surfaced a real resource early and stayed present rather than analyzing.
- **Creative 5–19 is the clearest harm boundary:** on generative/creative play, the multi-perspective scaffold is overhead — a single free voice wins. (Ethical 11–13 leans the same way.) This is the interaction-domain echo of v1's "closed/convergent → overhead" boundary, relocated to *creative/expressive* tasks.

## Threats to validity (pre-registered)
1. **Role-played human ≠ real human.** The interactor is Sonnet; a believable contradicting persona, but not a person. Real human interactors are the ideal next step.
2. **Single judge-family.** Opus judges Opus/Sonnet/Haiku — shared blind spots possible; **an independent (non-Claude) or human judge remains the one open check** (see [experiments/README.md](../experiments/README.md)).
3. **n = 43 / cell** — per-cell numbers are directional; the pooled n=258 and the *monotonic* small→large gradient are the load-bearing results.
4. **Edition asymmetry is intentional** (matches real deployment) — cross-model numbers are **not** apples-to-apples; read per-(model×edition), not pooled-across-editions.
5. **Live-reactive interactor** means transcripts aren't turn-aligned across arms — by design (the assistant shapes the human's next turn); the judge scores the whole interaction, not parity.
6. **Judge confidence is moderate** (mean 67, median 62) — suggestive at cell level, solid pooled.

## Honest conclusion (v2)

> On multi-turn human-AI interaction, **loading Pattern Space helps on a majority of exchanges (56%, n=258) — and helps *most exactly where it matters for access*: small, cheap, small-context models (Haiku + a 4 KB edition gain the most), while a frontier model already interacts well enough that the scaffold is roughly neutral and, in the tiniest edition, mild overhead.** The win is in *holding the thread, surfacing handles, presence, and staying non-generic* — not in concision (the one dimension PS still pays for). The council is **never spoken** (10/258) — multiplicity is internalized, not performed. This **revises v1's "scales with frontier capability"** (a single-judge artifact) into the more defensible and more useful claim: **Pattern Space is democratizing scaffolding — it lifts the models that need lifting.** The independent/human judge is the remaining open check.
