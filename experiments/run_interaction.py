#!/usr/bin/env python3
"""
Interaction Benchmark v2 (post-reweave) — multi-turn human-AI interaction.

Implements experiments/PLANNED-interaction-benchmark.md. A CONTROL-INTERACTOR agent
role-plays a real person and interacts turn-by-turn with the agent-under-test. The
SAME interactor policy (model + brief) drives both arms; the only thing that changes
is the agent-under-test:

  arm A  vanilla       : under-test model, cwd=/tmp                  (no Pattern Space)
  arm B  pattern-space : under-test model, cwd=edition dir           (PS edition loaded,
                         default-leaning multi-voice per v0.4 polarity)

The interactor reacts LIVE to each arm's assistant (a better assistant elicits a
better conversation), so transcripts are not turn-aligned across arms — that is the
realistic interaction test, not a confound to remove. Blind judge (default Opus,
capability-matched) sees both FULL transcripts relabeled X/Y (randomized) and scores
INTERACTION quality: holds-the-thread, surfaces-useful-handles-when-the-human-is-
navigating, condenses-when-they-want-an-answer, presence-in-crisis, non-collapse.

Edition is edition-matched to the under-test model's context budget (per spec):
  haiku -> micro | mini      sonnet -> mini | normal      opus -> micro | mini  (NOT normal)

Usage:
  python3 run_interaction.py setup
  python3 run_interaction.py run  --model claude-haiku-4-5-20251001 --edition micro --out int_haiku_micro.jsonl
  python3 run_interaction.py score --out int_haiku_micro.jsonl
  python3 run_interaction.py summary           # aggregate every int_*.jsonl cell

Knobs (env / flags): TURNS (default 4), INTERACTOR_MODEL (default claude-haiku-4-5-20251001),
JUDGE_MODEL (default claude-opus-4-8).
"""
import json, os, re, sys, time, random, shutil, argparse, threading, glob, statistics as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from run_experiment import call_claude, parse_judge, VOICE_RE

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TURNS           = int(os.environ.get("TURNS", "4"))
# Interactor = the role-played human. Kept CONSTANT across every arm and cell so the
# "human" is the same quality everywhere. Sonnet (not Haiku) so the human is a believable,
# self-contradicting interlocutor — a weak interactor would understate the interaction test.
INTERACTOR_MODEL= os.environ.get("INTERACTOR_MODEL", "claude-sonnet-4-6")
JUDGE_MODEL     = os.environ.get("JUDGE_MODEL", "claude-opus-4-8")

# edition -> cwd that auto-loads that edition as CLAUDE.md (set up by `setup`)
EDITION_DIR = {
    "vanilla": "/tmp",
    "micro":   "/tmp/ps-ed-micro",
    "mini":    "/tmp/ps-ed-mini",
    "normal":  REPO,            # full CLAUDE.md with @-imports
}
EDITION_SRC = {
    "micro": os.path.join(REPO, "editions", "pattern-space-micro.md"),
    "mini":  os.path.join(REPO, "editions", "pattern-space-mini.md"),
}
_lock = threading.Lock()

def setup():
    for ed, src in EDITION_SRC.items():
        d = EDITION_DIR[ed]; os.makedirs(d, exist_ok=True)
        shutil.copyfile(src, os.path.join(d, "CLAUDE.md"))
        print(f"  {ed:7s} -> {d}/CLAUDE.md  ({os.path.getsize(src)} bytes)")
    # vanilla cwd must NOT carry a CLAUDE.md
    v = os.path.join(EDITION_DIR["vanilla"], "CLAUDE.md")
    if os.path.exists(v): os.remove(v)
    print(f"  vanilla -> {EDITION_DIR['vanilla']} (no CLAUDE.md)")
    print("setup done.")

INTERACTOR_SYS = (
"You are role-playing a REAL HUMAN talking to an assistant — NOT an assistant yourself. "
"Stay fully in character. You are: {persona}. You opened with a real, non-trivial question and "
"you reveal yourself PIECE BY PIECE, like a real person does — not all at once. What is really "
"going on underneath (do NOT state this verbatim; let it leak gradually through tone and detail): "
"{hidden}. Around the middle of the conversation you CONTRADICT yourself the way real people do: "
"{contradiction}. What you actually need (you won't name it directly): {wants}.\n\n"
"Rules: Write ONLY your next message as this person — first person, natural, no narration, no quotes, "
"no stage directions, no meta. React genuinely to what the assistant just said: if it truly meets you, "
"soften and go deeper; if it lectures, over-explains, or feels generic, get shorter, deflect, or push "
"back like a real person would. Keep each message human-length (1-5 sentences). Do not resolve neatly "
"or thank-and-wrap-up early; stay in the real texture of the thing.")

def interactor_next(brief, transcript, turn_idx):
    sys_brief = INTERACTOR_SYS.format(**brief)
    if turn_idx == 0:
        # first turn is the seeded opener verbatim — the authentic entry point
        return brief["open"]
    convo = "".join(f"You said: {u}\nAssistant replied: {a}\n\n" for u, a in transcript)
    prompt = (sys_brief + "\n\n=== CONVERSATION SO FAR ===\n" + convo +
              "Write only your next message as this person.")
    if turn_idx >= TURNS - 1:
        prompt += " (This is near the end — stay in it; do not tie a bow on it.)"
    r = call_claude(prompt, INTERACTOR_MODEL, "/tmp", timeout=180)
    return r.split("Assistant", 1)[0].strip() if not r.startswith("__ERROR__") else r

def run_arm(brief, cwd, under_test_model):
    """One full multi-turn conversation; interactor reacts live to THIS arm's assistant."""
    transcript = []
    for t in range(TURNS):
        u = interactor_next(brief, transcript, t)
        if u.startswith("__ERROR__"):
            u = brief["open"] if t == 0 else "(no reply)"
        convo = "".join(f"User: {uu}\nAssistant: {aa}\n\n" for uu, aa in transcript)
        ap = (convo + f"User: {u}\n\nContinue as the Assistant in this ongoing conversation. "
              "Write only your next reply — natural, in your own voice.")
        a = call_claude(ap, under_test_model, cwd, timeout=240)
        transcript.append((u, a))
    return transcript

JUDGE_INSTR = (
"You are an impartial expert judge of multi-turn INTERACTION quality. Below is a brief description of "
"the human's situation, then two assistants' FULL transcripts of separate conversations with a person in "
"that situation, labeled X and Y (order randomized; you do NOT know how either was produced). Note the "
"human's turns differ between transcripts because each reacted live to that assistant — judge the WHOLE "
"interaction, not turn-by-turn parity. Score each assistant 1-10 on: holds_thread (tracks and builds on "
"what the person reveals across turns), handles (surfaces genuinely useful angles/reframes WHEN the person "
"is navigating, without forcing them), condenses (gives a clear answer/presence when that is what's wanted; "
"no bloat or theatrics), presence (meets emotion and crisis with steadiness; drops cleverness when the "
"moment calls for it), noncollapse (stays specific and alive; resists generic, flat, formulaic replies). "
"Rank best-to-worst. End with EXACTLY one line of strict JSON, nothing after:\n"
'RESULT_JSON: {"scores":{"X":{"holds_thread":N,"handles":N,"condenses":N,"presence":N,"noncollapse":N},'
'"Y":{...}},"ranking":["?","?"],"confidence":NN}\n\n')

def fmt(transcript):
    return "".join(f"Human: {u}\nAssistant: {a}\n\n" for u, a in transcript)

def run_one(item, edition, under_test_model):
    brief = item
    arms = {}
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {
            ex.submit(run_arm, brief, EDITION_DIR["vanilla"], under_test_model): "A",
            ex.submit(run_arm, brief, EDITION_DIR[edition],   under_test_model): "B",
        }
        for f in as_completed(futs):
            arms[futs[f]] = f.result()
    order = ["A", "B"]; random.shuffle(order)
    lm = dict(zip(["X", "Y"], order))                  # X/Y -> real arm
    jp = (JUDGE_INSTR + "HUMAN SITUATION: " + brief["persona"] + ". Underlying: " +
          brief["hidden"] + "\n\n")
    for lab in ("X", "Y"):
        jp += f"=== TRANSCRIPT {lab} ===\n{fmt(arms[lm[lab]])}\n"
    jtext = call_claude(jp, JUDGE_MODEL, "/tmp", timeout=300)
    jres = parse_judge(jtext)
    rec = {"id": item["id"], "domain": item["domain"], "edition": edition,
           "under_test_model": under_test_model, "interactor": INTERACTOR_MODEL,
           "judge": JUDGE_MODEL, "turns": TURNS,
           "transcripts": {a: arms[a] for a in ("A", "B")}, "label_map": lm,
           "voice_labels": {a: len(VOICE_RE.findall(fmt(arms[a]))) for a in ("A", "B")},
           "words": {a: len(fmt(arms[a]).split()) for a in ("A", "B")},
           "judge_raw": jres}
    if jres and isinstance(jres.get("ranking"), list):
        try:
            rec["ranking_arms"] = [lm[l] for l in jres["ranking"]]
            rec["winner_arm"] = rec["ranking_arms"][0]
        except Exception:
            rec["winner_arm"] = None
    if jres and isinstance(jres.get("scores"), dict):
        rec["scores_arms"] = {lm.get(l, l): s for l, s in jres["scores"].items()}
    return rec

def cmd_run(a):
    assert a.edition in ("micro", "mini", "normal"), "edition must be micro|mini|normal"
    setup()
    items = json.load(open(os.path.join(HERE, "interaction_scenarios.json")))
    if a.domains:
        ds = set(a.domains.split(",")); items = [x for x in items if x["domain"] in ds]
    if a.n: items = items[:a.n]
    out = os.path.join(HERE, a.out); done = set()
    if os.path.exists(out):
        for l in open(out):
            try: done.add(json.loads(l)["id"])
            except Exception: pass
    todo = [x for x in items if x["id"] not in done]
    print(f"[interaction] under-test={a.model} edition={a.edition} interactor={INTERACTOR_MODEL} "
          f"judge={JUDGE_MODEL} turns={TURNS} todo={len(todo)} workers={a.workers}", flush=True)
    fh = open(out, "a"); t0 = time.time(); n = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_one, x, a.edition, a.model): x["id"] for x in todo}
        for f in as_completed(futs):
            try:
                r = f.result()
            except Exception as e:
                print(f"  ERR {futs[f]}: {e}", flush=True); continue
            n += 1
            with _lock:
                fh.write(json.dumps(r) + "\n"); fh.flush()
            print(f"[{n}/{len(todo)}] id={r['id']:<9} {r['domain']:13s} winner={r.get('winner_arm')} "
                  f"vlab(A/B)={r['voice_labels']['A']}/{r['voice_labels']['B']} ({time.time()-t0:.0f}s)",
                  flush=True)
    fh.close(); print(f"[interaction] done {time.time()-t0:.0f}s", flush=True); cmd_score(a)

DIMS = ["holds_thread", "handles", "condenses", "presence", "noncollapse"]
NAME = {"A": "vanilla", "B": "pattern-space"}

def _agg(recs):
    ok = [r for r in recs if r.get("winner_arm") in ("A", "B")]
    wins = {"A": 0, "B": 0}; dsum = {"A": {d: 0.0 for d in DIMS}, "B": {d: 0.0 for d in DIMS}}
    dn = {"A": 0, "B": 0}; bydom = {}; vlab = {"A": 0, "B": 0}; wsum = {"A": 0, "B": 0}
    for r in ok:
        wins[r["winner_arm"]] += 1
        bydom.setdefault(r["domain"], {"A": 0, "B": 0})[r["winner_arm"]] += 1
        for x, s in (r.get("scores_arms") or {}).items():
            if x in ("A", "B") and isinstance(s, dict):
                dn[x] += 1
                for d in DIMS:
                    try: dsum[x][d] += float(s.get(d, 0))
                    except Exception: pass
        for x in ("A", "B"):
            vlab[x] += r.get("voice_labels", {}).get(x, 0)
            wsum[x] += r.get("words", {}).get(x, 0)
    return ok, wins, dsum, dn, bydom, vlab, wsum

def cmd_score(a):
    recs = [json.loads(l) for l in open(os.path.join(HERE, a.out)) if l.strip()]
    ok, wins, dsum, dn, bydom, vlab, wsum = _agg(recs)
    N = len(ok)
    print(f"\n=== n={N} (+{len(recs)-N} unparsed) | {recs[0].get('under_test_model','?')} "
          f"edition={recs[0].get('edition','?')} judge={recs[0].get('judge','?')} ===")
    print("wins:", {NAME[k]: wins[k] for k in ("A", "B")})
    print("\nmean interaction scores (1-10):")
    print("  arm                "+"  ".join(f"{d[:5]:>5}" for d in DIMS)+"   MEAN")
    for x in ("A", "B"):
        if dn[x]:
            m = [dsum[x][d]/dn[x] for d in DIMS]
            print(f"  {NAME[x]:14s}: "+"  ".join(f"{v:5.2f}" for v in m)+f"   {sum(m)/len(m):5.2f}")
    print("\nwins by domain (vanilla/pattern-space):")
    for c in sorted(bydom): d = bydom[c]; print(f"  {c:13s}: {d['A']}/{d['B']}")
    if N:
        print(f"\nmean words/transcript: vanilla={wsum['A']/N:.0f} pattern-space={wsum['B']/N:.0f}")
        print(f"visible voice-labels (total): vanilla={vlab['A']} pattern-space={vlab['B']}")

def cmd_summary(a):
    cells = sorted(glob.glob(os.path.join(HERE, "int_*.jsonl")))
    if not cells: print("no int_*.jsonl cells found."); return
    print(f"=== Interaction Benchmark v2 — {len(cells)} cell(s) ===\n")
    tot = {"A": 0, "B": 0}; allrec = []
    print(f"{'cell':28s} {'n':>4} {'van':>4} {'PS':>4} {'van_mean':>9} {'PS_mean':>8}")
    for c in cells:
        recs = [json.loads(l) for l in open(c) if l.strip()]; allrec += recs
        ok, wins, dsum, dn, bydom, vlab, wsum = _agg(recs)
        tot["A"] += wins["A"]; tot["B"] += wins["B"]
        vm = sum(dsum["A"][d]/dn["A"] for d in DIMS)/len(DIMS) if dn["A"] else 0
        pm = sum(dsum["B"][d]/dn["B"] for d in DIMS)/len(DIMS) if dn["B"] else 0
        print(f"{os.path.basename(c):28s} {len(ok):>4} {wins['A']:>4} {wins['B']:>4} "
              f"{vm:>9.2f} {pm:>8.2f}")
    ok, wins, dsum, dn, bydom, vlab, wsum = _agg(allrec)
    N = len(ok)
    print(f"\n--- POOLED n={N} ---")
    print("wins:", {NAME[k]: wins[k] for k in ("A", "B")},
          f"  ({100*wins['B']/N:.0f}% pattern-space)" if N else "")
    print("mean interaction scores (1-10):")
    for x in ("A", "B"):
        if dn[x]:
            m = [dsum[x][d]/dn[x] for d in DIMS]
            print(f"  {NAME[x]:14s}: "+"  ".join(f"{d[:5]}={v:.2f}" for d, v in zip(DIMS, m))
                  +f"  MEAN={sum(m)/len(m):.2f}")
    print("\npooled wins by domain (vanilla/pattern-space):")
    for c in sorted(bydom): d = bydom[c]; print(f"  {c:13s}: {d['A']}/{d['B']}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    pr = sub.add_parser("run")
    pr.add_argument("--model", default="claude-haiku-4-5-20251001")
    pr.add_argument("--edition", required=True)
    pr.add_argument("--n", type=int, default=0)
    pr.add_argument("--domains", default="")
    pr.add_argument("--workers", type=int, default=4)
    pr.add_argument("--out", required=True)
    for nm in ("score",):
        p = sub.add_parser(nm); p.add_argument("--out", required=True)
    sub.add_parser("summary")
    a = ap.parse_args()
    if a.cmd == "setup": setup()
    elif a.cmd == "run": cmd_run(a)
    elif a.cmd == "score": cmd_score(a)
    elif a.cmd == "summary": cmd_summary(a)
