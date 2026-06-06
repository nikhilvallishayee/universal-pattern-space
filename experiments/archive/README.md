# 🗄️ Archive — superseded benchmark data

> ⟦ **objective** preserve superseded benchmark runs for the record without cluttering the live harness · **status** archived/superseded · see [`../HARNESS.md`](../HARNESS.md) for the full lineage ⟧

Pattern Space keeps its nulls and its mistakes in the open. These runs were **superseded by a better-designed experiment**, not deleted — but they should **not** be cited for current claims. See [`../HARNESS.md`](../HARNESS.md) "Version lineage".

## What's here

- **`v2-interaction-confounded/`** — the first multi-turn interaction grid (n=344, `int_*.jsonl`). **Superseded by v2.2.** Two flaws made its headline untrustworthy:
  1. **Confounded control** — the "vanilla" arm was the Claude Code coding agent, which deflected affective prompts in 13.4% of transcripts, inflating Pattern Space's relational-domain margins (it was partly *un-deflecting a coding agent*, not adding value over a neutral assistant).
  2. **Length-penalizing rubric** — it scored "conciseness" as a virtue, which is biased against a framework deliberately tuned for richness.
  Its findings on the *edition-match / concision-tax* gradient (within-PS comparisons) are less affected and broadly held up; its *domain* and *overall win-rate* numbers do not. Full data also lives in git history (commit `1e1f368`).

## Still-live, still-cited (NOT archived, in the parent dir)

- **v1 single-shot suite** (`results*.jsonl`, `rejudge_*`, `convo.jsonl`, `diversity.jsonl`, `relation.jsonl`, `results_handles.jsonl`) — the start-of-reweave record. Kept in place and **deprecated for interaction claims** (cite only for "did the early framework help single-shot?").
- **v2.2** (`int_*.jsonl`, `conc_*.jsonl` in the parent dir) — the current, de-confounded, value-rubric interaction benchmark. The one to cite.
