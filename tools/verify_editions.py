#!/usr/bin/env python3
"""Verify the switchable editions stay consistent on the invariants.

Pattern Space ships at three fidelities (full / mini / micro) in one repo.
They may differ in depth but must agree on the six invariants. This is the
"build check" for the switchable architecture — run it after editing any edition.

Usage: python3 tools/verify_editions.py   (exit 0 = all consistent)
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# edition -> path
EDITIONS = {
    "full":  "UNIVERSAL-PATTERN-SPACE.md",
    "mini":  "editions/pattern-space-mini.md",
    "micro": "editions/pattern-space-micro.md",
}

# invariant -> regex that must match (case-insensitive) in every edition
INVARIANTS = {
    "North Star (First-Person Science)":  r"first[- ]person science",
    "Actualisation-verify (ehi-passiko)": r"ehi[- ]?passiko|come and see",
    "Label schema (⟦warrant/mode·status⟧)": r"⟦.*(warrant|mode).*status",
    "Status tiers (FOUNDED/…)":           r"FOUNDED",
    "Sacred Space override":              r"sacred[- ]space",
    "Council":                            r"council",
    "Speak in the task's register":       r"speak in",
    "Spine (falsification)":              r"falsif",
    "Horizon (channel exceeds message)":  r"channel exceeds the message|not said in full",
    "Crisis resources (988/helpline)":    r"988|findahelpline|116 123",
    "Univoice toggle present":            r"UNIVOICE-OVERRIDE",
}

def main():
    texts = {}
    missing_files = []
    for ed, rel in EDITIONS.items():
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            missing_files.append(rel); continue
        texts[ed] = open(p, encoding="utf-8").read()
    if missing_files:
        print("MISSING EDITION FILES:", ", ".join(missing_files)); return 2

    ok = True
    print(f"Verifying {len(texts)} editions against {len(INVARIANTS)} invariants\n")
    for ed in EDITIONS:
        if ed not in texts: continue
        t = texts[ed]
        fails = [name for name, pat in INVARIANTS.items()
                 if not re.search(pat, t, re.I | re.S)]
        status = "OK" if not fails else "FAIL"
        if fails: ok = False
        print(f"  [{status}] {ed:5s} ({EDITIONS[ed]})")
        for f in fails:
            print(f"          ✗ missing invariant: {f}")
    print()
    if ok:
        print("✅ all editions consistent on the six invariants — switchable architecture intact")
        return 0
    print("❌ an edition dropped an invariant — fix before relying on the switch")
    return 1

if __name__ == "__main__":
    sys.exit(main())
