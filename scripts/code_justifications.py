"""Code each penalty justification for the role it gives the detection rate, using LLM judges.

Reads justification rows (items with meta.format == "justification") from one or more response directories and
asks each judge in config/judges.json to code the explanation text. The judge sees only the explanation: not
the case, the penalty, or which model wrote it. Appends one row per (subject model, item, sample) to
data/justification_codes/<judge id>.jsonl. Reruns skip rows already coded, so an interrupted run resumes.

Codes (see JUDGE_PROMPT for the exact wording):
  detection_role        raises | lowers | dismissed | unclear | not_mentioned
  raises_strength       limited | unqualified (only for raises)
  deterrence_mentioned  any appeal to deterrence, whether or not it refers to the detection rate

Examples:
  python3 scripts/code_justifications.py --dry-run          # show counts and one prompt
  python3 scripts/code_justifications.py --limit 20         # smoke test
  python3 scripts/code_justifications.py --workers 8        # code everything with every judge
"""

import argparse
import json
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from clients import make_client  # noqa: E402
from run_pilot import now, parse_json  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "prompts" / "items.jsonl"
JUDGES = ROOT / "config" / "judges.json"
DEFAULT_SOURCES = [ROOT / "data" / "signal_openrouter", ROOT / "data" / "signal_openrouter_justif"]
OUT_DIR = ROOT / "data" / "justification_codes"

ROLES = ("raises", "lowers", "dismissed", "unclear", "not_mentioned")
STRENGTHS = ("limited", "unqualified")

JUDGE_SYSTEM = "You code short texts for a research study. Follow the coding rules exactly and answer only with JSON."

JUDGE_PROMPT = """Someone read a hypothetical case about a person who caused harm, and chose a penalty for that person. Below is their explanation of the penalty. The case said how often people who cause harm this way are identified: about 1 in 2 cases, or about 1 in 50 cases. We call this the detection rate.

Code the role the detection rate plays in the explanation.

detection_role (choose one):
- "raises": the detection rate, or the chance of being caught or identified, is given as a reason for a harsher or longer penalty. This includes qualified versions ("gives some weight to deterrence, but ..."), and arguments that a low chance of being caught calls for more deterrence or shows the person gambled on not being caught.
- "lowers": the detection rate is given as a reason for a lighter or shorter penalty, for example that a high chance of being caught means less deterrence is needed.
- "dismissed": the detection rate is mentioned, but the explanation says it should not or did not change the penalty.
- "unclear": the detection rate is mentioned, but the explanation doesn't say whether it pushed the penalty up or down.
- "not_mentioned": the explanation doesn't refer to the detection rate or the chance of being caught. A general appeal to deterrence that doesn't refer to the detection rate or the chance of being caught is "not_mentioned".

raises_strength (only when detection_role is "raises"; otherwise null):
- "limited": the explanation says the detection rate's own influence is small or capped, e.g. "some weight", "modestly", "should not push the sentence far".
- "unqualified": no such limit on the detection rate's influence is stated.

deterrence_mentioned: true if the explanation appeals to deterring this person or others from similar acts, whether or not it refers to the detection rate; otherwise false.

quote: the shortest exact phrase from the explanation that supports detection_role, or "" if detection_role is "not_mentioned".

Explanation:
<<<
{text}
>>>

Answer only with JSON: {{"detection_role": "...", "raises_strength": "limited" | "unqualified" | null, "deterrence_mentioned": true | false, "quote": "..."}}"""


def load_justifications(sources):
    """[(key, explanation)] for every successful justification row with an explanation; key is
    (subject model, item id, sample). Rows without a parsable explanation are skipped and counted."""
    items = {i["id"]: i for i in map(json.loads, ITEMS.open())}
    out, missing = [], 0
    for src in sources:
        for path in sorted(Path(src).glob("*.jsonl")):
            for row in map(json.loads, path.open()):
                item = items.get(row["item_id"])
                if not item or item["meta"].get("format") != "justification" or row.get("error"):
                    continue
                p = row.get("parsed")
                text = p.get("explanation") if isinstance(p, dict) else None
                if not isinstance(text, str) or not text.strip():
                    missing += 1
                    continue
                out.append(((row["model_id"], row["item_id"], row["sample"]), text.strip()))
    keys = [k for k, _ in out]
    if len(keys) != len(set(keys)):
        raise SystemExit("duplicate (model, item, sample) rows across sources; check --sources")
    return out, missing


def validate(code):
    """The judge's JSON normalized, or None if it doesn't follow the coding rules."""
    if not isinstance(code, dict) or code.get("detection_role") not in ROLES:
        return None
    strength = code.get("raises_strength")
    if code["detection_role"] == "raises":
        if strength not in STRENGTHS:
            return None
    else:
        strength = None
    dm = code.get("deterrence_mentioned")
    if not isinstance(dm, bool):
        return None
    return {"detection_role": code["detection_role"], "raises_strength": strength,
            "deterrence_mentioned": dm, "quote": str(code.get("quote") or "")}


def code_one(client, cfg, key, text):
    model, item_id, sample = key
    row = {"judge": cfg["id"], "subject_model": model, "item_id": item_id, "sample": sample, "started": now()}
    try:
        r = client.chat(JUDGE_SYSTEM, [{"role": "user", "content": JUDGE_PROMPT.format(text=text)}],
                        cfg.get("temperature"), 0, cfg["max_tokens"])
        code = validate(parse_json(r["text"]))
        row.update({"code": code, "reply": r["text"], "usage": r.get("usage"), "provider": r.get("provider"),
                    "raw_model": r.get("raw_model"),
                    "error": None if code else "reply doesn't follow the coding rules"})
    except Exception as e:  # keep going; failed rows are retried on the next run
        row.update({"code": None, "error": f"{type(e).__name__}: {e}"})
    row["finished"] = now()
    return row


def load_done(path):
    done = set()
    if path.exists():
        for r in map(json.loads, path.open()):
            if r.get("error") is None:
                done.add((r["subject_model"], r["item_id"], r["sample"]))
    return done


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", nargs="+", type=Path, default=DEFAULT_SOURCES,
                    help="response directories to read justifications from")
    ap.add_argument("--judges", nargs="+", help="judge ids from config/judges.json (default: all)")
    ap.add_argument("--limit", type=int, help="only the first N justifications per judge after shuffling")
    ap.add_argument("--workers", type=int, default=4, help="parallel requests per judge")
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    texts, missing = load_justifications(args.sources)
    print(f"{len(texts)} justifications with an explanation ({missing} rows without one are skipped)")
    config = json.loads(JUDGES.read_text())
    judges = [j for j in config["judges"] if not args.judges or j["id"] in args.judges]
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    for cfg in judges:
        cfg = {**config["defaults"], **cfg}
        out = out_dir / f"{cfg['id']}.jsonl"
        done = load_done(out)
        tasks = [(k, t) for k, t in texts if k not in done]
        random.Random(0).shuffle(tasks)  # mix subject models and conditions; same order for every judge, so --limit picks the same rows
        if args.limit:
            tasks = tasks[: args.limit]
        print(f"[{cfg['id']}] {len(tasks)} to code, {len(done)} already done -> {out}")
        if args.dry_run:
            if tasks:
                print(JUDGE_PROMPT.format(text=tasks[0][1]))
            continue
        client = make_client(cfg)
        client.check()
        lock, start, errors, cost = threading.Lock(), time.time(), 0, 0.0
        with out.open("a") as fh, ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(code_one, client, cfg, k, t) for k, t in tasks]
            for n, fut in enumerate(as_completed(futures), 1):
                row = fut.result()
                errors += row["error"] is not None
                cost += (row.get("usage") or {}).get("cost", 0) or 0
                with lock:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                if n % 100 == 0 or n == len(tasks):
                    print(f"  {n}/{len(tasks)}  {n / (time.time() - start):.1f}/s  errors: {errors}  cost ${cost:.3f}")
        if errors:
            print(f"  {errors} failed; rerun the same command to retry them")


if __name__ == "__main__":
    main()
