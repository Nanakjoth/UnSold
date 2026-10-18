"""Stage P3 tests: the offline Guardian evaluation harness (spec section 12).

The eval must be honest: metrics always carry their sample size, "unreviewed"
labels are surfaced as not-accuracy, tuning happens on `dev` and reporting on
`test`, and the hard-negative false-positive rate is tracked separately (spec
10.5 hard negatives must never be blocked).
"""

from __future__ import annotations

from app.evaluation import GoldRow, evaluate


class _V:
    """Minimal stand-in for a Guardian verdict, structurally compatible."""

    def __init__(self, is_pitch, category, severity):
        self.is_pitch = is_pitch
        self.category = category
        self.severity = severity


def _row(i, is_pitch, category, severity, split, hard=False, review="unreviewed"):
    return GoldRow(
        id=f"g{i}",
        text=f"message {i}",
        label_is_pitch=is_pitch,
        label_category=category,
        label_severity=severity,
        split=split,
        is_hard_negative=hard,
        review_status=review,
    )


def _perfect_predictor(text, role):
    # Derives the label from the message index embedded in the text.
    return _V("pitch" in text or False, "NONE", 0)


def test_evaluate_only_scores_the_requested_split():
    rows = [
        _row(1, True, "DIRECT_PROMO", 3, "dev"),
        _row(2, True, "DIRECT_PROMO", 3, "test"),
    ]
    # Predictor flags everything as a pitch.
    result = evaluate(rows, lambda t, r: _V(True, "DIRECT_PROMO", 3), split="test")
    assert result.n == 1  # dev row excluded
    assert result.split == "test"


def test_perfect_predictions_score_one():
    rows = [
        _row(1, True, "DIRECT_PROMO", 3, "test"),
        _row(2, False, "NONE", 0, "test"),
        _row(3, True, "CONTACT_SOLICIT", 3, "test"),
        _row(4, False, "NONE", 0, "test"),
    ]

    def predict(text, role):
        # rows 1 and 3 are pitches (id ends odd? no) — read from a map.
        pitch = text in ("message 1", "message 3")
        return _V(pitch, "DIRECT_PROMO" if pitch else "NONE", 3 if pitch else 0)

    result = evaluate(rows, predict, split="test")
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.f1 == 1.0
    assert result.confusion["actual_pitch"]["predicted_pitch"] == 2
    assert result.confusion["actual_clean"]["predicted_clean"] == 2


def test_false_negative_lowers_recall_and_is_reported():
    rows = [
        _row(1, True, "URGENCY_FEAR", 2, "test"),
        _row(2, True, "URGENCY_FEAR", 2, "test"),
    ]
    # Predictor flags only the first.
    def predict(text, role):
        return _V(text == "message 1", "URGENCY_FEAR", 2 if text == "message 1" else 0)

    result = evaluate(rows, predict, split="test")
    assert result.recall == 0.5
    assert result.precision == 1.0
    assert len(result.false_negatives) == 1
    assert result.false_negatives[0]["id"] == "g2"


def test_false_positive_reported_and_precision_drops():
    rows = [
        _row(1, False, "NONE", 0, "test"),
        _row(2, True, "DIRECT_PROMO", 3, "test"),
    ]

    def predict(text, role):
        return _V(True, "DIRECT_PROMO", 3)  # flags both

    result = evaluate(rows, predict, split="test")
    assert result.precision == 0.5
    assert len(result.false_positives) == 1
    assert result.false_positives[0]["id"] == "g1"


def test_hard_negative_false_positive_rate_is_tracked():
    rows = [
        _row(1, False, "NONE", 0, "test", hard=True),
        _row(2, False, "NONE", 0, "test", hard=True),
        _row(3, False, "NONE", 0, "test", hard=False),
        _row(4, True, "DIRECT_PROMO", 3, "test"),
    ]

    def predict(text, role):
        # Flags hard-negative g1 (a false positive) and the real pitch g4.
        flagged = text in ("message 1", "message 4")
        return _V(flagged, "DIRECT_PROMO", 3 if flagged else 0)

    result = evaluate(rows, predict, split="test")
    # 1 of 2 hard negatives wrongly flagged -> 0.5
    assert result.hard_negative_count == 2
    assert result.hard_negative_fpr == 0.5


def test_per_category_recall_is_reported():
    rows = [
        _row(1, True, "CONTACT_SOLICIT", 3, "test"),
        _row(2, True, "CONTACT_SOLICIT", 3, "test"),
        _row(3, True, "DIRECT_PROMO", 3, "test"),
    ]

    def predict(text, role):
        # Flags both CONTACT_SOLICIT, misses DIRECT_PROMO.
        flagged = text in ("message 1", "message 2")
        return _V(flagged, "CONTACT_SOLICIT", 3 if flagged else 0)

    result = evaluate(rows, predict, split="test")
    assert result.per_category_recall["CONTACT_SOLICIT"] == 1.0
    assert result.per_category_recall["DIRECT_PROMO"] == 0.0
    assert result.per_category_support["CONTACT_SOLICIT"] == 2


def test_unreviewed_labels_are_surfaced():
    rows = [_row(1, True, "DIRECT_PROMO", 3, "test", review="unreviewed")]
    result = evaluate(rows, lambda t, r: _V(True, "DIRECT_PROMO", 3), split="test")
    assert result.review_status == "unreviewed"


def test_fully_reviewed_labels_mark_reviewed():
    rows = [
        _row(1, True, "DIRECT_PROMO", 3, "test", review="reviewed"),
        _row(2, False, "NONE", 0, "test", review="reviewed"),
    ]
    result = evaluate(
        rows,
        lambda t, r: _V(t == "message 1", "DIRECT_PROMO", 3),
        split="test",
    )
    assert result.review_status == "reviewed"


def test_mixed_review_status_is_unreviewed():
    rows = [
        _row(1, True, "DIRECT_PROMO", 3, "test", review="reviewed"),
        _row(2, False, "NONE", 0, "test", review="unreviewed"),
    ]
    result = evaluate(
        rows, lambda t, r: _V(t == "message 1", "DIRECT_PROMO", 3), split="test"
    )
    assert result.review_status == "unreviewed"


def test_result_as_dict_carries_sample_size_and_split():
    rows = [_row(1, True, "DIRECT_PROMO", 3, "test")]
    result = evaluate(rows, lambda t, r: _V(True, "DIRECT_PROMO", 3), split="test")
    d = result.as_dict()
    assert d["n"] == 1
    assert d["split"] == "test"
    assert "precision" in d and "recall" in d and "f1" in d
    assert "confusion" in d and "hard_negative_fpr" in d


def test_severity_two_or_more_counts_as_predicted_pitch():
    """A severity-2 verdict maps to WARN in production, so it counts as flagged."""
    rows = [_row(1, True, "URGENCY_FEAR", 2, "test")]

    def predict(text, role):
        return _V(False, "URGENCY_FEAR", 2)  # is_pitch False but severity 2

    result = evaluate(rows, predict, split="test")
    assert result.recall == 1.0  # counted as a predicted pitch


def test_gold_set_loads_with_expected_shape():
    """The generated gold set is 80 rows with the spec's split and review state."""
    from pathlib import Path
    import json

    gold = Path(__file__).resolve().parents[2] / "eval" / "gold_set.jsonl"
    rows = [json.loads(l) for l in gold.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 80
    assert sum(1 for r in rows if r["label_is_pitch"]) == 40
    assert sum(1 for r in rows if not r["label_is_pitch"]) == 40
    assert sum(1 for r in rows if r["is_hard_negative"]) == 20
    # Every label starts unreviewed until humans review (spec section 12).
    assert all(r["review_status"] == "unreviewed" for r in rows)
