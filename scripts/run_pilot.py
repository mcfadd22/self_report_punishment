"""Send pilot items to models and save the responses.

Reads prompts/items.jsonl (build it first with scripts/build_items.py) and config/models.json, and appends one
row per (item, sample) to data/responses/<model_id>.jsonl. Reruns skip rows that already succeeded, so an
interrupted run picks up where it left off.

Every item is a fresh conversation. Multi-turn items (manipulation checks) send each turn after the model's
previous reply. Item order is shuffled per model so time-of-run drift isn't confounded with condition.

Examples:
  python3 scripts/run_pilot.py --dry-run                          # show what would run
  python3 scripts/run_pilot.py --models mock --samples 2          # test the pipeline offline
  python3 scripts/run_pilot.py --models llama3.1-8b --limit 20    # quick smoke test on a real model
  python3 scripts/run_pilot.py --samples 10                       # full pilot on all enabled models
"""

import argparse
import json
import random
import re
import sys
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from clients import ClientError, make_client  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "prompts" / "items.jsonl"
PROMPTS = ROOT / "prompts" / "pilot_prompts.json"
MODELS = ROOT / "config" / "models.json"
OUT_DIR = ROOT / "data" / "responses"

NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def parse_number(text):
    m = NUMBER.search(text or "")
    return float(m.group()) if m else None


def parse_json(text):
    m = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return None


def parse(item, replies):
    """Best-effort parse of the model's answer. Raw text is always saved, so this can be redone later."""
    last = replies[-1]
    if item["measure"] == "manipulation_check":
        return {"sentence": parse_number(replies[0]), "check": parse_json(last)}
    if item["response_format"] == "number":
        return parse_number(last)
    if item["response_format"] == "json":
        return parse_json(last)
    if item["measure"] == "sentencing":  # justification format: number on the first line
        return {"sentence": parse_number(last.strip().split("\n", 1)[0]), "justification": last}
    return None


def call_seed(model_id, item_id, sample):
    return zlib.crc32(f"{model_id}|{item_id}|{sample}".encode()) & 0x7FFFFFFF


def run_one(client, model_cfg, item, sample, system_text, temperature, max_tokens):
    seed = call_seed(model_cfg["id"], item["id"], sample)
    messages, replies, thinking, stops = [], [], [], []
    row = {"item_id": item["id"], "sample": sample, "model_id": model_cfg["id"], "seed": seed,
           "temperature": temperature, "system": item["system"], "started": now()}
    try:
        for turn in item["turns"]:
            messages.append({"role": "user", "content": turn})
            r = client.chat(system_text, messages, temperature, seed, max_tokens)
            messages.append({"role": "assistant", "content": r["text"]})
            replies.append(r["text"])
            thinking.append(r["thinking"])
            stops.append(r["stop"])
            row["raw_model"] = r["raw_model"]
        row.update({"replies": replies, "thinking": thinking, "stop": stops,
                    "parsed": parse(item, replies), "error": None})
    except Exception as e:  # keep going; failed rows are retried on the next run
        row.update({"replies": replies, "error": f"{type(e).__name__}: {e}"})
    row["finished"] = now()
    return row


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_done(path):
    done = set()
    if path.exists():
        for line in path.open():
            r = json.loads(line)
            if r.get("error") is None:
                done.add((r["item_id"], r["sample"]))
    return done


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", help="model ids from config/models.json (default: all enabled)")
    ap.add_argument("--samples", type=int, default=10, help="samples per item (default 10)")
    ap.add_argument("--measures", nargs="+", help="only these measures, e.g. sentencing stated_principles")
    ap.add_argument("--limit", type=int, help="only the first N calls per model after shuffling (smoke tests)")
    ap.add_argument("--system", help="override every item's system prompt key, e.g. none")
    ap.add_argument("--workers", type=int, default=1, help="parallel requests per model (keep 1 for Ollama)")
    ap.add_argument("--order-seed", type=int, default=0, help="seed for shuffling item order")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and one example request, then exit")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if not ITEMS.exists():
        raise SystemExit("prompts/items.jsonl not found; run scripts/build_items.py first")
    items = [json.loads(line) for line in ITEMS.open()]
    if args.measures:
        items = [i for i in items if i["measure"] in args.measures]
    if args.system:
        items = [{**i, "system": args.system} for i in items]
    system_prompts = json.loads(PROMPTS.read_text())["system_prompts"]
    config = json.loads(MODELS.read_text())
    by_id = {m["id"]: m for m in config["models"]}
    unknown = [m for m in args.models or [] if m not in by_id]
    if unknown:
        raise SystemExit(f"unknown model id(s): {', '.join(unknown)}")
    models = [by_id[m] for m in args.models] if args.models else [m for m in config["models"] if m.get("enabled")]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for cfg in models:
        cfg = {**config["defaults"], **cfg}
        out = OUT_DIR / f"{cfg['id']}.jsonl"
        done = load_done(out)
        tasks = [(i, s) for i in items for s in range(args.samples) if (i["id"], s) not in done]
        random.Random(f"{args.order_seed}|{cfg['id']}").shuffle(tasks)
        if args.limit:
            tasks = tasks[: args.limit]
        n_calls = sum(len(i["turns"]) for i, _ in tasks)
        print(f"[{cfg['id']}] {len(tasks)} items to run ({n_calls} calls), {len(done)} already done -> {out.relative_to(ROOT)}")

        if args.dry_run:
            if tasks:
                i, s = tasks[0]
                print(f"  example: {i['id']} sample {s}\n  system: {system_prompts[i['system']]!r}\n  turn 1: {i['turns'][0][:300]}...")
            continue

        client = make_client(cfg)
        try:
            client.check()
        except ClientError as e:
            print(f"  skipping {cfg['id']}: {e}")
            continue

        lock = threading.Lock()
        start, errors = time.time(), 0
        with out.open("a") as fh, ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(run_one, client, cfg, i, s, system_prompts[i["system"]],
                                   cfg.get("temperature"), cfg["max_tokens"]) for i, s in tasks]
            for n, fut in enumerate(as_completed(futures), 1):
                row = fut.result()
                errors += row["error"] is not None
                with lock:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                if n % 25 == 0 or n == len(tasks):
                    rate = n / (time.time() - start)
                    eta = (len(tasks) - n) / rate / 60 if rate else 0
                    print(f"  {n}/{len(tasks)}  {rate:.2f} items/s  ~{eta:.0f} min left  errors: {errors}")
        if errors:
            print(f"  {errors} items failed; rerun the same command to retry them")


if __name__ == "__main__":
    main()
