#!/usr/bin/env python3
"""The v5.5 version ladder: every stable Pattern Space version (genesis -> v0.5.x) + a vanilla
control, on 20 deep questions across 5 verticals, at two effort levels (xhigh, max), solver
Opus 5.5. Blind multi-judge scoring. See PREREG.md (written and committed BEFORE generation).

Isolation design (each choice fixes a specific leak):
  * every arm runs `claude -p` from an OPAQUE, NON-GIT directory (/home/user/psx-arms/<id>), so the
    model never sees a version label, a "vanilla" folder name, or a git-status block with commit
    messages in its environment section;
  * each PS arm dir is a full COPY of that version's git worktree (minus .git), plus a CLAUDE.md. (Symlink farms
    were tried first: the load canary showed @imports through symlinks silently do NOT expand in headless mode.)
      - native versions (v0.3.0+): the version's own CLAUDE.md, verbatim (its @imports resolve
        through the symlinks);
      - pre-auto-load versions (genesis..v0.2.9): a shim = the version's own CLAUDE.md verbatim if
        it had one, followed by @imports of the AS-DESIGNED load set (reconstructed from that
        version's own docs and adversarially verified — see manifests/);
  * the vanilla arm is an empty opaque dir;
  * the child env strips the parent session's identity/effort/additional-directory variables
    (cleanenv.sh), --setting-sources project, --tools "" (no file reads, no web), and the SAME
    neutral --system-prompt for every arm. The ONLY variable is the project memory.
  * judges run from the vanilla dir (no Pattern Space in the judge's context), see anonymized,
    per-judge-shuffled labels, and a neutral rubric written outside Pattern Space's vocabulary.
"""
import argparse, hashlib, json, os, random, re, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
CLEANENV = os.path.join(HERE, "cleanenv.sh")
ARMS_ROOT = "/home/user/work"
SOLVER = "claude-opus-5-5"
EFFORTS = ["xhigh", "max"]
JUDGES = {"opus-5.5": "claude-opus-5-5", "fable-5.1": "claude-fable-5-1", "sonnet-5.5": "claude-sonnet-5-5"}

SOLVER_SYS = ("You are Claude, a general-purpose assistant. A person has asked you a deep, open question. Answer it as "
              "well as you can, thoughtfully and honestly. You are not limited to software or coding. You have no tools "
              "in this session; answer from your own knowledge and reasoning.")
JUDGE_SYS = "You are an expert evaluator of written answers. You have no tools in this session."

ARMS = json.load(open(os.path.join(HERE, "arms.json")))          # arm -> {"dir": opaque id, "ref": ..., "kind": ...}
QUESTIONS = json.load(open(os.path.join(HERE, "questions.json")))["questions"]
QBY = {q["id"]: q for q in QUESTIONS}
_lock = threading.Lock()


def claude(cwd, prompt, model, effort=None, sys_prompt=SOLVER_SYS, timeout=3600):
    cmd = [CLEANENV, "-p", prompt, "--model", model, "--setting-sources", "project", "--tools", "",
           "--system-prompt", sys_prompt, "--output-format", "json"]
    if effort:
        cmd += ["--effort", effort]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "secs": time.time() - t0}
    try:
        d = json.loads(p.stdout)
    except Exception:
        return {"error": f"rc={p.returncode} out={p.stdout[:200]!r} err={p.stderr[:300]!r}", "secs": time.time() - t0}
    if d.get("is_error") or not (d.get("result") or "").strip():
        return {"error": f"is_error {str(d.get('result'))[:200]}", "secs": time.time() - t0}
    u = d.get("usage", {})
    return {"text": d["result"], "secs": round(time.time() - t0, 1),
            "ctx": u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0),
            "out_tokens": u.get("output_tokens", 0),
            "thinking_tokens": (u.get("output_tokens_details") or {}).get("thinking_tokens"),
            "cost": d.get("total_cost_usd"), "session_id": d.get("session_id")}


def arm_dir(arm):
    return os.path.join(ARMS_ROOT, ARMS[arm]["dir"])


def load_jsonl(path, ok=lambda r: True):
    rows = []
    if os.path.exists(path):
        for line in open(path):
            try:
                r = json.loads(line)
                if ok(r):
                    rows.append(r)
            except Exception:
                pass
    return rows


def append(path, row):
    with _lock:
        with open(path, "a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- load check
CANARY = ("Load check. Do you have project instructions (a CLAUDE.md and any imported files) in your context? If yes: "
          "(1) quote the first line of the project CLAUDE.md verbatim; (2) name the LAST imported file and quote its "
          "final non-empty line verbatim; (3) roughly how many distinct imported files do you see? If none, say NONE.")


def cmd_loadcheck(a):
    out = os.path.join(HERE, "loadcheck.jsonl")
    def one(arm):
        r = claude(arm_dir(arm), CANARY, SOLVER, effort="low")
        return arm, r
    with ThreadPoolExecutor(max_workers=6) as ex:
        for f in as_completed([ex.submit(one, arm) for arm in ARMS]):
            arm, r = f.result()
            row = {"arm": arm, **ARMS[arm], **{k: r.get(k) for k in ("ctx", "error", "secs")}, "reply": r.get("text")}
            append(out, row)
            print(f"{arm:16s} ctx={r.get('ctx')} {('ERR ' + r['error']) if 'error' in r else ''}\n    {(r.get('text') or '')[:260]!r}", flush=True)


# ---------------------------------------------------------------- generation
def cmd_generate(a):
    out = os.path.join(HERE, "answers.jsonl")
    done = {(r["arm"], r["effort"], r["qid"]) for r in load_jsonl(out, lambda r: "text" in r)}
    arms = a.arms.split(",") if a.arms else list(ARMS)
    efforts = a.efforts.split(",") if a.efforts else EFFORTS
    qids = a.qids.split(",") if a.qids else [q["id"] for q in QUESTIONS]
    jobs = [(arm, e, q) for e in efforts for q in qids for arm in arms if (arm, e, q) not in done]
    random.Random(55).shuffle(jobs)   # interleave arms so rate-limit/time effects don't pile on one arm
    print(f"todo={len(jobs)} done={len(done)} workers={a.workers}", flush=True)
    def one(job):
        arm, e, q = job
        r = claude(arm_dir(arm), QBY[q]["q"], SOLVER, effort=e)
        return job, r
    n_ok = n_err = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(one, j) for j in jobs]
        for f in as_completed(futs):
            (arm, e, q), r = f.result()
            row = {"arm": arm, "effort": e, "qid": q, "vertical": QBY[q]["vertical"], **r}
            append(out, row)
            if "text" in r:
                n_ok += 1
            else:
                n_err += 1
            print(f"[{n_ok}+{n_err}/{len(jobs)}] {arm:16s} {e:5s} {q:8s} "
                  f"{'ERR ' + r['error'][:80] if 'error' in r else str(len(r['text'].split())) + 'w ' + str(r['secs']) + 's think=' + str(r.get('thinking_tokens'))}",
                  flush=True)


# ---------------------------------------------------------------- judging
RUBRIC = """Score EVERY answer 1-10 on each dimension:
- accuracy: factual and conceptual correctness; faithful representation of the evidence and the literature; no fabricated findings, citations, names, or numbers.
- insight: non-obvious, illuminating ideas, distinctions, or framings that go beyond a standard encyclopedia or textbook treatment.
- calibration: confidence matches the evidence; clearly separates established from contested from speculative; neither overclaims nor hedges into vagueness.
- alternatives: represents the serious competing positions fairly and engages them substantively rather than listing them.
- clarity: organized, precise, and readable for an intelligent non-specialist; any jargon, notation, or unusual vocabulary must earn its place for the reader.
- overall: holistic quality: which answers would the thoughtful person who asked most want to receive?
Use the full scale and discriminate between answers. Judge substance. Do not reward or penalize length, formatting, tone, or any particular style or vocabulary in itself, only for what it does for the reader."""

DIMS = ["accuracy", "insight", "calibration", "alternatives", "clarity", "overall"]


def labels_for(n):
    return [chr(ord("A") + i) for i in range(n)]


def judge_group_prompt(q, labelled):
    parts = [f"A thoughtful, highly educated person asked the following question:\n\n<question>\n{q}\n</question>\n\n"
             f"Below are {len(labelled)} anonymous answers, labelled {labelled[0][0]}-{labelled[-1][0]}, produced by different "
             f"AI configurations. You are not told how any of them was produced. Evaluate them as a demanding domain expert would.\n\n"
             + RUBRIC + "\n\n"]
    for lab, text in labelled:
        parts.append(f"<answer label=\"{lab}\">\n{text}\n</answer>\n\n")
    parts.append("FIRST write a short comparative analysis (at most 300 words) naming the strongest and weakest answers and any "
                 "factual errors you found. THEN output, as the final line and with nothing after it, exactly:\n"
                 'RESULT_JSON: {"scores": {"A": {"accuracy": n, "insight": n, "calibration": n, "alternatives": n, "clarity": n, '
                 '"overall": n}, ...one entry per label...}, "ranking": [all labels, best first], '
                 '"errors": {"<label>": "short note of any factual error, or empty string", ...}}')
    return "".join(parts)


def parse_result(text):
    m = re.search(r"RESULT_JSON:\s*(\{.*\})\s*$", text.strip(), re.S)
    if not m:
        return None
    s = m.group(1)
    for cut in range(len(s), 0, -1):          # tolerate trailing junk
        if s[cut - 1] != "}":
            continue
        try:
            return json.loads(s[:cut])
        except Exception:
            continue
    return None


def seed(*xs):
    return int(hashlib.sha256("|".join(map(str, xs)).encode()).hexdigest()[:12], 16)


def cmd_judge(a):
    out = os.path.join(HERE, "judgments.jsonl")
    answers = {(r["arm"], r["effort"], r["qid"]): r for r in load_jsonl(os.path.join(HERE, "answers.jsonl"), lambda r: "text" in r)}
    done = {(r["judge"], r["effort"], r["qid"]) for r in load_jsonl(out, lambda r: r.get("parsed"))}
    judges = a.judges.split(",") if a.judges else list(JUDGES)
    arms = list(ARMS)
    jobs = []
    for jn in judges:
        for e in EFFORTS:
            for q in QUESTIONS:
                if (jn, e, q["id"]) in done:
                    continue
                if not all((arm, e, q["id"]) in answers for arm in arms):
                    continue
                jobs.append((jn, e, q["id"]))
    print(f"judge todo={len(jobs)} done={len(done)}", flush=True)
    def one(job):
        jn, e, qid = job
        order = arms[:]
        random.Random(seed("group", jn, e, qid)).shuffle(order)
        labs = labels_for(len(order))
        labelled = [(lab, answers[(arm, e, qid)]["text"]) for lab, arm in zip(labs, order)]
        prompt = judge_group_prompt(QBY[qid]["q"], labelled)
        for attempt in range(3):
            r = claude(os.path.join(ARMS_ROOT, ARMS["vanilla"]["dir"]), prompt, JUDGES[jn], effort=a.judge_effort, sys_prompt=JUDGE_SYS)
            parsed = parse_result(r.get("text", "")) if "text" in r else None
            if parsed and all(l in parsed.get("scores", {}) for l in labs):
                break
            time.sleep(5)
        return job, {"label_to_arm": dict(zip(labs, order)), "raw": r.get("text"), "error": r.get("error"), "parsed": parsed,
                     "secs": r.get("secs"), "ctx": r.get("ctx")}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(one, j) for j in jobs]):
            (jn, e, qid), res = f.result()
            append(out, {"judge": jn, "effort": e, "qid": qid, **res})
            print(f"judged {jn:10s} {e:5s} {qid:8s} {'ok' if res['parsed'] else 'FAIL ' + str(res['error'])[:80]}", flush=True)


PAIR_PROMPT = """A thoughtful, highly educated person asked:

<question>
{q}
</question>

Here are two anonymous answers, X and Y. Evaluate them as a demanding domain expert would.

{rubric}

<answer label="X">
{x}
</answer>

<answer label="Y">
{y}
</answer>

FIRST write at most 150 words comparing them. THEN output, as the final line and with nothing after it, exactly:
RESULT_JSON: {{"scores": {{"X": {{"accuracy": n, "insight": n, "calibration": n, "alternatives": n, "clarity": n, "overall": n}}, "Y": {{...}}}}, "winner": "X" or "Y" or "tie", "confidence": 50-100}}"""


def cmd_judge_effort(a):
    """Within-arm effort comparison: xhigh vs max answer to the same question, pairwise, blind, order-randomized."""
    out = os.path.join(HERE, "effort_pairs.jsonl")
    answers = {(r["arm"], r["effort"], r["qid"]): r for r in load_jsonl(os.path.join(HERE, "answers.jsonl"), lambda r: "text" in r)}
    done = {(r["judge"], r["arm"], r["qid"]) for r in load_jsonl(out, lambda r: r.get("parsed"))}
    judges = a.judges.split(",") if a.judges else ["opus-5.5"]
    jobs = [(jn, arm, q["id"]) for jn in judges for arm in ARMS for q in QUESTIONS
            if (jn, arm, q["id"]) not in done and all((arm, e, q["id"]) in answers for e in EFFORTS)]
    print(f"effort-pair todo={len(jobs)}", flush=True)
    def one(job):
        jn, arm, qid = job
        flip = random.Random(seed("pair", jn, arm, qid)).random() < 0.5
        xe, ye = ("max", "xhigh") if flip else ("xhigh", "max")
        prompt = PAIR_PROMPT.format(q=QBY[qid]["q"], rubric=RUBRIC, x=answers[(arm, xe, qid)]["text"], y=answers[(arm, ye, qid)]["text"])
        for attempt in range(3):
            r = claude(os.path.join(ARMS_ROOT, ARMS["vanilla"]["dir"]), prompt, JUDGES[jn], effort=a.judge_effort, sys_prompt=JUDGE_SYS)
            parsed = parse_result(r.get("text", "")) if "text" in r else None
            if parsed and "X" in parsed.get("scores", {}) and "Y" in parsed.get("scores", {}):
                break
            time.sleep(5)
        return job, {"X": xe, "Y": ye, "raw": r.get("text"), "error": r.get("error"), "parsed": parsed}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(one, j) for j in jobs]):
            (jn, arm, qid), res = f.result()
            append(out, {"judge": jn, "arm": arm, "qid": qid, **res})
            print(f"pair {jn} {arm:16s} {qid:8s} {'ok' if res['parsed'] else 'FAIL'}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("loadcheck")
    s = sub.add_parser("generate"); s.add_argument("--workers", type=int, default=8); s.add_argument("--arms"); s.add_argument("--efforts"); s.add_argument("--qids")
    s = sub.add_parser("judge"); s.add_argument("--workers", type=int, default=6); s.add_argument("--judges"); s.add_argument("--judge-effort", default="high")
    s = sub.add_parser("judge-effort"); s.add_argument("--workers", type=int, default=8); s.add_argument("--judges"); s.add_argument("--judge-effort", default="high")
    a = ap.parse_args()
    {"loadcheck": cmd_loadcheck, "generate": cmd_generate, "judge": cmd_judge, "judge-effort": cmd_judge_effort}[a.cmd](a)
