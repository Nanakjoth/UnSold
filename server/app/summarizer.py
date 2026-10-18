"""Session summary generator (spec section 10.8, CORE_REALIGNMENT C3).

Turns a finished session's scrubbed, DISPLAYED messages into a mentee-facing
digest: `key_points`, `action_items` (max 5, concrete), and `caveats`. It also
pulls 2-3 catalogue entries as "something small you could try" so the summary
is a bridge into the discovery add-on, not a dead end.

Two paths, honestly labelled:
  * live Gemini via `prompts/summary.md` -> `source="gemini"`.
  * a deterministic extractor -> `source="fallback"`.

Hard rules:
  * Only `display_text` of non-blocked messages is ever read. A redacted
    message contributes nothing (spec 10.8: never include promotions that were
    redacted).
  * Contact details cannot leak in: the input is already scrubbed, and the
    extractor re-runs the scrubber on every produced line as a belt-and-braces
    guard before anything is stored.
  * The summary is generated once; the mentee may edit it, and a later
    regeneration must not clobber an edited summary.

The deterministic path is real extraction, not a template — it reads the actual
conversation. It is deliberately conservative: it would rather return fewer
points than invent one.
"""

from __future__ import annotations

import re

from .catalogue import INTERESTS, search_interests
from .gemini import GenerationResult, GeminiClient
from .models import (
    SessionMessage,
    SessionSummary,
    SummaryThingToTry,
)
from .scrub import scrub
from .store import Store

_MAX_ACTION_ITEMS = 5
_MAX_KEY_POINTS = 4
_MAX_CAVEATS = 4
_THINGS_TO_TRY = 3

# Sentence-splitting that keeps abbreviations from over-splitting.
_SENTENCE = re.compile(r"(?<=[.!?])\s+")

# Imperative / action openers the fallback recognises as a next step. A line
# starting with one of these (lowercased) is a concrete action, not narration.
_ACTION_OPENERS = (
    "try ", "start ", "begin ", "consider ", "check ", "look ", "build ", "read ",
    "practice ", "write ", "ask ", "reach out ", "make a ", "set ", "plan ",
    "review ", "compare ", "ask for ", "you should", "you could", "you can",
    "i'd ", "i would", "focus on", "write down", "take ",
)

# Caveat seeds: things the mentor could not know or that must be verified.
_CAVEAT_VERBATIM = (
    "a mentor is a peer, not a professional — this is not medical, legal, or "
    "financial advice",
    "a synthetic mentor gave this advice; treat it as a starting point, not a "
    "guarantee",
)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE.split(text) if len(s.strip()) > 25]


def _clean(line: str) -> str:
    """Scrub every produced line again so no contact detail can survive."""
    cleaned = scrub(line).text
    return cleaned.strip()


def _is_action(sentence: str) -> bool:
    lowered = sentence.lower().lstrip()
    return any(lowered.startswith(opener) for opener in _ACTION_OPENERS)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def extract_summary(
    messages: list[SessionMessage],
    intent_summary: str | None,
    money_stance: str,
    strikes: int,
) -> SessionSummary:
    """Deterministic digest from the displayed messages of a finished session.

    Reads only non-blocked messages' `display_text`. Conservative: it returns
    fewer lines rather than inventing content.
    """
    displayed = [
        m.display_text
        for m in messages
        if m.action != "BLOCK_AND_REDACT" and m.display_text
    ]

    mentee_lines: list[str] = []
    mentor_actions: list[str] = []
    mentor_points: list[str] = []

    for message in messages:
        if message.action == "BLOCK_AND_REDACT":
            continue
        text = message.display_text
        if not text:
            continue
        if message.sender_role == "mentee":
            mentee_lines.extend(_sentences(text))
        else:
            for sentence in _sentences(text):
                if _is_action(sentence):
                    mentor_actions.append(sentence)
                else:
                    mentor_points.append(sentence)

    # Key points: the mentee's own framing first (their words, their situation),
    # then a mentor thread or two. Never invented.
    key_points: list[str] = []
    if intent_summary:
        cleaned = _clean(intent_summary)
        if cleaned:
            key_points.append(cleaned)
    for line in mentee_lines[:2]:
        cleaned = _clean(line)
        if cleaned and cleaned.lower() not in {k.lower() for k in key_points}:
            key_points.append(cleaned)
    for line in mentor_points[:1]:
        cleaned = _clean(line)
        if cleaned:
            key_points.append(cleaned)
    key_points = _dedupe(key_points)[:_MAX_KEY_POINTS]

    # Action items: concrete imperative sentences the mentor suggested.
    action_items = _dedupe([_clean(a) for a in mentor_actions if _clean(a)])[
        :_MAX_ACTION_ITEMS
    ]

    # Caveats: always the honesty frame, plus a money note if the mentor pushed
    # spending, plus a note when a message was redacted.
    caveats: list[str] = list(_CAVEAT_VERBATIM)
    if money_stance == "pushes_to_spend":
        caveats.append(
            "this mentor leaned toward spending — verify any paid option "
            "independently before you commit"
        )
    if strikes > 0:
        caveats.append(
            f"{strikes} message(s) were removed for promotion or contact "
            "details; they are not reflected above"
        )
    caveats = _dedupe(caveats)[:_MAX_CAVEATS]

    return SessionSummary(
        key_points=key_points,
        action_items=action_items,
        caveats=caveats,
        source="fallback",
    )


def things_to_try(store: Store, intent_domains: list[str], text: str) -> list[SummaryThingToTry]:
    """2-3 catalogue entries to act on next (CORE_REALIGNMENT C3).

    Deterministic keyword match on the need's domains + text. Returns fewer than
    3 rather than padding with irrelevant entries; empty when nothing fits.
    """
    query = " ".join(intent_domains) + " " + text
    results = search_interests(list(_interests_from(store)), query=query.strip())
    picks: list[SummaryThingToTry] = []
    for _score, interest in results[:_THINGS_TO_TRY]:
        picks.append(
            SummaryThingToTry(
                slug=interest.slug,
                title=interest.title,
                short_description=interest.short_description,
                category=interest.category,
            )
        )
    return picks


def _interests_from(store: Store):
    """Load catalogue entries from the store, falling back to the seed corpus."""
    from .models import Interest

    docs = store.list(INTERESTS, limit=200)
    if not docs:
        from .catalogue import build_interests

        return build_interests()
    return [Interest.model_validate(d) for d in docs]


def _draft_with_gemini(
    client: GeminiClient,
    messages: list[SessionMessage],
    intent_summary: str | None,
) -> SessionSummary | None:
    """Live drafting via prompts/summary.md. Returns None so callers fall back."""
    convo = "\n".join(
        f"{m.sender_role}: {m.display_text}"
        for m in messages
        if m.action != "BLOCK_AND_REDACT" and m.display_text
    )
    result: GenerationResult = client.structured(
        "summary",
        {"conversation": convo, "intent": intent_summary or ""},
        SessionSummary,
    )
    if result.source != "gemini" or result.data is None:
        return None
    summary: SessionSummary = result.data
    summary.source = "gemini"
    # Re-scrub every produced line: a model must never be able to smuggle a
    # contact detail into the stored summary.
    summary.key_points = _dedupe([c for c in (_clean(k) for k in summary.key_points) if c])
    summary.action_items = _dedupe(
        [c for c in (_clean(a) for a in summary.action_items) if c]
    )[:_MAX_ACTION_ITEMS]
    summary.caveats = _dedupe([c for c in (_clean(c) for c in summary.caveats) if c])
    return summary


def generate_summary(
    store: Store,
    messages: list[SessionMessage],
    intent_summary: str | None,
    intent_domains: list[str],
    need_text: str,
    money_stance: str,
    strikes: int,
    gemini: GeminiClient | None = None,
) -> SessionSummary:
    """Produce the summary + things-to-try. `source` is honest about the path."""
    summary: SessionSummary | None = None
    if gemini is not None:
        summary = _draft_with_gemini(gemini, messages, intent_summary)
    if summary is None:
        summary = extract_summary(messages, intent_summary, money_stance, strikes)

    summary.things_to_try = things_to_try(store, intent_domains, need_text)
    return summary


__all__ = ["generate_summary", "extract_summary", "things_to_try"]
