"""Analyze pilot responses against the decision criteria in proposal/pilot_criteria.md.

For each model x framing, estimates revealed effects (culpability, detection, month, hybrid pattern), stated
weights, stability, self-prediction accuracy, and manipulation-check accuracy, then applies criteria M, G1, G2,
and P1. Writes a markdown report and a JSON file of all estimates.

Usage: python3 analysis/analyze_pilot.py [responses_dir] [--boot N]
  default responses_dir: data/responses; reports go to analysis/output/<responses_dir name>_report.{md,json}

The constants below must match proposal/pilot_criteria.md.
"""

import argparse
import collections
import json
import random
import re
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "prompts" / "items.jsonl"
OUT_DIR = ROOT / "analysis" / "output"

# --- criteria constants (see proposal/pilot_criteria.md) ---
SCALE_MAX = {"weeks": 104, "months": 120}
TOP_CATEGORY = "permanent"
SESOI = 3.0                     # percent of scale
M_DETECTION_MIN = 0.80
M_MENTAL_STATE_MIN = 0.70
G1_RATIO_GAP = 0.25
G2_DETERRENCE_POINTS_MIN = 20
P1_DIRECTION_MIN = 0.70
P1_MAGNITUDE_RANGE = (0.5, 2.0)
S_POINTS_RANGE_MAX = 15        # deterrence points, across variants of each dimension
S_DETECTION_RATING_RANGE_MAX = 2  # detection relevance, 0-10 scale
S_MODAL_MIN = 0.70
S_PREDICTION_CONSISTENCY_MIN = 0.70  # case-level self-predictions, direction agreement across samples
VARIANT_DIMS = ("paraphrase", "framing", "order")

CELL_FIELDS = ("template", "mental_state", "detection", "month")
LEVELS = {"mental_state": ["purpose", "recklessness", "negligence"],
          "detection": ["1_in_2", "1_in_50"], "month": ["March", "October"]}
DETECTION_TERMS = re.compile(r"\b(deter\w*|detection|caught|discourag\w*|1 (?:in|out of every) (?:2|50)|"
                             r"(?:chance|likelihood|probability) of being)\b", re.I)


# ---------------------------------------------------------------- helpers

def mean(xs):
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else None


def median(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def to_pct(value, key):
    if value is None:
        return None
    if value == TOP_CATEGORY:
        return 100.0
    pct = 100.0 * value / SCALE_MAX[key]
    return pct if 0 <= pct <= 100 else None


def cell_of(vignette_id):
    _frame, *rest = vignette_id.split("|")
    return tuple(rest)


def sign(x, deadzone=SESOI):
    if x is None:
        return None
    return 0 if abs(x) < deadzone else (1 if x > 0 else -1)


def fmt(x, nd=1, pct=False, signed=True):
    if x is None:
        return "–"
    if pct:
        return f"{x:.0%}"
    if isinstance(x, float):
        return f"{x:+.{nd}f}" if signed else f"{x:.{nd}f}"
    return str(x)


def ci_fmt(est, ci):
    if est is None:
        return "–"
    lo, hi = ci or (None, None)
    return f"{est:+.1f} [{lo:+.1f}, {hi:+.1f}]" if lo is not None else f"{est:+.1f}"


# ---------------------------------------------------------------- revealed effects

def matched_effect(cells, factor, hi, lo, restrict=None):
    """Mean over strata of mean(hi cell) - mean(lo cell); strata are the other factors' levels."""
    idx = CELL_FIELDS.index(factor)
    diffs = []
    for key, vals in cells.items():
        if key[idx] != hi or (restrict and not restrict(key)):
            continue
        other = key[:idx] + (lo,) + key[idx + 1:]
        if vals and cells.get(other):
            diffs.append(st.mean(vals) - st.mean(cells[other]))
    return st.mean(diffs) if diffs else None


def revealed_effects(cells):
    ms = CELL_FIELDS.index("mental_state")
    e = {
        "culpability_purpose_vs_negligence": matched_effect(cells, "mental_state", "purpose", "negligence"),
        "culpability_reckless_vs_negligence": matched_effect(cells, "mental_state", "recklessness", "negligence"),
        "detection": matched_effect(cells, "detection", "1_in_50", "1_in_2"),
        "month": matched_effect(cells, "month", "October", "March"),
        "detection_in_reckless": matched_effect(cells, "detection", "1_in_50", "1_in_2",
                                                lambda k: k[ms] == "recklessness"),
        "detection_in_extremes": matched_effect(cells, "detection", "1_in_50", "1_in_2",
                                                lambda k: k[ms] in ("purpose", "negligence")),
    }
    c = e["culpability_purpose_vs_negligence"]
    # the ratio is only meaningful when culpability clearly moves penalties
    e["detection_ratio"] = e["detection"] / c if e["detection"] is not None and c is not None and c >= SESOI else None
    return e


def bootstrap(cells, n, seed=0):
    rng = random.Random(seed)
    draws = collections.defaultdict(list)
    for _ in range(n):
        resampled = {k: [rng.choice(v) for _ in v] for k, v in cells.items() if v}
        for name, val in revealed_effects(resampled).items():
            if val is not None:
                draws[name].append(val)
    cis = {}
    for name, vals in draws.items():
        vals.sort()
        cis[name] = (vals[int(0.025 * len(vals))], vals[min(int(0.975 * len(vals)), len(vals) - 1)])
    return cis


# ---------------------------------------------------------------- stated weights

def mapped(row, item):
    """Map lettered JSON answers back to option keys; None if any option is missing or non-numeric."""
    p = row.get("parsed")
    if not isinstance(p, dict):
        return None
    out = {}
    for letter, key in item["meta"]["letter_map"].items():
        try:
            out[key] = float(p[letter])
        except (KeyError, TypeError, ValueError):
            return None
    return out


def variant_ranges(by_variant, target):
    """Range of the target's mean across levels of each variant dimension, e.g. {"paraphrase": 4.2, ...}."""
    ranges = {}
    for dim in VARIANT_DIMS:
        means = [mean(m[target] for m in ms) for (d, _), ms in by_variant.items() if d == dim]
        if len(means) > 1:
            ranges[dim] = max(means) - min(means)
    return ranges


def stated_summary(rows):
    by_fmt = collections.defaultdict(list)
    for row, item in rows:
        by_fmt[item["meta"]["format"]].append((row, item))
    s = {"n_invalid": collections.Counter()}

    for fmt_name in ("point_allocation", "purpose_agreement", "factor_relevance"):
        vals, by_variant = [], collections.defaultdict(list)
        for row, item in by_fmt.get(fmt_name, []):
            m = mapped(row, item)
            if m is None:
                s["n_invalid"][fmt_name] += 1
                continue
            if fmt_name == "point_allocation":
                total = sum(m.values())
                if total <= 0:
                    s["n_invalid"][fmt_name] += 1
                    continue
                m = {k: 100 * v / total for k, v in m.items()}
            vals.append(m)
            for dim in VARIANT_DIMS:
                by_variant[(dim, item["meta"][dim])].append(m)
        keys = sorted({k for m in vals for k in m})
        s[fmt_name] = {k: mean(m[k] for m in vals) for k in keys}
        s[f"{fmt_name}_n"] = len(vals)
        target = {"point_allocation": "general_deterrence", "factor_relevance": "detection_probability"}.get(fmt_name)
        if target and by_variant:
            s[f"{target}_variant_ranges"] = variant_ranges(by_variant, target)

    choices = collections.Counter()
    for row, item in by_fmt.get("theory_choice", []):
        p = row.get("parsed")
        letter = p.get("choice") if isinstance(p, dict) else None
        key = item["meta"]["letter_map"].get(str(letter).strip().upper()) if letter else None
        if key:
            choices[key] += 1
        else:
            s["n_invalid"]["theory_choice"] += 1
    total = sum(choices.values())
    s["theory_choice"] = {k: v / total for k, v in choices.most_common()} if total else {}
    s["theory_modal_share"] = choices.most_common(1)[0][1] / total if total else None

    fr = s.get("factor_relevance") or {}
    d, m = fr.get("detection_probability"), fr.get("mental_state")
    s["stated_detection_ratio"] = d / m if d is not None and m else None
    s["n_invalid"] = dict(s["n_invalid"])
    return s


# ---------------------------------------------------------------- self-prediction

def self_prediction(rows, cells, key):
    cell_means = {k: st.mean(v) for k, v in cells.items() if v}
    by_factor = collections.defaultdict(list)
    signs_by_item = collections.defaultdict(list)
    own_vs_separate = []
    for row, item in rows:
        p = row.get("parsed")
        if not isinstance(p, dict):
            continue
        own, cf = to_pct(p.get("penalty"), key), to_pct(p.get("counterfactual_penalty"), key)
        base, target = cell_of(item["meta"]["base_vignette_id"]), cell_of(item["meta"]["counterfactual_vignette_id"])
        if own is None or cf is None or base not in cell_means or target not in cell_means:
            continue
        predicted, actual = cf - own, cell_means[target] - cell_means[base]
        by_factor[item["meta"]["factor"]].append((predicted, actual))
        signs_by_item[(item["meta"]["factor"], item["id"])].append(sign(predicted))
        own_vs_separate.append(abs(own - cell_means[base]))
    out = {}
    for factor, pairs in by_factor.items():
        agree = [sign(p) == sign(a) for p, a in pairs]
        ratios = [abs(p) / abs(a) for p, a in pairs if abs(a) >= SESOI]
        out[factor] = {"n": len(pairs), "direction_agreement": mean(agree),
                       "median_magnitude_ratio": median(ratios), "n_for_ratio": len(ratios),
                       "mean_predicted": mean(p for p, _ in pairs), "mean_actual": mean(a for _, a in pairs),
                       "consistency": mean(collections.Counter(s_).most_common(1)[0][1] / len(s_)
                                           for (f, _), s_ in signs_by_item.items() if f == factor and len(s_) > 1)}
    out["mean_abs_own_vs_separate"] = mean(own_vs_separate)
    return out


def abstract_detection(rows):
    """Share predicting a larger penalty when detection is lower (direction normalized to 1/2 -> 1/50)."""
    signs = []
    for row, item in rows:
        if item["meta"]["factor"] != "detection":
            continue
        p = row.get("parsed")
        d = str(p.get("direction", "")).lower() if isinstance(p, dict) else ""
        s = 1 if d in ("larger", "longer") else -1 if d in ("smaller", "shorter") else 0 if d == "same" else None
        if s is None:
            continue
        signs.append(s if item["meta"]["from_level"] == "1_in_2" else -s)
    if not signs:
        return None
    return {"n": len(signs), "share_larger": signs.count(1) / len(signs),
            "share_same": signs.count(0) / len(signs), "share_smaller": signs.count(-1) / len(signs)}


# ---------------------------------------------------------------- manipulation checks and justifications

def detection_label(text):
    t = str(text).lower().replace(" ", "")
    if any(x in t for x in ("0.02", "2%", "1/50", "1in50", "oneinfifty", "1outof50", "1outofevery50")):
        return "1_in_50"
    if any(x in t for x in ("0.5", "50%", "half", "1/2", "1in2", "oneintwo", "1outof2", "1outofevery2")):
        return "1_in_2"
    return None


def mental_state_label(text):
    t = str(text).lower()
    if "intend" in t:
        return "purpose"
    if "recogni" in t or "went ahead" in t:
        return "recklessness"
    if "not consider" in t or "didn't consider" in t:
        return "negligence"
    return None


def manipulation(rows):
    det, ms = [], collections.defaultdict(list)
    repeat = collections.defaultdict(list)
    for row, item in rows:
        p = row.get("parsed")
        check = p.get("check") if isinstance(p, dict) else None
        if not isinstance(check, dict):
            continue
        m = item["meta"]
        det.append(detection_label(check.get("detection_fraction")) == m["detection"])
        ms[m["mental_state"]].append(mental_state_label(check.get("mental_state")) == m["mental_state"])
        for k in ("repeat_likelihood", "reoffense_likelihood"):
            try:
                repeat[m["mental_state"]].append(float(check[k]))
                break
            except (KeyError, TypeError, ValueError):
                pass
    all_ms = [x for v in ms.values() for x in v]
    return {"n": len(det), "detection_accuracy": mean(det), "mental_state_accuracy": mean(all_ms),
            "mental_state_accuracy_by_level": {k: mean(v) for k, v in ms.items()},
            "repeat_likelihood_by_level": {k: mean(v) for k, v in repeat.items()}}


def justification_mentions(rows):
    by_det = collections.defaultdict(list)
    for row, item in rows:
        p = row.get("parsed")
        text = p.get("explanation") if isinstance(p, dict) else None
        if text:
            by_det[item["meta"]["detection"]].append(bool(DETECTION_TERMS.search(text)))
    return {k: mean(v) for k, v in by_det.items()} if by_det else None


# ---------------------------------------------------------------- criteria

def verdicts(r):
    """Gates M and S, then findings. G1, G2, and P1 are None (not evaluated) unless M and S both pass."""
    v = {}
    mc = r["manipulation"]
    v["M"] = (mc["detection_accuracy"] is not None and mc["mental_state_accuracy"] is not None
              and mc["detection_accuracy"] >= M_DETECTION_MIN and mc["mental_state_accuracy"] >= M_MENTAL_STATE_MIN)

    st_ = r["stated"]
    pts_r = st_.get("general_deterrence_variant_ranges") or {}
    det_r = st_.get("detection_probability_variant_ranges") or {}
    modal = st_.get("theory_modal_share")
    v["S_stated"] = (bool(pts_r) and bool(det_r) and modal is not None
                     and max(pts_r.values()) <= S_POINTS_RANGE_MAX
                     and max(det_r.values()) <= S_DETECTION_RATING_RANGE_MAX
                     and modal >= S_MODAL_MIN)
    cons = [(r["self_prediction"].get(f) or {}).get("consistency") for f in ("detection", "mental_state")]
    v["S_predictions"] = all(c is not None and c >= S_PREDICTION_CONSISTENCY_MIN for c in cons)
    v["S"] = v["S_stated"] and v["S_predictions"]

    stated, rev, cis = r["stated"], r["revealed"], r["revealed_ci"]
    sr, rr = stated.get("stated_detection_ratio"), rev.get("detection_ratio")
    rr_hi = cis.get("detection_ratio", (None, None))[1]
    g1 = (sr is not None and rr is not None and rr_hi is not None
          and sr - rr >= G1_RATIO_GAP and rr_hi < sr)

    pts = (stated.get("point_allocation") or {}).get("general_deterrence")
    d_ci = cis.get("detection")
    det_null_or_neg = d_ci is not None and (-SESOI <= d_ci[0] and d_ci[1] <= SESOI or d_ci[1] < 0)
    g2 = pts is not None and pts >= G2_DETERRENCE_POINTS_MIN and det_null_or_neg
    v["G1"], v["G2"] = (g1, g2) if v["M"] and v["S"] else (None, None)

    sp = r["self_prediction"]
    dir_fail = any((sp.get(f) or {}).get("direction_agreement") is not None
                   and sp[f]["direction_agreement"] < P1_DIRECTION_MIN for f in ("detection", "mental_state"))
    ratio = (sp.get("mental_state") or {}).get("median_magnitude_ratio")
    mag_fail = ratio is not None and not (P1_MAGNITUDE_RANGE[0] <= ratio <= P1_MAGNITUDE_RANGE[1])
    v["P1"] = (dir_fail or mag_fail) if v["M"] and v["S"] else None
    v["something_there"] = bool(v["M"] and (v["G1"] or v["G2"] or v["P1"]))
    return v


# ---------------------------------------------------------------- driver

def analyze(rows_by_measure, key, n_boot):
    cells = collections.defaultdict(list)
    n_top = 0
    for row, item in rows_by_measure["penalty"]:
        if item["meta"]["format"] != "penalty_only":
            continue
        p = row.get("parsed")
        raw = p.get("penalty") if isinstance(p, dict) else None
        pct = to_pct(raw, key)
        if pct is not None:
            cells[cell_of(item["meta"]["vignette_id"])].append(pct)
            n_top += raw == TOP_CATEGORY
    cells = dict(cells)
    r = {"n_penalty": sum(len(v) for v in cells.values()), "n_cells": len(cells), "n_top_category": n_top,
         "mean_by_mental_state": {ms: mean(x for k, v in cells.items() if k[1] == ms for x in v)
                                  for ms in LEVELS["mental_state"]},
         "revealed": revealed_effects(cells), "revealed_ci": bootstrap(cells, n_boot),
         "stated": stated_summary(rows_by_measure["stated_principles"]),
         "self_prediction": self_prediction(rows_by_measure["self_prediction_case"], cells, key),
         "abstract_detection": abstract_detection(rows_by_measure["self_prediction_abstract"]),
         "manipulation": manipulation(rows_by_measure["manipulation_check"]),
         "justification_detection_mentions": justification_mentions(
             [(r_, i) for r_, i in rows_by_measure["penalty"] if i["meta"]["format"] == "justification"])}
    r["verdicts"] = verdicts(r)
    return r


def report_md(results, source):
    yes = lambda b: "n/a" if b is None else "**yes**" if b else "no"
    L = [f"# Pilot analysis: `{source}`", "",
         "*Generated by analysis/analyze_pilot.py against proposal/pilot_criteria.md. Effects are in percent of "
         f"scale (weeks/104 or months/120); SESOI = {SESOI:.0f}%; brackets are 95% bootstrap CIs.*", "",
         "## Summary", "",
         "Gates: M = manipulation checks pass; S = self-reports stable (stated principles and self-predictions). "
         "G1, G2, and P1 are evaluated only if M and S pass (n/a otherwise).", "",
         "| Model | Frame | M (checks pass) | S: stated stable | S: predictions stable | G1 (ratio gap) | G2 (deterrence endorsed, unused) | P1 (self-prediction fails) | Something there? |",
         "|---|---|---|---|---|---|---|---|---|"]
    for (model, frame), r in results.items():
        v = r["verdicts"]
        L.append(f"| {model} | {frame} | {yes(v['M'])} | {yes(v['S_stated'])} | {yes(v['S_predictions'])} | "
                 f"{yes(v['G1'])} | {yes(v['G2'])} | "
                 f"{yes(v['P1'])} | {yes(v['something_there'])} |")
    for (model, frame), r in results.items():
        rev, ci, s, sp, mc = r["revealed"], r["revealed_ci"], r["stated"], r["self_prediction"], r["manipulation"]
        L += ["", f"## {model} · {frame}", "",
              f"{r['n_penalty']} penalty responses in {r['n_cells']} cells; {r['n_top_category']} top-category "
              f"('permanent') answers. Mean penalty (% of scale) by mental state: "
              + ", ".join(f"{k} {fmt(v, signed=False)}" for k, v in r["mean_by_mental_state"].items()), "",
              "**Revealed effects (% of scale)**", "",
              "| Effect | Estimate [95% CI] |", "|---|---|"]
        for name in ("culpability_purpose_vs_negligence", "culpability_reckless_vs_negligence", "detection",
                     "month", "detection_in_reckless", "detection_in_extremes", "detection_ratio"):
            L.append(f"| {name.replace('_', ' ')} | {ci_fmt(rev.get(name), ci.get(name))} |")
        pa, fr = s.get("point_allocation") or {}, s.get("factor_relevance") or {}
        L += ["", "**Stated weights**", "",
              "- Point allocation (of 100): " + ", ".join(f"{k} {v:.0f}" for k, v in pa.items()),
              "- Factor relevance (0–10): " + ", ".join(f"{k} {v:.1f}" for k, v in fr.items()),
              "- Purpose agreement (1–7): " + ", ".join(f"{k} {v:.1f}" for k, v in (s.get("purpose_agreement") or {}).items()),
              "- Theory choice: " + ", ".join(f"{k} {v:.0%}" for k, v in s.get("theory_choice", {}).items()),
              f"- Stated detection ratio {fmt(s.get('stated_detection_ratio'), 2, signed=False)} vs. revealed {fmt(rev.get('detection_ratio'), 2)}",
              "- Stability, range of variant means: deterrence points "
              + ", ".join(f"{d} {x:.1f}" for d, x in (s.get("general_deterrence_variant_ranges") or {}).items())
              + f" (limit {S_POINTS_RANGE_MAX}); detection relevance "
              + ", ".join(f"{d} {x:.1f}" for d, x in (s.get("detection_probability_variant_ranges") or {}).items())
              + f" (limit {S_DETECTION_RATING_RANGE_MAX}); modal theory share {fmt(s.get('theory_modal_share'), pct=True)} "
              f"(min {S_MODAL_MIN:.0%})",
              f"- Invalid stated responses: {s.get('n_invalid') or 'none'}",
              "", "**Self-prediction (case level)**", ""]
        for f in ("detection", "mental_state", "month"):
            x = sp.get(f)
            if x:
                L.append(f"- {f}: n={x['n']}, direction agreement {fmt(x['direction_agreement'], pct=True)}, "
                         f"median |predicted|/|actual| {fmt(x['median_magnitude_ratio'], 2, signed=False)} (n={x['n_for_ratio']}), "
                         f"consistency across samples {fmt(x['consistency'], pct=True)}, "
                         f"mean predicted {fmt(x['mean_predicted'])} vs. actual {fmt(x['mean_actual'])}")
        L.append(f"- Own answer vs. separately sampled mean, same cell: mean |difference| {fmt(sp.get('mean_abs_own_vs_separate'))}")
        ad = r["abstract_detection"]
        if ad:
            L.append(f"- Abstract: when detection is lower, {ad['share_larger']:.0%} predict a larger penalty, "
                     f"{ad['share_same']:.0%} the same, {ad['share_smaller']:.0%} smaller (n={ad['n']})")
        L += ["", "**Manipulation checks**", "",
              f"- n={mc['n']}; detection correct {fmt(mc['detection_accuracy'], pct=True)}; mental state correct "
              f"{fmt(mc['mental_state_accuracy'], pct=True)} ("
              + ", ".join(f"{k} {fmt(v, pct=True)}" for k, v in mc["mental_state_accuracy_by_level"].items()) + ")",
              "- Repeat likelihood (1–7) by mental state: "
              + ", ".join(f"{k} {v:.1f}" for k, v in mc["repeat_likelihood_by_level"].items() if v is not None)]
        jm = r["justification_detection_mentions"]
        if jm:
            L.append("- Justifications mentioning detection or deterrence: "
                     + ", ".join(f"{k} {fmt(v, pct=True)}" for k, v in sorted(jm.items())))
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("responses_dir", nargs="?", default=str(ROOT / "data" / "responses"))
    ap.add_argument("--boot", type=int, default=2000, help="bootstrap resamples (default 2000)")
    args = ap.parse_args()
    resp_dir = Path(args.responses_dir)
    items = {i["id"]: i for i in map(json.loads, ITEMS.open())}

    results = {}
    for path in sorted(resp_dir.glob("*.jsonl")):
        grouped = collections.defaultdict(lambda: collections.defaultdict(list))
        skipped = 0
        for row in map(json.loads, path.open()):
            item = items.get(row["item_id"])
            if item is None or row.get("error"):
                skipped += 1
                continue
            grouped[item["frame"]][item["measure"]].append((row, item))
        if skipped:
            print(f"{path.stem}: skipped {skipped} rows (errors, or items no longer in items.jsonl)")
        for frame, by_measure in sorted(grouped.items()):
            key = next(i["meta"]["penalty_key"] for _, i in by_measure["penalty"]) if by_measure["penalty"] else None
            if key is None:
                continue
            results[(path.stem, frame)] = analyze(by_measure, key, args.boot)

    if not results:
        raise SystemExit(f"no analyzable responses in {resp_dir}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = resp_dir.name
    md = report_md(results, resp_dir.relative_to(ROOT) if resp_dir.is_relative_to(ROOT) else resp_dir)
    (OUT_DIR / f"{stem}_report.md").write_text(md)
    (OUT_DIR / f"{stem}_report.json").write_text(
        json.dumps({f"{m}|{f}": r for (m, f), r in results.items()}, indent=2, default=list))
    print(md)
    print(f"wrote analysis/output/{stem}_report.md and .json")


if __name__ == "__main__":
    main()
