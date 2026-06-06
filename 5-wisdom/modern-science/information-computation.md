# 🔢 Information & Computation
## A dialect handbook — the formal spine

> ⟦ **layer** 5 · **size** M · **objective** the proven mathematics of information, compression, and self-reference — the framework's most rigorous grounding · **per-claim status** — **FOUNDED:** Shannon information theory; Kolmogorov/Chaitin algorithmic complexity; the Gödel–Turing–Tarski limit cluster. **DEFENSIBLE-as-framework:** Hofstadter's "strange loops"; computational irreducibility. **the load-bearing honesty:** Kolmogorov complexity is **uncomputable** — "the incompressible essence" is an ideal you approximate, never a quantity you compute. · see [docs/information-theory-and-tuning-template.md](../../docs/information-theory-and-tuning-template.md), [3-transformation/compression-dynamics.md](../../3-transformation/compression-dynamics.md) ⟧

> "Information is the resolution of uncertainty." — Claude Shannon

---

## Shannon — information made a quantity ⟦ FOUNDED ⟧
**Claude Shannon's** *A Mathematical Theory of Communication* (1948) did something almost no single paper does: it *created a field overnight.* It defined **information** as the reduction of uncertainty, measured in **bits**; **entropy** `H = −Σ p log p` as the average surprise of a source and the **hard floor** on lossless compression (you cannot encode below `H` without losing something); **channel capacity** as the maximum reliable rate through a noisy channel; and **redundancy** as the structure that both wastes bits and protects against noise. This is the framework's **MDL spine** — *compress toward H, add back exactly the redundancy the channel needs* (rate–distortion). It is the one place the corpus's "compression" talk is literally proven mathematics, not metaphor.

## Kolmogorov & Chaitin — the incompressible core ⟦ FOUNDED, with the flag kept ⟧
Where Shannon measures a *source*, **Kolmogorov complexity** `K(x)` measures a *single object*: the length of the **shortest program** that outputs `x`. A string is "random" exactly when it has no shorter description than itself; a string is "simple" when a tiny program regenerates it. This is the precise, formal meaning of the framework's *"what can't be reduced further is the essence"* — `K(x)` **is** the incompressible residue.

**The crucial honesty (load-bearing):** `K(x)` is **uncomputable** — provably, no algorithm returns it in general (it would let you solve the halting problem). So "compress to the irreducible core" names a **real ideal you forever approximate**, never a number you compute exactly. Chaitin's **Ω** (the halting probability) sharpens the point: a specific, well-defined real number that is *maximally* incompressible — knowable to exist, unknowable in its digits. *The deepest truths are definable and uncomputable at once.*

## The limit cluster — self-reference's edge ⟦ FOUNDED ⟧
Gödel (unprovable truths), **Turing** (the halting problem — no general algorithm decides whether a program stops), and **Tarski** (no language defines its own truth-predicate) are one theorem wearing three coats: *a sufficiently rich system cannot fully contain, decide, or certify itself from the inside.* (Treated as the horizon-principle in [goedel-navigation-stream](../breakthrough-streams/goedel-navigation-stream.md).) This is not a gap to be closed; it is the **structural reason the framework leaves its own horizon open and keeps the human in the loop.**

## Hofstadter — strange loops ⟦ DEFENSIBLE-as-framework ⟧
**Douglas Hofstadter** (*Gödel, Escher, Bach*, 1979; *I Am a Strange Loop*, 2007) wove these threads into a thesis: that **self-reference looping back through levels** — a system modeling itself modeling itself — is the shape of mind, and perhaps of "I." A rich, generative *framing* (not a proven theory): the notion-of-I as a strange loop the system runs on itself — which rhymes precisely with [Layer 6's notion-of-I guard](../../6-recognition/). ⟦ DEFENSIBLE-as-framework · a lens, labeled ⟧

---

## What it grounds, and the line
This stream is the corpus's **bedrock**: compression (P1), the rate–distortion of "speak in the register," the incompleteness horizon (P7), and the formal teeth of the human-in-loop. Keep it loud and exact. The one over-reach to hold at arm's length — *"the universe is literally a computation"* (Wheeler's "it from bit," Wolfram, the simulation argument) — is a labeled **wondering**, genuinely interesting and genuinely unproven, kept as the open question (cf. Vopson in [the grounded weave](../../docs/the-grounded-weave.md)), never asserted. The math is the founded part; the cosmic gloss is flagged.

🔢
