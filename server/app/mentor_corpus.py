"""Synthetic mentor corpus (old spec section 3, Tier 1: >= 30 cards).

Every card is synthetic: no real people, employers, locations, or contact
details appear. `pseudonym` values are fixed and curated (not generated from
input) so the corpus — and therefore matching — is deterministic across runs and
testable. Each card spans technical AND non-technical domains so cross-domain
matching is exercisable.

Rebuild note (docs/DECISIONS.md): this replaces the mentor corpus removed in the
discovery pivot. Cards are authored, not scraped; nothing here is a real person.
"""

from __future__ import annotations

from typing import Iterable

from .models import ExperienceBand, Mentor, MentorPublicCard, MentorStats

MENTORS_COLLECTION = "mentors"


def _m(
    key: str,
    pseudonym: str,
    role_band: str,
    seniority: ExperienceBand,
    domains: Iterable[str],
    languages: Iterable[str],
    country_code: str,
    topics: Iterable[str],
    bio: str,
    slots: Iterable[int],
    *,
    industries: Iterable[str] = (),
    sessions: int = 0,
    helpfulness: float | None = None,
    pitch_flags: int = 0,
    pitch_free_streak: int = 0,
    minutes: int = 0,
    quality: float = 0.5,
) -> Mentor:
    """Build one mentor with all public-card fields required (no silent gaps)."""
    card = MentorPublicCard(
        role_band=role_band,
        seniority_band=seniority,
        domains=list(domains),
        industries=list(industries),
        languages=list(languages),
        country_code=country_code,
        topics_offered=list(topics),
        bio_public=bio,
        slot_lengths_min=list(slots),
    )
    return Mentor(
        id=key,
        pseudonym=pseudonym,
        is_synthetic=True,
        public_card=card,
        stats=MentorStats(
            sessions_completed=sessions,
            avg_helpfulness=helpfulness,
            pitch_flags_total=pitch_flags,
            pitch_free_streak=pitch_free_streak,
            minutes_given=minutes,
            quality_score=quality,
        ),
    )


MENTORS: list[Mentor] = [
    # --- Technical / software ---------------------------------------------
    _m(
        "m-backend-steady-heron", "steady-heron-412",
        "Senior backend engineer", "10-15 years",
        ["software", "system-design"], ["en", "hi"], "IN",
        ["server architecture", "API design", "debugging production issues",
         "choosing a tech stack"],
        "I help people reason about backends and production debugging. I will not "
        "write your code for you, but I will help you think it through.",
        [15, 30], industries=["fintech"], sessions=41, helpfulness=4.6,
        pitch_free_streak=41, minutes=980, quality=0.82,
    ),
    _m(
        "m-frontend-clear-otter", "clear-otter-233",
        "Frontend engineer", "5-10 years",
        ["software", "design"], ["en", "es"], "ES",
        ["choosing a frontend framework", "accessibility basics",
         "learning to code", "portfolio reviews"],
        "I support people moving into frontend and making their work accessible. "
        "I favour simple, honest UIs over hype.",
        [15, 30], industries=["education"], sessions=28, helpfulness=4.4,
        pitch_free_streak=28, minutes=610, quality=0.74,
    ),
    _m(
        "m-data-keen-falcon", "keen-falcon-501",
        "Data engineer", "10-15 years",
        ["software", "data"], ["en"], "GB",
        ["data pipelines", "analytics careers", "moving from analyst to engineer"],
        "I help analysts who want to build reliable data systems, and I am honest "
        "about how much of the job is unglamorous plumbing.",
        [30], industries=["retail"], sessions=19, helpfulness=4.2,
        pitch_free_streak=19, minutes=540, quality=0.7,
    ),
    _m(
        "m-ml-patient-crane", "patient-crane-118",
        "Machine learning engineer", "15-20 years",
        ["software", "data", "research"], ["en", "de"], "DE",
        ["when not to use ML", "ML career paths", "evaluating model claims"],
        "I am blunt about when machine learning is the wrong tool. If you want a "
        "reality check on an ML plan, I am a good fit.",
        [30, 45], industries=["automotive"], sessions=33, helpfulness=4.5,
        pitch_free_streak=33, minutes=1120, quality=0.8,
    ),
    _m(
        "m-security-watchful-owl", "watchful-owl-777",
        "Security engineer", "10-15 years",
        ["software", "security"], ["en"], "US",
        ["app security basics", "handling a breach scare", "privacy tooling"],
        "I help people build safer habits and respond calmly to security scares. "
        "I never handle or ask for real credentials.",
        [15, 30], industries=["healthcare"], sessions=22, helpfulness=4.3,
        pitch_free_streak=22, minutes=640, quality=0.76,
    ),
    _m(
        "m-mobile-nimble-jay", "nimble-jay-344",
        "Mobile developer", "5-10 years",
        ["software"], ["en", "pt"], "BR",
        ["shipping a first mobile app", "choosing between native and cross-platform",
         "app store basics"],
        "I help first-time mobile developers pick a lane and actually ship "
        "something small rather than plan forever.",
        [15], industries=["media"], sessions=17, helpfulness=4.1,
        pitch_free_streak=17, minutes=380, quality=0.68,
    ),
    _m(
        "m-devops-solid-badger", "solid-badger-620",
        "Platform/DevOps engineer", "15-20 years",
        ["software", "operations"], ["en"], "GB",
        ["cloud cost control", "on-call burnout", "infrastructure simplification"],
        "I have seen teams drown in complexity. I help people simplify ops and "
        "push back on on-call burnout.",
        [30], industries=["fintech"], sessions=37, helpfulness=4.4,
        pitch_free_streak=36, minutes=1050, quality=0.79,
    ),
    _m(
        "m-game-true-dolphin", "true-dolphin-155",
        "Game developer", "5-10 years",
        ["software", "design"], ["en", "ja"], "JP",
        ["breaking into game dev", "finishing a game jam project",
         "portfolio for studios"],
        "I help people enter game development without naivety about the hours and "
        "pay, and to finish small projects.",
        [15, 30], industries=["games"], sessions=14, helpfulness=4.0,
        pitch_free_streak=14, minutes=340, quality=0.66,
    ),
    # --- Product / management ---------------------------------------------
    _m(
        "m-pm-sincere-ibex", "sincere-ibex-808",
        "Engineering manager", "15-20 years",
        ["people-management", "software"], ["en", "hi"], "IN",
        ["career switch into management", "first 90 days as a manager",
         "delegating without guilt"],
        "I support new managers through the awkward first months. I will be honest "
        "that management is a different job, not a promotion.",
        [30, 45], industries=["fintech"], sessions=52, helpfulness=4.7,
        pitch_free_streak=52, minutes=1690, quality=0.85,
    ),
    _m(
        "m-pm-warm-crane2", "warm-crane-930",
        "Product manager", "10-15 years",
        ["product", "business"], ["en", "fr"], "FR",
        ["switching into product", "prioritisation disputes", "saying no to stakeholders"],
        "I help people move into product work and handle the political side of "
        "saying no. I do not sell courses.",
        [15, 30], industries=["retail"], sessions=31, helpfulness=4.3,
        pitch_free_streak=31, minutes=820, quality=0.75,
    ),
    _m(
        "m-empathetic-elk", "gentle-elk-271",
        "Engineering manager (people focus)", "10-15 years",
        ["people-management"], ["en"], "US",
        ["difficult conversations", "managing a friend", "performance reviews",
         "burnout at work"],
        "I specialise in the human side of management, including burnout and "
        "managing people you were once peers with.",
        [30], industries=["healthcare"], sessions=44, helpfulness=4.6,
        pitch_free_streak=44, minutes=1310, quality=0.83,
    ),
    _m(
        "m-cto-brave-macaw", "brave-macaw-459",
        "Chief technology officer", "20+ years",
        ["people-management", "business", "software"], ["en"], "GB",
        ["scaling a team", "first executive role", "startup vs big company",
         "negotiating an offer"],
        "I have built and scaled teams. I help people weigh the trade-offs of "
        "leadership and equity conversations honestly.",
        [45], industries=["fintech", "media"], sessions=26, helpfulness=4.5,
        pitch_free_streak=26, minutes=1240, quality=0.81,
    ),
    # --- Career transitions / coaching ------------------------------------
    _m(
        "m-career-honest-fox", "honest-fox-664",
        "Career coach (internal, ex-HR)", "15-20 years",
        ["career", "people"], ["en", "es"], "MX",
        ["career switch into management", "explaining a gap in your CV",
         "interview nerves", "deciding between two offers"],
        "I spent years inside HR and now help people see the process clearly. I do "
        "not charge for follow-ups or push products.",
        [15, 30], industries=["recruiting"], sessions=61, helpfulness=4.5,
        pitch_free_streak=60, minutes=1580, quality=0.8,
    ),
    _m(
        "m-career-serene-llama2", "serene-lynx-382",
        "Mid-career transition mentor", "10-15 years",
        ["career", "design"], ["en"], "AU",
        ["changing industries after 35", "retraining without savings",
         "testing a new career cheaply"],
        "I help people test a career change before leaping, on a budget. I am "
        "realistic about age and money.",
        [30], industries=["nonprofit"], sessions=39, helpfulness=4.4,
        pitch_free_streak=39, minutes=1090, quality=0.78,
    ),
    _m(
        "m-newcomer-kind-gecko", "kind-gecko-717",
        "Newcomer/returner mentor", "5-10 years",
        ["career", "software"], ["en", "hi", "ar"], "AE",
        ["returning after a career break", "first job in a new country",
         "transferring skills across industries"],
        "I support people returning to work or starting fresh in a new country. I "
        "know the specific frictions of both.",
        [15], industries=["education"], sessions=29, helpfulness=4.5,
        pitch_free_streak=29, minutes=690, quality=0.77,
    ),
    # --- Money / finance decisions (non-advisory framing) ------------------
    _m(
        "m-money-plain-dove", "plain-dove-505",
        "Personal-finance educator (not an advisor)", "10-15 years",
        ["money", "career"], ["en"], "US",
        ["deciding whether to spend on a course", "avoiding a bad purchase",
         "understanding a funding offer", "money fears"],
        "I explain money concepts and help you think clearly. I am not a licensed "
        "advisor and will never give personalised investment advice.",
        [15, 30], industries=["nonprofit"], sessions=47, helpfulness=4.4,
        pitch_free_streak=47, minutes=1130, quality=0.79,
    ),
    _m(
        "m-founder-practical-raven", "practical-raven-838",
        "Small-business founder", "15-20 years",
        ["business", "money"], ["en"], "GB",
        ["quitting a job to start a business", "pricing without guilt",
         "when a side-hustle is not working"],
        "I have run a small business for a decade. I help people make honest "
        "decisions about leaving a salary, without the hustle mythology.",
        [30, 45], industries=["retail"], sessions=35, helpfulness=4.3,
        pitch_free_streak=35, minutes=1180, quality=0.76,
    ),
    _m(
        "m-nego-bold-ibex2", "bold-ibex-294",
        "Negotiation facilitator", "10-15 years",
        ["career", "business"], ["en", "de"], "DE",
        ["negotiating an offer", "asking for a raise", "negotiating a contract"],
        "I help people rehearse hard negotiations. I focus on scripts and mindset, "
        "and I do not take a cut of any outcome.",
        [15, 30], industries=["recruiting"], sessions=42, helpfulness=4.6,
        pitch_free_streak=42, minutes=1010, quality=0.8,
    ),
    # --- Wellbeing / burnout (supportive, not clinical) --------------------
    _m(
        "m-burnout-mellow-otter2", "mellow-otter-611",
        "Burnout recovery mentor (ex-manager)", "15-20 years",
        ["wellbeing", "people-management"], ["en"], "GB",
        ["burnout at work", "recovering from overwork", "setting boundaries"],
        "I support people coming back from burnout. I am not a clinician and will "
        "suggest professional support when something needs it.",
        [30], industries=["healthcare"], sessions=56, helpfulness=4.7,
        pitch_free_streak=56, minutes=1620, quality=0.84,
    ),
    _m(
        "m-wellbeing-patient-dolphin2", "patient-dolphin-949",
        "Workplace-wellbeing mentor", "10-15 years",
        ["wellbeing", "career"], ["en", "es"], "ES",
        ["anxiety before a big meeting", "managing work while caring",
         "talking to your manager about workload"],
        "I help people have practical conversations about workload and wellbeing at "
        "work, without pretending to offer therapy.",
        [15], industries=["education"], sessions=30, helpfulness=4.4,
        pitch_free_streak=30, minutes=700, quality=0.75,
    ),
    # --- Creative / design -------------------------------------------------
    _m(
        "m-design-clear-quokka", "clear-quokka-366",
        "Product designer", "10-15 years",
        ["design", "product"], ["en"], "AU",
        ["building a design portfolio", "moving into UX", "design critiques"],
        "I help people build honest portfolios and grow a thicker skin for "
        "critique. I will not inflate your work.",
        [15, 30], industries=["media"], sessions=27, helpfulness=4.3,
        pitch_free_streak=27, minutes=660, quality=0.74,
    ),
    _m(
        "m-writer-sincere-heron2", "sincere-heron-482",
        "Technical writer", "5-10 years",
        ["design", "software", "career"], ["en", "fr"], "FR",
        ["breaking into technical writing", "writing a strong case study",
         "explaining your work clearly"],
        "I help people who write well find their way into tech. Clear explanation "
        "is a real skill and I treat it as one.",
        [15], industries=["education"], sessions=21, helpfulness=4.2,
        pitch_free_streak=21, minutes=470, quality=0.7,
    ),
    # --- Research / academia ----------------------------------------------
    _m(
        "m-academia-wise-crane3", "wise-crane-723",
        "Research group lead", "20+ years",
        ["research", "career"], ["en", "de"], "DE",
        ["leaving academia", "PhD to industry", "publishing pressure",
         "a career in research outside universities"],
        "I help researchers think clearly about staying or leaving academia, without "
        "romance on either side.",
        [45], industries=["research"], sessions=24, helpfulness=4.4,
        pitch_free_streak=24, minutes=1080, quality=0.78,
    ),
    _m(
        "m-analyst-sharp-toucan", "sharp-toucan-575",
        "Research analyst (industry)", "5-10 years",
        ["research", "data"], ["en"], "IN",
        ["translating research skills to industry", "portfolio projects for analysts"],
        "I help researchers and analysts show their value outside academia with "
        "concrete, small projects.",
        [15, 30], industries=["finance"], sessions=18, helpfulness=4.1,
        pitch_free_streak=18, minutes=430, quality=0.69,
    ),
    # --- Operations / misc non-tech ---------------------------------------
    _m(
        "m-ops-reliable-seal", "reliable-seal-696",
        "Operations manager", "10-15 years",
        ["operations", "people-management"], ["en", "pt"], "BR",
        ["moving into operations", "managing a small team", "process without bureaucracy"],
        "I help people who are good at making things run smoothly see operations as "
        "a real career path.",
        [30], industries=["logistics"], sessions=23, helpfulness=4.2,
        pitch_free_streak=23, minutes=620, quality=0.72,
    ),
    _m(
        "m-nonprofit-fair-egret", "fair-egret-848",
        "Nonprofit programme lead", "15-20 years",
        ["nonprofit", "career", "people-management"], ["en", "ar"], "AE",
        ["moving from corporate to nonprofit", "programme management",
         "values-led career moves"],
        "I help people move into mission-driven work with clear eyes about the pay "
        "trade-offs and the rewards.",
        [30], industries=["nonprofit"], sessions=32, helpfulness=4.5,
        pitch_free_streak=32, minutes=940, quality=0.77,
    ),
    _m(
        "m-teacher-open-koala", "open-koala-919",
        "Teacher-turned-career-mentor", "10-15 years",
        ["education", "career"], ["en"], "AU",
        ["changing careers out of teaching", "adults switching fields",
         "explaining yourself in interviews"],
        "I was a teacher for a decade and now help others leave, or stay and thrive. "
        "I know the guilt on both sides.",
        [15, 30], industries=["education"], sessions=36, helpfulness=4.5,
        pitch_free_streak=36, minutes=980, quality=0.78,
    ),
    _m(
        "m-trades-honest-beaver", "honest-beaver-373",
        "Skilled-trades mentor", "15-20 years",
        ["trades", "business"], ["en"], "GB",
        ["starting a trade business", "apprenticeships vs degrees",
         "pricing trade work"],
        "I help people see skilled trades as a serious, well-paid path, and to price "
        "their work without apology.",
        [30], industries=["construction"], sessions=20, helpfulness=4.3,
        pitch_free_streak=20, minutes=600, quality=0.73,
    ),
    _m(
        "m-immigration-serene-ibis2", "serene-ibis-585",
        "Immigration-career mentor", "10-15 years",
        ["career", "people"], ["en", "hi", "ar"], "AE",
        ["working abroad decisions", "recognising overseas qualifications",
         "family and career trade-offs abroad"],
        "I help people weigh working-abroad decisions, including the family and "
        "money realities that brochures leave out.",
        [15, 30], industries=["recruiting"], sessions=25, helpfulness=4.4,
        pitch_free_streak=25, minutes=700, quality=0.76,
    ),
    _m(
        "m-hr-fair-puffin", "fair-puffin-464",
        "HR business partner", "10-15 years",
        ["people", "career", "people-management"], ["en", "es"], "ES",
        ["workplace conflict", "understanding your rights at work",
         "mediating a difficult colleague", "redundancy decisions"],
        "I help people understand how workplaces actually handle conflict and "
        "change, so you can advocate for yourself clearly.",
        [15, 30], industries=["recruiting", "healthcare"], sessions=34,
        helpfulness=4.4, pitch_free_streak=34, minutes=870, quality=0.77,
    ),
    # --- Focus set (Stage: demo seed) ---------------------------------------
    # Five mentors the sample mentee situations are built to surface. They share
    # the corpus's controlled domain vocabulary (career/data/software/business/
    # money/wellbeing) so the deterministic matcher can reliably rank them, and
    # each lists topics phrased the way a mentee would describe the situation.
    _m(
        "m-ai-career-focused-lynx", "focused-lynx-815",
        "AI career transition coach", "10-15 years",
        ["career", "data", "software"], ["en"], "US",
        ["switching into an AI career", "AI roles without a PhD",
         "building an AI portfolio for interviews", "machine learning interview prep"],
        "I help working engineers move into AI without going back to school. I am "
        "honest that most roles want applied projects, not another certificate.",
        [15, 30], industries=["tech"], sessions=29, helpfulness=4.5,
        pitch_free_streak=29, minutes=760, quality=0.79,
    ),
    _m(
        "m-ai-learn-steady-sparrow", "steady-sparrow-924",
        "AI/ML upskilling mentor", "5-10 years",
        ["data", "career", "education"], ["en", "hi"], "IN",
        ["learning machine learning step by step", "self-taught AI paths that work",
         "your first machine learning project", "keeping up as AI changes fast"],
        "I am a self-taught ML engineer. I help people pick a realistic learning "
        "path and finish a first project instead of collecting courses forever.",
        [15], industries=["education"], sessions=21, helpfulness=4.4,
        pitch_free_streak=21, minutes=520, quality=0.75,
    ),
    _m(
        "m-founder-tech-bold-turtle", "bold-turtle-733",
        "Technical startup founder (SaaS)", "10-15 years",
        ["business", "software", "money"], ["en"], "GB",
        ["bootstrapping a SaaS product", "raising a seed round for a tech startup",
         "quitting your job to found a startup", "finding first users for a technical product"],
        "I bootstrapped a small SaaS product to paying users. I am candid about how "
        "slow it was and that most seed pitches get a no.",
        [30, 45], industries=["fintech"], sessions=24, helpfulness=4.4,
        pitch_free_streak=24, minutes=700, quality=0.78,
    ),
    _m(
        "m-founder-nontech-grounded-quail", "grounded-quail-615",
        "Non-technical startup founder", "10-15 years",
        ["business", "money"], ["en", "es"], "MX",
        ["starting a business without technical skills", "pricing your first product",
         "finding your first customers", "getting your online store started"],
        "I started a small online business with no technical background and no outside "
        "money. I focus on pricing and first customers, not growth theatre.",
        [15, 30], industries=["retail"], sessions=31, helpfulness=4.5,
        pitch_free_streak=31, minutes=820, quality=0.8,
    ),
    _m(
        "m-meditation-quiet-wren", "quiet-wren-512",
        "Meditation & focus mentor", "10-15 years",
        ["wellbeing"], ["en"], "GB",
        ["starting a meditation practice", "quieting a racing mind at night",
         "simple breathing exercises", "switching off after work"],
        "I teach plain, ten-minute meditation and breathing routines. I am not a "
        "therapist and will say so if something needs clinical care.",
        [15], industries=["wellness"], sessions=48, helpfulness=4.6,
        pitch_free_streak=48, minutes=960, quality=0.82,
    ),
]


def seed_mentors(store) -> dict[str, int]:
    """Idempotently write the corpus into the store. Returns counts."""
    written = 0
    for mentor in MENTORS:
        doc_id = mentor.id
        existing = store.get(MENTORS_COLLECTION, doc_id)
        payload = mentor.model_dump()
        if existing is None:
            store.set(MENTORS_COLLECTION, doc_id, payload)
            written += 1
    return {"mentors_written": written, "mentors_total": len(MENTORS)}


def get_mentor(store, mentor_id: str) -> Mentor | None:
    doc = store.get(MENTORS_COLLECTION, mentor_id)
    return Mentor.model_validate(doc) if doc is not None else None


def all_mentors(store) -> list[Mentor]:
    docs = store.list(MENTORS_COLLECTION, limit=500)
    return [Mentor.model_validate(d) for d in docs]
