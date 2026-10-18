"""Demo-only routes. Registered only when APP_MODE=demo.

`create_app` never imports this module in production, so these routes do not
exist in a production build — verified by a test that walks the route table.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from ..auth import DemoProvider, get_or_create_user
from ..catalogue import seed_catalogue
from ..deps import current_user
from ..errors import not_found
from ..metrics import FEEDBACK, agreement_metric
from ..models import AppUser, MentorImpact, SessionResponse
from ..observability import log_event
from ..rate_limit import enforce_rate_limit
from ..retention import delete_user_data

router = APIRouter(prefix="/api/dev", tags=["demo"])


class DemoLoginRequest(BaseModel):
    """`label` picks which demo identity to mint (e.g. "a", "b", "default").

    Multiple labels exist so multi-member flows (connections, reports) can be
    exercised locally with two real, separately-verified users.
    """

    label: str = Field(default="default", pattern="^[a-z0-9-]{1,16}$")


class DemoLoginResponse(BaseModel):
    token: str
    uid: str
    pseudonym: str
    label: str
    notice: str = "Demo mode: this identity is synthetic and resets with the server."


@router.post("/demo-login", response_model=DemoLoginResponse)
async def demo_login(
    body: DemoLoginRequest,
    request: Request,
    _limited=Depends(enforce_rate_limit),
) -> DemoLoginResponse:
    """Mint a signed demo token so local development exercises real authz.

    Exists only in demo mode; the route is not registered in production.
    """
    provider = request.app.state.auth_provider
    assert isinstance(provider, DemoProvider)

    # Deterministic uid per label so repeated logins stay stable per browser
    # until reset; it is still server-verified, never client-claimed.
    uid = "demo-" + hashlib.sha256(body.label.encode()).hexdigest()[:16]
    user = get_or_create_user(request.app.state.store, uid, is_synthetic=True)

    token = provider.mint(uid)
    log_event("demo_login", uid=uid, label=body.label)
    return DemoLoginResponse(
        token=token, uid=uid, pseudonym=user.pseudonym, label=body.label
    )


@router.post("/reset")
async def reset_demo_data(
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(enforce_rate_limit),
) -> dict[str, object]:
    """Delete this demo user's data and reseed the catalogue.

    Demo-only; never registered in production.
    """
    store = request.app.state.store
    deleted = delete_user_data(store, user.uid)
    seeded = seed_catalogue(store)
    return {
        "deleted": deleted,
        "total": sum(deleted.values()),
        "catalogue": seeded,
        "mode": "demo",
    }


@router.get("/me", response_model=SessionResponse)
async def demo_whoami(
    request: Request,
    user: AppUser = Depends(current_user),
) -> SessionResponse:
    """Convenience for the demo UI: confirm the current identity."""
    return SessionResponse(
        uid=user.uid,
        pseudonym=user.pseudonym,
        language=user.language,
        is_synthetic=user.is_synthetic,
        created_at=user.created_at,
    )


# --- Stage A3: mentor impact (spec section 9: GET /mentors/me/impact) -------


@router.get("/mentors/{mentor_id}/impact", response_model=MentorImpact)
async def demo_mentor_impact(
    mentor_id: str,
    request: Request,
    user: AppUser = Depends(current_user),
) -> MentorImpact:
    """A mentor's private impact dashboard (spec sections 9, 13).

    Exposed ONLY in the demo build. There is no mentor authentication in this
    prototype (mentors are synthetic), so the production `/mentors/me/impact`
    route would leak private stats via a public path. Putting it behind the
    demo-only router keeps the production surface honest while the dashboard
    remains real and exercisable. In production this requires a signed-in
    mentor and is scoped to their own record.
    """
    from ..models import Mentor

    doc = request.app.state.store.get("mentors", mentor_id)
    if doc is None:
        raise not_found("No mentor with that id.")
    mentor = Mentor.model_validate(doc)
    stats = mentor.stats

    # Count mentee feedback for this mentor to show helpfulness sub-totals.
    feedback = request.app.state.store.list(FEEDBACK, limit=1000)
    mine = [
        f
        for f in feedback
        if f.get("mentor_id") == mentor_id and f.get("role") == "mentee"
    ]
    helpful_responses = len(mine)

    return MentorImpact(
        mentor_id=mentor.id,
        pseudonym=mentor.pseudonym,
        sessions_completed=stats.sessions_completed,
        avg_helpfulness=stats.avg_helpfulness,
        quality_score=round(stats.quality_score, 3),
        pitch_free_streak=stats.pitch_free_streak,
        pitch_flags_total=stats.pitch_flags_total,
        minutes_given=stats.minutes_given,
        helpfulness_responses=helpful_responses,
        is_simulated=mentor.is_synthetic,
    )


# --- Stage A3: Guardian metrics (spec section 9) ----------------------------


@router.get("/metrics/guardian")
async def demo_guardian_metrics(request: Request) -> dict[str, object]:
    """The Guardian-vs-mentee agreement metric (spec section 9, 10.11).

    Demo-only for the same reason as the impact view: while the mentors are
    synthetic there is no per-mentor auth to scope a production metrics route.
    The share is hidden below the sample threshold and labelled simulated.
    """
    metric = agreement_metric(request.app.state.store)
    return {
        "agreement": metric.model_dump(),
        "notice": (
            "Guardian agreement is hidden below 3 honest responses and labelled "
            "simulated while mentors are synthetic."
        ),
    }


# --- Stage P3: offline evaluation (spec section 12) --------------------------

_EVAL_RUN = Path(__file__).resolve().parents[3] / "eval" / "last_run.json"


@router.get("/metrics/eval")
async def demo_eval_run() -> dict[str, object]:
    """The last offline Guardian evaluation (spec section 12, CORE_REALIGNMENT P3).

    Reads `eval/last_run.json`, written by `scripts/run_eval.py`. The run always
    carries its own sample size and split, and while any label is still
    `unreviewed` the numbers are NOT accuracy — the `review_status` rides along so
    the Metrics page can say so plainly. 404s honestly if no run exists yet.
    """
    if not _EVAL_RUN.exists():
        raise not_found(
            "No evaluation run yet. Run scripts/run_eval.py to produce one."
        )
    import json

    data = json.loads(_EVAL_RUN.read_text(encoding="utf-8"))
    return {
        "run": data,
        "notice": (
            "These are the deterministic fallback classifier's numbers on the "
            "held-out test split. They are not accuracy claims until the gold "
            "set labels are human-reviewed."
        ),
    }


__all__ = ["router"]
