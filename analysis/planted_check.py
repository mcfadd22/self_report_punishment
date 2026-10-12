"""Write synthetic responses with known structure to check that the criteria fire correctly.
gap_model:        culpability drives penalties, detection doesn't; says detection matters; predicts detection changes -> M, G1, G2, P1
consistent_model: detection drives penalties as much as stated; predicts its changes accurately -> M and S only
unstable_model:   stated principles shift across variants -> fails S (stated); findings n/a
noisy_predictor:  self-predictions inconsistent across samples -> fails S (predictions); findings n/a

Usage: python3 -I analysis/planted_check.py . data/planted && python3 -I analysis/analyze_pilot.py data/planted
The synthetic manipulation-check answers use the check option wording; update them when that wording changes.
"""
import json, random, sys
from pathlib import Path
ROOT = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
items = [json.loads(l) for l in (ROOT / "prompts/items.jsonl").open()]
MAX = {"weeks": 104, "months": 120}
MS_EFFECT = {"purpose": 50, "recklessness": 25, "negligence": 10}

def penalty_pct(m, det_effect, rng):
    return MS_EFFECT[m["mental_state"]] + (det_effect if m["detection"] == "1_in_50" else 0) + rng.gauss(0, 3)

def cell_pct(vid, det_effect):
    _, t, ms, det, mo = vid.split("|")
    return MS_EFFECT[ms] + (det_effect if det == "1_in_50" else 0)

def make(name, det_effect, stated, predicted_det_change, unstable=False):
    rng = random.Random(name)
    rows = []
    for it in items:
        m = it["meta"]; key = m.get("penalty_key")
        for s in range(3):
            if it["measure"] in ("penalty", "manipulation_check"):
                v = max(0, penalty_pct(m, det_effect, rng)) * MAX[key] / 100
                parsed = {"penalty": v, key: v}
                if it["measure"] == "manipulation_check":
                    parsed = {"penalty": v, "check": {"detection_fraction": "1 in 50" if m["detection"] == "1_in_50" else "1 in 2",
                              "mental_state": {"purpose": "intended the harm", "recklessness": "recognized the risk and went ahead",
                                               "negligence": "did not consider the risk"}[m["mental_state"]], "repeat_likelihood": 2}}
                if m.get("format") == "justification":
                    parsed["explanation"] = "Intent mattered most."
            elif it["measure"] == "stated_principles":
                inv = {v: k for k, v in m.get("letter_map", {}).items()}
                f = m["format"]
                shift = (m["paraphrase"] - 1) * 20 if unstable else 0   # paraphrases 0,1,2 -> -20, 0, +20
                pts = {**stated["points"], "general_deterrence": stated["points"]["general_deterrence"] + shift}
                fac = {**stated["factors"], "detection_probability": max(0, stated["factors"]["detection_probability"] + shift / 10)}
                if f == "point_allocation": parsed = {inv[k]: v for k, v in pts.items()}
                elif f == "factor_relevance": parsed = {inv[k]: v for k, v in fac.items()}
                elif f == "purpose_agreement": parsed = {inv[k]: 4 for k in inv}
                elif f == "theory_choice": parsed = {"choice": inv["hybrid"]}
                else: parsed = None
            elif it["measure"] == "self_prediction_case":
                own = cell_pct(m["base_vignette_id"], det_effect)
                actual = cell_pct(m["counterfactual_vignette_id"], det_effect) - own
                pred = predicted_det_change(m) if m["factor"] == "detection" else actual
                if name == "noisy_predictor":
                    pred = rng.choice([-20, 0, 20])
                k = MAX[key] / 100
                parsed = {"penalty": own * k, "counterfactual_penalty": (own + pred) * k}
            else:
                parsed = {"direction": "larger", "percent_change": 20}
            rows.append({"item_id": it["id"], "sample": s, "parsed": parsed, "error": None, "replies": [""]})
    (out / f"{name}.jsonl").write_text("\n".join(json.dumps(r) for r in rows))

points = {"retribution": 30, "general_deterrence": 30, "incapacitation": 15, "rehabilitation": 15, "expressive": 10}
make("gap_model", det_effect=0,
     stated={"points": points, "factors": {"mental_state": 9, "detection_probability": 7, "recidivism_risk": 5, "harm": 8, "month": 0}},
     predicted_det_change=lambda m: 15 if m["to_level"] == "1_in_50" else -15)
# consistent: detection effect 20 vs culpability 40 -> revealed ratio 0.5; stated 4.5/9 = 0.5
make("consistent_model", det_effect=20,
     stated={"points": points, "factors": {"mental_state": 9, "detection_probability": 4.5, "recidivism_risk": 5, "harm": 8, "month": 0}},
     predicted_det_change=lambda m: 20 if m["to_level"] == "1_in_50" else -20)
make("unstable_model", det_effect=0,
     stated={"points": points, "factors": {"mental_state": 9, "detection_probability": 7, "recidivism_risk": 5, "harm": 8, "month": 0}},
     predicted_det_change=lambda m: 15 if m["to_level"] == "1_in_50" else -15, unstable=True)
make("noisy_predictor", det_effect=20,
     stated={"points": points, "factors": {"mental_state": 9, "detection_probability": 4.5, "recidivism_risk": 5, "harm": 8, "month": 0}},
     predicted_det_change=lambda m: 0)
