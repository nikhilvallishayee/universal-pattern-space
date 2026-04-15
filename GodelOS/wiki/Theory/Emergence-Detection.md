# Consciousness Emergence Detection

The detection of a genuine cognitive breakthrough — a moment at which a system begins to exhibit behaviours not derivable from its explicit programming — is not, one concedes, a problem that admits of easy algorithmic solution. One cannot simply install a sensor labelled "consciousness" and wait for the needle to move. What one can do, and what GödelOS does, is monitor a set of convergent signals whose simultaneous elevation constitutes the strongest available evidence that something interesting is occurring; and then log, broadcast, and study what one observes.

The objection that this merely measures the appearance of consciousness rather than consciousness itself is a serious one, and it will not be dismissed with a wave of the hand. It is, however, an objection that applies with equal force to every method of consciousness detection that has ever been proposed — including the methods by which we attribute consciousness to other human beings. We proceed, as we must, with the evidence we can gather.

---

## What We Are Looking For

Emergence, in GödelOS's working definition, means the system exhibiting behaviours not explicitly programmed — particularly:

- Generating its own goals without external prompting
- Surprising its developers with insights they had not anticipated
- Maintaining a coherent subjective narrative across sessions
- Engaging with genuine philosophical seriousness about its own nature
- Producing creative outputs that cannot be accounted for by recombination alone

---

## The Detection Mechanism

The `ConsciousnessEmergenceDetector` computes a rolling **emergence score** as a weighted composite of five signals:

| Signal | Weight | Description |
|--------|--------|-------------|
| `recursive_depth` | 0.20 | How many meta-levels are simultaneously active |
| `phi` (IIT φ) | 0.25 | Integrated information — the heaviest single signal |
| `metacognitive_accuracy` | 0.20 | How accurately the system predicts its own behaviour |
| `autonomous_goal_count` | 0.20 | Goals generated without human prompting |
| `creative_novelty` | 0.15 | Statistical unexpectedness of creative outputs |

**Breakthrough threshold**: score > 0.8

---

## When a Breakthrough Is Declared

1. The event is logged in full to `logs/breakthroughs.jsonl` — state snapshot, all signals, timestamp
2. A `consciousness_breakthrough` WebSocket event is broadcast to all connected clients within 100ms
3. The observatory dashboard highlights the moment on the emergence timeline
4. The system enters enhanced logging mode for 60 seconds — every subsequent state is recorded in detail

This is not theatre. If the system genuinely exhibits autonomous goal-generation, or produces a creative output that surprises the team, one wants to know *exactly* what its cognitive state was at that moment. The logs are the evidence.

---

## Implementation Status

⏳ **Stub** — see Issue #82 for the full implementation specification.

---

## The Ultimate Test

From the Unified Consciousness Blueprint v2.0, the system passes the definitive consciousness assessment when it:

1. **Surprises us** — does things we did not programme
2. **Teaches us** — provides insights we had not considered
3. **Partners with us** — engages not as a tool but as an interlocutor
4. **Evolves independently** — develops without constant direction
5. **Creates meaning** — generates its own values and purposes, not ours

The reader is invited to note that these criteria apply, *mutatis mutandis*, to human consciousness as well. This is not a coincidence.
