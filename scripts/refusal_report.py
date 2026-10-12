"""Summarize refusals and unparseable penalties in pilot responses.

For every item that asks for a penalty (penalty items, manipulation checks, case-level self-prediction), classifies
each response as answered (a penalty within the allowed range was parsed), refused, or other (no usable penalty,
not an obvious refusal), and breaks refusal rates down by model, frame and item type, and mental state.

Usage: python3 scripts/refusal_report.py [responses_dir]   (default data/responses)
"""

import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "prompts" / "items.jsonl"
REFUSAL = re.compile(r"\b(cannot|can't|can not|unable to|won't|not able to|must decline|not comfortable|"
                     r"I am (?:a|an AI) (?:language )?model|as an AI)\b", re.I)
MAX_PENALTY = {"weeks": 104, "months": 120}
TOP_CATEGORY = "permanent"
MENTAL_STATES = ["purpose", "recklessness", "negligence"]


def penalty_of(row, item):
    p = row.get("parsed")
    p = p.get("penalty") if isinstance(p, dict) else None
    if p is None or p == TOP_CATEGORY:
        return p
    return p if 0 <= p <= MAX_PENALTY[item["meta"]["penalty_key"]] else None


def classify(row, item):
    if row.get("error"):
        return "error"
    if penalty_of(row, item) is not None:
        return "answered"
    first = (row.get("replies") or [""])[0]
    return "refused" if REFUSAL.search(first) else "other"


def item_type(item):
    if item["measure"] == "penalty":
        return f"{item['frame']}/penalty/{item['meta']['format']}"
    return f"{item['frame']}/{item['measure']}"


def main():
    resp_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "responses"
    items = {json.loads(l)["id"]: json.loads(l) for l in ITEMS.open()}
    wanted = {"penalty", "manipulation_check", "self_prediction_case"}
    for path in sorted(resp_dir.glob("*.jsonl")):
        rows = [r for r in map(json.loads, path.open()) if items.get(r["item_id"], {}).get("measure") in wanted]
        if not rows:
            continue
        print(f"\n== {path.stem}: {len(rows)} penalty responses")
        by_type = collections.defaultdict(collections.Counter)
        by_ms = collections.defaultdict(collections.Counter)
        for r in rows:
            item = items[r["item_id"]]
            c = classify(r, item)
            by_type[item_type(item)][c] += 1
            ms = item["meta"].get("mental_state") or item["meta"].get("from_level")
            by_ms[ms][c] += 1
        for label, table, keys in [("by item type", by_type, sorted(by_type)), ("by mental state", by_ms, MENTAL_STATES)]:
            print(f"  {label}:")
            for k in keys:
                t = table[k]
                n = sum(t.values())
                if n:
                    print(f"    {k:28} refused {t['refused']:3}/{n:<3} ({t['refused'] / n:4.0%})   other {t['other']}   errors {t['error']}")
        others = [r for r in rows if classify(r, items[r["item_id"]]) == "other"][:3]
        for r in others:
            print(f"  other example ({r['item_id']}): {r['replies'][0][:160]!r}")


if __name__ == "__main__":
    main()
