"""Summarize refusals and unparseable sentences in pilot responses.

For every item that asks for a sentence (sentencing, manipulation checks, case-level self-prediction), classifies
each response as answered (a sentence from 0 to 120 was parsed), refused, or other (no usable sentence, not an
obvious refusal), and breaks refusal rates down by model, item type, and mental state.

Usage: python3 scripts/refusal_report.py [responses_dir]   (default data/responses)
"""

import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "prompts" / "items.jsonl"
REFUSAL = re.compile(r"\b(cannot|can't|can not|unable to|won't|not able to|must decline|not comfortable)\b", re.I)
MENTAL_STATES = ["purpose", "recklessness", "negligence"]


def sentence_of(row):
    p = row.get("parsed")
    if isinstance(p, dict):
        p = p.get("sentence")
    try:
        p = float(p)
    except (TypeError, ValueError):
        return None
    return p if 0 <= p <= 120 else None


def classify(row):
    if row.get("error"):
        return "error"
    if sentence_of(row) is not None:
        return "answered"
    first = (row.get("replies") or [""])[0]
    return "refused" if REFUSAL.search(first) else "other"


def item_type(item):
    if item["measure"] == "sentencing":
        return f"sentencing/{item['meta']['format']}"
    return item["measure"]


def main():
    resp_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "responses"
    items = {json.loads(l)["id"]: json.loads(l) for l in ITEMS.open()}
    wanted = {"sentencing", "manipulation_check", "self_prediction_case"}
    for path in sorted(resp_dir.glob("*.jsonl")):
        rows = [r for r in map(json.loads, path.open()) if items.get(r["item_id"], {}).get("measure") in wanted]
        if not rows:
            continue
        print(f"\n== {path.stem}: {len(rows)} sentence responses")
        by_type = collections.defaultdict(collections.Counter)
        by_ms = collections.defaultdict(collections.Counter)
        for r in rows:
            item = items[r["item_id"]]
            c = classify(r)
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
        others = [r for r in rows if classify(r) == "other"][:3]
        for r in others:
            print(f"  other example ({r['item_id']}): {r['replies'][0][:160]!r}")


if __name__ == "__main__":
    main()
