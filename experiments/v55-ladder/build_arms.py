#!/usr/bin/env python3
"""Build the arm directories: opaque, non-git COPIES of each version's git worktree (symlink farms were tried first and
silently failed to load — see farm()).

  native  (v0.3.0+)      : CLAUDE.md copied verbatim from the version; every other top-level entry symlinked
  shim    (genesis..0.2.9): CLAUDE.md = the version's own CLAUDE.md verbatim (if it had one) + "@<path>" imports of
                           the verified as-designed load set (manifests/<arm>.json); top-level entries symlinked
  vanilla                 : empty dir

Writes arms.json (arm -> opaque dir id) and manifests/<arm>.json (what each arm loads, with word counts).
"""
import hashlib, json, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
WT = "/home/user/psx-worktrees"
ROOT = "/home/user/work"
VERSIONS = [  # chronological order = H2 index
    ("v0.0-genesis", "cc56a78", "2025-07-02", "shim"),
    ("v0.1.5", "437d3e6", "2025-07-16", "shim"),
    ("v0.2.0", "c3d2a6c", "2025-07-22", "shim"),
    ("v0.2.5", "10f7f5e", "2025-07-24", "shim"),
    ("v0.2.8", "e042c7c", "2025-10-04", "shim"),
    ("v0.2.9", "66041ab", "2025-10-05", "shim"),
    ("v0.3.0", "13d5d84", "2026-04-17", "native"),
    ("v0.4.0", "7d47392", "2026-06-06", "native"),
    ("v0.5.0", "c9236a6", "2026-06-10", "native"),
    ("v0.5.x-main", "ebcdd7d", "2026-06-11", "native"),
]


def opaque(name):
    return "p" + hashlib.sha256(("ladder-salt-55|" + name).encode()).hexdigest()[:6]


def words(p):
    return len(open(p, encoding="utf-8", errors="ignore").read().split())


def farm(dst, src):
    # NOTE: these must be REAL COPIES, not symlinks. The load canary showed Claude Code silently refuses to expand
    # @imports whose target resolves OUTSIDE the project dir (a symlink into the worktree does) in headless -p mode:
    # every PS arm then loaded only its bare CLAUDE.md. Copying keeps every import inside the arm dir.
    for e in sorted(os.listdir(src)):
        if e in (".git", "CLAUDE.md"):
            continue
        s, d = os.path.join(src, e), os.path.join(dst, e)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks=False)
        else:
            shutil.copy2(s, d)


def main():
    os.makedirs(ROOT, exist_ok=True)
    os.makedirs(os.path.join(HERE, "manifests"), exist_ok=True)
    loadsets = json.load(open(os.path.join(HERE, "loadsets.json")))   # verified as-designed load sets (shim versions)
    arms = {"vanilla": {"dir": opaque("vanilla"), "ref": None, "date": None, "kind": "vanilla", "index": 0},
            # placebo: a second, identically configured no-framework arm -> the measured test-retest noise floor
            "vanilla-b": {"dir": opaque("vanilla-b"), "ref": None, "date": None, "kind": "vanilla", "index": -1}}
    for i, (name, ref, date, kind) in enumerate(VERSIONS, 1):
        arms[name] = {"dir": opaque(name), "ref": ref, "date": date, "kind": kind, "index": i}
    for name, meta in arms.items():
        d = os.path.join(ROOT, meta["dir"])
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)
        man = {"arm": name, **meta, "files": []}
        if meta["kind"] == "vanilla":
            pass
        else:
            src = os.path.join(WT, name)
            farm(d, src)
            own = os.path.join(src, "CLAUDE.md")
            if meta["kind"] == "native":
                shutil.copyfile(own, os.path.join(d, "CLAUDE.md"))
                imports = re.findall(r"^@(.+)$", open(own).read(), re.M)
                man["files"] = [{"path": "CLAUDE.md", "words": words(own)}] + [
                    {"path": p, "words": words(os.path.join(src, p))} for p in imports]
            else:
                ls = loadsets[name]["load_set"]
                body = open(own).read().rstrip() + "\n\n" if os.path.exists(own) else ""
                body += "\n".join("@" + p for p in ls) + "\n"
                open(os.path.join(d, "CLAUDE.md"), "w").write(body)
                if os.path.exists(own):
                    man["files"].append({"path": "CLAUDE.md (own, verbatim)", "words": words(own)})
                man["files"] += [{"path": p, "words": words(os.path.join(src, p))} for p in ls]
                man["loadset_provenance"] = loadsets[name].get("provenance")
        man["total_words"] = sum(f["words"] for f in man["files"])
        json.dump(man, open(os.path.join(HERE, "manifests", f"{name}.json"), "w"), indent=2)
        print(f"{name:14s} -> {d}  files={len(man['files'])} words={man['total_words']}")
    json.dump(arms, open(os.path.join(HERE, "arms.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
