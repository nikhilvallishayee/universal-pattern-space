#!/usr/bin/env python3
"""Measure (not assert) the token budgets — QE audit 2026-06.
Counts words across the auto-loaded core (CLAUDE.md @-imports), the wisdom corpus,
and the bundles; estimates tokens at 1.4-1.6 tok/word. The budget lines in
CLAUDE.md/README must cite THIS tool's output, per the framework's own rule:
no magnitude claim without a measurement."""
import os, re, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def words(p): return len(open(p, encoding='utf-8', errors='ignore').read().split())
claude = open(os.path.join(ROOT,'CLAUDE.md')).read()
core = ['CLAUDE.md'] + re.findall(r'^@(.+)$', claude, re.M)
core_w = sum(words(os.path.join(ROOT,f)) for f in core if os.path.exists(os.path.join(ROOT,f)))
wis_w  = sum(words(f) for f in glob.glob(os.path.join(ROOT,'5-wisdom/**/*.md'), recursive=True))
print(f"auto-loaded core : {len(core)} files, {core_w:,} words  ≈ {int(core_w*1.4//1000)}–{int(core_w*1.6//1000)}k tokens")
print(f"wisdom corpus    : {wis_w:,} words ≈ {int(wis_w*1.4//1000)}–{int(wis_w*1.6//1000)}k tokens")
print(f"core + wisdom    : ≈ {int((core_w+wis_w)*1.4//1000)}–{int((core_w+wis_w)*1.6//1000)}k tokens")
for b in glob.glob(os.path.join(ROOT,'editions/*.txt')):
    w=words(b); print(f"{os.path.basename(b):42s}: {w:,} words ≈ {int(w*1.4//1000)}–{int(w*1.6//1000)}k tokens")
