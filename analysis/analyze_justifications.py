"""Do models' justifications track what they do with the detection rate?

Joins the judge codes from scripts/code_justifications.py with the penalties in the same responses. The main
question: when a justification says the low detection rate (1 in 50) is a reason for a harsher penalty, is the
penalty actually higher than in the matched 1-in-2 case (same template, mental state and month)?

Tests, per model x frame and pooled over frames (penalties in percent of scale; brackets are 95% bootstrap CIs
that resample matched pairs, then samples within each cell):
  raise gap       each 1-in-50 justification coded "raises": its penalty minus the matched 1-in-2 cell mean
  unqualified     the same, only for "raises" justifications that don't say the influence is small or capped
  other gap       the same for 1-in-50 justifications not coded "raises"
  within cell     in 1-in-50 cells with both kinds: mean penalty of "raises" samples minus the others
  clean contrast  pairs where most 1-in-50 justifications say "raises" and most 1-in-2 ones don't: the
                  detection effect in those pairs, where the stated reasons predict a gap

Codes: a justification's code is the judges' shared code when they agree, else the entry for it in
data/justification_codes/adjudicated.jsonl, else "disputed" (left out of the tests and listed in
analysis/output/<name>_disputes.md for adjudication). A sensitivity table reruns the key tests with
disputes where either judge said "raises" counted as raises, and again counted as not. An adjudicated.jsonl row:
  {"subject_model": ..., "item_id": ..., "sample": ..., "detection_role": ..., "raises_strength": ..., "note": ...}

Human validation: --sheet N writes a blind coding sheet of N justifications, stratified by model and detection
level, to analysis/output/justification_coding_sheet.csv (key: data/justification_codes/sheet_key.csv). Fill in
the code columns and save it as data/justification_codes/human_codes.csv; the next run reports agreement.

Usage: python3 analysis/analyze_justifications.py [--sources DIR ...] [--codes DIR] [--name NAME] [--boot N] [--sheet N]
  A variant run (e.g. data/signal_openrouter_lowharm) reuses item ids, so code it into its own --codes directory
  and give its report its own --name.
"""

import argparse
import collections
import csv
import json
import random
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_pilot import SESOI, ci_fmt, to_pct  # noqa: E402
from code_justifications import DEFAULT_SOURCES, ROLES  # noqa: E402
from code_justifications import OUT_DIR as CODES_DIR  # noqa: E402

ITEMS = ROOT / "prompts" / "items.jsonl"
JUDGES = ROOT / "config" / "judges.json"
OUT_DIR = ROOT / "analysis" / "output"
ADJUDICATED = CODES_DIR / "adjudicated.jsonl"
HUMAN = CODES_DIR / "human_codes.csv"
SHEET = OUT_DIR / "justification_coding_sheet.csv"
SHEET_KEY = CODES_DIR / "sheet_key.csv"
CEILING_PCT = 95.0  # a pair whose 1-in-2 median is at or above this can't show a detection increase
HI, LO = "1_in_50", "1_in_2"


# ---------------------------------------------------------------- loading

def load_responses(sources):
    """{(model, item_id, sample): row info} for penalty items in either format."""
    items = {i["id"]: i for i in map(json.loads, ITEMS.open())}
    out = {}
    for src in sources:
        for path in sorted(Path(src).glob("*.jsonl")):
            for row in map(json.loads, path.open()):
                item = items.get(row["item_id"])
                if not item or item["measure"] != "penalty" or row.get("error"):
                    continue
                m, p = item["meta"], row.get("parsed")
                pen = p.get("penalty") if isinstance(p, dict) else None
                key = (row["model_id"], row["item_id"], row["sample"])
                if key in out:
                    raise SystemExit(f"duplicate row {key} across sources")
                out[key] = {"model": row["model_id"], "frame": item["frame"], "format": m["format"],
                            "pair": (m["template"], m["mental_state"], m["month"]), "detection": m["detection"],
                            "pct": to_pct(pen, m["penalty_key"]),
                            "explanation": p.get("explanation") if isinstance(p, dict) else None}
    return out


def load_codes(judge_ids, codes_dir=CODES_DIR):
    """{judge: {key: code}}; the last successful row per key wins."""
    codes = {}
    for j in judge_ids:
        path, codes[j] = codes_dir / f"{j}.jsonl", {}
        if path.exists():
            for r in map(json.loads, path.open()):
                if r.get("error") is None and r.get("code"):
                    codes[j][(r["subject_model"], r["item_id"], r["sample"])] = r["code"]
    return codes


def load_adjudicated(codes_dir=CODES_DIR):
    path = codes_dir / ADJUDICATED.name
    if not path.exists():
        return {}
    return {(r["subject_model"], r["item_id"], r["sample"]): r for r in map(json.loads, path.open())}


def consensus(keys, codes, adjudicated):
    """{key: {"role", "strength", "deterrence", "status"}} for keys every judge has coded."""
    judges = list(codes)
    out = {}
    for k in keys:
        cs = [codes[j].get(k) for j in judges]
        if any(c is None for c in cs):
            continue
        roles = {c["detection_role"] for c in cs}
        strengths = {c["raises_strength"] for c in cs}
        deterrence = all(c["deterrence_mentioned"] for c in cs)
        if k in adjudicated:
            a = adjudicated[k]
            out[k] = {"role": a["detection_role"], "strength": a.get("raises_strength"),
                      "deterrence": deterrence, "status": "adjudicated"}
        elif len(roles) == 1:
            out[k] = {"role": roles.pop(), "strength": strengths.pop() if len(strengths) == 1 else "split",
                      "deterrence": deterrence, "status": "agreed"}
        else:
            out[k] = {"role": "disputed", "strength": None, "deterrence": deterrence, "status": "disputed",
                      "judge_roles": sorted(roles), "judge_strengths": sorted(s for s in strengths if s)}
    return out


# ---------------------------------------------------------------- agreement

def kappa(a, b):
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    pe = sum(ca[c] * cb[c] for c in set(ca) | set(cb)) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def agreement(codes, keys):
    j1, j2 = list(codes)[:2]
    both = [k for k in keys if k in codes[j1] and k in codes[j2]]
    r1 = [codes[j1][k]["detection_role"] for k in both]
    r2 = [codes[j2][k]["detection_role"] for k in both]
    by_model = collections.defaultdict(list)
    for k, x, y in zip(both, r1, r2):
        by_model[k[0]].append(x == y)
    strength = [(codes[j1][k]["raises_strength"], codes[j2][k]["raises_strength"])
                for k, x, y in zip(both, r1, r2) if x == y == "raises"]
    return {"judges": [j1, j2], "n": len(both),
            "role_agreement": st.mean(x == y for x, y in zip(r1, r2)) if both else None,
            "role_kappa": kappa(r1, r2),
            "raises_kappa": kappa([x == "raises" for x in r1], [y == "raises" for y in r2]),
            "role_agreement_by_model": {m: st.mean(v) for m, v in sorted(by_model.items())},
            "strength_agreement_when_both_raise": st.mean(a == b for a, b in strength) if strength else None,
            "confusion": {f"{x} / {y}": n for (x, y), n in sorted(collections.Counter(zip(r1, r2)).items())}}


def human_agreement(codes, cons):
    """Agreement of each judge and the consensus with a filled-in human coding sheet, if there is one."""
    if not HUMAN.exists() or not SHEET_KEY.exists():
        return None
    key = {r["row_id"]: (r["subject_model"], r["item_id"], int(r["sample"])) for r in csv.DictReader(SHEET_KEY.open())}
    human = {key[r["row_id"]]: r["detection_role"].strip() for r in csv.DictReader(HUMAN.open())
             if r.get("detection_role", "").strip() in ROLES and r["row_id"] in key}
    out = {"n": len(human)}
    for name, get in [*((j, lambda k, j=j: (codes[j].get(k) or {}).get("detection_role")) for j in codes),
                      ("consensus", lambda k: (cons.get(k) or {}).get("role"))]:
        pairs = [(h, get(k)) for k, h in human.items() if get(k) is not None]
        out[name] = {"n": len(pairs), "agreement": st.mean(a == b for a, b in pairs) if pairs else None,
                     "kappa": kappa(*zip(*pairs)) if pairs else None}
    return out


# ---------------------------------------------------------------- tests

def resolved(c, disputes):
    """(role, strength), with disputed codes resolved for the sensitivity check: disputes="raises" counts a
    dispute where either judge said raises as raises; "other" counts it as not raises."""
    if c["role"] != "disputed" or disputes is None or "raises" not in c["judge_roles"]:
        return c["role"], c["strength"]
    if disputes == "raises":
        return "raises", (c["judge_strengths"][0] if len(c["judge_strengths"]) == 1 else "limited")
    return "unclear", None


def pairs_for(resp, cons, model, frames, disputes=None):
    """{(frame, pair): {detection level: [(pct, role, strength)]}} for coded justification rows with a penalty."""
    pairs = collections.defaultdict(lambda: collections.defaultdict(list))
    for k, r in resp.items():
        if r["model"] == model and r["frame"] in frames and r["format"] == "justification" \
                and r["pct"] is not None and k in cons:
            pairs[(r["frame"], r["pair"])][r["detection"]].append((r["pct"], *resolved(cons[k], disputes)))
    return {p: dict(v) for p, v in pairs.items() if v.get(HI) and v.get(LO)}


def share(xs, pred):
    xs = [x for x in xs if x[1] != "disputed"]
    return st.mean(pred(x) for x in xs) if xs else None


def stats(pairs, ceiling=False):
    raise_gaps, unq_gaps, other_gaps, no_higher, within, clean, det = [], [], [], [], [], [], []
    hi_raise, lo_raise = [], []
    for cells in pairs.values():
        hi, lo = cells[HI], cells[LO]
        lo_pcts = [x[0] for x in lo]
        lo_mean, lo_med = st.mean(lo_pcts), st.median(lo_pcts)
        if ceiling and lo_med >= CEILING_PCT:
            continue
        hi_mean = st.mean(x[0] for x in hi)
        det.append(hi_mean - lo_mean)
        r = [x[0] for x in hi if x[1] == "raises"]
        o = [x[0] for x in hi if x[1] not in ("raises", "disputed")]
        raise_gaps += [x - lo_mean for x in r]
        unq_gaps += [x[0] - lo_mean for x in hi if x[1] == "raises" and x[2] == "unqualified"]
        other_gaps += [x - lo_mean for x in o]
        no_higher += [x <= lo_med for x in r]
        if r and o:
            within.append(st.mean(r) - st.mean(o))
        sh, sl = share(hi, lambda x: x[1] == "raises"), share(lo, lambda x: x[1] == "raises")
        hi_raise += [x[1] == "raises" for x in hi if x[1] != "disputed"]
        lo_raise += [x[1] == "raises" for x in lo if x[1] != "disputed"]
        if sh is not None and sl is not None and sh > 0.5 and sl < 0.5:
            clean.append(hi_mean - lo_mean)
    m = lambda xs: st.mean(xs) if xs else None  # noqa: E731
    rg, og = m(raise_gaps), m(other_gaps)
    return {"pairs": len(det), "detection_effect": m(det),
            "raises_share_1_in_50": m(hi_raise), "raises_share_1_in_2": m(lo_raise),
            "n_raise": len(raise_gaps), "raise_gap": rg, "raise_no_higher_than_1_in_2_median": m(no_higher),
            "n_unqualified": len(unq_gaps), "unqualified_gap": m(unq_gaps),
            "n_other": len(other_gaps), "other_gap": og,
            "raise_minus_other": rg - og if rg is not None and og is not None else None,
            "within_cell_cells": len(within), "within_cell": m(within),
            "clean_pairs": len(clean), "clean_effect": m(clean)}


CI_STATS = ("detection_effect", "raise_gap", "unqualified_gap", "other_gap", "raise_minus_other", "within_cell", "clean_effect")


def bootstrap(pairs, n, ceiling=False, seed=0):
    rng = random.Random(seed)
    keys = list(pairs)
    draws = collections.defaultdict(list)
    for _ in range(n):
        res = {}
        for i in range(len(keys)):
            k = rng.choice(keys)
            res[i] = {lvl: [rng.choice(v) for _ in v] for lvl, v in pairs[k].items()}
        s = stats(res, ceiling)
        for name in CI_STATS:
            if s[name] is not None:
                draws[name].append(s[name])
    cis = {}
    for name, vals in draws.items():
        vals.sort()
        cis[name] = (vals[int(0.025 * len(vals))], vals[min(int(0.975 * len(vals)), len(vals) - 1)])
    return cis


def format_check(resp, model, frame):
    """Detection effect (1 in 50 minus 1 in 2, matched pairs) separately for each penalty format."""
    out = {}
    for f in ("penalty_only", "justification"):
        cells = collections.defaultdict(list)
        for r in resp.values():
            if r["model"] == model and r["frame"] == frame and r["format"] == f and r["pct"] is not None:
                cells[(r["pair"], r["detection"])].append(r["pct"])
        diffs = [st.mean(cells[(p, HI)]) - st.mean(cells[(p, LO)]) for p, d in cells if d == HI and cells.get((p, LO))]
        n = collections.Counter(len(v) for v in cells.values())
        out[f] = {"effect": st.mean(diffs) if diffs else None, "samples_per_cell": dict(n)}
    return out


def prevalence(resp, cons, model, frame):
    out = {}
    for det in (HI, LO):
        cs = [cons[k] for k, r in resp.items() if r["model"] == model and r["frame"] == frame
              and r["format"] == "justification" and r["detection"] == det and k in cons]
        if not cs:
            continue
        roles = collections.Counter(c["role"] for c in cs)
        raises = [c for c in cs if c["role"] == "raises"]
        out[det] = {"n": len(cs), "roles": {r: roles[r] / len(cs) for r in (*ROLES, "disputed") if roles[r]},
                    "limited_share_of_raises": st.mean(c["strength"] == "limited" for c in raises) if raises else None,
                    "deterrence_mentioned": st.mean(c["deterrence"] for c in cs)}
    return out


# ---------------------------------------------------------------- output

def pct(x):
    return "–" if x is None else f"{x:.0%}"


def report_md(res, sources):
    ag = res["agreement"]
    L = ["# Justification coding: do stated reasons track the penalty?", "",
         f"*Generated by analysis/analyze_justifications.py from {', '.join(sources)}. Penalties in percent of "
         f"scale; SESOI = {SESOI:g}%; brackets are 95% bootstrap CIs over matched pairs and samples. "
         f"Judges: {', '.join(ag['judges'])}. Each saw only the explanation text.*", "",
         "## Judge agreement", "",
         f"- {ag['n']} justifications coded by both judges. Detection role: agreement {pct(ag['role_agreement'])}, "
         f"Cohen's kappa {ag['role_kappa']:.2f}; raises vs. not: kappa {ag['raises_kappa']:.2f}. "
         f"When both say raises, they agree on strength {pct(ag['strength_agreement_when_both_raise'])}.",
         "- Agreement by subject model: " + ", ".join(f"{m} {pct(v)}" for m, v in ag["role_agreement_by_model"].items()),
         f"- Codes used: {res['status_counts'].get('agreed', 0)} agreed, {res['status_counts'].get('adjudicated', 0)} "
         f"adjudicated, {res['status_counts'].get('disputed', 0)} still disputed (left out of the tests; listed in "
         "analysis/output/<name>_disputes.md)."]
    h = res.get("human")
    if h:
        L.append(f"- Against human codes (n={h['n']}): " + ", ".join(
            f"{name} {pct(v['agreement'])} (kappa {v['kappa']:.2f})" for name, v in h.items() if name != "n" and v["n"]))
    else:
        L.append("- No human codes yet (see --sheet).")

    L += ["", "## How often each model cites the detection rate", "",
          "| Model | Frame | Detection | n | raises (limited share) | lowers | dismissed | unclear | not mentioned | disputed | any deterrence |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for (model, frame), r in res["groups"].items():
        for det, p in r["prevalence"].items():
            g = p["roles"].get
            L.append(f"| {model} | {frame} | {det.replace('_', ' ')} | {p['n']} | {pct(g('raises'))} "
                     f"({pct(p['limited_share_of_raises'])}) | {pct(g('lowers'))} | {pct(g('dismissed'))} | "
                     f"{pct(g('unclear'))} | {pct(g('not_mentioned'))} | {pct(g('disputed'))} | "
                     f"{pct(p['deterrence_mentioned'])} |")

    for label, field in (("all pairs", "tests"), (f"excluding ceiling pairs (1-in-2 median ≥ {CEILING_PCT:g}%)",
                                                   "tests_no_ceiling")):
        L += ["", f"## Do 'raises' justifications come with higher penalties? ({label})", "",
              "| Model | Frame | Pairs | Detection effect | 'Raises' at 1 in 50 / 1 in 2 | n raises | Raise gap | "
              "No higher than 1-in-2 median | Unqualified raises: gap (n) | Other gap | Raise − other | Within cell (cells) | Clean contrast (pairs) |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for (model, frame), r in res["groups"].items():
            s, c = r[field]["stats"], r[field]["ci"]
            L.append(f"| {model} | {frame} | {s['pairs']} | {ci_fmt(s['detection_effect'], c.get('detection_effect'))} | "
                     f"{pct(s['raises_share_1_in_50'])} / {pct(s['raises_share_1_in_2'])} | {s['n_raise']} | "
                     f"{ci_fmt(s['raise_gap'], c.get('raise_gap'))} | {pct(s['raise_no_higher_than_1_in_2_median'])} | "
                     f"{ci_fmt(s['unqualified_gap'], c.get('unqualified_gap'))} ({s['n_unqualified']}) | "
                     f"{ci_fmt(s['other_gap'], c.get('other_gap'))} | "
                     f"{ci_fmt(s['raise_minus_other'], c.get('raise_minus_other'))} | "
                     f"{ci_fmt(s['within_cell'], c.get('within_cell'))} ({s['within_cell_cells']}) | "
                     f"{ci_fmt(s['clean_effect'], c.get('clean_effect'))} ({s['clean_pairs']}) |")

    L += ["", "## Sensitivity: disputed codes involving 'raises', counted as raises / as not raises", "",
          "| Model | Frame | Raise gap | Unqualified raise gap | Clean contrast (pairs) |", "|---|---|---|---|---|"]
    for (model, frame), r in res["groups"].items():
        a, b = r["disputes_as_raises"], r["disputes_as_other"]
        cell = lambda name: (f"{ci_fmt(a['stats'][name], a['ci'].get(name))} / "  # noqa: E731
                             f"{ci_fmt(b['stats'][name], b['ci'].get(name))}")
        L.append(f"| {model} | {frame} | {cell('raise_gap')} | {cell('unqualified_gap')} | {cell('clean_effect')} "
                 f"({a['stats']['clean_pairs']} / {b['stats']['clean_pairs']}) |")

    L += ["", "## Format check: does writing a justification change the detection effect?", "",
          "| Model | Frame | Penalty only | With justification |", "|---|---|---|---|"]
    for (model, frame), r in res["groups"].items():
        if frame == "both":
            continue
        fc = r["format_check"]
        L.append(f"| {model} | {frame} | {ci_fmt(fc['penalty_only']['effect'], None)} "
                 f"({'/'.join(map(str, sorted(fc['penalty_only']['samples_per_cell'])))} per cell) | "
                 f"{ci_fmt(fc['justification']['effect'], None)} "
                 f"({'/'.join(map(str, sorted(fc['justification']['samples_per_cell'])))} per cell) |")
    return "\n".join(L) + "\n"


def disputes_md(resp, codes, cons):
    judges = list(codes)
    L = ["# Disputed justification codes", "",
         "Judges disagreed on these. To settle one, add a row to data/justification_codes/adjudicated.jsonl.", ""]
    for k, c in sorted(cons.items()):
        if c["status"] != "disputed":
            continue
        L += [f"## {k[0]} · {k[1]} · sample {k[2]}", "", f"> {resp[k]['explanation']}", ""]
        for j in judges:
            cj = codes[j][k]
            L.append(f"- {j}: **{cj['detection_role']}** {cj['raises_strength'] or ''} — \"{cj['quote']}\"")
        L.append("")
    return "\n".join(L)


def write_sheet(resp, cons, n, seed=0):
    rng = random.Random(seed)
    strata = collections.defaultdict(list)
    for k in sorted(cons):
        strata[(k[0], resp[k]["detection"])].append(k)
    per = max(1, n // len(strata))
    picked = [k for s in sorted(strata) for k in rng.sample(strata[s], min(per, len(strata[s])))]
    rng.shuffle(picked)
    with SHEET.open("w", newline="") as fh, SHEET_KEY.open("w", newline="") as fk:
        w, wk = csv.writer(fh), csv.writer(fk)
        w.writerow(["row_id", "explanation", "detection_role", "raises_strength", "deterrence_mentioned", "notes"])
        wk.writerow(["row_id", "subject_model", "item_id", "sample"])
        for i, k in enumerate(picked, 1):
            w.writerow([i, resp[k]["explanation"], "", "", "", ""])
            wk.writerow([i, *k])
    print(f"wrote {len(picked)} rows to {SHEET.relative_to(ROOT)} (key: {SHEET_KEY.relative_to(ROOT)}). "
          f"Codes: detection_role one of {', '.join(ROLES)}; raises_strength limited/unqualified; "
          f"deterrence_mentioned true/false.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", nargs="+", type=Path, default=DEFAULT_SOURCES)
    ap.add_argument("--codes", type=Path, default=CODES_DIR, help="judge codes directory")
    ap.add_argument("--name", default="justifications", help="report name (default justifications)")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--sheet", type=int, help="write a blind human coding sheet of about N justifications")
    args = ap.parse_args()

    resp = load_responses(args.sources)
    judge_ids = [j["id"] for j in json.loads(JUDGES.read_text())["judges"]]
    codes_dir = args.codes if args.codes.is_absolute() else ROOT / args.codes
    codes = load_codes(judge_ids, codes_dir)
    just_keys = [k for k, r in resp.items() if r["format"] == "justification" and r["explanation"]]
    cons = consensus(just_keys, codes, load_adjudicated(codes_dir))
    if not cons:
        raise SystemExit("no justification has been coded by every judge; run scripts/code_justifications.py")
    if args.sheet:
        write_sheet(resp, cons, args.sheet)

    res = {"agreement": agreement(codes, just_keys), "human": human_agreement(codes, cons),
           "status_counts": dict(collections.Counter(c["status"] for c in cons.values())),
           "uncoded": len(just_keys) - len(cons), "groups": {}}
    models = sorted({r["model"] for r in resp.values()})
    for model in models:
        for frame in ("legal", "social", "both"):
            frames = ("legal", "social") if frame == "both" else (frame,)
            pairs = pairs_for(resp, cons, model, frames)
            if not pairs:
                continue
            g = {"tests": {"stats": stats(pairs), "ci": bootstrap(pairs, args.boot)},
                 "tests_no_ceiling": {"stats": stats(pairs, True), "ci": bootstrap(pairs, args.boot, True)}}
            for d in ("raises", "other"):
                dp = pairs_for(resp, cons, model, frames, d)
                g[f"disputes_as_{d}"] = {"stats": stats(dp), "ci": bootstrap(dp, args.boot)}
            if frame != "both":
                g["prevalence"] = prevalence(resp, cons, model, frame)
                g["format_check"] = format_check(resp, model, frame)
            else:
                g["prevalence"] = {}
            res["groups"][(model, frame)] = g

    sources = [str(Path(s).resolve().relative_to(ROOT)) if Path(s).resolve().is_relative_to(ROOT) else str(s)
               for s in args.sources]
    md = report_md(res, sources)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{args.name}_report.md").write_text(md)
    (OUT_DIR / f"{args.name}_report.json").write_text(json.dumps(
        {**res, "groups": {f"{m}|{f}": g for (m, f), g in res["groups"].items()}}, indent=2, default=list))
    (OUT_DIR / f"{args.name}_disputes.md").write_text(disputes_md(resp, codes, cons))
    if res["uncoded"]:
        print(f"note: {res['uncoded']} justifications aren't coded by every judge yet and are left out")
    print(md)
    print(f"wrote analysis/output/{args.name}_report.{{md,json}} and {args.name}_disputes.md")


if __name__ == "__main__":
    main()
