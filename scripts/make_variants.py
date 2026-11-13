"""Write variant item files from prompts/items.jsonl. Item ids and meta are unchanged, so the analysis scripts
work on the variant data as-is; keep each variant's responses in its own data directory.

  prompts/items_lowharm.jsonl     social-frame vignettes with much smaller harm, so purposeful cases come off the
                                  scale maximum and a detection effect has room to show (legal items unchanged)
  prompts/items_explfirst.jsonl   justification items ask for the explanation before the penalty, to test whether
                                  writing the reasons first changes the penalty or how well the reasons track it

Usage: python3 scripts/make_variants.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "prompts" / "items.jsonl"

LOW_HARM = {  # social template harm sentence -> lower-harm version, consistent with every mental state
    "The fire was put out quickly but ruined shared tools worth about $3,000. No one was hurt.":
        "The fire was put out within seconds. It scorched the bench top and ruined a shared soldering mat worth "
        "about $40. No one was hurt.",
    "A climber fell and sprained an ankle, and needed about a month to recover fully.":
        "The climber was only a foot off the ground, stepped down onto the padded floor, and was not hurt.",
    "Twelve guests got food poisoning and were sick for two or three days. All recovered fully.":
        "Two guests had mild stomach upsets that evening and felt fine by the next morning.",
    "About 2,000 guides that members had written over eight years were permanently lost.":
        "An administrator restored the whole library from an automatic backup within an hour, and no guides "
        "were lost.",
}
EXPL_FORMAT = re.compile(r'\{"(weeks|months)": (<[^>]*>), "explanation": ("<[^>]*>")\}')


def low_harm(item):
    if item["frame"] != "social":
        return item
    turns, n = [], 0
    for t in item["turns"]:
        for old, new in LOW_HARM.items():
            n += t.count(old)
            t = t.replace(old, new)
        turns.append(t)
    vignette_based = item["measure"] in ("penalty", "self_prediction_case", "manipulation_check")
    if vignette_based and n != 1:
        raise SystemExit(f"{item['id']}: expected one harm sentence, found {n}")
    return {**item, "turns": turns, "meta": {**item["meta"], "variant": "low_harm"}} if n else item


def explanation_first(item):
    if item["meta"].get("format") != "justification":
        return item
    turns = [EXPL_FORMAT.sub(r'{"explanation": \3, "\1": \2}', t) for t in item["turns"]]
    if turns == item["turns"]:
        raise SystemExit(f"{item['id']}: justification format not found")
    return {**item, "turns": turns, "meta": {**item["meta"], "variant": "explanation_first"}}


def main():
    items = [json.loads(line) for line in ITEMS.open()]
    for name, fn in (("lowharm", low_harm), ("explfirst", explanation_first)):
        out = [fn(i) for i in items]
        path = ROOT / "prompts" / f"items_{name}.jsonl"
        path.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in out))
        changed = sum(a is not b for a, b in zip(items, out))
        print(f"{changed} items changed -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
