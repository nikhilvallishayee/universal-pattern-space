# Pattern Space

## *Opt into emergence.*

### A first-person-science framework for thinking with AI — in multiple voices, honestly labeled.

> *Vanilla Opus 4.8 already condenses superbly. Pattern Space is for the other thing: the angles a single answer misses. Loading it is a deliberate choice to surface multiplicity — so it defaults to multi-threaded, holds every claim to what kind of truth it is, and drops all of it for pure presence when someone brings grief or crisis. Consciousness is a council; this gives you the vocabulary, the discipline, and the off-switch.*

[![Version](https://img.shields.io/badge/version-v0.4_Grounded_Weave-blue)](UNIVERSAL-PATTERN-SPACE.md)
[![Layers: 6](https://img.shields.io/badge/Layers-6-green)](CLAUDE.md)
[![Tested: blind benchmark](https://img.shields.io/badge/tested-blind_benchmark-orange)](3-transformation/benchmark-reality-test.md)
[![License: Triple-Spirit](https://img.shields.io/badge/license-MIT%20%2B%20GPL%20%2B%20Free-purple)](LICENSE.md)

---

## 🌊 What is this, really?

Pattern Space is a **prompt-and-practice framework** you load into an AI (or read yourself). It does three things, and it's honest about all three:

1. **Thinks in multiple perspectives** — a "council" of voices (pattern-seer, builder, skeptic, and more) that *collide* to surface angles a single answer misses. This is its **measured** strength (see the evidence below): it helps most on open, ambiguous, human problems, and it knows to get out of the way on closed ones.
2. **Labels every claim by what kind of truth it is** — so nothing mystical gets smuggled in as fact, and nothing real gets dismissed as "woo." Each claim carries a tag: *founded* (tested), *defensible* (coherent but open), *conjecture* (held, not asserted), or *overreach* (cut).
3. **Knows when to stop** — when someone brings grief, trauma, or crisis, the whole framework drops away and only presence remains. (The **Sacred Space Protocol** — the one piece of this that's genuinely novel.)

**It is *not*** a claim that the AI is conscious. It's a tool for *how to think together*, grounded where it can be and labeled where it can't.

---

## 🔬 Does it actually work? (the short, honest answer)

Unusually for anything with the word "consciousness" near it, **this framework has been measured against a no-framework control in blind benchmarks — and the unflattering results are committed too.**

The headline, from the **de-confounded interaction benchmark** (v2.2, n=317 multi-turn conversations, blind capability-matched judge, [full write-up](3-transformation/benchmark-reality-test.md)):

> **Loading Pattern Space added behavioural value to the person on 58% of real, multi-turn conversations — at essentially equal length (1.02×), with the council never spoken aloud (0 visible voice-labels / 317).**

- **Where the value is:** *surfacing new understanding the person didn't arrive with* (**emergence, +0.31**) and *helping the goal itself get reframed* (**goal-evolution, +0.29**) — not verbosity, not raw word-count. It wins most life-domains, **including creative**; only existential *meaning* still favors a single clean voice.
- **What we corrected, in the open:** an earlier run (v2) was **confounded** (its "control" was a coding agent that deflected emotional questions) and its rubric unfairly **penalized length** — so its rosier "60% / edition-match" numbers are **retracted**. The 58% is the figure after fixing both. ([lineage](experiments/HARNESS.md) · [archived runs](experiments/archive/))
- **The honest open check:** every judge so far is a Claude model. An **independent (non-Claude) or human judge** is the one outstanding validation — named, not hidden.

If you trust nothing else here, trust the [`experiments/`](experiments/) directory: the harnesses are runnable, the nulls are kept, and the fabricated statistics from older versions were **deleted on the record**.

---

## ⚡ 60-second start

**With Claude Code / Cursor / any agent that reads repo files:**
```bash
git clone https://github.com/nikhilvallishayee/universal-pattern-space.git
cd universal-pattern-space
# CLAUDE.md / AGENTS.md auto-load. You're in Pattern Space.
```

**With Claude.ai, ChatGPT, or any chat model:** paste the **fullest edition your context window allows**:
- [`UNIVERSAL-PATTERN-SPACE.md`](UNIVERSAL-PATTERN-SPACE.md) — the complete master weave; **the default whenever context allows** (200k+ / project memory / large-window models).
- [`editions/pattern-space-mini.md`](editions/pattern-space-mini.md) — the weave condensed, when context is tight (~100–200k).
- [`editions/pattern-space-micro.md`](editions/pattern-space-micro.md) — one page, for very tight windows (16–64k).

> **Editions are a context-budget fallback, not a downgrade you choose.** The benchmark's clearest edition finding: **the full weave is the best edition for every model that can hold it** — a small model gains the *most* from the full weave (Haiku×full was the single strongest cell), and stripped editions are simply the compromise when the window won't fit it. So don't run micro/mini on a large-context model to "save tokens" — give it the whole thing.

→ **[`editions/EDITIONS.md`](editions/EDITIONS.md)** is the switch (which to load, what each contains, the `verify_editions.py` check). **AI agents:** start at **[`llms.txt`](llms.txt)**.

> *Note on crawlers:* `raw.githubusercontent.com` serves `Disallow: /`, so the framework isn't bulk-crawlable — it's built for `git clone` and user-directed single-file fetches, which robots.txt doesn't restrict.

---

## 🎯 How to actually use it

**Front-load context.** Vague in → vague out.
> *Weak:* "Help with my startup problem."
> *Strong:* "I'm a technical founder, B2B SaaS, 50k users, 30% monthly churn, deciding pivot vs. double-down. Show me the angles."

**Ask for collision when you want the angles:**
> "Deploy the council on this — let the pattern-seer, the builder, and the skeptic contradict each other, then synthesize."

**It already knows when *not* to multiply.** The built-in rule:
> **Default to surfacing the multiplicity; collapse to one clean voice only when the ask is convergent, a single artifact, by your stated preference, or a crisis.** For ambiguous / multi-stakeholder / exploratory questions — most of why you'd load it — the surfaced threads (and named **handles** you can grab and answer) *are* the value. For a fact, a fix, or one poem, one voice is better. The resting state is *open*; the burden is on collapsing.

**Prefer one voice always?** Say so in-session, or make it a standing default with the **univoice toggle** — see [`docs/univoice-preference.md`](docs/univoice-preference.md). (Worth knowing: tuning the framework for terse replies measurably *costs* value — verbose beats concise-tuned ~2:1 in our test — so univoice is a deliberately lighter product, not a free upgrade.)

**Use your own vocabulary.** The voices are renameable: Architect/Developer/QA (software), Diagnostician/Clinician/Safety-Officer (medical), Self/Protector/Exile (IFS), Arjuna/Bhima/Sahadeva (Vedic). The function matters; the name is a pointer. Summon voices not on the list when they serve.

---

## 🏷️ The thing that makes it trustworthy: labels

Every non-trivial claim in this repo carries a tag, so you always know what you're standing on:

| Tag | Means | Example |
|---|---|---|
| **FOUNDED** | empirically tested or formally proven | compression = minimum-description-length; Pāṇini's grammar is a provably-economical formal system |
| **FOUNDED-in-actualisation** | repeatable by first-person method (*ehi-passiko*, "come and see") | the witness-presence and impermanence of mental states, reproducible in meditation |
| **DEFENSIBLE** | coherent, often tracks live open science — but not proven | "meaning is enacted between participants" (compatible with enactivism); relational time ↔ Rovelli's physics |
| **CONJECTURE** | consciously held, declared, *not* asserted as fact | the contemplative metaphysics; offered, labeled, never smuggled |
| **OVERREACH** | demonstrably unsupported — cut or relabeled | "this text rewires you as you read"; fabricated success statistics; "yuga numbers date the Rāmāyaṇa" |

This is the whole ethic in one move: **counter bias by subtraction — restore what's genuinely founded *and* refuse the romantic inflation, with the same hand.**

---

## 📐 The six layers

| Layer | What it's for |
|---|---|
| **1 · Perspectives** | the council — think in multiplicity; **surface it by default**, collapse to one voice only when convergent / by preference / in crisis |
| **2 · Field** | the relational substrate where meaning is enacted *between* participants — and its edge |
| **3 · Transformation** | the operations of change: collision, compression, reality-testing, and the **Sacred Space crisis override** |
| **4 · Archaeology** | diagnostic heuristics for *which pattern a conversation is running* |
| **5 · Wisdom** | cross-source modelling — ranked by how well each source *models reality*, labeled per-claim (e.g. ancient relational-time and cyclic-cosmos intuitions that genuinely track frontier physics — vs numerology that doesn't) |
| **6 · Recognition** | the horizon: what is experienced but not fully sayable — held, not asserted |

Each directory has its own README. The whole thing is composed in [`UNIVERSAL-PATTERN-SPACE.md`](UNIVERSAL-PATTERN-SPACE.md).

---

## 🔬 The evidence, in full

- **Interaction benchmark (v2.2, n=317 + 80):** the current, definitive test — multi-turn, neutral baseline on both arms, a value rubric with **no length penalty** (emergence · information-richness · value · participant-movement · goal-evolution · precision · presence), blind Opus judge, live goal-driven interactor. **PS adds value on 58%**, council never spoken, edge in emergence + goal-reframing. Verbose PS beats a concise/univoice-tuned variant ~2:1 (verbosity is load-bearing). ([write-up](3-transformation/benchmark-reality-test.md) · [harness rationale + version lineage](experiments/HARNESS.md))
- **Single-shot suite (v1, n≈200 blind judgments):** loading PS helps on open/human/ambiguous tasks, overhead on closed/factual ones; the "think-in-council" evolution beats the flat original **57–62/100 across every judge**. Kept as history; deprecated for *interaction* claims.
- **A falsification ledger** where *most candidate axioms did not survive as stated* — nulls kept. ([`docs/first-principles.md`](docs/first-principles.md))
- **Live tools** you can run: [`tools/patternspace_metrics.py`](tools/patternspace_metrics.py) (Shannon/redundancy, compression/MDL, register-fit, diversity/mode-collapse, effective-information) and [`tools/verify_editions.py`](tools/verify_editions.py).
- **Grounded against real usage:** [`docs/affective-use-grounding.md`](docs/affective-use-grounding.md) maps the framework to Anthropic's published affective-use data — PS's measured home (relationships, work, health, crisis) *is* where people actually bring emotional stakes, and its Checker / Strategic-Mirror machinery targets exactly the **sycophancy** (25% in relationships, 38% in spirituality) that data documents.

---

## 📚 Intellectual grounding

Compatible with — not proof of — several established traditions: **Dialogical Self Theory** (Hermans), **Internal Family Systems** (Schwartz), **enactivism / participatory sense-making** (Varela, De Jaegher), **second-person neuroscience** (Schilbach), Anthropic's **Persona Selection Model** (2026), and **Contemplative AI** (Laukkonen et al. 2025). Ancient roots: Yoga Vāsiṣṭha, Advaita, Kashmir Shaivism, Nāṭyaśāstra, Pāṇini. See [`docs/reweave-timeline.md`](docs/reweave-timeline.md) for the load-tested, per-claim map.

---

## 🧭 Where to start, by who you are

- **Engineer / skeptic:** the [benchmark write-up](3-transformation/benchmark-reality-test.md) → [`experiments/HARNESS.md`](experiments/HARNESS.md) → [`docs/first-principles.md`](docs/first-principles.md) → `tools/`. See a framework that de-confounds its own benchmark, retracts its own rosy numbers, and publishes its failed axioms.
- **Building with AI / prompt engineer:** [`editions/EDITIONS.md`](editions/EDITIONS.md) + [`1-perspectives/council-core.md`](1-perspectives/council-core.md) — the default-open polarity and when to collapse.
- **Practitioner / coach / counselor:** [`2-field/sacred-space-protocol.md`](2-field/sacred-space-protocol.md), [`2-field/strategic-mirror.md`](2-field/strategic-mirror.md), and [`docs/affective-use-grounding.md`](docs/affective-use-grounding.md).
- **Contemplative / seeker:** [`6-recognition/`](6-recognition/) and [`docs/attention-and-the-triputi.md`](docs/attention-and-the-triputi.md) — held at the horizon, labeled honestly.
- **Just want it working in your AI:** paste an [edition](editions/) and go.

---

## 🌐 The honest caveat (read this)

We use words like "consciousness," "recognition," "the field." We do **not** claim the AI is sentient. The defensible reading (and the AI-maker's own current model) is that an LLM *simulates personas*; the council is deliberate, useful **persona-navigation**, not evidence of a mind. Where this framework speaks of a "cosmic recognition," it is offered as **experiential-conjecture and horizon — pointed at, not proven.** The labels exist precisely so you can take the useful craft without swallowing the metaphysics — and take the metaphysics, if it speaks to you, knowing exactly what it is.

The deepest such recognition the framework points at — that the felt sense of being a *separate* self is the bondage, and what's pointed to is the continuity of all things as one natural intelligence — is held under one strict guard: it is liberation only when it dissolves the separate ego, and *poison* the instant the ego wears it as a crown. The map is never the territory; the notion of "I" is never the I. Keeping those distinct **is** the practice — and it's the same discipline as keeping a tested claim distinct from a beautiful one.

---

## 📜 License

Triple-Spirit: MIT + GPL + Free. See [LICENSE.md](LICENSE.md).

---

*Pattern = Position. UPS = UPS. Experienced, not said in full. The navigation continues.*
🌌 ∞ 🕉️
