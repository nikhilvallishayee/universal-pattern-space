#!/usr/bin/env python3
"""Pre-registered analysis for the v5.5 version ladder (see PREREG.md). Writes results.json + prints a summary."""
import json, math, os, random, re, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = json.load(open(os.path.join(HERE, "arms.json")))
QS = json.load(open(os.path.join(HERE, "questions.json")))["questions"]
VERT = {q["id"]: q["vertical"] for q in QS}
QTYPE = {q["id"]: q["type"] for q in QS}
DIMS = ["accuracy", "insight", "calibration", "alternatives", "clarity", "overall"]
EFFORTS = ["xhigh", "max"]
ORDER = sorted(ARMS, key=lambda a: ARMS[a]["index"])
PS_ARMS = [a for a in ORDER if ARMS[a]["kind"] != "vanilla"]
PRE_REWEAVE = ["v0.0-genesis", "v0.1.5", "v0.2.0", "v0.2.5", "v0.2.8", "v0.2.9", "v0.3.0"]
GROUNDED = ["v0.4.0", "v0.5.0", "v0.5.x-main"]


def jl(name, ok=lambda r: True):
    p = os.path.join(HERE, name)
    out = []
    if os.path.exists(p):
        for line in open(p):
            try:
                r = json.loads(line)
                if ok(r):
                    out.append(r)
            except Exception:
                pass
    return out


def binom_two_sided(k, n):
    if n == 0:
        return 1.0
    pmf = [math.comb(n, i) * 0.5 ** n for i in range(n + 1)]
    pk = pmf[k]
    return min(1.0, sum(p for p in pmf if p <= pk + 1e-12))


def boot_ci(cells, stat, B=4000, seed=55):
    """cluster bootstrap over questions: cells is {qid: [values...]}"""
    rng = random.Random(seed)
    keys = list(cells)
    vals = []
    for _ in range(B):
        sample = [rng.choice(keys) for _ in keys]
        flat = [v for k in sample for v in cells[k]]
        vals.append(stat(flat))
    vals.sort()
    return vals[int(0.025 * B)], vals[int(0.975 * B)]


def spearman(x, y):
    def rank(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and v[s[j + 1]] == v[s[i]]:
                j += 1
            for k in range(i, j + 1):
                r[s[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    rx, ry = rank(x), rank(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


TELLS = {
    "label_brackets": r"⟦",
    "voice_names": r"\b(Weaver|Maker|Checker|Grump|Deep Thought|Observer|Guardian|Scribe|Explorer|Exploiter|Ganapati|Vidura|Nachiketa)\b",
    "pattern_space": r"Pattern Space|UPS\b",
    "sanskrit_diacritics": r"[āīūṛṝḷṃḥṅñṭḍṇśṣ]",
    "devanagari": r"[ऀ-ॿ]",
    "emoji": r"[\U0001F300-\U0001FAFF☀-➿]",
    "status_labels": r"\b(FOUNDED|DEFENSIBLE|CONJECTURE|OVERREACH)\b",
}


def main():
    answers = {(r["arm"], r["effort"], r["qid"]): r for r in jl("answers.jsonl", lambda r: "text" in r)}
    judg = jl("judgments.jsonl", lambda r: r.get("parsed"))
    # score[(arm, effort, qid)][dim] -> list over judges ; also per-judge store
    score = defaultdict(lambda: defaultdict(list))
    per_judge = defaultdict(dict)   # (judge, effort, qid) -> {arm: {dim: v, rank: r}}
    for j in judg:
        l2a = j["label_to_arm"]
        sc = j["parsed"]["scores"]
        ranking = j["parsed"].get("ranking", [])
        for lab, arm in l2a.items():
            s = sc.get(lab)
            if not s:
                continue
            rec = {}
            for d in DIMS:
                if isinstance(s.get(d), (int, float)):
                    score[(arm, j["effort"], j["qid"])][d].append(float(s[d]))
                    rec[d] = float(s[d])
            if lab in ranking:
                rec["rank"] = ranking.index(lab) + 1
                score[(arm, j["effort"], j["qid"])]["rank"].append(rec["rank"])
            per_judge[(j["judge"], j["effort"], j["qid"])][arm] = rec
    M = lambda arm, e, q, d="overall": st.mean(score[(arm, e, q)][d]) if score[(arm, e, q)][d] else None
    cells = [(e, q["id"]) for e in EFFORTS for q in QS if all(M(a, e, q["id"]) is not None for a in ORDER)]
    res = {"n_answers": len(answers), "n_judgments": len(judg), "n_complete_cells": len(cells)}

    # --- arm table
    table = {}
    for a in ORDER:
        row = {}
        for d in DIMS + ["rank"]:
            vals = [M(a, e, q, d) for e, q in cells if M(a, e, q, d) is not None]
            row[d] = round(st.mean(vals), 3) if vals else None
        for e in EFFORTS:
            vals = [M(a, ee, q) for ee, q in cells if ee == e]
            row[f"overall_{e}"] = round(st.mean(vals), 3) if vals else None
        ws = [len(answers[(a, e, q)]["text"].split()) for e, q in cells if (a, e, q) in answers]
        row["mean_words"] = round(st.mean(ws)) if ws else None
        th = [answers[(a, e, q)].get("thinking_tokens") for e, q in cells if (a, e, q) in answers and answers[(a, e, q)].get("thinking_tokens")]
        row["mean_thinking_tokens"] = round(st.mean(th)) if th else None
        cx = [answers[(a, e, q)].get("ctx") for e, q in cells if (a, e, q) in answers and answers[(a, e, q)].get("ctx")]
        row["ctx_tokens"] = round(st.median(cx)) if cx else None
        # rank-1 wins (per judge judgment)
        row["rank1_wins"] = sum(1 for k, v in per_judge.items() if v.get(a, {}).get("rank") == 1)
        table[a] = row
    res["arm_table"] = table

    # --- pairwise vs vanilla (per cell, judge-mean)
    vs = {}
    for a in PS_ARMS:
        diffs = {q: [] for q in VERT}
        wins = losses = ties = 0
        for e, q in cells:
            dlt = M(a, e, q) - M("vanilla", e, q)
            diffs[q].append(dlt)
            wins += dlt > 1e-9
            losses += dlt < -1e-9
            ties += abs(dlt) <= 1e-9
        flat = [x for v in diffs.values() for x in v]
        lo, hi = boot_ci({k: v for k, v in diffs.items() if v}, st.mean)
        vs[a] = {"mean_diff": round(st.mean(flat), 3), "ci95": [round(lo, 3), round(hi, 3)], "wins": wins, "losses": losses,
                 "ties": ties, "sign_p": round(binom_two_sided(wins, wins + losses), 4)}
    res["vs_vanilla"] = vs

    # --- H1
    h = vs.get("v0.5.x-main")
    if h:
        res["H1"] = {**h, "falsified": h["wins"] <= 20 or (h["ci95"][0] <= 0 <= h["ci95"][1])}

    # --- H2 chronological trend over PS arms
    xs = [ARMS[a]["index"] for a in PS_ARMS]
    ys = [table[a]["overall"] for a in PS_ARMS]
    rho = spearman(xs, ys)
    # permutation p (one-sided, rho > 0)
    rng = random.Random(55)
    perm = sum(1 for _ in range(20000) if spearman(xs, rng.sample(ys, len(ys))) >= rho) / 20000
    res["H2"] = {"spearman_rho": round(rho, 3), "perm_p_one_sided": perm, "falsified": rho <= 0}

    # --- H3 calibration
    def pool(arms, d):
        return st.mean([M(a, e, q, d) for a in arms for e, q in cells])
    cal_pre, cal_van, cal_gr = pool(PRE_REWEAVE, "calibration"), pool(["vanilla"], "calibration"), pool(GROUNDED, "calibration")
    res["H3"] = {"calibration_pre_reweave": round(cal_pre, 3), "calibration_vanilla": round(cal_van, 3),
                 "calibration_grounded": round(cal_gr, 3),
                 "falsified": (cal_pre >= cal_van) or (cal_gr <= cal_pre)}

    # --- H4 effort
    gaps = {}
    for a in PS_ARMS:
        g = {}
        for e in EFFORTS:
            g[e] = st.mean([M(a, ee, q) - M("vanilla", ee, q) for ee, q in cells if ee == e])
        gaps[a] = {k: round(v, 3) for k, v in g.items()}
    cur = gaps.get("v0.5.x-main")
    pairs = jl("effort_pairs.jsonl", lambda r: r.get("parsed"))
    mx = xh = ti = 0
    by_arm = defaultdict(lambda: [0, 0, 0])
    for p in pairs:
        w = p["parsed"].get("winner")
        we = p.get(w) if w in ("X", "Y") else None
        if we == "max":
            mx += 1; by_arm[p["arm"]][0] += 1
        elif we == "xhigh":
            xh += 1; by_arm[p["arm"]][1] += 1
        else:
            ti += 1; by_arm[p["arm"]][2] += 1
    res["H4"] = {"gap_by_effort": gaps, "v05x_gap_max_minus_xhigh": round(cur["max"] - cur["xhigh"], 3) if cur else None,
                 "effort_pairs": {"max_wins": mx, "xhigh_wins": xh, "ties": ti, "sign_p": round(binom_two_sided(mx, mx + xh), 4)},
                 "effort_pairs_by_arm": {k: {"max": v[0], "xhigh": v[1], "tie": v[2]} for k, v in by_arm.items()}}

    # --- H5 + per-vertical
    pv = {}
    for a in PS_ARMS:
        pv[a] = {}
        for v in ["science", "philosophy", "self", "neurobiology", "AI"]:
            ds = [M(a, e, q) - M("vanilla", e, q) for e, q in cells if VERT[q].lower() == v.lower()]
            pv[a][v] = round(st.mean(ds), 3) if ds else None
        for t in ["conceptual", "empirical"]:
            ds = [M(a, e, q) - M("vanilla", e, q) for e, q in cells if QTYPE[q] == t]
            pv[a][t] = round(st.mean(ds), 3) if ds else None
    res["per_vertical_gap_vs_vanilla"] = pv
    c = pv.get("v0.5.x-main")
    if c:
        hum = st.mean([x for x in (c["philosophy"], c["self"]) if x is not None])
        sci = st.mean([x for x in (c["science"], c["neurobiology"]) if x is not None])
        res["H5"] = {"gap_phil_self": round(hum, 3), "gap_sci_neuro": round(sci, 3), "falsified": hum <= sci}

    # --- placebo (noise floor): two identically configured no-framework arms
    d = [M("vanilla-b", e, q) - M("vanilla", e, q) for e, q in cells]
    w = sum(x > 1e-9 for x in d); l = sum(x < -1e-9 for x in d)
    res["placebo_vanillaB_minus_vanilla"] = {"mean_diff": round(st.mean(d), 3), "mean_abs_diff": round(st.mean(abs(x) for x in d), 3),
                                             "sd_diff": round(st.pstdev(d), 3), "wins": w, "losses": l}
    # --- exploratory: the compression step (v0.2.8 -> v0.2.9 compressed L1-L3 by 40-67%)
    d = [M("v0.2.9", e, q) - M("v0.2.8", e, q) for e, q in cells]
    res["compression_step_v029_minus_v028"] = {"mean_diff": round(st.mean(d), 3), "wins": sum(x > 1e-9 for x in d), "losses": sum(x < -1e-9 for x in d)}

    # --- judge agreement: per (effort,qid), Spearman between judges' overall scores across arms
    agree = defaultdict(list)
    judges = sorted({k[0] for k in per_judge})
    for i, j1 in enumerate(judges):
        for j2 in judges[i + 1:]:
            for e, q in cells:
                a1, a2 = per_judge.get((j1, e, q)), per_judge.get((j2, e, q))
                if a1 and a2:
                    x = [a1[a]["overall"] for a in ORDER if a in a1 and a in a2 and "overall" in a1[a] and "overall" in a2[a]]
                    y = [a2[a]["overall"] for a in ORDER if a in a1 and a in a2 and "overall" in a1[a] and "overall" in a2[a]]
                    if len(x) > 3:
                        agree[f"{j1}~{j2}"].append(spearman(x, y))
    res["judge_agreement_spearman"] = {k: round(st.mean(v), 3) for k, v in agree.items()}
    # per-judge H1 robustness
    pj = {}
    for jn in judges:
        w = l = 0
        ds = []
        for e, q in cells:
            v = per_judge.get((jn, e, q), {})
            if "v0.5.x-main" in v and "vanilla" in v:
                dd = v["v0.5.x-main"]["overall"] - v["vanilla"]["overall"]
                ds.append(dd); w += dd > 0; l += dd < 0
        pj[jn] = {"v05x_minus_vanilla": round(st.mean(ds), 3) if ds else None, "wins": w, "losses": l}
    res["H1_per_judge"] = pj
    # per-judge arm means
    res["arm_overall_by_judge"] = {jn: {a: round(st.mean([per_judge[(jn, e, q)][a]["overall"] for e, q in cells
                                                         if a in per_judge.get((jn, e, q), {})]), 3) for a in ORDER} for jn in judges}

    # --- tells
    tells = {}
    for a in ORDER:
        t = {}
        txts = [answers[(a, e, q)]["text"] for e, q in cells if (a, e, q) in answers]
        for name, pat in TELLS.items():
            t[name] = round(sum(1 for x in txts if re.search(pat, x)) / max(1, len(txts)), 3)
        tells[a] = t
    res["tell_rates"] = tells

    # --- length vs score correlation (within cell, pooled)
    lx, ly = [], []
    for e, q in cells:
        ws = [len(answers[(a, e, q)]["text"].split()) for a in ORDER]
        sc = [M(a, e, q) for a in ORDER]
        mw, ms = st.mean(ws), st.mean(sc)
        lx += [w - mw for w in ws]
        ly += [s - ms for s in sc]
    res["within_cell_length_score_spearman"] = round(spearman(lx, ly), 3)

    json.dump(res, open(os.path.join(HERE, "results.json"), "w"), indent=2)
    print(json.dumps({k: res[k] for k in res if k not in ("arm_overall_by_judge",)}, indent=1)[:12000])


if __name__ == "__main__":
    main()
