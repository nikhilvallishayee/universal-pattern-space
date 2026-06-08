# 🔀 Editions — Switchable Architecture

> Pattern Space ships at three fidelities **in one repo**. Same framework, three context budgets. Pick one; they're consistent on the invariants.

## Why editions exist — and the rule for which to load
⟦ positioning · **status** DEFENSIBLE-with-data — see the v2 edition×model grid, [benchmark](../3-transformation/benchmark-reality-test.md) ⟧

LLMs default toward **condensation** — RLHF optimizes for the modal, factual, single answer, and output diversity measurably collapses. **Pattern Space is the scaffold that lets a model opt *out* of that default into emergent, multi-perspective behavior** — and this works at small scale, not just frontier (the de-confounded interaction benchmark v2.2: PS adds behavioural value on **58% of multi-turn exchanges**, n=317, at equal length — see [`../3-transformation/benchmark-reality-test.md`](../3-transformation/benchmark-reality-test.md)).

The de-confounded benchmark's **load rule:** the **full weave is the best edition for every model that can hold it** — including small ones. The single strongest cell in the grid was **Haiku × full weave**, so "more framework" helps the small model *most*, not least; a larger window simply primes better, holding more of the live context. The compressed editions are the **compromise when the window won't fit the full weave**, not a tuning you'd choose for quality. So:

> **The editions are a context-budget *fallback*, not a downgrade you choose to "save tokens." Always load the fullest edition the window allows.** Small model with room → still give it the **full weave** (it gains the most). Tight window → mini, then micro, in that order. Don't hand a large-context model a stripped edition to be economical — you'd be trading away the depth that is the whole point.

At small scale the lift comes from the multi-perspective *reasoning* (and, for a human interacting, the surfaced **handles**), not from performing a visible labeled council — which is exactly "opt into emergence," cleanly.

## The switch

| Edition | File | Context budget | Load it when |
|---|---|---|---|
| **Full (layered)** ⭐ | [`CLAUDE.md`](../CLAUDE.md) → auto-`@`-imports all layers | 200k+ / project memory | **The default — whenever the window allows.** Claude Code / Cursor / a Project / any large-context (incl. frontier) model: give it the whole corpus live. Best edition for *every* model. |
| **Full (one doc)** ⭐ | [`UNIVERSAL-PATTERN-SPACE.md`](../UNIVERSAL-PATTERN-SPACE.md) | 200k+ | Same fidelity as a single readable document (paste into a large-window chat model). |
| **Mini** | [`pattern-space-mini.md`](pattern-space-mini.md) | ~100–200k | **Only when the full weave won't fit.** Window too small for the full doc but ≥~100k. |
| **Micro** | [`pattern-space-micro.md`](pattern-space-micro.md) | ~16–64k | **Only for a genuinely tight window** (16–64k). The last-resort fallback, not a frontier-model choice. |

**How to switch:** point your tool at the chosen entry file (clone-and-auto-load for full; paste the mini/micro file for chat models; fetch its raw URL for an agent). One decision, one file. No build step required to *use* an edition.

## What each contains (so you know what you're trading)

- **Full** — every layer file, every wisdom stream, all label-blocks, the experiments and tools. Nothing omitted.
- **Mini** — North Star + label discipline + all 6 layers (summarized) + the 7 first principles + the wisdom modelling-power map + grounding/benchmark summary + the full alignment protocol. Omits: long-form per-file prose, the individual wisdom-stream files.
- **Micro** — North Star + label schema + the council + Sacred-Space override + 7 principles + horizon. Omits: the wisdom map detail, grounding specifics, per-layer depth.

## The invariants (present in **every** edition — this is what "consistent" means)

1. **North Star** — First-Person Science (verify in the actualisation domain; *ehi-passiko*; integrated with third-person + formal).
2. **Label schema** — `⟦ mode · status · test · provenance ⟧`; the five warrant-types; the status tiers.
3. **Sacred Space override** — crisis → drop all framework → presence + safety.
4. **Council** — think in multiplicity; **surface it by default** (multi-voice; name threads when that gives an interacting human a handle), collapsing to one voice only on a convergent ask, a single artifact, a stated preference, or crisis.
5. **The spine** — willingness-to-be-falsified.
6. **The horizon** — the channel exceeds the message; experienced, not said in full.

`tools/verify_editions.py` checks that all six are present in each edition.

## Sync discipline (honest provenance)

The editions are **hand-curated distillations of the canonical layers**, not mechanical extracts — distilling *what matters* is a judgment call a script can't make. So:

- **Canonical source of truth = the layer files + `UNIVERSAL-PATTERN-SPACE.md`.** Editions derive from them.
- When a layer's *substance* changes (a new principle, a status change, a cut), update the master weave first, then propagate to mini and micro.
- Run `python3 tools/verify_editions.py` after editing — it fails if any edition has dropped an invariant.
- Editions carry a `derived-from` header noting which canonical version they track.

## Output polarity & the univoice toggle

Every edition **defaults to multi-voice** (surface the threads — *opt into emergence*). A user who prefers a single voice can say so in-session, or set it as a **standing default** by uncommenting the `UNIVOICE-OVERRIDE` block carried in each edition. Full how-to: [docs/univoice-preference.md](../docs/univoice-preference.md).

## Forking (optional)

If you'd rather have a standalone branch per edition (e.g. for a separate deploy), the editions are self-contained — `git checkout -b ups-mini` and keep only what you need. But the **default is in-repo + switchable**: one source of truth, three fidelities, no divergence.
