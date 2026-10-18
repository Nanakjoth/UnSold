"""Guardian vs mentee agreement metric (spec section 10.11).

Online agreement = the share of sessions where the mentee's report
(`felt_pitched == "yes"`) matches the Guardian's verdict (`max_severity >= 2`).
"unsure" responses are EXCLUDED per spec. The share is NEVER reported without
its sample size, and is withheld entirely below `MIN_AGREEMENT_SAMPLES` — a
percentage built from two sessions is noise, not a metric.

Labelled `is_simulated` while the mentors are synthetic, so no reader mistakes
it for production telemetry.
"""

from __future__ import annotations

from .models import AgreementMetric

FEEDBACK = "session_feedback"

# Spec 10.11 / CORE_REALIGNMENT P2.4: hide the share below this many samples.
MIN_AGREEMENT_SAMPLES = 3


def agreement_metric(store) -> AgreementMetric:
    """Compute the agreement metric across all stored mentee feedback."""
    raw = store.list(FEEDBACK, limit=1000)
    mentee_fb = [f for f in raw if f.get("role") == "mentee" and f.get("felt_pitched")]

    considered = 0
    agree = 0
    guardian_flagged = 0
    reported_pitch = 0
    for fb in mentee_fb:
        felt = fb.get("felt_pitched")
        if felt == "unsure":
            continue  # excluded per spec
        severity = int(fb.get("max_severity", 0))
        guardian_says_pitch = severity >= 2
        mentee_says_pitch = felt == "yes"
        considered += 1
        if guardian_says_pitch:
            guardian_flagged += 1
        if mentee_says_pitch:
            reported_pitch += 1
        if guardian_says_pitch == mentee_says_pitch:
            agree += 1

    if considered < MIN_AGREEMENT_SAMPLES:
        return AgreementMetric(
            share=None,
            sample_size=considered,
            label=(
                f"Not enough feedback yet to report agreement "
                f"({considered} of a required {MIN_AGREEMENT_SAMPLES} "
                "honest responses)."
            ),
            is_simulated=True,
            guardian_flagged=guardian_flagged,
            mentee_reported_pitch=reported_pitch,
        )

    share = round(agree / considered, 3)
    return AgreementMetric(
        share=share,
        sample_size=considered,
        label=(
            f"The Guardian and mentees agreed on {round(share * 100)}% of "
            f"{considered} sessions. This is simulated data."
        ),
        is_simulated=True,
        guardian_flagged=guardian_flagged,
        mentee_reported_pitch=reported_pitch,
    )


__all__ = ["agreement_metric", "FEEDBACK", "MIN_AGREEMENT_SAMPLES"]
