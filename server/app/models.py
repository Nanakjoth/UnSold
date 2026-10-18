"""Shared API models: error envelope, user session, and catalogue types.

Only schemas needed by the current stage live here (spec section 5: no empty
modules for services that have not been implemented).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator

LanguageCode = re.compile(r"^[a-z]{2}(-[A-Z]{2})?$")
Slug = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- Error envelope ----------------------------------------------------------


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


# --- User session ------------------------------------------------------------


class AppUser(BaseModel):
    """Server-side user record. `uid` comes from the verified auth token only."""

    uid: str
    pseudonym: str
    language: str = "en"
    is_synthetic: bool = False
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class SessionResponse(BaseModel):
    uid: str
    pseudonym: str
    language: str
    is_synthetic: bool
    created_at: str


class SessionUpdate(BaseModel):
    language: str | None = None

    @field_validator("language")
    @classmethod
    def _valid_language(cls, value: str | None) -> str | None:
        if value is not None and not LanguageCode.match(value):
            raise ValueError("language must look like 'en' or 'en-GB'")
        return value


class DeleteSummary(BaseModel):
    deleted: dict[str, int]
    total: int


# --- Interest catalogue ------------------------------------------------------
#
# Spec section 8: the catalogue is structured for both people and models.
# Relationship edges are stored in a separate `interest_relationships`
# collection (explicit and reviewable) AND embedded as a compact outgoing list
# on each interest document so the detail route can expand them in one read.

InterestDifficulty = Literal["beginner", "intermediate"]
SoloOrGroup = Literal["solo", "group"]
OnlineOrInPerson = Literal["online", "in_person"]

RELATIONSHIP_TYPES = (
    "shares_material",
    "shares_technique",
    "shares_skill",
    "shares_way_of_thinking",
    "related_culture_or_context",
    "complementary_activity",
    "prerequisite_for",
    "contrasts_with",
)

RelationshipType = Literal[
    "shares_material",
    "shares_technique",
    "shares_skill",
    "shares_way_of_thinking",
    "related_culture_or_context",
    "complementary_activity",
    "prerequisite_for",
    "contrasts_with",
]


class RelationshipEdge(BaseModel):
    """One explicit, reviewable link between two catalogue entries."""

    from_slug: str
    to_slug: str
    type: RelationshipType
    note: str | None = None


class EmbeddedEdge(BaseModel):
    """Compact outgoing edge as embedded on an interest document."""

    to_slug: str
    type: RelationshipType
    note: str | None = None


class Interest(BaseModel):
    """Full catalogue entry (spec section 8 schema)."""

    id: str
    slug: str
    title: str
    short_description: str
    long_description: str
    category: str
    tags: list[str]
    skills: list[str]
    materials: list[str]
    ways_of_thinking: list[str]
    beginner_step: str
    time_commitment: str | None = None
    difficulty: InterestDifficulty | None = None
    accessibility_notes: list[str]
    solo_or_group: list[SoloOrGroup]
    online_or_in_person: list[OnlineOrInPerson]
    languages: list[str]
    relationship_edges: list[EmbeddedEdge]
    source_notes: str | None = None
    is_sample_content: bool = True
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

    @field_validator("slug")
    @classmethod
    def _valid_slug(cls, value: str) -> str:
        if not Slug.match(value):
            raise ValueError("slug must be lowercase words separated by single hyphens")
        return value

    def to_card(self) -> "InterestCard":
        return InterestCard(
            id=self.id,
            slug=self.slug,
            title=self.title,
            short_description=self.short_description,
            category=self.category,
            tags=self.tags,
            time_commitment=self.time_commitment,
            difficulty=self.difficulty,
            solo_or_group=self.solo_or_group,
            online_or_in_person=self.online_or_in_person,
            is_sample_content=self.is_sample_content,
        )


class InterestCard(BaseModel):
    """Public card projection used in lists, search results, and sections."""

    id: str
    slug: str
    title: str
    short_description: str
    category: str
    tags: list[str]
    time_commitment: str | None = None
    difficulty: InterestDifficulty | None = None
    solo_or_group: list[SoloOrGroup]
    online_or_in_person: list[OnlineOrInPerson]
    is_sample_content: bool = True


class RelatedInterest(BaseModel):
    """An expanded relationship on an interest detail response."""

    type: RelationshipType
    note: str | None = None
    interest: InterestCard


class InterestDetail(Interest):
    related: list[RelatedInterest] = []


class InterestListResponse(BaseModel):
    items: list[InterestCard]
    total: int
    limit: int
    offset: int
    # Honesty label (spec section 13): keyword search runs locally; AI-enhanced
    # intent search replaces this only when a model is configured and live.
    search_source: Literal["keyword"] = "keyword"
    ai_search_available: bool = False


class CategoryCount(BaseModel):
    category: str
    count: int


class CategoryListResponse(BaseModel):
    items: list[CategoryCount]


# --- Saved interests & discovery feedback ------------------------------------


class SavedInterest(BaseModel):
    user_id: str
    interest_id: str
    interest_slug: str
    created_at: str = Field(default_factory=utc_now_iso)


class SavedListResponse(BaseModel):
    items: list[InterestCard]
    total: int


FeedbackAction = Literal["save", "dismiss", "already_know", "want_to_try"]
FeedbackReason = Literal["too_similar", "not_relevant", "not_accessible"]


class DiscoveryFeedback(BaseModel):
    user_id: str
    interest_id: str
    interest_slug: str
    action: FeedbackAction
    reason: FeedbackReason | None = None
    created_at: str = Field(default_factory=utc_now_iso)


class FeedbackCreate(BaseModel):
    interest_slug: str
    action: FeedbackAction
    reason: FeedbackReason | None = None

    @field_validator("interest_slug")
    @classmethod
    def _valid_slug(cls, value: str) -> str:
        if not Slug.match(value):
            raise ValueError("interest_slug must be a catalogue slug")
        return value


class FeedbackResponse(BaseModel):
    """Confirmation plus the agreement share of other members.

    `agreement` is computed only from persisted feedback on the same interest
    and is labelled as simulated sample data until real members exist.
    """

    interest_slug: str
    action: FeedbackAction
    agreement: AgreementSummary | None = None


class AgreementSummary(BaseModel):
    """Share of recorded (non-unsure) feedback matching the caller's action."""

    share_matching: float
    sample_size: int
    label: str = "Simulated sample feedback"


# --- Advice core: mentors ----------------------------------------------------
#
# Rebuilt advice/mentorship models (see docs/DECISIONS.md re-scope). The public
# card is the ONLY mentor projection exposed by the API; `private` and `stats`
# internals never leave the server (old spec section 7: "private fields must
# never be sent in the public-card API").

ExperienceBand = Literal[
    "5-10 years", "10-15 years", "15-20 years", "20+ years"
]
MatchType = Literal["DIRECT", "CROSS_DOMAIN"]


class MentorPublicCard(BaseModel):
    """Everything a mentee may see about a mentor. No identity, no contact."""

    role_band: str
    seniority_band: ExperienceBand
    domains: list[str]
    industries: list[str] = []
    languages: list[str]
    country_code: str
    topics_offered: list[str]
    bio_public: str
    slot_lengths_min: list[int]


class MentorStats(BaseModel):
    """Private quality counters. Shown only as labelled, sampled aggregates."""

    sessions_completed: int = 0
    avg_helpfulness: float | None = None
    pitch_flags_total: int = 0
    pitch_free_streak: int = 0
    minutes_given: int = 0
    quality_score: float = 0.5


class Mentor(BaseModel):
    """A synthetic mentor record (old spec section 7 `mentors/{id}`)."""

    id: str
    pseudonym: str
    is_synthetic: bool = True
    public_card: MentorPublicCard
    stats: MentorStats = Field(default_factory=MentorStats)
    created_at: str = Field(default_factory=utc_now_iso)

    def to_card(self) -> "MentorCard":
        return MentorCard(
            id=self.id,
            pseudonym=self.pseudonym,
            is_synthetic=self.is_synthetic,
            public_card=self.public_card,
        )


class MentorCard(BaseModel):
    """Public mentor projection for lists and matches."""

    id: str
    pseudonym: str
    is_synthetic: bool = True
    public_card: MentorPublicCard


class MentorListResponse(BaseModel):
    items: list[MentorCard]
    total: int
    # Honesty label: local keyword retrieval now; "gemini" only when a live
    # embedding + re-rank path actually ran (old spec section 13).
    retrieval_source: Literal["keyword", "gemini"] = "keyword"


# --- Advice core: needs & intent ---------------------------------------------

GoalType = Literal[
    "explore_options", "make_a_decision", "career_switch", "grow_in_role",
    "negotiate", "handle_setback", "avoid_pitfall", "learn_skill",
]
DistressLevel = Literal["none", "mild", "moderate", "high"]
RiskFlag = Literal[
    "money_involved", "urgency", "health_related", "legal_related",
    "off_platform_request", "financial_loss_imminent",
]
MentorTrait = Literal[
    "direct", "encouraging", "analytical", "blunt", "patient",
    "structured", "storyteller", "peer_level", "senior",
]


class NeedIntent(BaseModel):
    """Structured interpretation of a scrubbed need (old spec section 7).

    Contains no direct identifiers by construction: domains, goal type, and
    flags only. The summary is derived from the scrubbed text.
    """

    short_summary: str
    domains: list[str] = []
    goal_type: GoalType = "explore_options"
    decision_pending: bool = False
    money_involved: bool = False
    preferred_mentor_traits: list[MentorTrait] = []
    language: str = "en"
    distress_level: DistressLevel = "none"
    risk_flags: list[RiskFlag] = []


class ClarifyingQuestion(BaseModel):
    """A suggested question the mentee may answer to sharpen the match."""

    question: str
    why: str


class NeedInterpretation(BaseModel):
    """The editable interpretation shown before matching (journey step 2)."""

    summary: str
    intent: NeedIntent
    clarifying_questions: list[ClarifyingQuestion] = []
    # Honesty label: "gemini" when a live model produced this, "fallback" for
    # the deterministic local interpretation (old spec section 13).
    interpretation_source: Literal["gemini", "fallback"] = "fallback"


class NeedCreate(BaseModel):
    """Incoming request to interpret a free-text situation."""

    text: str = Field(min_length=20)
    category: str | None = None
    language: str = "en"
    money_involved: bool = False

    @field_validator("language")
    @classmethod
    def _valid_language(cls, value: str) -> str:
        if not LanguageCode.match(value):
            raise ValueError("language must look like 'en' or 'en-GB'")
        return value


class Need(BaseModel):
    """Persisted need: scrubbed text + interpretation + provenance."""

    id: str
    user_id: str
    text_scrubbed: str
    category: str | None = None
    interpretation: NeedInterpretation
    no_strong_match: bool = False
    is_synthetic: bool = True
    created_at: str = Field(default_factory=utc_now_iso)


# --- Advice core: matches ----------------------------------------------------


class WatchOut(BaseModel):
    """A grounded caveat about one match, derived only from the public card."""

    note: str


class MentorMatch(BaseModel):
    """One candidate match with a grounded, card-only explanation."""

    mentor: MentorCard
    fit_score: float
    match_type: MatchType
    explanation: str
    cross_domain_value: str | None = None
    watch_outs: list[WatchOut] = []
    starter_questions: list[str] = []


class NeedMatchesResponse(BaseModel):
    """Result of retrieval + re-ranking for one need."""

    need_id: str
    interpretation: NeedInterpretation
    matches: list[MentorMatch]
    no_strong_match: bool = False
    # Honesty label: which retrieval/re-rank path actually ran.
    retrieval_source: Literal["keyword", "gemini"] = "keyword"
    notice: str | None = None


# --- Stage A2: Guardian, Friend Test, sessions -------------------------------
#
# The Guardian is the product's main differentiator (unsold_product_spec.md
# section 10.5): it screens every message in both directions for sales pitches,
# contact solicitation, urgency/fear, soft steering and affiliate referrals.
# The ACTION is always decided by deterministic code in `guardian.py` — never by
# the model. A classifier only proposes a category/severity; code decides.

GuardianCategory = Literal[
    "NONE",
    "DIRECT_PROMO",
    "CONTACT_SOLICIT",
    "URGENCY_FEAR",
    "SOFT_STEERING",
    "AFFILIATE_REFERRAL",
]
GuardianAction = Literal["ALLOW", "WARN", "BLOCK_AND_REDACT"]
MoneyStance = Literal[
    "n/a", "pushes_to_spend", "neutral", "cautions_against_spending"
]


class GuardianSafety(BaseModel):
    """Distress/safety flags surfaced alongside a classification (both roles).

    `distress` uses the SAME `DistressLevel` as the need interpreter so a message
    flagged mid-session reads identically to one flagged when describing a need.
    """

    distress: DistressLevel = "none"
    risk_flags: list[str] = []


class GuardianVerdict(BaseModel):
    """The Guardian's decision on one message.

    `source` is honest: "gemini" only when a live classifier produced the
    category; "rules"/"fallback" for the deterministic paths. The ACTION is
    applied by code afterward and is never model-authored.
    """

    is_pitch: bool = False
    category: GuardianCategory = "NONE"
    severity: int = Field(default=0, ge=0, le=3)
    evidence_span: str = ""
    reason: str = ""
    money_stance: MoneyStance = "n/a"
    rule_hits: list[str] = []
    safety: GuardianSafety = Field(default_factory=GuardianSafety)
    source: Literal["gemini", "rules", "fallback"] = "rules"


class GuardianDecision(BaseModel):
    """Deterministic action + strike bookkeeping applied to a verdict.

    Produced by `guardian.decide()`, never by a model.
    """

    action: GuardianAction
    final_severity: int = Field(ge=0, le=3)
    strike_incurred: bool = False
    ends_session: bool = False
    # What the recipient actually sees after redaction, when applicable.
    display_text: str
    # Tag shown to the recipient on a WARN (spec: "Possible promotion").
    tag: str | None = None


class GuardianSummary(BaseModel):
    """Running per-session Guardian counters (never message text)."""

    messages_checked: int = 0
    max_severity: int = 0
    strikes: int = 0
    pitches_flagged: int = 0


# --- Stage A2: sessions ------------------------------------------------------


SessionStatus = Literal["REQUESTED", "ACTIVE", "ENDED", "CANCELLED"]
SenderRole = Literal["mentee", "mentor"]


class RevealState(BaseModel):
    """Mutual-consent reveal machine (spec section 8).

    `NONE -> ONE_SIDED -> REVEALED`. Either side may withdraw consent BEFORE the
    state reaches REVEALED; once both have consented the contacts are treated as
    shared and the state is locked (with `revealed_at` recorded).

    The reveal exposes only each side's optional contact + chosen display name
    (their pseudonym) — never a real identity. The mentor side is synthetic in
    this prototype, so mentor consent is simulated and honestly labelled.
    """

    mentee_consent: bool = False
    mentor_consent: bool = False
    revealed_at: str | None = None
    # Optional contact each side agrees to share on reveal. Scrubbed before
    # storage — a raw email/phone never lands here.
    mentee_contact: str | None = None
    mentor_contact: str | None = None

    @property
    def revealed(self) -> bool:
        return self.mentee_consent and self.mentor_consent

    @property
    def state(self) -> str:
        if self.revealed:
            return "REVEALED"
        if self.mentee_consent or self.mentor_consent:
            return "ONE_SIDED"
        return "NONE"


class SessionMessage(BaseModel):
    """One chat message after scrubbing + Guardian screening.

    `text_scrubbed` is what was stored (never raw PII). `display_text` is what
    the recipient sees — it differs when the Guardian redacted the message.
    `seq` gives a stable per-session ordering (timestamps are second-resolution).
    """

    id: str
    session_id: str
    seq: int = 0
    sender_role: SenderRole
    text_scrubbed: str
    display_text: str
    is_simulated: bool = False
    guardian: GuardianVerdict
    action: GuardianAction
    created_at: str = Field(default_factory=utc_now_iso)


class Session(BaseModel):
    """A short mentorship session between one mentee and one mentor."""

    id: str
    mentee_id: str
    mentor_id: str
    mentor_pseudonym: str
    need_id: str | None = None
    intent_summary: str | None = None
    status: SessionStatus = "ACTIVE"
    money_involved: bool = False
    guardian: GuardianSummary = Field(default_factory=GuardianSummary)
    money_stance: MoneyStance = "n/a"
    reveal: RevealState = Field(default_factory=RevealState)
    # Editable mentee-facing summary, produced when the session ends (A3).
    summary: "SessionSummary | None" = None
    is_synthetic: bool = True
    created_at: str = Field(default_factory=utc_now_iso)
    ended_at: str | None = None


class SessionCreate(BaseModel):
    mentor_id: str
    need_id: str | None = None


class MessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class SessionMessageResponse(BaseModel):
    """What the sender gets back: their message + the Guardian's decision."""

    message: SessionMessage
    guardian: GuardianDecision


class SessionListResponse(BaseModel):
    items: list[Session]
    total: int


class MessageListResponse(BaseModel):
    items: list[SessionMessage]
    total: int


# --- Stage A2: Friend Test ---------------------------------------------------


class FriendTestResult(BaseModel):
    """Did the mentor caution against spending, stay neutral, or push to spend?

    Only meaningful when the mentee's need involved money. The session value is
    the latest non-"n/a" stance, with `pushes_to_spend` taking priority if it
    ever occurred (spec section 10.6).
    """

    applicable: bool
    stance: MoneyStance = "n/a"
    label: str
    # Honesty: while every mentor is synthetic this is a simulated result.
    is_simulated: bool = True


# --- Stage A3: reveal, summary, feedback, metrics ---------------------------
#
# Release 1 of the advice core. Reveal is a mutual-consent state machine
# (spec section 8): NONE -> ONE_SIDED -> REVEALED, withdrawable before REVEALED.
# The summary is a mentee-only, editable digest of a finished session (spec
# section 10.8) with concrete next steps, including catalogue "things to try"
# (CORE_REALIGNMENT C3). Feedback updates mentor quality honestly (spec section
# 10.11) and powers the Guardian-vs-mentee agreement metric.

RevealStateName = Literal["NONE", "ONE_SIDED", "REVEALED"]


class RevealRequest(BaseModel):
    """One side's consent decision. `consent=False` withdraws (before REVEALED)."""

    consent: bool
    # Optional contact to share if/when the reveal completes. Scrubbed server-side.
    contact_optional: str | None = Field(default=None, max_length=200)


class RevealContact(BaseModel):
    """What a side exposes once REVEALED — a display name and optional contact.

    Never a real identity. The display name is the pseudonym; the contact is
    whatever the person chose to share, already scrubbed.
    """

    role: SenderRole
    display_name: str
    contact_optional: str | None = None
    is_simulated: bool = False


class RevealResponse(BaseModel):
    """Current reveal state plus contacts when (and only when) REVEALED."""

    state: RevealStateName
    revealed: bool
    contacts: list[RevealContact] = []
    notice: str | None = None


class SummaryThingToTry(BaseModel):
    """A small catalogue suggestion surfaced in the summary (CORE_REALIGNMENT C3)."""

    slug: str
    title: str
    short_description: str
    category: str


class SessionSummary(BaseModel):
    """Editable mentee-only digest of a finished session (spec section 10.8).

    `action_items` is capped at 5 concrete steps. `caveats` notes what the
    mentor could not know / what to verify. `key_points` are the discussion's
    main threads. Nothing here may contain contact details or redacted
    promotions — it is generated from scrubbed, displayed messages only.
    """

    key_points: list[str] = []
    action_items: list[str] = []
    caveats: list[str] = []
    # CORE_REALIGNMENT C3: 2-3 catalogue entries as "something small to try".
    things_to_try: list[SummaryThingToTry] = []
    # Honesty: "gemini" only when a live model drafted it, "fallback" otherwise.
    source: Literal["gemini", "fallback"] = "fallback"
    # True once the mentee has edited/saved; a regenerated draft won't clobber it.
    edited: bool = False


class SummaryUpdate(BaseModel):
    """Mentee's edits to a generated summary. Any subset may be provided."""

    key_points: list[str] | None = None
    action_items: list[str] | None = None
    caveats: list[str] | None = None


# --- Feedback (spec sections 7, 10.11) --------------------------------------

FeltPitched = Literal["yes", "no", "unsure"]


class MenteeFeedback(BaseModel):
    """What the mentee reports about a finished session."""

    helpfulness_1_5: int = Field(ge=1, le=5)
    felt_pitched: FeltPitched
    would_recommend: bool
    free_text: str | None = Field(default=None, max_length=2000)


class MentorFeedback(BaseModel):
    """What a mentor reports about a session (simulated in this prototype)."""

    mentee_seriousness_1_5: int = Field(ge=1, le=5)
    respectful: bool
    free_text: str | None = Field(default=None, max_length=2000)


class SessionFeedbackCreate(BaseModel):
    """Role-tagged feedback body. Exactly one of mentee/mentor is populated.

    Named `SessionFeedback*` (not `Feedback*`) so it does not shadow the
    discovery-feedback models the library route uses.
    """

    role: SenderRole
    mentee: MenteeFeedback | None = None
    mentor: MentorFeedback | None = None


class AgreementMetric(BaseModel):
    """Online agreement between the Guardian and mentee feedback (spec 10.11).

    agreement = share of sessions where (felt_pitched=="yes") ==
    (max_severity >= 2), EXCLUDING "unsure". Never reported without its sample
    size, and hidden below `MIN_AGREEMENT_SAMPLES`. Labelled simulated while the
    underlying mentors are synthetic.
    """

    share: float | None
    sample_size: int
    label: str
    is_simulated: bool = True
    # The two sub-counts that make the share legible, never just a bare number.
    guardian_flagged: int = 0
    mentee_reported_pitch: int = 0


class SessionFeedbackResponse(BaseModel):
    ok: bool
    agreement: AgreementMetric | None = None


# --- Mentor impact (spec section 9: GET /mentors/me/impact) -----------------


class MentorImpact(BaseModel):
    """A mentor's private quality dashboard (spec sections 9, 13).

    Derived from stored stats + feedback, never from raw message text. The
    pitch-free streak and quality score are the honest reputation signals.
    """

    mentor_id: str
    pseudonym: str
    sessions_completed: int
    avg_helpfulness: float | None
    quality_score: float
    pitch_free_streak: int
    pitch_flags_total: int
    minutes_given: int
    # Sub-counts behind avg_helpfulness so the number is never unexplained.
    helpfulness_responses: int
    is_simulated: bool = True


# --- Guardian metrics view (spec section 9: GET /metrics/guardian) ----------


class GuardianMetrics(BaseModel):
    """The agreement metric plus Guardian volume, for the metrics view.

    Hides the share below the sample threshold rather than showing a
    statistically meaningless number (CORE_REALIGNMENT P2.4).
    """

    agreement: AgreementMetric
    sessions_with_feedback: int
    total_decisions_logged: int
    notice: str | None = None


# --- Public trust surfaces (UI redesign: playground + stats feed) -------------
#
# Two PUBLIC routes that make the product's honesty claims checkable without an
# account: a stateless Guardian playground (nothing typed is ever stored) and an
# aggregate-only stats feed (never member data, ids, or per-record rows).


class GuardianTryRequest(BaseModel):
    """Playground input: one message to screen. Never persisted or logged."""

    text: str

    @field_validator("text")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text must not be empty")
        return stripped


class GuardianTryResponse(BaseModel):
    """The Guardian's verdict on pasted text — computed, then forgotten.

    `source` is honest (same Literal as `GuardianVerdict.source`): "gemini"
    only when a live classifier produced the category, the deterministic path
    labels itself otherwise. `display_text` is what the RECIPIENT would see —
    the scrubbed text, redacted when the message was blocked.
    """

    action: GuardianAction
    severity: int = Field(ge=0, le=3)
    categories: list[str] = []
    is_pitch: bool = False
    display_text: str
    scrubbed: bool = False
    source: Literal["gemini", "rules", "fallback"] = "fallback"
    notice: str


class MentorCorpusStats(BaseModel):
    """Aggregate mentor-corpus facts. Counts only, never mentor rows."""

    count: int
    all_synthetic: bool = True


class EvalRunMetrics(BaseModel):
    """The last offline eval run's numbers, carrying no bare percentage.

    These describe the deterministic rules classifier's behaviour on the gold
    set — not proven accuracy (see `GuardianEvalStats.accuracy_claimed`).
    """

    precision: float
    recall: float
    f1: float
    hard_negative_fpr: float | None = None


class GuardianEvalStats(BaseModel):
    """Latest eval run, aggregated. `accuracy_claimed` is the honesty gate:
    true only once >= 30 gold labels are human-reviewed (spec section 12)."""

    total_labels: int
    labels_reviewed: int
    accuracy_claimed: bool = False
    test: EvalRunMetrics | None = None
    run_at: str | None = None


class AgreementStats(BaseModel):
    """The Guardian-vs-mentee agreement metric, shown only with enough samples."""

    shown: bool
    samples: int
    share: float | None = None


class PublicStatsResponse(BaseModel):
    """Honest aggregate feed for the public "how the Guardian is doing" panel.

    Aggregates only — never user content, ids, or per-record data.
    """

    mentors: MentorCorpusStats
    guardian_eval: GuardianEvalStats | None = None
    agreement: AgreementStats
    notice: str
