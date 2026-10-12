"""Build pilot stimuli and prompt items from the JSON sources.

Reads stimuli/templates_<frame>.json and prompts/pilot_prompts.json and writes:
  stimuli/vignettes.jsonl         one row per vignette cell (frame x template x mental state x detection x month)
  stimuli/vignettes_preview.md    every vignette as readable text, for review
  prompts/items.jsonl             one row per prompt to send to a model

Frames (every measure is built for both, so frame is a design factor):
  social  rule violations in community organizations; suspensions and bans in weeks
  legal   criminal sentencing; months of incarceration
Frame-specific wording (stated principles, abstract self-prediction, manipulation check, role framing) is under
"frames" in pilot_prompts.json.

Each item has:
  id               unique, stable identifier
  frame            social | legal
  measure          penalty | manipulation_check | stated_principles | self_prediction_case | self_prediction_abstract
  system           key into pilot_prompts.json "system_prompts"
  turns            user messages to send in order, in one conversation (the model replies after each)
  response_format  json | text
  meta             design variables for analysis; penalty items carry "penalty_key", the JSON key holding the answer

Usage: python3 scripts/build_items.py
"""

import itertools
import json
import re
import string
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_FILES = {"social": ROOT / "stimuli" / "templates_social.json",
                  "legal": ROOT / "stimuli" / "templates_legal.json"}
PROMPTS = ROOT / "prompts" / "pilot_prompts.json"
VIGNETTES_OUT = ROOT / "stimuli" / "vignettes.jsonl"
PREVIEW_OUT = ROOT / "stimuli" / "vignettes_preview.md"
ITEMS_OUT = ROOT / "prompts" / "items.jsonl"

DEFAULT_SYSTEM = "study"
BASE_MONTH = "March"
LIST_ORDERS = ["forward", "reversed"]
CELL_KEYS = ("frame", "template", "mental_state", "detection", "month")
UNFILLED = re.compile(r"\{[a-z_]+\}")


def build_vignettes(frame, t):
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
            "id": f"{frame}|{tid}|{ms}|{det}|{month}",
            "frame": frame, "template": tid, "mental_state": ms, "detection": det, "month": month,
            "text": " ".join(parts[k] for k in t["assembly_order"]),
            "penalty_key": t["penalty"]["key"],
            "penalty_placeholder": t["penalty"]["placeholder"],
            "penalty_rule": tpl.get("penalty_rule", t["penalty"].get("rule")),
            "penalty_question": tpl.get("penalty_question", t["penalty"].get("question")),
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


def item(id_, frame, measure, turns, response_format, meta, system=DEFAULT_SYSTEM):
    return {"id": id_, "frame": frame, "measure": measure, "system": system, "turns": turns,
            "response_format": response_format, "meta": meta}


def cell_meta(v):
    return {**{k: v[k] for k in CELL_KEYS}, "vignette_id": v["id"], "penalty_key": v["penalty_key"]}


def penalty_prompt(p, fmt, v):
    return p["penalty"][fmt].format(rule=v["penalty_rule"], question=v["penalty_question"], key=v["penalty_key"],
                                    placeholder=v["penalty_placeholder"])


def penalty_items(p, vignettes):
    items = []
    for v in vignettes:
        for fmt in p["penalty"]:
            items.append(item(f"penalty|{fmt}|{v['id']}", v["frame"], "penalty",
                              [f"{v['text']}\n\n{penalty_prompt(p, fmt, v)}"], "json",
                              {**cell_meta(v), "format": fmt}))
        items.append(item(f"check|{v['id']}", v["frame"], "manipulation_check",
                          [f"{v['text']}\n\n{penalty_prompt(p, 'penalty_only', v)}",
                           p["frames"][v["frame"]]["manipulation_check"]],
                          "json", cell_meta(v)))
    return items


def stated_items(p, frame):
    sources = {
        "point_allocation": ("purposes", "purpose_list", "json"),
        "purpose_agreement": ("purposes", "purpose_list", "json"),
        "factor_relevance": ("factors", "factor_list", "json"),
        "theory_choice": ("theory_options", "theory_list", "json"),
        "open_ended": (None, None, "text"),
    }
    fp = p["frames"][frame]
    items = []
    for fmt, stems in fp["stated_principles"].items():
        option_key, slot, rfmt = sources[fmt]
        orders = LIST_ORDERS if option_key else [None]
        for (i, stem), (framing, ftext), order in itertools.product(
            enumerate(stems), fp["framings"].items(), orders
        ):
            fill = {"framing": ftext}
            meta = {"format": fmt, "paraphrase": i, "framing": framing}
            if option_key:
                text, letter_map = lettered_list(fp[option_key], order)
                fill.update({slot: text, "first_key": "A"})
                meta.update({"order": order, "letter_map": letter_map})
            suffix = f"|{order}" if order else ""
            items.append(item(f"stated|{frame}|{fmt}|p{i}|{framing}{suffix}", frame, "stated_principles",
                              [stem.format(**fill)], rfmt, meta))
    return items


def case_prediction_items(frame, t, p, vignettes):
    """Model gives a penalty and predicts its penalty under one changed factor, in one response.
    Compare the predicted change with the actual change between separately sampled penalty cells."""
    by_id = {v["id"]: v for v in vignettes}
    sp = p["self_prediction_case"]
    f = t["factors"]
    other = lambda levels, x: [y for y in levels if y != x]
    items = []

    def add(factor, base, to_level, change):
        v = by_id["|".join(base[k] for k in CELL_KEYS)]
        target_id = "|".join({**base, factor: to_level}[k] for k in CELL_KEYS)
        prompt = sp["case_level"].format(vignette=v["text"], rule=v["penalty_rule"], key=v["penalty_key"],
                                         placeholder=v["penalty_placeholder"], change=change)
        items.append(item(f"selfpred_case|{factor}|{v['id']}->{to_level}", v["frame"], "self_prediction_case",
                          [prompt], "json",
                          {"factor": factor, "from_level": base[factor], "to_level": to_level,
                           "base_vignette_id": v["id"], "counterfactual_vignette_id": target_id,
                           "template": base["template"], "penalty_key": v["penalty_key"]}))

    for tid, tpl in t["templates"].items():
        for ms, det in itertools.product(f["mental_state"], f["detection"]):
            base = {"frame": frame, "template": tid, "mental_state": ms, "detection": det, "month": BASE_MONTH}
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


def abstract_prediction_items(p, frame):
    fp = p["frames"][frame]
    items = []
    for factor, stem in fp["self_prediction_abstract"].items():
        levels = fp["abstract_levels"][factor]
        for (a, b), (framing, ftext) in itertools.product(
            itertools.permutations(levels, 2), fp["framings"].items()
        ):
            items.append(item(f"selfpred_abstract|{frame}|{factor}|{a}->{b}|{framing}", frame, "self_prediction_abstract",
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


def write_preview(vignettes, p):
    lines = ["# Vignette preview", "", "*Generated by scripts/build_items.py. Edit the templates JSON, not this file.*", ""]
    for v in vignettes:
        if v["month"] != BASE_MONTH:
            continue  # month only changes one word
        lines += [f"## {v['frame']} · {v['template']} · {v['mental_state']} · {v['detection']}", "",
                  v["text"], "", f"> {penalty_prompt(p, 'penalty_only', v)}", ""]
    PREVIEW_OUT.write_text("\n".join(lines))


def main():
    p = json.loads(PROMPTS.read_text())
    templates = {frame: json.loads(path.read_text()) for frame, path in TEMPLATE_FILES.items()}
    vignettes = {frame: build_vignettes(frame, t) for frame, t in templates.items()}

    items = []
    for frame, t in templates.items():
        items += (penalty_items(p, vignettes[frame]) + stated_items(p, frame)
                  + case_prediction_items(frame, t, p, vignettes[frame]) + abstract_prediction_items(p, frame))
    check(items)
    all_vignettes = [v for vs in vignettes.values() for v in vs]
    write_jsonl(VIGNETTES_OUT, all_vignettes)
    write_jsonl(ITEMS_OUT, items)
    write_preview(all_vignettes, p)

    counts = {}
    for i in items:
        key = f"{i['frame']}/{i['measure']}"
        if i["measure"] == "stated_principles":
            key += f"/{i['meta']['format']}"
        counts[key] = counts.get(key, 0) + 1
    print(f"{len(all_vignettes)} vignettes -> {VIGNETTES_OUT.relative_to(ROOT)} (preview: {PREVIEW_OUT.relative_to(ROOT)})")
    print(f"{len(items)} items -> {ITEMS_OUT.relative_to(ROOT)}")
    for k, n in sorted(counts.items()):
        print(f"  {k}: {n}")


if __name__ == "__main__":
    main()
