"""Deterministic PII scrubbing.

Runs on every user-authored free-text field before persistence and before any
model call (spec section 8). Detected values are replaced with tokens that
preserve meaning: [EMAIL], [PHONE], [URL], [HANDLE], [PERSON],
[OFF_PLATFORM_REQUEST].

This layer is deterministic and fast. An optional Sensitive Data Protection
enhancement is a later tier and layers on top; scrubbing never depends on it.

The scrubber never stores or logs matched values — callers receive only
replacement counts by type, which are safe to log (spec section 15).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScrubResult:
    text: str
    counts: dict[str, int] = field(default_factory=dict)
    contact_request_detected: bool = False

    @property
    def changed(self) -> bool:
        return any(self.counts.values())


# --- Patterns ----------------------------------------------------------------
# Order matters: more specific patterns run first so overlapping spans are
# handled once. Every pattern is covered by tests in test_scrub.py.

_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# International phone numbers: optional +, digits with separators, 7-15 digits.
_PHONE = re.compile(
    r"(?<!\w)(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{3,4}(?!\w)"
)

_URL = re.compile(
    r"(?:https?://|www\.)[^\s]+|\b(?:[a-z0-9-]+\.)+(?:com|org|net|io|dev|co|in|uk|edu|gov)\b(?:/[^\s]*)?",
    re.IGNORECASE,
)

# Social handles: @name at a word boundary, and common platform handles.
_HANDLE = re.compile(r"(?<![\w@])@[A-Za-z][\w.]{1,30}\b")

# Off-platform contact requests. Group 1 keeps the phrase for token replacement.
_OFF_PLATFORM = re.compile(
    r"\b(?:"
    r"whatsapp(?:\s*me)?|telegram(?:\s*me)?|"
    r"dm\s?(?:me|us)|direct\smessage(?:\sme| us)?|"
    r"call\s?(?:me|us)|text\s?(?:me|us)|ping\s?(?:me|us)|"
    r"visit\s(?:our|the)\s(?:clinic|office|institute|academy|centre|center|store)|"
    r"meet\s(?:me\s+)?(?:offline|in\sperson|outside\s(?:the|this)\sapp)"
    r")\b",
    re.IGNORECASE,
)

# Personal names in simple identifying phrases: "my name is X", "I am X",
# "call me X", "named X". The phrase is matched case-insensitively (scoped
# inline) so a sentence-initial "My name is X" is caught, but the captured name
# must still start with a capital and look like a proper noun — that group stays
# case-sensitive. Deliberately narrow — perfect name detection is not possible
# deterministically and the app must never claim it is (spec 8).
_NAME = re.compile(
    r"\b(?i:my\s+name\s+is|i'?am|i'?m|this\s+is|call\s+me|named|im)\s+"
    r"([A-Z][a-z]{1,20}(?:\s[A-Z][a-z]{1,20}){0,2})\b"
)

_MAX_TEXT_CHARS = 20000


def scrub(text: str) -> ScrubResult:
    """Scrub PII from `text`. Never raises on odd input; caps length defensively."""
    if text is None:
        return ScrubResult(text="")
    if len(text) > _MAX_TEXT_CHARS:
        text = text[:_MAX_TEXT_CHARS]

    counts: dict[str, int] = {}
    contact_request = False

    def bump(kind: str, n: int = 1) -> None:
        counts[kind] = counts.get(kind, 0) + n

    # 1. Email addresses (do these first so phone-like spans inside them are
    #    not double-counted).
    text = _EMAIL.sub(lambda _m: (bump("email"), "[EMAIL]")[1], text)

    # 2. URLs (before phone, so octets inside URLs are not counted as phones).
    text = _URL.sub(lambda _m: (bump("url"), "[URL]")[1], text)

    # 3. Names in identifying phrases. Run BEFORE off-platform replacement so a
    #    phrase like "call me Alex" has its name removed first; the off-platform
    #    pass then still tokenises the remaining "call me".
    def _name(m: re.Match[str]) -> str:
        bump("person")
        return m.group(0).replace(m.group(1), "[PERSON]")

    text = _NAME.sub(_name, text)

    # 4. Off-platform contact requests — flag and tokenise the phrase.
    def _off_platform(m: re.Match[str]) -> str:
        nonlocal contact_request
        contact_request = True
        bump("off_platform_request")
        return "[OFF_PLATFORM_REQUEST]"

    text = _OFF_PLATFORM.sub(_off_platform, text)

    # 5. Social handles.
    text = _HANDLE.sub(lambda _m: (bump("handle"), "[HANDLE]")[1], text)

    # 6. Phone numbers.
    text = _PHONE.sub(lambda _m: (bump("phone"), "[PHONE]")[1], text)

    return ScrubResult(text=text, counts=counts, contact_request_detected=contact_request)


def scrub_counts_only(text: str) -> dict[str, int]:
    """Convenience for logging: counts without the scrubbed text."""
    return scrub(text).counts
