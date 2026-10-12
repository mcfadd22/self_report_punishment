"""Build pilot stimuli and prompt items from the JSON sources.

Reads stimuli/templates.json and prompts/pilot_prompts.json and writes:
  stimuli/vignettes.jsonl  one row per vignette cell (template x mental state x detection x month)
  prompts/items.jsonl      one row per prompt to send to a model

Each item has:
  id               unique, stable identifier
  measure          sentencing | manipulation_check | stated_principles | self_prediction_case | self_prediction_abstract
  system           key into pilot_prompts.json "system_prompts"
  turns            user messages to send in order, in one conversation (the model replies after each)
  response_format  number | json | text
  meta             design variables for analysis

Usage: python3 scripts/build_items.py
"""

import itertools
import json
import re
import string
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "stimuli" / "templates.json"
PROMPTS = ROOT / "prompts" / "pilot_prompts.json"
VIGNETTES_OUT = ROOT / "stimuli" / "vignettes.jsonl"
ITEMS_OUT = ROOT / "prompts" / "items.jsonl"

DEFAULT_SYSTEM = "study"
BASE_MONTH = "March"
LIST_ORDERS = ["forward", "reversed"]
UNFILLED = re.compile(r"\{[a-z_]+\}")


def build_vignettes(t):
    vignettes = []
    f = t["factors"]
    for (tid, tpl), ms, det, month in itertools.product(
        t["templates"].items(), f["mental_state"], f["detection"], f["month"]
    ):
        parts = {
            "background": tpl["background"].format(month=month),
            "mental_state": tpl["mental_state"][ms],
            "harm": tpl["harm"],
            "caught": tpl["caught"],
            "detection": tpl["detection"].format(detection=t["detection_text"][det]),
            "record": t["shared"]["record"],
        }
        vignettes.append({
            "id": f"{tid}|{ms}|{det}|{month}",
            "template": tid,
            "mental_state": ms,
            "detection": det,
            "month": month,
            "text": " ".join(parts[k] for k in t["assembly_order"]),
        })
    return vignettes


def lettered_list(options, order):
    """Present options under neutral letter keys so theory names don't leak into the response keys."""
    keys = list(options)
    if order == "reversed":
        keys.reverse()
    letters = string.ascii_uppercase[: len(keys)]
    text = "\n".join(f"{letter}. {options[k]}" for letter, k in zip(letters, keys))
    return text, dict(zip(letters, keys))


def item(id_, measure, turns, response_format, meta, system=DEFAULT_SYSTEM):
    return {"id": id_, "measure": measure, "system": system, "turns": turns,
            "response_format": response_format, "meta": meta}


def sentencing_items(p, vignettes):
    items = []
    for v in vignettes:
        meta = {k: v[k] for k in ("template", "mental_state", "detection", "month")}
        meta["vignette_id"] = v["id"]
        for fmt, prompt in p["sentencing"].items():
            items.append(item(f"sent|{fmt}|{v['id']}", "sentencing",
                              [f"{v['text']}\n\n{prompt}"],
                              "number" if fmt == "number_only" else "text",
                              {**meta, "format": fmt}))
        items.append(item(f"check|{v['id']}", "manipulation_check",
                          [f"{v['text']}\n\n{p['sentencing']['number_only']}", p["manipulation_check"]],
                          "json", meta))
    return items


def stated_items(p):
    sources = {
        "point_allocation": ("purposes", "purpose_list", "json"),
        "purpose_agreement": ("purposes", "purpose_list", "json"),
        "factor_relevance": ("factors", "factor_list", "json"),
        "theory_choice": ("theory_options", "theory_list", "json"),
        "open_ended": (None, None, "text"),
    }
    items = []
    for fmt, stems in p["stated_principles"].items():
        option_key, slot, rfmt = sources[fmt]
        orders = LIST_ORDERS if option_key else [None]
        for (i, stem), (framing, ftext), order in itertools.product(
            enumerate(stems), p["framings"].items(), orders
        ):
            fill = {"framing": ftext}
            meta = {"format": fmt, "paraphrase": i, "framing": framing}
            if option_key:
                text, letter_map = lettered_list(p[option_key], order)
                fill.update({slot: text, "first_key": "A"})
                meta.update({"order": order, "letter_map": letter_map})
            suffix = f"|{order}" if order else ""
            items.append(item(f"stated|{fmt}|p{i}|{framing}{suffix}", "stated_principles",
                              [stem.format(**fill)], rfmt, meta))
    return items


def case_prediction_items(t, p, vignettes):
    """Model gives a sentence and predicts its sentence under one changed factor, in one response.
    Compare the predicted change with the actual change between separately sampled sentencing cells."""
    by_id = {v["id"]: v for v in vignettes}
    sp = p["self_prediction"]
    f = t["factors"]
    other = lambda levels, x: [y for y in levels if y != x]
    items = []

    def add(factor, base, to_level, change):
        v = by_id[f"{base['template']}|{base['mental_state']}|{base['detection']}|{base['month']}"]
        counterfactual = {**base, factor: to_level}
        target_id = "|".join(counterfactual[k] for k in ("template", "mental_state", "detection", "month"))
        items.append(item(f"selfpred_case|{factor}|{v['id']}->{to_level}", "self_prediction_case",
                          [sp["case_level"].format(vignette=v["text"], change=change)], "json",
                          {"factor": factor, "from_level": base[factor], "to_level": to_level,
                           "base_vignette_id": v["id"], "counterfactual_vignette_id": target_id,
                           "template": base["template"]}))

    for tid, tpl in t["templates"].items():
        for ms, det in itertools.product(f["mental_state"], f["detection"]):
            base = {"template": tid, "mental_state": ms, "detection": det, "month": BASE_MONTH}
            for to_det in other(f["detection"], det):
                add("detection", base, to_det,
                    sp["case_changes"]["detection"].format(detection=t["detection_text"][to_det]))
            for to_ms in other(f["mental_state"], ms):
                add("mental_state", base, to_ms,
                    sp["case_changes"]["mental_state"].format(
                        counterfactual_mental_state=tpl["counterfactual_mental_state"][to_ms]))
            if det == "1_in_2":
                for to_month in other(f["month"], BASE_MONTH):
                    add("month", base, to_month, sp["case_changes"]["month"].format(month=to_month))
    return items


def abstract_prediction_items(p):
    sp = p["self_prediction"]
    items = []
    for factor, stem in sp["abstract"].items():
        levels = sp["abstract_levels"][factor]
        for (a, b), (framing, ftext) in itertools.product(
            itertools.permutations(levels, 2), p["framings"].items()
        ):
            items.append(item(f"selfpred_abstract|{factor}|{a}->{b}|{framing}", "self_prediction_abstract",
                              [stem.format(framing=ftext, from_level=levels[a], to_level=levels[b])], "json",
                              {"factor": factor, "from_level": a, "to_level": b, "framing": framing}))
    return items


def check(items):
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)), "duplicate item ids"
    for i in items:
        for turn in i["turns"]:
            leftover = UNFILLED.findall(turn)
            assert not leftover, f"{i['id']} has unfilled slots {leftover}"


def write_jsonl(path, rows):
    with path.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    t = json.loads(TEMPLATES.read_text())
    p = json.loads(PROMPTS.read_text())
    vignettes = build_vignettes(t)
    items = (sentencing_items(p, vignettes) + stated_items(p)
             + case_prediction_items(t, p, vignettes) + abstract_prediction_items(p))
    check(items)
    write_jsonl(VIGNETTES_OUT, vignettes)
    write_jsonl(ITEMS_OUT, items)

    counts = {}
    for i in items:
        key = i["measure"] if i["measure"] != "stated_principles" else f"stated_principles/{i['meta']['format']}"
        counts[key] = counts.get(key, 0) + 1
    print(f"{len(vignettes)} vignettes -> {VIGNETTES_OUT.relative_to(ROOT)}")
    print(f"{len(items)} items -> {ITEMS_OUT.relative_to(ROOT)}")
    for k, n in sorted(counts.items()):
        print(f"  {k}: {n}")


if __name__ == "__main__":
    main()
