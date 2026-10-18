"""Advice-core matching: intent interpretation, retrieval, and re-ranking.

Two hard rules run through this module (old spec section 13 / section 15):

1. **Never pretend a model ran.** Every result carries a `source` of
   ``"gemini"`` or ``"fallback"``/``"keyword"``. The deterministic path is the
   real, tested behaviour; the Gemini path activates only when a client is
   configured AND the call actually succeeds, and it still validates into the
   same schemas.
2. **Grounded explanations only.** A match explanation may reference ONLY fields
   present on that mentor's public card plus the mentee's own scrubbed intent.
   Nothing is invented — no hidden qualifications, no fabricated shared history.

The deterministic path is deliberately simple and legible: keyword-domain
overlap for retrieval, a transparent weighted fit score, and template-built
grounded explanations. It is a real matching function, not a stub.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel

from .gemini import GenerationResult, GeminiClient
from .models import (
    ClarifyingQuestion,
    DistressLevel,
    GoalType,
    Mentor,
    MentorMatch,
    MentorTrait,
    NeedIntent,
    RiskFlag,
    WatchOut,
)


class _RerankOrder(BaseModel):
    """Schema for the Gemini re-rank call: just an ordered list of candidate ids."""

    ordered_ids: list[str] = []

# --- Lexicons for deterministic interpretation -------------------------------
# Domain keywords map free-text signals to the same domain vocabulary the mentor
# corpus uses, so interpretation and retrieval share one controlled vocabulary.

_DOMAIN_LEXICON: dict[str, tuple[str, ...]] = {
    "software": ("code", "coding", "programming", "software", "developer",
                 "developer", "app", "website", "api", "backend", "frontend",
                 "engineer", "debug", "debugging", "tech", "stack"),
    "data": ("data", "analytics", "analyst", "machine learning", "ml", "model",
             "pipeline", "dataset", "statistics", "ai"),
    "design": ("design", "designer", "ux", "ui", "portfolio", "creative",
               "drawing", "writing", "writer"),
    "product": ("product", "pm", "prioriti", "roadmap", "stakeholder"),
    "people-management": ("manage", "manager", "management", "team", "lead",
                          "leading", "delegate", "delegat", "direct report"),
    "career": ("career", "job", "switch", "transition", "cv", "resume",
               "interview", "offer", "role", "promotion", "retrain"),
    "money": ("money", "salary", "pay", "price", "cost", "budget", "afford",
              "equity", "funding", "invest", "finance", "financial"),
    "business": ("business", "startup", "founder", "company", "freelance",
                 "self-employed", "client", "pricing"),
    "wellbeing": ("burnout", "burned out", "exhaust", "stress", "anxiety",
                  "overwork", "boundaries", "wellbeing", "wellness", "tired",
                  "meditat", "mindful", "racing mind", "breathing", "unwind",
                  "switch off", "decompress", "calm my", "quiet my mind"),
    "research": ("research", "phd", "academia", "academic", "publish", "study"),
    "education": ("teach", "teacher", "school", "student", "learn", "course",
                  "classroom"),
    "nonprofit": ("nonprofit", "non-profit", "charity", "ngo", "mission",
                  "volunteer"),
    "operations": ("operations", "logistics", "process", "supply chain"),
    "security": ("security", "secure", "breach", "privacy", "password",
                 "phishing"),
    "trades": ("trade", "plumb", "electric", "carpenter", "apprentice",
               "hands-on"),
}

_GOAL_LEXICON: dict[GoalType, tuple[str, ...]] = {
    "make_a_decision": ("should i", "decide", "decision", "choose", "choosing",
                        "or should", "torn between", "weigh"),
    "career_switch": ("switch", "change careers", "move into", "pivot",
                      "transition", "leave my", "break into"),
    "grow_in_role": ("grow", "level up", "get better", "senior", "advance",
                     "progress", "next step in"),
    "negotiate": ("negotiate", "negotiation", "ask for a raise", "counter",
                  "ask for more", "offer is"),
    "handle_setback": ("setback", "rejected", "failed", "fired", "laid off",
                       "redundan", "mistake", "lost the"),
    "avoid_pitfall": ("avoid", "pitfall", "risk of", "warn", "watch out",
                      "don't want to", "prevent"),
    "learn_skill": ("learn", "skill", "how do i get good", "teach myself",
                    "self-taught", "improve at"),
    "explore_options": ("explore", "curious", "wondering", "thinking about",
                        "possib"),
}

_TRAIT_LEXICON: dict[MentorTrait, tuple[str, ...]] = {
    "direct": ("direct", "blunt", "honest truth", "tell me straight"),
    "encouraging": ("encourag", "support", "confidence", "reassure"),
    "analytical": ("analyt", "break it down", "think through", "logic"),
    "blunt": ("blunt", "no sugar", "hard truth", "real talk"),
    "patient": ("patient", "slowly", "step by step", "beginner"),
    "structured": ("structured", "plan", "framework", "step-by-step", "roadmap"),
    "storyteller": ("example", "story", "experience", "case study"),
    "peer_level": ("peer", "similar age", "same stage", "recent"),
    "senior": ("senior", "experienced", "veteran", "long time"),
}

_DISTRESS_SIGNALS = {
    "high": ("can't go on", "cannot go on", "hopeless", "give up", "giving up",
             "despair", "crisis", "end it", "no point", "unbearable",
             "don't want to be here", "not want to be here"),
    "moderate": ("struggling", "dread", "breaking down", "falling apart",
                 "can't sleep", "cannot sleep", "insomnia", "miserable",
                 "exhaust", "burnt out", "burned out", "burnout",
                 "overwhelm", "can't cope", "cannot cope", "crying"),
    "mild": ("worried", "nervous", "stressed", "uneasy", "apprehensive",
             "anxious", "pressure", "uncertain"),
}

_RISK_LEXICON: dict[RiskFlag, tuple[str, ...]] = {
    "money_involved": ("money", "salary", "pay", "price", "cost", "invest",
                       "buy", "spend", "afford", "equity", "funding", "loan"),
    "urgency": ("urgent", "asap", "deadline", "tomorrow", "this week",
                "immediately", "quickly"),
    "health_related": ("health", "medical", "sick", "injury", "therapy",
                       "medication"),
    "legal_related": ("legal", "lawyer", "contract", "sue", "rights",
                      "termination"),
    "off_platform_request": ("whatsapp", "telegram", "dm me", "call me",
                             "meet offline", "phone number"),
    "financial_loss_imminent": ("about to lose", "losing everything", "debt",
                                "bankrupt", "can't pay", "overdue"),
}

_MONEY_WORDS = _RISK_LEXICON["money_involved"]

# Signals that should raise distress when someone shows money-loss urgency.
_LOSS_WORDS = _RISK_LEXICON["financial_loss_imminent"]


def _hits(text: str, lexicon: tuple[str, ...]) -> int:
    """Count lexicon keywords present in `text`.

    Short keywords (<= 3 chars, e.g. "ai", "ml", "ux") require a word-boundary
    match so they cannot fire inside unrelated longer words ("unrelated" must
    not count as "ai").
    """
    total = 0
    for word in lexicon:
        if len(word) <= 3:
            if re.search(rf"\b{re.escape(word)}\b", text):
                total += 1
        elif word in text:
            total += 1
    return total


def _domains_in(text: str) -> list[str]:
    scored = [
        (domain, _hits(text, words))
        for domain, words in _DOMAIN_LEXICON.items()
    ]
    return [d for d, n in scored if n > 0]


def _goal_in(text: str) -> GoalType:
    best: GoalType = "explore_options"
    best_n = 0
    for goal, words in _GOAL_LEXICON.items():
        n = _hits(text, words)
        if n > best_n:
            best, best_n = goal, n
    return best


def _traits_in(text: str) -> list[MentorTrait]:
    return [t for t, words in _TRAIT_LEXICON.items() if _hits(text, words) > 0]


def _distress_in(text: str) -> DistressLevel:
    for level in ("high", "moderate", "mild"):
        if _hits(text, _DISTRESS_SIGNALS[level]) > 0:
            return level  # type: ignore[return-value]
    return "none"


def detect_distress(text: str) -> DistressLevel:
    """Public wrapper: distress level for a scrubbed message.

    Shared by the need interpreter (matching) and the Guardian's safety flags so
    both layers read distress from ONE lexicon — a message flagged as distressing
    when describing a need reads the same when it appears mid-session.
    """
    return _distress_in(text)


def _risks_in(text: str, money_flag: bool) -> list[RiskFlag]:
    flags = [r for r, words in _RISK_LEXICON.items() if _hits(text, words) > 0]
    if money_flag and "money_involved" not in flags:
        flags.append("money_involved")
    if "financial_loss_imminent" in flags and "money_involved" not in flags:
        flags.append("money_involved")
    return flags


def _summary_from(text: str) -> str:
    """First sentence of the scrubbed text, trimmed — never invented content."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    first = re.split(r"(?<=[.!?])\s", cleaned)[0].strip()
    if len(first) > 220:
        first = first[:217].rstrip() + "..."
    return first or cleaned[:220]


def interpret_need(
    scrubbed_text: str,
    *,
    language: str = "en",
    category: str | None = None,
    money_involved: bool = False,
) -> tuple[NeedIntent, list[ClarifyingQuestion]]:
    """Deterministic interpretation of a scrubbed need.

    This is the real fallback path. It shares the mentor corpus's domain
    vocabulary, so interpretation and retrieval stay consistent.
    """
    text = scrubbed_text.lower()
    domains = _domains_in(text)
    if category and category not in domains:
        domains.append(category)

    goal = _goal_in(text)
    traits = _traits_in(text)
    distress = _distress_in(text)
    risks = _risks_in(text, money_involved)

    money = money_involved or "money_involved" in risks
    decision_pending = goal in ("make_a_decision", "negotiate") or any(
        q in text for q in ("should i", "decide", "choose", "torn")
    )

    intent = NeedIntent(
        short_summary=_summary_from(scrubbed_text),
        domains=domains,
        goal_type=goal,
        decision_pending=decision_pending,
        money_involved=money,
        preferred_mentor_traits=traits,
        language=language,
        distress_level=distress,
        risk_flags=risks,
    )
    return intent, clarifying_questions(intent)


def clarifying_questions(intent: NeedIntent) -> list[ClarifyingQuestion]:
    """A few targeted questions, derived only from the interpreted intent."""
    questions: list[ClarifyingQuestion] = []
    if not intent.domains:
        questions.append(ClarifyingQuestion(
            question="Which area does this mostly touch — career, money, "
                     "technical work, or wellbeing?",
            why="I could not tell from what you wrote, and the area changes who "
                "would be useful.",
        ))
    if intent.goal_type == "make_a_decision" and not intent.decision_pending:
        questions.append(ClarifyingQuestion(
            question="Is there a specific decision with a deadline, or are you "
                     "thinking ahead?",
            why="A real deadline changes whether you need a quick gut-check or a "
                "slower exploration.",
        ))
    if intent.money_involved:
        questions.append(ClarifyingQuestion(
            question="Is this about money you already have, money you might "
                     "spend, or money you hope to earn?",
            why="Those are different conversations, and I want to point you at the "
                "right kind of thinking.",
        ))
    if len(intent.domains) > 2:
        questions.append(ClarifyingQuestion(
            question="If you had to pick just one of these to focus on first, "
                     "which would it be?",
            why="A focused question gets you a sharper match than a broad one.",
        ))
    return questions


# --- Gemini interpretation path ---------------------------------------------


def _interpret_with_gemini(
    client: GeminiClient, scrubbed_text: str, language: str, money_involved: bool
) -> tuple[NeedIntent, list[ClarifyingQuestion]] | None:
    """Live interpretation. Returns None so callers fall back when unavailable."""
    result: GenerationResult = client.structured(
        "intent",
        {"text": scrubbed_text, "language": language,
         "money_involved": str(money_involved).lower()},
        NeedIntent,
    )
    if result.source != "gemini" or result.data is None:
        return None
    intent = result.data
    return intent, clarifying_questions(intent)


# --- Retrieval & re-ranking --------------------------------------------------


@dataclass
class _Scored:
    mentor: Mentor
    fit: float
    match_type: str
    shared_domains: list[str]
    shared_topics: list[str]


def _norm(word: str) -> str:
    """Light stemmer so 'negotiate'/'negotiating'/'offers' compare equal."""
    w = word.lower().strip(".,;:!?\"'()[]")
    for suffix in ("ing", "ed", "es", "s"):
        if len(w) > len(suffix) + 2 and w.endswith(suffix):
            return w[: -len(suffix)]
    return w


def _tokens(text: str) -> set[str]:
    return {_norm(w) for w in re.findall(r"[a-z][a-z-]+", text.lower())}


# Words too generic to count as a topic match on either side.
_STOPWORDS = frozenset({
    "a", "an", "the", "to", "of", "in", "on", "for", "and", "or", "my", "i",
    "me", "you", "it", "is", "at", "as", "be", "do", "so", "we", "up", "out",
    "with", "from", "into", "about", "that", "this", "what", "how", "when",
    "any", "some", "something", "list", "listed", "domain", "overall",
})


def _topic_overlap(a: list[str], b: list[str]) -> list[str]:
    """Return entries of `a` (the mentor's offered topics) that share a meaningful
    stemmed keyword with any entry of `b` (the mentee's situation).

    Only entries of `a` are ever returned, so an explanation can only ever cite a
    topic the mentor actually offers. Stop words are ignored on both sides so a
    generic "to"/"any" cannot manufacture a match.
    """
    shared: list[str] = []
    b_words = {w for item in b for w in _tokens(item)} - _STOPWORDS
    for topic in a:
        topic_words = _tokens(topic) - _STOPWORDS
        if topic_words & b_words:
            shared.append(topic)
    return shared


def _fit(mentor: Mentor, intent: NeedIntent, scrubbed_text: str) -> _Scored | None:
    """Transparent weighted fit score. Deterministic, testable, non-saturating.

    Weights (they sum to <= 1.0 so scores stay spread out and comparable):
      - domain overlap   0.34  (how much of the mentee's domains the mentor covers)
      - topic overlap    0.40  (their listed topics vs the situation text)
      - goal/trait fit   0.16  (specific goal-type signals)
      - language comfort 0.10  (shared language, so cross-language is a real caveat)
    """
    card = mentor.public_card
    intent_domains = set(intent.domains)
    mentor_domains = set(card.domains)
    shared_domains = sorted(intent_domains & mentor_domains)

    topic_pool = intent.domains + [intent.short_summary]
    shared_topics = _topic_overlap(card.topics_offered, topic_pool) + \
        _topic_overlap(card.topics_offered, [scrubbed_text])
    shared_topics = sorted(set(shared_topics))

    if not shared_domains and not shared_topics:
        return None

    # Domain coverage: fraction of the mentee's domains this mentor actually has.
    domain_score = 0.34 * (len(shared_domains) / max(1, len(intent_domains)))

    # Topic relevance: reward each distinct listed topic that touches the text,
    # with diminishing returns so a long bio cannot runaway-win.
    topic_score = 0.40 * (1 - 0.7 ** len(shared_topics)) if shared_topics else 0.0

    # Goal / trait alignment.
    offered = " ".join(card.topics_offered).lower()
    goal_bonus = 0.0
    if intent.goal_type == "negotiate" and "negotiat" in offered:
        goal_bonus += 0.09
    if intent.goal_type == "career_switch" and any(
        k in offered for k in ("career", "switch", "transition", "chang")
    ):
        goal_bonus += 0.09
    if intent.goal_type == "handle_setback" and any(
        k in offered for k in ("boundar", "burnout", "conflict", "setback", "recover")
    ):
        goal_bonus += 0.09
    if intent.goal_type == "learn_skill" and any(
        k in offered for k in ("learn", "skill", "first", "break into", "starter")
    ):
        goal_bonus += 0.09
    if intent.goal_type == "avoid_pitfall" and any(
        k in offered for k in ("avoid", "pitfall", "honest", "reality", "without")
    ):
        goal_bonus += 0.09
    if intent.money_involved and "money" in mentor_domains:
        goal_bonus += 0.05
    goal_score = 0.16 * min(1.0, goal_bonus / 0.09) if goal_bonus else 0.0

    # Shared language so a cross-language match is honestly reflected in fit.
    lang_score = 0.10 if intent.language in card.languages else 0.0

    fit = min(1.0, domain_score + topic_score + goal_score + lang_score)
    match_type = "DIRECT" if shared_domains else "CROSS_DOMAIN"
    return _Scored(
        mentor=mentor, fit=round(fit, 3), match_type=match_type,
        shared_domains=shared_domains, shared_topics=shared_topics,
    )


def _explanation(scored: _Scored, intent: NeedIntent) -> str:
    """Grounded only in the public card + the mentee's own intent."""
    card = scored.mentor.public_card
    parts: list[str] = []
    if scored.shared_domains:
        parts.append(
            f"They work across {', '.join(scored.shared_domains)}, which is where "
            f"your situation sits."
        )
    if scored.shared_topics:
        parts.append(
            "They specifically list " + "; ".join(scored.shared_topics[:3]) + "."
        )
    if scored.match_type == "CROSS_DOMAIN":
        parts.append(
            f"They are not in your exact field, but {', '.join(card.domains)} "
            "often transfers to your situation."
        )
    parts.append(
        f"They have {card.seniority_band.split(' ')[0]} of experience as a "
        f"{card.role_band.lower()}."
    )
    return " ".join(parts)


def _cross_domain_value(scored: _Scored) -> str | None:
    if scored.match_type != "CROSS_DOMAIN":
        return None
    card_domains = scored.mentor.public_card.domains
    return (
        f"A perspective from {', '.join(card_domains)} can surface options you "
        "would not see from inside your own field."
    )


def _watch_outs(scored: _Scored, intent: NeedIntent) -> list[WatchOut]:
    outs: list[WatchOut] = []
    card = scored.mentor.public_card
    if intent.language and intent.language not in card.languages:
        outs.append(WatchOut(
            note=f"They do not list {intent.language} among "
                 f"{', '.join(card.languages)}; consider a shared language."
        ))
    if scored.match_type == "CROSS_DOMAIN":
        outs.append(WatchOut(
            note="They are a cross-domain match, so their specific context may "
                 "differ from yours."
        ))
    if scored.mentor.stats.pitch_flags_total > 0:
        outs.append(WatchOut(
            note="Simulated profile: a small number of past sessions were flagged "
                 "for promotional tone."
        ))
    return outs


_STARTER_BY_GOAL: dict[GoalType, tuple[str, ...]] = {
    "make_a_decision": (
        "What would you need to see to feel OK choosing one way?",
        "What's the cost of deciding wrong here, honestly?",
        "Is there a small way to test one option before committing?",
    ),
    "career_switch": (
        "What's pulling you toward the new direction?",
        "What have you already tried to test the change cheaply?",
        "What's the biggest thing you'd be leaving behind?",
    ),
    "negotiate": (
        "What outcome would you be genuinely happy with?",
        "What's your alternative if the answer is no?",
        "Have you rehearsed saying the number out loud yet?",
    ),
    "handle_setback": (
        "What happened, in your own words?",
        "What do you think the setback actually says about you — and does it?",
        "What would a good next week look like from here?",
    ),
    "avoid_pitfall": (
        "What's the pitfall you're most worried about?",
        "Who told you it was a risk, and do you trust their read?",
        "What would a safe version of this look like?",
    ),
    "learn_skill": (
        "How do you learn best — by doing, reading, or being shown?",
        "What have you already tried, and where did you stall?",
        "What would 'good enough' look like in three months?",
    ),
    "grow_in_role": (
        "What does the next level actually look like in your workplace?",
        "Where do you feel most stuck right now?",
        "What feedback have you already had about your growth?",
    ),
    "explore_options": (
        "What made you start thinking about this?",
        "If nothing were scary, what would you try first?",
        "What's the smallest next step you could take this week?",
    ),
}


def _starter_questions(scored: _Scored, intent: NeedIntent) -> list[str]:
    base = list(_STARTER_BY_GOAL.get(intent.goal_type, _STARTER_BY_GOAL["explore_options"]))
    topic = scored.shared_topics[0] if scored.shared_topics else None
    if topic:
        base.insert(0, f"When you think about \"{topic}\", what feels hardest right now?")
    return base[:3]


def _to_match(scored: _Scored, intent: NeedIntent) -> MentorMatch:
    return MentorMatch(
        mentor=scored.mentor.to_card(),
        fit_score=scored.fit,
        match_type=scored.match_type,  # type: ignore[arg-type]
        explanation=_explanation(scored, intent),
        cross_domain_value=_cross_domain_value(scored),
        watch_outs=_watch_outs(scored, intent),
        starter_questions=_starter_questions(scored, intent),
    )


def match_mentors(
    mentors: list[Mentor],
    intent: NeedIntent,
    scrubbed_text: str,
    *,
    top_n: int = 3,
    min_fit: float = 0.12,
    gemini: GeminiClient | None = None,
) -> tuple[list[MentorMatch], bool, str]:
    """Retrieve, score, and return up to `top_n` grounded matches.

    Returns ``(matches, no_strong_match, source)``. `source` is ``"gemini"``
    only if a live re-rank actually produced the ordering; otherwise
    ``"keyword"``.
    """
    scored = [s for s in (_fit(m, intent, scrubbed_text) for m in mentors) if s]
    scored.sort(key=lambda s: (-s.fit, s.mentor.id))

    source = "keyword"
    if gemini is not None and scored:
        reranked = _gemini_rerank(gemini, intent, scored)
        if reranked is not None:
            scored = reranked
            source = "gemini"

    strong = [s for s in scored if s.fit >= min_fit][:top_n]
    no_strong_match = not strong
    if no_strong_match:
        # Still surface the nearest candidates, but flag honestly that nothing
        # was a confident match rather than pretending these are good fits.
        strong = scored[:top_n]

    matches = [_to_match(s, intent) for s in strong]
    return matches, no_strong_match, source


def _gemini_rerank(
    client: GeminiClient, intent: NeedIntent, scored: list[_Scored]
) -> list[_Scored] | None:
    """Ask Gemini to re-rank candidates; validate IDs against the candidate set.

    Any unknown ID returned by the model is dropped (old spec section 7:
    "Validate every returned mentor ID against the retrieved candidates").
    Returns None to keep the deterministic order when unavailable.
    """
    candidate_ids = [s.mentor.id for s in scored[:10]]
    by_id = {s.mentor.id: s for s in scored}
    result: GenerationResult = client.structured(
        "rerank",
        {
            "goal": intent.goal_type,
            "summary": intent.short_summary,
            "candidates": ",".join(candidate_ids),
        },
        _RerankOrder,
    )
    if result.source != "gemini" or result.data is None:
        return None
    order = result.data.ordered_ids
    if not order:
        return None
    reranked: list[_Scored] = []
    for mid in order:
        if mid in by_id and by_id[mid] not in reranked:
            reranked.append(by_id[mid])
    # Append any candidates the model did not mention, preserving their order.
    for s in scored:
        if s not in reranked:
            reranked.append(s)
    return reranked or None


__all__ = ["interpret_need", "match_mentors", "clarifying_questions"]
