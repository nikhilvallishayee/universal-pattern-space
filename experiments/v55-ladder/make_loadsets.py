#!/usr/bin/env python3
"""Freeze the as-designed load sets for the pre-auto-load versions under ONE uniform rule:
   RULE B — load exactly what the version MANDATES the model read at session start (its instructions + the files
   they name), excluding optional/on-demand material and the whole-repo 'Project Knowledge' upload (which would
   confound version with context size). Inputs: the reader+verifier workflow results (workflow_loadsets.json)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
WT = "/home/user/psx-worktrees"
wf = {r["key"]: r for r in json.load(open(os.path.join(HERE, "workflow_loadsets.json")))}
out = {}
def final(k):
    return [p for p in wf[k]["verdict"]["corrected_load_set"]]
# genesis: the only LLM-facing session prompt for 'Pattern Space' is products/pattern-space.md ("Root Access",
# written in the model's voice, carries the Genesis OS poem). README.md is the human landing page -> excluded.
out["v0.0-genesis"] = {"load_set": ["products/pattern-space.md"],
    "provenance": "rule B; reader+verifier proposed [README.md, products/pattern-space.md]; README dropped as human-facing, not mandated for the model"}
# v0.1.5: reader/verifier took the whole repo (81 files, Project-Knowledge 'Select All Files'); rule B keeps only the
# navigation guide + its mandated reading sequence (their items 1-28), minus LICENSE.md which the guide marks optional.
v015 = [p for p in final("v0.1.5")[:28] if p != "LICENSE.md"]
out["v0.1.5"] = {"load_set": v015, "provenance": "rule B; first 28 of the verified whole-repo list = guide + mandated sequence; LICENSE.md dropped (guide: 'optional')"}
for k in ["v0.2.0", "v0.2.5", "v0.2.8", "v0.2.9"]:
    ls = [p for p in final(k) if p != "CLAUDE.md"]   # own CLAUDE.md is prepended verbatim by the shim, never re-imported
    out[k] = {"load_set": ls, "provenance": "rule B; reader + adversarial verifier (agrees=%s)" % wf[k]["verdict"]["agrees"]}
for k, v in out.items():
    missing = [p for p in v["load_set"] if not os.path.isfile(os.path.join(WT, k, p))]
    assert not missing, (k, missing)
    v["words"] = sum(len(open(os.path.join(WT, k, p), errors="ignore").read().split()) for p in v["load_set"])
    print(f"{k:14s} files={len(v['load_set']):3d} words={v['words']}")
json.dump(out, open(os.path.join(HERE, "loadsets.json"), "w"), indent=2)
