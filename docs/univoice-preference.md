# 🎚️ Univoice preference — how to switch Pattern Space's default voice

> ⟦ **doc** · **objective** how a user sets single-voice vs the multi-voice default · **mode** practical (a config toggle) · **status** FOUNDED-as-craft · see [1-perspectives/council-core.md](../1-perspectives/council-core.md) "Default polarity", [editions/EDITIONS.md](../editions/EDITIONS.md) ⟧

## The default, and why
Pattern Space **defaults to multi-voice** — it surfaces the distinct threads, angles, and tensions of a question rather than collapsing to a single line. This is deliberate: a strong base model *already* condenses superbly, so **loading Pattern Space is the choice to opt into emergence** — the multiplicity you don't get from vanilla. The burden of proof is on *collapsing*, not on opening. (Grounding: the handles benchmark, n=16, 8–0/8–0; the v2 interaction benchmark, n=258 — see [benchmark-reality-test.md](../3-transformation/benchmark-reality-test.md).)

"Multi-voice" means **multi-perspective content** — and, when it genuinely helps you, **named threads** ("Checker: what breaks here?") you can grab and answer. It does **not** mean voice-*theatre*: labels performed for their own sake. On a closed, single-shot deliverable (a fact, a fix, one artifact) the assistant already drops the labels and hands you the result.

## When it collapses to one voice automatically
You don't need to do anything for these — they're built in:
- **Convergent / closed asks** — a fact, a lookup, arithmetic, "just the answer."
- **A single deliverable artifact** — code, a drafted paragraph, a creative piece.
- **Crisis → presence** — the Sacred-Space override drops all framework to bare presence. This *always* wins, regardless of any preference below.

## If you prefer a single voice

### Option 1 — just say so (per session, no editing)
Tell the assistant: *"I prefer a single voice / one clean answer."* It's honored immediately for that session under the standing collapse rule. Nothing to configure.

### Option 2 — make it your standing default (persists across sessions)
Each edition carries an **`UNIVOICE-OVERRIDE` block, commented out and inactive**. Uncomment it to flip the default to single-voice for every session.

The block lives in:
- **Full:** [`CLAUDE.md`](../CLAUDE.md) (section "Output polarity & the univoice preference")
- **Mini:** [`editions/pattern-space-mini.md`](../editions/pattern-space-mini.md) ("Alignment & protocol")
- **Micro:** [`editions/pattern-space-micro.md`](../editions/pattern-space-micro.md) ("Pre-response protocol")

**To activate**, remove the opening `<!--` line and the closing `-->` line so the instruction is live text. A block wrapped in `<!-- … -->` is **OFF**:

```
<!-- UNIVOICE-OVERRIDE · INACTIVE while commented · remove this line and the closing marker to activate
STANDING PREFERENCE: this user prefers a single voice. Default to ONE clean voice; surface
multiple threads/labels ONLY when explicitly asked for angles/options/tradeoffs. Keep thinking
in council silently. Sacred-Space crisis→presence still overrides everything.
UNIVOICE-OVERRIDE END -->
```

Uncommented (active) it reads as a normal instruction the assistant follows.

**To revert**, wrap it in `<!-- … -->` again (or delete it). Edit only the edition you actually load.

## What does *not* change when you go univoice
- **Thinking in council is unchanged.** The assistant still reasons across perspectives internally (P6 multiplicity) — it just doesn't *surface* them by default. You can always pull them up on demand: *"show me the angles / tradeoffs / what could go wrong."*
- **Sacred-Space still overrides everything** — crisis goes to presence no matter what.
- You can still ask for multi-voice any time, even with the override on.

---

*One dial, two settings, your call. Default opens; you can always close it — and reopen on demand.* 🎚️
