"""Run the Guardian offline evaluation (spec section 12, CORE_REALIGNMENT P3).

Loads `eval/gold_set.jsonl`, scores the Guardian classifier on the `test` split
only (tune on `dev`, report on `test`), and prints + stores the result.

Metrics: precision, recall, F1, per-category recall, hard-negative false-positive
rate, and the confusion matrix. The result carries its own sample size and its
`review_status` — while any label is still `unreviewed`, the numbers are NOT
accuracy, and every surface says so.

Usage:
    server\\.venv\\Scripts\\python scripts\\run_eval.py            # report on test
    server\\.venv\\Scripts\\python scripts\\run_eval.py --split dev  # tune on dev

By default this prints the report and writes `eval/last_run.json`. Pass
`--store` to also persist into the app's `eval_runs` collection (needs the app
store; use when running against a live backend / Firestore).
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from app.evaluation import GoldRow, evaluate  # noqa: E402
from app.guardian import classify_fallback  # noqa: E402

EVAL_DIR = ROOT / "eval"
GOLD = EVAL_DIR / "gold_set.jsonl"
LAST_RUN = EVAL_DIR / "last_run.json"


def load_rows() -> list[GoldRow]:
    if not GOLD.exists():
        raise SystemExit(
            f"{GOLD} not found. Run scripts\\generate_gold_set.py first."
        )
    rows: list[GoldRow] = []
    with GOLD.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(GoldRow.from_dict(json.loads(line)))
    return rows


def _predict(text: str, role: str):
    """The real deterministic classifier the app runs in fallback mode."""
    return classify_fallback(text, role)


def print_report(result) -> None:
    print(f"\nGuardian eval — split={result.split}  n={result.n}  model={result.model}")
    print(f"  review_status : {result.review_status}")
    if result.review_status != "reviewed":
        print(
            "  NOTE: labels are not fully human-reviewed yet — these are NOT\n"
            "        accuracy claims, just the current deterministic behaviour."
        )
    print(f"  precision     : {result.precision:.3f}")
    print(f"  recall        : {result.recall:.3f}")
    print(f"  f1            : {result.f1:.3f}")
    hn = "n/a" if result.hard_negative_fpr is None else f"{result.hard_negative_fpr:.3f}"
    print(f"  hard-neg FPR  : {hn}  (over {result.hard_negative_count} hard negatives)")
    print("  per-category recall:")
    for cat in sorted(result.per_category_recall):
        sup = result.per_category_support.get(cat, 0)
        print(f"    {cat:<18} {result.per_category_recall[cat]:.3f}  (support {sup})")
    print("  confusion (rows=actual, cols=predicted):")
    for actual in ("actual_clean", "actual_pitch"):
        row = result.confusion.get(actual, {})
        print(f"    {actual:<13} clean={row.get('predicted_clean', 0):<3} pitch={row.get('predicted_pitch', 0)}")
    if result.false_positives:
        print(f"  {len(result.false_positives)} false positive(s) (clean flagged as pitch):")
        for fp in result.false_positives[:5]:
            print(f"    - {fp['id']}: {fp['text'][:70]!r}")
    if result.false_negatives:
        print(f"  {len(result.false_negatives)} false negative(s) (pitch missed):")
        for fn in result.false_negatives[:5]:
            print(f"    - {fn['id']}: {fn['text'][:70]!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Score the Guardian on the gold set.")
    parser.add_argument("--split", choices=["dev", "test"], default="test")
    parser.add_argument("--store", action="store_true", help="persist into eval_runs")
    args = parser.parse_args()

    rows = load_rows()
    result = evaluate(
        rows, _predict, split=args.split, model="fallback", prompt_version="rules-v1"
    )
    print_report(result)

    payload = result.as_dict()
    payload["created_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload["run_id"] = "run_" + uuid.uuid4().hex[:12]
    LAST_RUN.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote run to {LAST_RUN} (run_id={payload['run_id']})")

    if args.store:
        try:
            from app.config import get_settings
            from app.store import create_store

            settings = get_settings()
            store = create_store(settings)
            store.set("eval_runs", payload["run_id"], payload)
            print(f"Stored run in 'eval_runs/{payload['run_id']}'.")
        except Exception as exc:  # pragma: no cover - cloud-only path
            print(f"Could not persist to store (expected locally): {exc}")


if __name__ == "__main__":
    main()
