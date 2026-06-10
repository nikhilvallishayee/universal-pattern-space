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
