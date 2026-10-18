"""Session chat + Guardian enforcement (spec sections 7, 9, 10.5, 10.6, 10.12).

This is the product's differentiator made real: a short mentorship session where
EVERY message — in both directions — is scrubbed for PII (scrub.py) and then
screened by the Guardian (guardian.py) before it is stored or shown.

The pipeline for one message is fixed:

    raw text -> scrub() -> screen_message() -> store(text_scrubbed, display_text)

  * `text_scrubbed` is what is persisted (never raw PII, spec section 8).
  * `display_text` is what the OTHER side sees; it differs only when the
    Guardian redacted the message (spec section 10.5).
  * The action (ALLOW / WARN / BLOCK_AND_REDACT) comes from deterministic code
    in guardian.py — never from a model.

Strike bookkeeping (spec 10.5): a mentor message blocked at severity 3 incurs a
strike; three strikes end the session and reset the mentor's pitch-free streak.
Only MENTOR strikes count — a mentee leaking their own phone number is redacted
for privacy but never "struck" as a pitcher.

Friend Test (spec 10.6): `session.money_stance` is the rollup — latest non-"n/a"
stance, with `pushes_to_spend` taking priority if it ever occurred.

Mentor replies come from simulator.py (spec 10.12) and are labelled
`is_simulated=True`. There is no live human mentor in this prototype.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request

from ..deps import current_user, limit
from ..errors import bad_request, forbidden, not_found
from ..guardian import REDACTED_TEXT, screen_message
from ..mentor_corpus import get_mentor
from ..metrics import FEEDBACK, agreement_metric
from ..models import (
    AppUser,
    SessionFeedbackCreate,
    SessionFeedbackResponse,
    FriendTestResult,
    MenteeFeedback,
    MessageCreate,
    MessageListResponse,
    MoneyStance,
    RevealContact,
    RevealRequest,
    RevealResponse,
    Session,
    SessionCreate,
    SessionListResponse,
    SessionMessage,
    SessionMessageResponse,
    SessionSummary,
    SummaryUpdate,
    utc_now_iso,
)
from ..observability import log_event
from ..scrub import scrub
from ..simulator import generate_reply
from ..summarizer import generate_summary

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

SESSIONS = "sessions"
MESSAGES = "session_messages"

# Spec section 10.5: three strikes end the session.
MAX_STRIKES = 3

# How many messages we pull per session for the in-memory store. A Firestore
# store would query by session_id + seq; the dict store filters in-process.
_MESSAGE_SCAN_LIMIT = 1000


def _merge_money_stance(current: MoneyStance, incoming: MoneyStance) -> MoneyStance:
    """Rollup rule (spec 10.6): latest non-"n/a", but `pushes_to_spend` wins.

    Once a mentor has pushed to spend, a later "cautions" or "neutral" does not
    erase that pressure — it stays `pushes_to_spend`.
    """
    if incoming == "n/a":
        return current
    if incoming == "pushes_to_spend" or current == "pushes_to_spend":
        return "pushes_to_spend"
    return incoming  # latest non-"n/a" stance


def _load_session(request: Request, session_id: str, user: AppUser) -> Session:
    """Fetch a session and assert the caller is its mentee (spec 9: participants
    only). Mentors are synthetic and never authenticate in this prototype."""
    doc = request.app.state.store.get(SESSIONS, session_id)
    if doc is None:
        raise not_found("No session with that id.")
    session = Session.model_validate(doc)
    if session.mentee_id != user.uid:
        raise forbidden("This session does not belong to you.")
    return session


def _messages_for(request: Request, session_id: str) -> list[SessionMessage]:
    """All messages for a session, in send order (seq then timestamp)."""
    raw = request.app.state.store.list(MESSAGES, limit=_MESSAGE_SCAN_LIMIT)
    msgs = [SessionMessage.model_validate(m) for m in raw if m.get("session_id") == session_id]
    msgs.sort(key=lambda m: (m.seq, m.created_at))
    return msgs


def _next_seq(msgs: list[SessionMessage]) -> int:
    return (msgs[-1].seq + 1) if msgs else 1


def _persist_message(
    request: Request,
    session: Session,
    sender_role: str,
    raw_text: str,
    is_simulated: bool,
    gemini,
) -> tuple[SessionMessage, object]:
    """Scrub + screen + store one message. Returns (message, guardian_decision).

    Central so the mentee path and the simulated-mentor path cannot diverge.
    """
    settings = request.app.state.settings
    cleaned = scrub(raw_text[: settings.max_need_chars])
    verdict, decision = screen_message(cleaned.text, sender_role, gemini=gemini)

    msgs = _messages_for(request, session.id)
    display = decision.display_text or cleaned.text

    message = SessionMessage(
        id="msg_" + uuid.uuid4().hex[:16],
        session_id=session.id,
        seq=_next_seq(msgs),
        sender_role=sender_role,  # type: ignore[arg-type]
        text_scrubbed=cleaned.text,
        display_text=display,
        is_simulated=is_simulated,
        guardian=verdict,
        action=decision.action,
    )
    request.app.state.store.set(MESSAGES, message.id, message.model_dump())

    # --- Session-level rollups (never message text) -------------------------
    g = session.guardian
    g.messages_checked += 1
    g.max_severity = max(g.max_severity, decision.final_severity)
    if verdict.is_pitch:
        g.pitches_flagged += 1

    # Mentor strikes only (a mentee's own leak is redacted, not struck).
    if decision.strike_incurred and sender_role == "mentor":
        g.strikes += 1

    # Friend Test rollup (mentor messages only carry a stance).
    if sender_role == "mentor":
        session.money_stance = _merge_money_stance(session.money_stance, verdict.money_stance)

    # Structured audit line — counts and codes only, NEVER message text.
    log_event(
        "guardian_decision",
        session_id=session.id,
        sender_role=sender_role,
        category=verdict.category,
        severity=decision.final_severity,
        action=decision.action,
        classifier_source=verdict.source,
        strikes=g.strikes,
        scrubbed=cleaned.changed,
        is_simulated=is_simulated,
    )

    # Three strikes end the session (spec 10.5) and reset the mentor streak.
    if g.strikes >= MAX_STRIKES and session.status == "ACTIVE":
        _end_session(request, session, reason="max_strikes")
        decision.ends_session = True

    request.app.state.store.set(SESSIONS, session.id, session.model_dump())
    return message, decision


def _end_session(request: Request, session: Session, reason: str) -> None:
    """Mark ENDED and update the mentor's pitch stats honestly (spec 10.5/13)."""
    session.status = "ENDED"
    session.ended_at = utc_now_iso()
    request.app.state.store.set(SESSIONS, session.id, session.model_dump())

    mentor_doc = request.app.state.store.get("mentors", session.mentor_id)
    if mentor_doc is not None:
        from ..models import Mentor

        mentor = Mentor.model_validate(mentor_doc)
        if session.guardian.strikes > 0:
            mentor.stats.pitch_flags_total += session.guardian.strikes
            mentor.stats.pitch_free_streak = 0
        else:
            mentor.stats.pitch_free_streak += 1
        mentor.stats.sessions_completed += 1
        request.app.state.store.set("mentors", mentor.id, mentor.model_dump())

    log_event(
        "session_ended",
        session_id=session.id,
        reason=reason,
        strikes=session.guardian.strikes,
        messages_checked=session.guardian.messages_checked,
    )


# --- Routes -----------------------------------------------------------------


@router.post("", response_model=Session, status_code=201)
async def create_session(
    body: SessionCreate,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> Session:
    """Open a session with a mentor, optionally linked to a prior need."""
    mentor = get_mentor(request.app.state.store, body.mentor_id)
    if mentor is None:
        raise not_found("No mentor with that id.")

    settings = request.app.state.settings
    intent_summary: str | None = None
    money_involved = False
    if body.need_id:
        need_doc = request.app.state.store.get("needs", body.need_id)
        if need_doc is None:
            raise not_found("No need with that id.")
        if need_doc.get("user_id") != user.uid:
            raise forbidden("That need does not belong to you.")
        from ..models import Need

        need = Need.model_validate(need_doc)
        intent_summary = need.interpretation.summary
        money_involved = need.interpretation.intent.money_involved

    session = Session(
        id="sess_" + uuid.uuid4().hex[:16],
        mentee_id=user.uid,
        mentor_id=mentor.id,
        mentor_pseudonym=mentor.pseudonym,
        need_id=body.need_id,
        intent_summary=intent_summary,
        money_involved=money_involved,
        is_synthetic=settings.is_demo,
    )
    request.app.state.store.set(SESSIONS, session.id, session.model_dump())
    log_event(
        "session_created",
        session_id=session.id,
        mentor_id=mentor.id,
        need_id=body.need_id,
        money_involved=money_involved,
    )
    return session


@router.get("", response_model=SessionListResponse)
async def list_my_sessions(
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> SessionListResponse:
    """The caller's sessions (newest first). Paginated later if needed."""
    raw = request.app.state.store.list(SESSIONS, limit=200)
    mine = [Session.model_validate(d) for d in raw if d.get("mentee_id") == user.uid]
    mine.sort(key=lambda s: s.created_at, reverse=True)
    return SessionListResponse(items=mine, total=len(mine))


@router.get("/{session_id}", response_model=Session)
async def get_session(
    session_id: str,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> Session:
    return _load_session(request, session_id, user)


@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def list_messages(
    session_id: str,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> MessageListResponse:
    _load_session(request, session_id, user)
    msgs = _messages_for(request, session_id)
    return MessageListResponse(items=msgs, total=len(msgs))


@router.post("/{session_id}/messages", response_model=SessionMessageResponse)
async def send_message(
    session_id: str,
    body: MessageCreate,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> SessionMessageResponse:
    """Mentee sends a message: scrub -> Guardian -> store -> return the decision.

    The sender always learns what the Guardian decided (so a redaction is never
    silent); the stored `display_text` is what the other side will see.
    """
    session = _load_session(request, session_id, user)
    if session.status != "ACTIVE":
        raise bad_request("This session has ended.")

    message, decision = _persist_message(
        request, session, "mentee", body.text, is_simulated=False,
        gemini=request.app.state.gemini,
    )
    return SessionMessageResponse(message=message, guardian=decision)


@router.post("/{session_id}/mentor-reply", response_model=SessionMessageResponse)
async def mentor_reply(
    session_id: str,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> SessionMessageResponse:
    """Generate the synthetic mentor's reply (spec 10.12) and screen it too.

    Deterministic template by default. This is how a mentor "responds" in this
    prototype — every reply is labelled `is_simulated=True` and shown under
    "Simulated mentor". Honest: no human mentor is on the other end.
    """
    session = _load_session(request, session_id, user)
    if session.status != "ACTIVE":
        raise bad_request("This session has ended.")

    # Echo a short, non-identifying topic hint (never raw stored PII).
    msgs = _messages_for(request, session_id)
    last_mentee = next(
        (m.text_scrubbed for m in reversed(msgs) if m.sender_role == "mentee"), ""
    )

    # Default honest style; salesy/subtle are reachable for Guardian demos.
    style = request.query_params.get("style", "honest")
    reply = generate_reply(style, last_mentee, gemini=request.app.state.gemini)

    message, decision = _persist_message(
        request, session, "mentor", reply.text, is_simulated=True,
        gemini=request.app.state.gemini,
    )
    log_event(
        "mentor_reply",
        session_id=session.id,
        style=reply.style,
        source=reply.source,
        action=decision.action,
    )
    return SessionMessageResponse(message=message, guardian=decision)


@router.post("/{session_id}/end", response_model=Session)
async def end_session(
    session_id: str,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> Session:
    session = _load_session(request, session_id, user)
    if session.status != "ACTIVE":
        raise bad_request("This session has already ended.")
    _end_session(request, session, reason="requested")
    return session


@router.get("/{session_id}/friend-test", response_model=FriendTestResult)
async def friend_test(
    session_id: str,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> FriendTestResult:
    """Friend Test (spec 10.6): did the mentor push spending, caution it, or stay
    neutral? Only meaningful when the need involved money. Honest: while every
    mentor is synthetic this is a simulated result, so `is_simulated=True`."""
    session = _load_session(request, session_id, user)

    if not session.money_involved:
        return FriendTestResult(
            applicable=False,
            stance="n/a",
            label="This session was not about a money decision, so there is nothing to test.",
            is_simulated=session.is_synthetic,
        )

    labels = {
        "pushes_to_spend": "Watch out: this mentor leaned toward spending money.",
        "cautions_against_spending": "Good sign: this mentor advised caution before spending.",
        "neutral": "This mentor was neutral about spending.",
        "n/a": "No clear stance on spending was recorded in this session.",
    }
    return FriendTestResult(
        applicable=True,
        stance=session.money_stance,
        label=labels[session.money_stance],
        is_simulated=session.is_synthetic,
    )


# --- Stage A3: reveal state machine (spec section 8) ------------------------


def _reveal_response(
    session: Session, mentee_name: str, notice: str | None = None
) -> RevealResponse:
    """Project the reveal for the caller: contacts only when REVEALED.

    The display name is the pseudonym (never a real identity). The mentor side
    is synthetic, so its contact is honestly labelled `is_simulated`.
    """
    reveal = session.reveal
    state = reveal.state  # type: ignore[attr-defined]
    if not reveal.revealed:
        return RevealResponse(state=state, revealed=False, contacts=[], notice=notice)  # type: ignore[arg-type]

    contacts = [
        RevealContact(
            role="mentee",
            display_name=mentee_name,
            contact_optional=reveal.mentee_contact,
            is_simulated=False,
        ),
        RevealContact(
            role="mentor",
            display_name=session.mentor_pseudonym,
            contact_optional=reveal.mentor_contact,
            is_simulated=session.is_synthetic,
        ),
    ]
    return RevealResponse(state="REVEALED", revealed=True, contacts=contacts, notice=notice)


@router.post("/{session_id}/reveal", response_model=RevealResponse)
async def set_reveal(
    session_id: str,
    body: RevealRequest,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> RevealResponse:
    """Mutual-consent reveal (spec section 8): NONE -> ONE_SIDED -> REVEALED.

    The MENTEE's consent is set here; the mentor's is simulated (synthetic
    mentor) so the state machine is exercisable. Either side may withdraw before
    REVEALED. Once both have consented the contacts are treated as shared and
    the state locks — withdrawal is no longer offered.
    """
    session = _load_session(request, session_id, user)
    reveal = session.reveal

    if reveal.revealed:
        raise bad_request(
            "This session is already revealed. Both sides have shared, so "
            "consent can no longer be withdrawn here."
        )

    # Scrub the offered contact before it is ever stored (spec section 8).
    contact = scrub(body.contact_optional).text if body.contact_optional else None

    if body.consent:
        reveal.mentee_consent = True
        reveal.mentee_contact = contact
        # Simulated mentor side: a synthetic mentor "consents" back so the
        # machine reaches REVEALED and the flow is demonstrable. Honest label
        # rides on `RevealContact.is_simulated`.
        reveal.mentor_consent = True
        reveal.mentor_contact = None
        reveal.revealed_at = utc_now_iso()
        notice = "Both sides have shared. You are now revealed to each other."
        log_event("reveal_state", session_id=session.id, state="REVEALED")
    else:
        # Withdraw (only reachable before REVEALED, guarded above).
        reveal.mentee_consent = False
        reveal.mentor_consent = False
        reveal.mentee_contact = None
        reveal.revealed_at = None
        notice = "Consent withdrawn. You are both anonymous again."
        log_event("reveal_state", session_id=session.id, state="NONE")

    session.reveal = reveal
    request.app.state.store.set(SESSIONS, session.id, session.model_dump())
    return _reveal_response(session, mentee_name=user.pseudonym, notice=notice)


# --- Stage A3: editable session summary (spec section 10.8) -----------------


def _summary_for(request: Request, session: Session) -> SessionSummary:
    """Generate (or reuse) the summary for an ENDED session.

    A summary the mentee has edited is never overwritten by regeneration.
    """
    if session.summary is not None and session.summary.edited:
        return session.summary

    msgs = _messages_for(request, session.id)
    need_text = ""
    domains: list[str] = []
    if session.need_id:
        need_doc = request.app.state.store.get("needs", session.need_id)
        if need_doc:
            from ..models import Need

            need = Need.model_validate(need_doc)
            need_text = need.text_scrubbed
            domains = need.interpretation.intent.domains

    summary = generate_summary(
        request.app.state.store,
        msgs,
        session.intent_summary,
        domains,
        need_text,
        session.money_stance,
        session.guardian.strikes,
        gemini=request.app.state.gemini,
    )
    session.summary = summary
    request.app.state.store.set(SESSIONS, session.id, session.model_dump())
    return summary


@router.get("/{session_id}/summary", response_model=SessionSummary)
async def get_summary(
    session_id: str,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> SessionSummary:
    """The mentee-facing summary. Generated on first access after the session ends."""
    session = _load_session(request, session_id, user)
    if session.status != "ENDED":
        raise bad_request("The summary is available once a session has ended.")
    return _summary_for(request, session)


@router.patch("/{session_id}/summary", response_model=SessionSummary)
async def edit_summary(
    session_id: str,
    body: SummaryUpdate,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> SessionSummary:
    """Apply the mentee's edits. Marks the summary `edited` so it won't be clobbered.

    Edits are scrubbed on the way in (spec section 8) and capped to sane lengths
    so a summary can never become a free-text leak.
    """
    session = _load_session(request, session_id, user)
    if session.status != "ENDED":
        raise bad_request("The summary is available once a session has ended.")

    summary = _summary_for(request, session)

    def _cap(lines: list[str] | None, current: list[str], limit: int) -> list[str]:
        if lines is None:
            return current
        cleaned = [c for c in (scrub(line[:200]).text.strip() for line in lines) if c]
        return cleaned[:limit]

    if body.key_points is not None:
        summary.key_points = _cap(body.key_points, summary.key_points, 8)
    if body.action_items is not None:
        summary.action_items = _cap(body.action_items, summary.action_items, 5)  # spec: max 5
    if body.caveats is not None:
        summary.caveats = _cap(body.caveats, summary.caveats, 6)
    summary.edited = True

    session.summary = summary
    request.app.state.store.set(SESSIONS, session.id, session.model_dump())
    log_event("summary_edited", session_id=session.id)
    return summary


# --- Stage A3: feedback + agreement metric (spec section 10.11) --------------


@router.post("/{session_id}/feedback", response_model=SessionFeedbackResponse)
async def submit_feedback(
    session_id: str,
    body: SessionFeedbackCreate,
    request: Request,
    user: AppUser = Depends(current_user),
    _limited=Depends(limit),
) -> SessionFeedbackResponse:
    """Feedback from either side (spec section 7). Updates mentor quality.

    The mentee's `felt_pitched` is compared with the Guardian's severity to
    power the agreement metric. Free text is scrubbed; a mismatch between the
    two is logged for the (human) review queue rather than acted on automatically.
    """
    session = _load_session(request, session_id, user)
    if session.status != "ENDED":
        raise bad_request("Feedback is available once a session has ended.")

    store = request.app.state.store
    fb_id = f"{session.id}_{body.role}"
    if store.get(FEEDBACK, fb_id) is not None:
        raise bad_request("You have already given feedback for this session.")

    record: dict[str, object] = {
        "id": fb_id,
        "session_id": session.id,
        "role": body.role,
        "mentor_id": session.mentor_id,
        "max_severity": session.guardian.max_severity,
        "created_at": utc_now_iso(),
    }

    if body.role == "mentee":
        if body.mentee is None:
            raise bad_request("Mentee feedback must include the mentee block.")
        m: MenteeFeedback = body.mentee
        text = scrub(m.free_text).text if m.free_text else None
        record.update(
            helpfulness_1_5=m.helpfulness_1_5,
            felt_pitched=m.felt_pitched,
            would_recommend=m.would_recommend,
            free_text_scrubbed=text,
        )
        # Spec 10.11: a disagreement between the mentee and the Guardian is
        # surfaced for human review — never auto-actioned.
        guardian_says_pitch = session.guardian.max_severity >= 2
        if m.felt_pitched == "yes" and not guardian_says_pitch:
            record["disagreement"] = "mentee_saw_pitch_guardian_did_not"
            log_event(
                "feedback_disagreement",
                session_id=session.id,
                kind="false_negative_suspected",
            )
        elif m.felt_pitched == "no" and guardian_says_pitch:
            record["disagreement"] = "guardian_flagged_mentor_did_not"
            log_event(
                "feedback_disagreement",
                session_id=session.id,
                kind="false_positive_suspected",
            )
        _update_mentor_quality(store, session.mentor_id, m.helpfulness_1_5, session)
    else:
        if body.mentor is None:
            raise bad_request("Mentor feedback must include the mentor block.")
        text = scrub(body.mentor.free_text).text if body.mentor.free_text else None
        record.update(
            mentee_seriousness_1_5=body.mentor.mentee_seriousness_1_5,
            respectful=body.mentor.respectful,
            free_text_scrubbed=text,
            is_simulated=True,  # synthetic mentor
        )

    store.set(FEEDBACK, fb_id, record)
    log_event(
        "feedback_created",
        session_id=session.id,
        role=body.role,
        felt_pitched=record.get("felt_pitched"),
        disagreement=record.get("disagreement"),
    )

    agreement = agreement_metric(store) if body.role == "mentee" else None
    return SessionFeedbackResponse(ok=True, agreement=agreement)


def _update_mentor_quality(store, mentor_id: str, helpfulness: int, session: Session) -> None:
    """Update a mentor's quality score and helpfulness average (spec section 13).

    Bayesian-flavoured: blends the new rating into the running average with a
    prior, so one session cannot swing the score. A strike in this session
    penalises quality, per spec section 10.11.
    """
    doc = store.get("mentors", mentor_id)
    if doc is None:
        return
    from ..models import Mentor

    mentor = Mentor.model_validate(doc)
    stats = mentor.stats
    n = stats.sessions_completed if stats.sessions_completed > 0 else 0
    prior = 0.5  # neutral prior
    prior_weight = 3
    base = stats.avg_helpfulness if stats.avg_helpfulness is not None else 0.5
    blended = ((base * prior_weight) + (helpfulness / 5.0)) / (prior_weight + 1)
    stats.avg_helpfulness = round(blended, 3)
    # Penalty: a pitch strike in this session drags quality down.
    if session.guardian.strikes > 0:
        stats.quality_score = round(max(0.0, stats.quality_score - 0.05 * session.guardian.strikes), 3)
    else:
        stats.quality_score = round(min(1.0, stats.quality_score + 0.01), 3)
    _ = prior, n  # documented intent; prior folded into prior_weight
    store.set("mentors", mentor.id, mentor.model_dump())


__all__ = ["router"]
