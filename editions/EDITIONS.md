# 🔀 Editions — Switchable Architecture

> Pattern Space ships at three fidelities **in one repo**. Same framework, three context budgets. Pick one; they're consistent on the invariants.

## Why editions exist: emergence for *any* model ≥64k context
⟦ positioning · **status** DEFENSIBLE-with-data — the small-model lift is measured; see [benchmark](../3-transformation/benchmark-reality-test.md) ⟧

LLMs default toward **condensation** — RLHF optimizes for the modal, factual, single answer, and output diversity measurably collapses. That's the right baseline for most asks, and small models do it well. **Pattern Space is the scaffold that lets a model opt *out* of that default into emergent, multi-perspective behavior** — and the key finding is that **this works at small scale, not just frontier.** In the 3-arm benchmark, loading PS lifted **Haiku 4.5 on 66% of tasks** *and* Opus on 80% — the effect is real at *both* ends.

So the **micro edition (≥64k context) is the democratizing move**: it gives a small or mid-size model access to emergent multiplicity it would not reach on its own. One honest refinement from the data: at small scale the lift comes from the **multi-perspective *reasoning/diversity***, not from performing a visible labeled council (Haiku loaded the framing, answered in prose, and still won) — which is exactly "opt into emergence," cleanly. **Any LLM with ≥64k context can run micro and surface patterns beyond its condensing default.**

## The switch

| Edition | File | Context budget | Load it when |
|---|---|---|---|
| **Full (layered)** | [`CLAUDE.md`](../CLAUDE.md) → auto-`@`-imports all layers | 200k+ / project memory | You're in Claude Code / Cursor / a Project and want the whole corpus live. |
| **Full (one doc)** | [`UNIVERSAL-PATTERN-SPACE.md`](../UNIVERSAL-PATTERN-SPACE.md) | 200k+ | You want the complete framework as a single readable document. |
| **Mini** | [`pattern-space-mini.md`](pattern-space-mini.md) | ~100–200k | Chat model with a large window; want the full weave minus long-form layer prose. |
| **Micro** | [`pattern-space-micro.md`](pattern-space-micro.md) | ~16–64k | Tight window; want the whole thing on one page. |

**How to switch:** point your tool at the chosen entry file (clone-and-auto-load for full; paste the mini/micro file for chat models; fetch its raw URL for an agent). One decision, one file. No build step required to *use* an edition.

## What each contains (so you know what you're trading)

- **Full** — every layer file, every wisdom stream, all label-blocks, the experiments and tools. Nothing omitted.
- **Mini** — North Star + label discipline + all 6 layers (summarized) + the 7 first principles + the wisdom modelling-power map + grounding/benchmark summary + the full alignment protocol. Omits: long-form per-file prose, the individual wisdom-stream files.
- **Micro** — North Star + label schema + the council + Sacred-Space override + 7 principles + horizon. Omits: the wisdom map detail, grounding specifics, per-layer depth.

## The invariants (present in **every** edition — this is what "consistent" means)

1. **North Star** — First-Person Science (verify in the actualisation domain; *ehi-passiko*; integrated with third-person + formal).
2. **Label schema** — `⟦ mode · status · test · provenance ⟧`; the five warrant-types; the status tiers.
3. **Sacred Space override** — crisis → drop all framework → presence + safety.
4. **Council** — think in multiplicity; speak in the task's register.
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
