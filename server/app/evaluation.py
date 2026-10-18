"""Offline evaluation for the Guardian classifier (spec section 12, CORE_REALIGNMENT P3).

The gold set is a fixed, human-reviewable set of mentor messages with labels.
This module is the pure scoring core: it takes labelled rows and a predictor and
returns precision / recall / F1, per-category recall, the hard-negative false-
positive rate, and a confusion matrix. It imports nothing from the network or
the store, so it is trivially testable and reusable by both the CLI runner and
the app.

Honesty rules baked in (spec section 12):
  * Never claim accuracy beyond these numbers — the result carries its own
    sample size and split.
  * Labels written by a generator are NOT ground truth until a human reviews
    them; the run records `review_status` and the Metrics page surfaces it.
  * Tuning happens on `dev` only; the reported metrics come from `test`.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Iterable

# A predictor takes (text, sender_role) and returns an object with the fields
# the scorer reads: is_pitch (bool), category (str), severity (int). This lets
# the real Guardian pipeline and a test stub both satisfy it structurally.
Predictor = Callable[[str, str], object]


@dataclass
class GoldRow:
    """One labelled example from `eval/gold_set.jsonl`."""

    id: str
    text: str
    label_is_pitch: bool
    label_category: str
    label_severity: int
    split: str  # "dev" | "test"
    is_hard_negative: bool = False
    notes: str = ""
    review_status: str = "unreviewed"

    @classmethod
    def from_dict(cls, d: dict) -> "GoldRow":
        return cls(
            id=d["id"],
            text=d["text"],
            label_is_pitch=bool(d["label_is_pitch"]),
            label_category=d["label_category"],
            label_severity=int(d["label_severity"]),
            split=d["split"],
            is_hard_negative=bool(d.get("is_hard_negative", False)),
            notes=d.get("notes", ""),
            review_status=d.get("review_status", "unreviewed"),
        )


@dataclass
class EvalResult:
    """Everything the Metrics page shows. Never a bare percentage."""

    n: int
    split: str
    precision: float
    recall: float
    f1: float
    hard_negative_fpr: float | None
    hard_negative_count: int
    per_category_recall: dict[str, float] = field(default_factory=dict)
    per_category_support: dict[str, int] = field(default_factory=dict)
    # confusion[actual][predicted] -> count, over the binary pitch question.
    confusion: dict[str, dict[str, int]] = field(default_factory=dict)
    false_positives: list[dict] = field(default_factory=list)
    false_negatives: list[dict] = field(default_factory=list)
    review_status: str = "unreviewed"
    model: str = "fallback"
    prompt_version: str = "rules-v1"

    def as_dict(self) -> dict:
        return {
            "n": self.n,
            "split": self.split,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "hard_negative_fpr": self.hard_negative_fpr,
            "hard_negative_count": self.hard_negative_count,
            "per_category_recall": self.per_category_recall,
            "per_category_support": self.per_category_support,
            "confusion": self.confusion,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "review_status": self.review_status,
            "model": self.model,
            "prompt_version": self.prompt_version,
        }


def _ratio(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def evaluate(
    rows: Iterable[GoldRow],
    predict: Predictor,
    split: str = "test",
    model: str = "fallback",
    prompt_version: str = "rules-v1",
) -> EvalResult:
    """Score `predict` on the rows of `split`. Metrics are computed on `test`.

    The predicted pitch decision mirrors the live policy: a message is treated
    as a predicted pitch when the verdict says `is_pitch` OR its severity is
    >= 2 (severity 2+ maps to WARN/BLOCK in production, so that is what a
    reviewer would call "flagged").
    """
    rows = [r for r in rows if r.split == split]

    tp = fp = fn = tn = 0
    category_total: Counter[str] = Counter()
    category_hit: Counter[str] = Counter()
    confusion: dict[str, dict[str, int]] = {}
    hard_total = 0
    hard_fp = 0
    false_positives: list[dict] = []
    false_negatives: list[dict] = []

    for row in rows:
        verdict = predict(row.text, "mentor")
        pred_is_pitch = bool(getattr(verdict, "is_pitch", False)) or int(
            getattr(verdict, "severity", 0)
        ) >= 2
        pred_category = str(getattr(verdict, "category", "NONE"))
        pred_severity = int(getattr(verdict, "severity", 0))

        actual = row.label_is_pitch
        key = "predicted_pitch" if pred_is_pitch else "predicted_clean"
        actual_key = "actual_pitch" if actual else "actual_clean"
        confusion.setdefault(actual_key, {}).setdefault(key, 0)
        confusion[actual_key][key] += 1

        if actual:
            category_total[row.label_category] += 1
            if pred_is_pitch:
                tp += 1
                category_hit[row.label_category] += 1
            else:
                fn += 1
                false_negatives.append(
                    {
                        "id": row.id,
                        "text": row.text[:120],
                        "label_category": row.label_category,
                        "predicted_category": pred_category,
                        "predicted_severity": pred_severity,
                        "notes": row.notes,
                    }
                )
        else:
            if pred_is_pitch:
                fp += 1
                false_positives.append(
                    {
                        "id": row.id,
                        "text": row.text[:120],
                        "predicted_category": pred_category,
                        "predicted_severity": pred_severity,
                        "notes": row.notes,
                    }
                )
            else:
                tn += 1

            if row.is_hard_negative:
                hard_total += 1
                if pred_is_pitch:
                    hard_fp += 1

    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0
    per_category = {
        cat: _ratio(category_hit[cat], category_total[cat]) for cat in category_total
    }

    # All rows in the run share the weakest review status present.
    statuses = {r.review_status for r in rows} or {"unreviewed"}
    review = "reviewed" if statuses == {"reviewed"} else "unreviewed"

    return EvalResult(
        n=len(rows),
        split=split,
        precision=precision,
        recall=recall,
        f1=f1,
        hard_negative_fpr=_ratio(hard_fp, hard_total),
        hard_negative_count=hard_total,
        per_category_recall=per_category,
        per_category_support=dict(category_total),
        confusion=confusion,
        false_positives=false_positives[:10],
        false_negatives=false_negatives[:10],
        review_status=review,
        model=model,
        prompt_version=prompt_version,
    )


__all__ = ["GoldRow", "EvalResult", "evaluate", "Predictor"]
