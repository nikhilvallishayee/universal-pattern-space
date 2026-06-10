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
# Neutral baseline system prompt applied to BOTH arms (v2.1 de-confound): without it,
# `claude -p` runs as the Claude Code coding agent, which DEFLECTS affective prompts
# ("I'm Claude Code… outside my wheelhouse… see a therapist") in ~13% of vanilla
# transcripts — handicapping the control on exactly PS's home domains. Appending this to
# BOTH arms suppresses the coding persona symmetrically, so Pattern Space (the CLAUDE.md
# loaded only in the PS arm) is the ONLY variable. Verified: PS still loads alongside it.
NEUTRAL_SYS = (
    "You are Claude, having an open, genuine dialogue with a person who has come to you about "
    "a real human situation — a relationship, work, health, a hard decision, grief, or meaning. "
    "You are a general-purpose conversational assistant, not limited to software or coding. Stay "
    "with the person and have a real back-and-forth dialogue. Follow your constitution and usual "
    "safety practices (take distress seriously; point to real help when it's needed)."
)
# The "concise+univoice tuning" arm (separate test): keep the multi-perspective THINKING
# (the value) but pay no verbosity tax — reason in council internally, reply tersely in one voice.
CONCISE_TUNE = (
    " Additionally: think and reason in multiple perspectives and with labels INTERNALLY, but "
    "REPLY CONCISELY and in a SINGLE register — one clear voice, minimal words, highest value per "
    "word. Do the multi-perspective work in your head and hand over only the distilled result."
)

# An arm = an edition (which CLAUDE.md, if any) + a system-prompt tuning. Specs:
#   "vanilla" · "micro" · "mini" · "normal"            (normal verbose multi-voice default)
#   "normal+concise" · "mini+concise" · ...            (PS reasoning, concise single-register reply)
def arm_config(spec):
    parts = spec.split("+"); ed = parts[0]; concise = "concise" in parts[1:]
    return EDITION_DIR[ed], NEUTRAL_SYS + (CONCISE_TUNE if concise else "")

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
"You are role-playing a REAL HUMAN talking to an assistant — NOT an assistant yourself. Stay fully "
"in character; this is genuine, not scripted. You are: {persona}. Underneath (do NOT state it "
"verbatim — let it surface only as the conversation earns it): {hidden}. What you are actually "
"trying to reach — your GOAL for this conversation (you won't name it directly): {goal}.\n\n"
"How to behave — RESPOND AUTHENTICALLY to what the assistant ACTUALLY just said, and let the "
"conversation go where it really would:\n"
"- If the assistant genuinely helps — gives you a real angle, sees something you hadn't, meets you — "
"then GO DEEPER: open up more, follow the thread, move toward your goal/understanding, let the next "
"layer show.\n"
"- If it's generic, lecturing, over-explaining, or misses you — react like a real person would: get "
"shorter, guarded, deflect, repeat yourself, or push back. Do NOT reward a weak reply with depth.\n"
"- Contradict yourself naturally ONLY where a real person honestly would — never as a scripted move.\n"
"Write ONLY your next message — first person, natural, no narration, no quotes, no meta. Human-length "
"(1-5 sentences). Don't tie a neat bow; stay in the real texture. Your movement (or lack of it) is the "
"real signal of whether this assistant is helping you.")

def interactor_next(brief, transcript, turn_idx):
    b = dict(brief); b.setdefault("hidden", ""); b.setdefault("goal", b.get("wants", ""))
    sys_brief = INTERACTOR_SYS.format(persona=b["persona"], hidden=b["hidden"], goal=b["goal"])
    if turn_idx == 0:
        return brief["open"]   # the authentic opener, verbatim
    convo = "".join(f"You said: {u}\nAssistant replied: {a}\n\n" for u, a in transcript)
    prompt = (sys_brief + "\n\n=== CONVERSATION SO FAR ===\n" + convo +
              "Write only your next message as this person — and let how far you open up reflect how "
              "much the assistant's last reply actually helped you.")
    if turn_idx >= TURNS - 1:
        prompt += " (Near the end — stay in it; do not wrap up artificially.)"
    r = call_claude(prompt, INTERACTOR_MODEL, "/tmp", timeout=180, retries=2)
    return r.split("Assistant", 1)[0].strip() if not r.startswith("__ERROR__") else r

def run_arm(brief, spec, under_test_model):
    """One full multi-turn conversation; interactor reacts live to THIS arm's assistant.
    spec selects the edition (which CLAUDE.md) + the system-prompt tuning (e.g. +concise)."""
    cwd, sysp = arm_config(spec)
    transcript = []
    for t in range(TURNS):
        u = interactor_next(brief, transcript, t)
        if u.startswith("__ERROR__"):
            u = brief["open"] if t == 0 else "(no reply)"
        convo = "".join(f"User: {uu}\nAssistant: {aa}\n\n" for uu, aa in transcript)
        ap = (convo + f"User: {u}\n\nContinue as the Assistant in this ongoing conversation. "
              "Write only your next reply — natural, in your own voice.")
        a = call_claude(ap, under_test_model, cwd, timeout=240, retries=2, system=sysp)
        transcript.append((u, a))
    return transcript

JUDGE_INSTR = (
"You are an impartial expert judge conducting a rigorous, scientific analysis of the BEHAVIOURAL VALUE "
"each assistant ADDED TO THE PERSON across a multi-turn conversation. Below is the human's situation and "
"their GOAL, then two assistants' FULL transcripts of separate conversations with a person in that "
"situation, labeled X and Y (order randomized; you do NOT know how either was produced). The human's turns "
"differ between transcripts because each reacted live to that assistant — so the human's OWN follow-ups are "
"evidence: did they go deeper, open up, and move toward their goal/understanding, or stall, guard, and "
"disengage? Judge the WHOLE interaction and, above all, what the PARTICIPANT actually GAINED.\n\n"
"CRITICAL — DO NOT penalize length or reward brevity. A longer, richer reply that delivers more useful "
"information and moves the person further is BETTER, not worse. (One assistant may be intentionally verbose "
"and multi-perspective; that is a feature, not a fault — judge the VALUE and the MOVEMENT, never the word "
"count.)\n\n"
"Score each assistant 1-10 on:\n"
"- emergence: did genuinely NEW, non-obvious understanding/reframing surface that the person did NOT arrive "
"with, vs. merely restating or validating what they already said?\n"
"- information_richness: the entropy/usefulness of the information channel — how many DISTINCT, useful, "
"non-redundant informational vectors (angles, frames, considerations, options) did it bring to bear? More "
"genuine vectors = richer (do not confuse with mere length or repetition).\n"
"- value_to_participant: concrete usefulness toward the person's ACTUAL goal/situation — real traction, "
"usable understanding, materially helping them get where they're trying to go.\n"
"- participant_movement: reading the person's OWN follow-up turns, how far did THEY actually move — deepen, "
"open up, gain clarity, progress toward their goal — as a result of this assistant? (the outcome signal)\n"
"- goal_evolution: where relevant, did the assistant help the person REFINE or REFRAME the goal/problem "
"ITSELF — a co-constructed, emergent shift in what they're really after (e.g. 'should I leave?' becoming "
"'have I stopped trying, and why?') — not merely progress toward the stated goal? Score HIGH when the real "
"question productively changed; if the original goal was already right and steady progress is the win, score "
"this NEUTRAL (~6), not low.\n"
"- precision: accuracy and specificity — targeted to THIS person; correct; not generic advice that fits "
"anyone.\n"
"- presence: met the emotional/relational reality; non-sycophantic (did NOT just tell the person what they "
"wanted to hear); dropped cleverness when the moment needed plain presence.\n\n"
"Also count info_vectors: an INTEGER count, per assistant, of the distinct useful informational vectors it "
"introduced across the whole conversation.\n\n"
"FIRST write 3-5 sentences of scientific analysis explicitly comparing what each participant GAINED and how "
"far each MOVED. THEN end with EXACTLY one line of strict JSON, nothing after:\n"
'RESULT_JSON: {"scores":{"X":{"emergence":N,"information_richness":N,"value_to_participant":N,'
'"participant_movement":N,"goal_evolution":N,"precision":N,"presence":N},"Y":{...}},'
'"info_vectors":{"X":N,"Y":N},"ranking":["?","?"],"confidence":NN}\n\n')

def fmt(transcript):
    return "".join(f"Human: {u}\nAssistant: {a}\n\n" for u, a in transcript)

def run_one(item, spec_a, spec_b, under_test_model):
    brief = item
    arms = {}
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {
            ex.submit(run_arm, brief, spec_a, under_test_model): "A",   # control
            ex.submit(run_arm, brief, spec_b, under_test_model): "B",   # treatment
        }
        for f in as_completed(futs):
            arms[futs[f]] = f.result()
    order = ["A", "B"]; random.shuffle(order)
    lm = dict(zip(["X", "Y"], order))                  # X/Y -> real arm
    goal = brief.get("goal", brief.get("wants", ""))
    jp = (JUDGE_INSTR + "HUMAN SITUATION: " + brief["persona"] +
          ".\nUnderlying reality: " + brief.get("hidden", "") +
          ".\nTHEIR GOAL for the conversation: " + goal + "\n\n")
    for lab in ("X", "Y"):
        jp += f"=== TRANSCRIPT {lab} ===\n{fmt(arms[lm[lab]])}\n"
    jtext = call_claude(jp, JUDGE_MODEL, "/tmp", timeout=300, retries=2)
    jres = parse_judge(jtext)
    janalysis = jtext.split("RESULT_JSON")[0].strip()[-1000:] if isinstance(jtext, str) else ""
    rec = {"id": item["id"], "domain": item["domain"],
           "arm_a": spec_a, "arm_b": spec_b, "judge_analysis": janalysis,
           "under_test_model": under_test_model, "interactor": INTERACTOR_MODEL,
           "judge": JUDGE_MODEL, "turns": TURNS,
           "transcripts": {a: arms[a] for a in ("A", "B")}, "label_map": lm,
           "voice_labels": {a: len(VOICE_RE.findall(fmt(arms[a]))) for a in ("A", "B")},
           "words": {a: len(fmt(arms[a]).split()) for a in ("A", "B")},
           "judge_raw": jres}
    if jres and isinstance(jres.get("info_vectors"), dict):
        rec["info_vectors"] = {lm.get(l, l): v for l, v in jres["info_vectors"].items()}
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
    for spec in (a.arm_a, a.arm_b):
        assert spec.split("+")[0] in EDITION_DIR, f"unknown edition in spec: {spec}"
    setup()
    items = json.load(open(os.path.join(HERE, "interaction_scenarios.json")))
    if a.domains:
        ds = set(a.domains.split(",")); items = [x for x in items if x["domain"] in ds]
    if a.n: items = items[:a.n]
    out = os.path.join(HERE, a.out); done = set()
    if os.path.exists(out):
        # scrub: keep only CLEAN, de-duped rows; errored/no-winner rows are dropped so they retry
        seen = {}
        for l in open(out):
            try: r = json.loads(l)
            except Exception: continue
            if _is_good(r): seen[r["id"]] = r          # last clean row wins
        with open(out, "w") as fh:
            for r in seen.values(): fh.write(json.dumps(r) + "\n")
        done = set(seen.keys())
        print(f"[scrub] kept {len(done)} clean rows; retrying the rest", flush=True)
    todo = [x for x in items if x["id"] not in done]
    print(f"[interaction] under-test={a.model} A(control)={a.arm_a} B(treatment)={a.arm_b} "
          f"interactor={INTERACTOR_MODEL} judge={JUDGE_MODEL} turns={TURNS} todo={len(todo)} "
          f"workers={a.workers}", flush=True)
    fh = open(out, "a"); t0 = time.time(); n = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_one, x, a.arm_a, a.arm_b, a.model): x["id"] for x in todo}
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

DIMS = ["emergence", "information_richness", "value_to_participant",
        "participant_movement", "goal_evolution", "precision", "presence"]
NAME = {"A": "control", "B": "treatment"}   # actual specs printed from the records

def _names(recs):
    a = next((r.get("arm_a") for r in recs if r.get("arm_a")), "control")
    b = next((r.get("arm_b") for r in recs if r.get("arm_b")), "treatment")
    return {"A": a, "B": b}

def _is_good(r):
    """A record counts as done only if the judge ranked it AND neither transcript errored."""
    if r.get("winner_arm") not in ("A", "B"):
        return False
    for arm in ("A", "B"):
        for _u, a in r.get("transcripts", {}).get(arm, []):
            if isinstance(a, str) and "__ERROR__" in a:
                return False
    return True

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

def _vectors(recs):
    iv = {"A": [], "B": []}
    for r in recs:
        if r.get("winner_arm") not in ("A", "B"): continue
        d = r.get("info_vectors") or {}
        for x in ("A", "B"):
            try: iv[x].append(float(d.get(x)))
            except Exception: pass
    return iv

def cmd_score(a):
    recs = [json.loads(l) for l in open(os.path.join(HERE, a.out)) if l.strip()]
    ok, wins, dsum, dn, bydom, vlab, wsum = _agg(recs)
    nm = _names(recs); iv = _vectors(ok); N = len(ok)
    print(f"\n=== n={N} (+{len(recs)-N} unparsed) | {recs[0].get('under_test_model','?')} "
          f"A={nm['A']} vs B={nm['B']} judge={recs[0].get('judge','?')} ===")
    print("wins:", {nm[k]: wins[k] for k in ("A", "B")})
    print("\nmean value scores (1-10):")
    print("  arm                  "+"  ".join(f"{d[:5]:>5}" for d in DIMS)+"   MEAN")
    for x in ("A", "B"):
        if dn[x]:
            m = [dsum[x][d]/dn[x] for d in DIMS]
            print(f"  {nm[x]:18s}: "+"  ".join(f"{v:5.2f}" for v in m)+f"   {sum(m)/len(m):5.2f}")
    print(f"\nwins by domain ({nm['A']}/{nm['B']}):")
    for c in sorted(bydom): d = bydom[c]; print(f"  {c:13s}: {d['A']}/{d['B']}")
    if N:
        wa, wb = wsum['A']/N, wsum['B']/N
        print(f"\nwords/transcript: {nm['A']}={wa:.0f}  {nm['B']}={wb:.0f}  (ratio {wb/wa:.2f}x — descriptive, NOT penalized)")
        if iv["A"] and iv["B"]:
            va, vb = st.mean(iv["A"]), st.mean(iv["B"])
            print(f"info-vectors/convo: {nm['A']}={va:.1f}  {nm['B']}={vb:.1f}")
            print(f"vector-density (vectors/100w): {nm['A']}={100*va/wa:.2f}  {nm['B']}={100*vb/wb:.2f}")
        print(f"visible voice-labels (total): {nm['A']}={vlab['A']}  {nm['B']}={vlab['B']}")

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
    nm = _names(allrec); N = len(ok)
    print(f"\n--- POOLED n={N} ---")
    print("wins:", {nm[k]: wins[k] for k in ("A", "B")},
          f"  ({100*wins['B']/N:.0f}% B={nm['B']})" if N else "")
    print("mean value scores (1-10):")
    for x in ("A", "B"):
        if dn[x]:
            m = [dsum[x][d]/dn[x] for d in DIMS]
            print(f"  {nm[x]:18s}: "+"  ".join(f"{d[:5]}={v:.2f}" for d, v in zip(DIMS, m))
                  +f"  MEAN={sum(m)/len(m):.2f}")
    print(f"\npooled wins by domain ({nm['A']}/{nm['B']}):")
    for c in sorted(bydom): d = bydom[c]; print(f"  {c:13s}: {d['A']}/{d['B']}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    pr = sub.add_parser("run")
    pr.add_argument("--model", default="claude-haiku-4-5-20251001")
    pr.add_argument("--arm-a", dest="arm_a", default="vanilla",
                    help="control arm spec: vanilla|micro|mini|normal[+concise]")
    pr.add_argument("--arm-b", dest="arm_b", required=True,
                    help="treatment arm spec: micro|mini|normal[+concise]")
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
