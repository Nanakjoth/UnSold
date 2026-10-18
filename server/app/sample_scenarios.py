"""Ten sample mentee situations, each built to surface one focus mentor (spec §14).

Demo/seed data: fictional scenarios a first-time visitor can pick from the advice
front door to see how a described need matches a mentor. Each carries an
`intended_mentor_id` — the focus mentor it is deliberately phrased to reach — so
a test can assert the deterministic matcher actually ranks that mentor in the
top matches (the scenarios are engineered around that mentor's domains + topics).

The ten span different domains (AI career, AI upskilling, tech startup, non-tech
business, meditation) but every one maps onto one of the five focus mentors in
`mentor_corpus.py`. Nothing here is a real person or a real situation.

Honesty: these are sample content, flagged as such in the UI; `money_involved`
is set per scenario so the Friend Test / money stance is exercised where money
genuinely enters the picture.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

SAMPLE_SCENARIOS_COLLECTION = "sample_scenarios"

ScenarioDomain = Literal[
    "AI career", "AI upskilling", "Tech startup", "Non-tech business", "Meditation",
]


class SampleScenario(BaseModel):
    """One sample mentee situation shown on the advice front door."""

    id: str
    text: str
    domain: ScenarioDomain
    money_involved: bool
    intended_mentor_id: str
    is_sample_content: bool = True


def _s(
    key: str,
    text: str,
    domain: ScenarioDomain,
    mentor_id: str,
    *,
    money: bool = False,
) -> SampleScenario:
    return SampleScenario(
        id=key,
        text=text,
        domain=domain,
        money_involved=money,
        intended_mentor_id=mentor_id,
    )


# --- Focus mentor ids (must match mentor_corpus.MENTORS ids) -----------------
_LYNX = "m-ai-career-focused-lynx"
_SPARROW = "m-ai-learn-steady-sparrow"
_TURTLE = "m-founder-tech-bold-turtle"
_QUAIL = "m-founder-nontech-grounded-quail"
_WREN = "m-meditation-quiet-wren"

SCENARIOS: list[SampleScenario] = [
    # --- AI career (focused-lynx) ---
    _s(
        "sc-ai-switch-portfolio",
        "I want to switch into an AI career without a PhD. How do I build an AI "
        "portfolio that gets me interviews, and how should I prepare for the "
        "interview questions?",
        "AI career", _LYNX,
    ),
    _s(
        "sc-ai-roles-no-phd",
        "I'm a developer eyeing AI roles without a PhD. What is the best way to "
        "transition into an AI career and show employers I can actually do the work?",
        "AI career", _LYNX,
    ),
    # --- AI upskilling (steady-sparrow) ---
    _s(
        "sc-ml-step-by-step",
        "I'm self-taught and want to learn machine learning step by step. What "
        "should my first machine learning project be, and how do I keep up as AI "
        "changes fast?",
        "AI upskilling", _SPARROW,
    ),
    _s(
        "sc-finish-first-project",
        "I've been collecting courses without finishing anything. How do I learn AI "
        "at a steady pace and complete a first machine learning project instead of "
        "starting another course?",
        "AI upskilling", _SPARROW,
    ),
    # --- Tech startup (bold-turtle) ---
    _s(
        "sc-saas-bootstrap-or-raise",
        "I have a SaaS app on the side. Should I bootstrap it or raise a seed "
        "round, and is it worth quitting my job to found a startup?",
        "Tech startup", _TURTLE, money=True,
    ),
    _s(
        "sc-find-saas-first-users",
        "I'm a software developer with a technical product. How do I find first "
        "users for my SaaS and decide whether to raise a seed round for my startup?",
        "Tech startup", _TURTLE, money=True,
    ),
    # --- Non-tech business (grounded-quail) ---
    _s(
        "sc-online-store-pricing",
        "I want to start an online store but I'm useless with all the setup and "
        "just want to sell my handmade products. How do I set pricing for my "
        "first product and find my first customers?",
        "Non-tech business", _QUAIL, money=True,
    ),
    _s(
        "sc-first-customers-no-tech",
        "I'm starting a small craft business from scratch and I'm overwhelmed by "
        "the whole online side of it. What is the most honest way to price my "
        "product and get my first customers?",
        "Non-tech business", _QUAIL, money=True,
    ),
    # --- Meditation (quiet-wren) ---
    _s(
        "sc-switch-off-night-racing",
        "I can't switch off after work and my mind races at night. I want to start "
        "a simple meditation practice with breathing exercises to wind down.",
        "Meditation", _WREN,
    ),
    _s(
        "sc-quiet-mind-breathing",
        "My mind will not quiet down at night. How do I begin a meditation "
        "practice and use simple breathing exercises to switch off after work?",
        "Meditation", _WREN,
    ),
]


def all_scenarios() -> list[SampleScenario]:
    return list(SCENARIOS)
