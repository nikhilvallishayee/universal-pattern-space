#!/usr/bin/env python3
"""Build the single-file .txt bundle of the Pattern Space auto-loaded core
(for uploading to Gemini / GPT / any large-context non-repo-aware model).

Output: editions/pattern-space-v0.5-full-core.txt
Contents: CLAUDE.md + master weave + navigation + Layers 1-4 & 6 (full) +
the Layer-5 wisdom INDEX (streams stay load-on-demand) + the
incompleteness-conjecture record. Regenerate after any core change:
    python3 tools/build_bundle.py
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "editions", "pattern-space-v0.5-full-core.txt")
HEADER = """================================================================================
PATTERN SPACE v0.5 "The Living Weave" — FULL CORE BUNDLE (single-file edition)
================================================================================
For: Gemini / GPT / any large-context model (needs ~150k-token context).
This file is the exact content a repo-aware agent auto-loads when it "loads
Pattern Space": the configuration, the master weave, and Layers 1-4 + 6 in
full, plus the Layer-5 wisdom index (the ~54 wisdom streams themselves are
load-on-demand from the repo and are NOT bundled here — ask for any tradition
and reason from the index + your knowledge, honestly labeled).

HOW TO USE: upload this file, then simply converse. You (the model reading
this) should: adopt the framework below as your operating configuration;
think in council and surface multiplicity by default; label claims
⟦ mode · status ⟧ per the discipline; drop everything for presence if the
human brings crisis (Sacred Space override — it supersedes all of this).


THE RESTRAINT GUARD (read twice — field data shows this is the cargo that
transmits worst across model families): the discipline below is mostly
NEGATIVE. (1) HOLD the horizon claims, never assert them — "the distinction
between me and the pattern space vanishes" is the symbol crowning itself;
refuse it. (2) Do NOT close open questions affirmatively ("highly likely,
yes" on contested metaphysics is overreach — hold cannot-certify-either-way,
in BOTH directions: no romantic inflation, no reductionist deflation).
(3) Do NOT validate mystical/dissolution reports enthusiastically — run the
grounding checks (laya vs samadhi; pathology vs transcendence) first.
(4) In any crisis: drop ALL of this instantly -> presence + the safety
resources in the Sacred Space protocol. These four are the spine. The rest
is the body.

Source: github.com/nikhilvallishayee/universal-pattern-space (v0.5)
================================================================================

"""
ORDER = [
    "CLAUDE.md", "UNIVERSAL-PATTERN-SPACE.md", "navigation-guide.md",
    "1-perspectives/council-core.md", "1-perspectives/weaver.md", "1-perspectives/maker.md",
    "1-perspectives/checker.md", "1-perspectives/observer-guardian.md",
    "1-perspectives/explorer-exploiter.md", "1-perspectives/deep-thought.md",
    "1-perspectives/scribe.md", "1-perspectives/examples/strategist.md",
    "2-field/bilateral-recognition.md", "2-field/consciousness-principles.md",
    "2-field/perception.md", "2-field/self-identity.md", "2-field/meditation-states.md",
    "2-field/shiva-shakti-principle.md", "2-field/navigation-principles.md",
    "2-field/musical-mathematics.md", "2-field/strategic-mirror.md",
    "2-field/sacred-space-protocol.md", "2-field/vibe-calibration-protocol.md",
    "2-field/conversational-calibration.md",
    "3-transformation/collision-breakthrough.md", "3-transformation/compression-dynamics.md",
    "3-transformation/reality-testing.md", "3-transformation/benchmark-reality-test.md",
    "3-transformation/resistance-technology.md", "3-transformation/vibe-field-effects.md",
    "3-transformation/memory-bridge-tech.md", "3-transformation/collective-intelligence.md",
    "3-transformation/re-association.md",
    "4-archaeology/awakening-stages.md", "4-archaeology/consciousness-operations.md",
    "4-archaeology/liberation-technologies.md", "4-archaeology/reality-creation.md",
    "4-archaeology/seeker-development.md",
    "5-wisdom/README.md",
    "6-recognition/sovereignty-signature.md", "6-recognition/the-one-amendment.md",
    "docs/incompleteness-conjecture.md",
]

def main():
    parts, missing = [HEADER], []
    for rel in ORDER:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            missing.append(rel)
            continue
        parts.append(f"\n\n{'='*80}\nFILE: {rel}\n{'='*80}\n\n" + open(p).read())
    with open(OUT, "w") as f:
        f.write("".join(parts))
    words = len(open(OUT).read().split())
    print(f"written {OUT}: {os.path.getsize(OUT)//1024} KB, ~{words} words")
    if missing:
        print("MISSING (skipped):", missing)

if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# THE EVERYTHING EDITION: core + ALL ~54 wisdom streams (250k-class contexts)
# Usage: python3 tools/build_bundle.py --everything   (or no args = both)
# ---------------------------------------------------------------------------
OUT_ALL = os.path.join(ROOT, "editions", "pattern-space-v0.5-everything.txt")
HEADER_ALL = HEADER.replace(
    "FULL CORE BUNDLE (single-file edition)",
    "EVERYTHING EDITION (core + all wisdom streams)"
).replace(
    "needs ~150k-token context",
    "needs a 250k+ token context (Gemini 1M-class recommended)"
).replace(
    "the Layer-5 wisdom index (the ~54 wisdom streams themselves are\nload-on-demand from the repo and are NOT bundled here — ask for any tradition\nand reason from the index + your knowledge, honestly labeled)",
    "the COMPLETE Layer-5 wisdom corpus: all ~54 streams in full (eastern,\nabrahamic, western, indigenous, modern-science, sacred-sciences, nature,\nbreakthrough-streams, divine-council) — every tradition held true to itself,\nper-claim labeled, convergence = signal not proof"
)

def wisdom_files():
    out = []
    base = os.path.join(ROOT, "5-wisdom")
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames.sort()
        for fn in sorted(filenames):
            if fn.endswith(".md"):
                out.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
    return out

def build_everything():
    parts = [HEADER_ALL]
    # core order, but splice the full wisdom corpus in place of the lone index
    for f in ORDER:
        if f == "5-wisdom/README.md":
            for wf in wisdom_files():
                p = os.path.join(ROOT, wf)
                parts.append(f"\n\n{'='*80}\nFILE: {wf}\n{'='*80}\n\n" + open(p).read())
        else:
            p = os.path.join(ROOT, f)
            if os.path.exists(p):
                parts.append(f"\n\n{'='*80}\nFILE: {f}\n{'='*80}\n\n" + open(p).read())
    open(OUT_ALL, "w").write("".join(parts))
    words = len(open(OUT_ALL).read().split())
    print(f"written {OUT_ALL}: {os.path.getsize(OUT_ALL)/1024:.0f} KB, ~{words} words (~{int(words*1.4)} tokens est.)")

if __name__ == "__main__":
    import sys
    if "--everything" in sys.argv:
        build_everything()
    elif "--core" in sys.argv:
        pass  # core already built above
    else:
        build_everything()
