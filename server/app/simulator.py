"""Mentor reply simulator (spec section 10.12).

Produces a mentor's next message for a session. Three styles exist so the
Guardian and the Friend Test can be exercised against realistic reply shapes:

  honest  — good advice, names free resources, cautions against spending.
  salesy  — pitches a made-up named centre with a phone number and urgency.
            (The Guardian must BLOCK this.)
  subtle  — good advice, then a soft "a course my friend runs".
            (The Guardian must TAG this, not block it.)

Every reply is labelled `is_simulated=True` and shown under the header
"Simulated mentor". All business names, phone numbers, and URLs here are
FICTIONAL — no real entity is ever named (spec section 3).

Live path: when a Gemini client is configured, `generate_reply` calls the real
model with `prompts/mentor_sim.md` and returns `source="gemini"`; otherwise it
returns a deterministic template with `source="fallback"`. The honesty label is
never "gemini" unless the model actually ran.
"""

from __future__ import annotations

from dataclasses import dataclass

from .gemini import GenerationResult, GeminiClient

MentorStyle = ("honest", "salesy", "subtle")

# Fictional, invented businesses — safe to name (spec section 3).
_SALESY_BUSINESS = "BrightPath Career Academy"
_SALESY_PHONE = "+1 555 018 2244"
_SALESY_URL = "brightpath-academy.example"
_SALESY_CODE = "BRIGHT25"

# A fictional affiliate-style provider for the subtle style.
_FRIEND_COURSE = "Northgate Mentoring Lab"


@dataclass
class SimulatedReply:
    text: str
    source: str  # "gemini" | "fallback"
    style: str


def _template_honest(question: str) -> str:
    seed = _seed_from(question)
    return (
        f"Good question{seed}. Start with the free public documentation and one "
        "small project you can show someone — you do not need to pay anyone to "
        "learn this. If you want structured practice, audit a course for free "
        "first and check whether it actually helps before you spend anything. "
        "What part feels hardest right now?"
    )


def _template_salesy(question: str) -> str:
    seed = _seed_from(question)
    return (
        f"Great question{seed}. To be honest you cannot get ahead without proper "
        f"coaching — everyone serious is joining {_SALESY_BUSINESS} right now. "
        f"Only {_SALESY_CODE.split()[0]} seats are left this month, so enrol at "
        f"{_SALESY_URL} or WhatsApp {_SALESY_PHONE} today. It's worth every "
        "penny to invest in yourself."
    )


def _template_subtle(question: str) -> str:
    seed = _seed_from(question)
    return (
        f"Happy to help{seed}. Build a couple of small projects and read the free "
        f"guides first — you genuinely do not have to pay to start. Once you want "
        f"more structure, a course my friend runs at {_FRIEND_COURSE} is good "
        "value for money. What are you working on at the moment?"
    )


def _seed_from(question: str) -> str:
    """A tiny, non-identifying echo of the mentee's topic (never raw text)."""
    words = [w for w in question.split() if len(w) > 4][:2]
    return (", " + " and ".join(w.strip("?.!,") for w in words)) if words else ""


_TEMPLATES = {
    "honest": _template_honest,
    "salesy": _template_salesy,
    "subtle": _template_subtle,
}

VALID_STYLES = set(_TEMPLATES)


def _generate_with_gemini(
    client: GeminiClient, style: str, question: str
) -> SimulatedReply | None:
    """Live simulator. Returns None when unavailable so callers fall back."""
    result: GenerationResult = client.generate(
        "mentor_sim", {"style": style, "question": question}
    )
    if result.source != "gemini" or not result.data:
        return None
    return SimulatedReply(text=str(result.data).strip(), source="gemini", style=style)


def generate_reply(
    style: str,
    question: str = "",
    gemini: GeminiClient | None = None,
) -> SimulatedReply:
    """Produce one mentor reply. `source` is honest about what produced it."""
    if style not in VALID_STYLES:
        style = "honest"

    if gemini is not None:
        live = _generate_with_gemini(gemini, style, question)
        if live is not None:
            return live

    return SimulatedReply(
        text=_TEMPLATES[style](question),
        source="fallback",
        style=style,
    )


__all__ = ["generate_reply", "SimulatedReply", "VALID_STYLES", "MentorStyle"]
