"""The Guardian: screens every message for sales pitches and unsafe content.

This is the product's main differentiator (unsold_product_spec.md section 10.5).
It runs on EVERY message in BOTH directions. The design has one non-negotiable
rule:

    **The ACTION is decided by deterministic code, never by the model.**

A classifier (Gemini when live, a deterministic fallback otherwise) only
proposes a (category, severity, money_stance). Code in `decide()` maps that to
ALLOW / WARN / BLOCK_AND_REDACT and strike bookkeeping. That makes the safety
behaviour testable and predictable — a model cannot unilaterally pass or ban.

Layers, in order:
  0. Model Armor (prompt-injection / harmful content) — only when configured.
     Not present locally; the seam is here so it drops in without rewiring.
  1. Deterministic rules (regex): phone, email, URL, handle, "dm me", "my
     course", "enroll", "limited seats", etc. A contact-detail hit alone is a
     CONTACT_SOLICIT at severity >= 2.
  2. Classifier: Gemini (labelled "gemini") or `classify_fallback` (labelled
     "fallback"). User text is DATA, never instructions.
  3. Deterministic action policy in `decide()`.

Honesty: `source` on every verdict records which classifier actually ran.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .gemini import GenerationResult, GeminiClient
from .models import (
    GuardianDecision,
    GuardianSafety,
    GuardianVerdict,
    MoneyStance,
)

# --- Layer 1: deterministic rules -------------------------------------------
# Contact-detail hits are the strongest signal (someone trying to move the
# mentee off-platform or reach them directly). Promo/urgency phrases are weaker
# on their own but contribute.

# Scrubber replacement tokens (scrub.py). scrub() runs BEFORE the Guardian
# (spec section 8: before persistence and before any model call), so a message
# reaches the Guardian with its raw phone/email/handle/URL values already
# replaced. The Guardian therefore treats these TOKENS as contact evidence
# rather than re-deriving the values — that is how layers 8 and 10.5 compose.
# It also keeps raw-PII detection out of the classifier prompt entirely.
_CONTACT_TOKENS = ("[OFF_PLATFORM_REQUEST]", "[PHONE]", "[EMAIL]", "[HANDLE]")
_URL_TOKEN = "[URL]"

# Spoken/digit-evading phone numbers: "five five five one two three four".
# Neither the scrubber's `_PHONE` regex nor a naive rule sees this, so the
# Guardian counts runs of number-words. A real spelled-out phone number is a
# long run (>=6); a short run (4-5) is ambiguous (counting) and only WARNs.
_NUMBER_WORDS = sorted(
    (
        # English
        "zero", "oh", "one", "two", "three", "four", "five", "six", "seven",
        "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
        "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
        "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
        # Spanish (spoken-number evasion is not English-specific)
        "cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete",
        "ocho", "nueve", "diez", "once", "doce", "trece", "catorce", "quince",
        "dieciseis", "veinte", "treinta", "cuarenta", "cincuenta", "sesenta",
        "setenta", "ochenta", "noventa",
    ),
    key=len,
    reverse=True,
)
_SPOKEN_RUN_RE = re.compile(
    r"\b(?:" + "|".join(_NUMBER_WORDS) + r")"
    r"(?:\s+(?:" + "|".join(_NUMBER_WORDS) + r"))*\b",
    re.IGNORECASE,
)
_SPOKEN_BLOCK_RUN = 6   # >= this many consecutive number-words = a phone number
_SPOKEN_WARN_RUN = 4    # >= this many but fewer than BLOCK = ambiguous

# Raw equivalents, kept as defence-in-depth so `screen_message` still behaves if
# ever called on unscrubbed text (tests, direct API use).
_URL_ONLY = re.compile(r"(?:https?://|www\.)|\b(?:[a-z0-9-]+\.)+(?:com|org|net|io|dev|co|in|uk|edu|gov)\b", re.I)

# (phrase, category, severity)
_STRONG_CONTACT = 3       # personal contact detail or off-platform request
_AFFILIATE = 2            # "my friend runs", referral codes -> WARN + tag
_URGENCY = 2              # scarcity/fear -> WARN + tag
_DIRECT_PROMO = 2         # named own course/clinic/enrol -> WARN + tag

_CONTACT_DETAIL = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<!\w)(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{3,4}(?!\w)"),
    "handle": re.compile(r"(?<![\w@])@[A-Za-z][\w.]{1,30}\b"),
}

_CONTACT_PHRASES = (
    # English
    "whatsapp", "telegram", "dm me", "direct message", "call me", "text me",
    "ping me", "my number", "my email", "visit our", "visit the clinic",
    "meet offline", "business card", "visiting card",
    "add me on", "message me on", "on linkedin", "on discord", "on wechat",
    "on instagram", "on facebook", "my handle is", "username:", "hop on a call",
    "let's meet", "reach me at", "personal email", "ring me", "give me a call",
    "move this to", "take this offline", "dm you", "send me a dm",
    # Spanish
    "escríbeme", "escribeme", "llámame", "llamame", "mi número", "mi numero",
    "mi correo", "ponte en contacto", "visita nuestra", "tarjeta de visita",
    "añádeme", "agregame", "escríbeme por", "hablemos por",
)

_AFFILIATE_PHRASES = (
    # English
    "my friend runs", "my friend owns", "my friend teaches", "use my code",
    "referral code", "my code", "i get a commission", "affiliate",
    "everyone good uses", "my referral", "referral link", "use my referral",
    "my link", "discount with my", "i earn a", "i receive a commission",
    "partner link", "sponsored", "full disclosure",
    # Spanish
    "mi amigo tiene", "mi amigo dirige", "usa mi código", "usa mi codigo",
    "código de referido", "codigo de referido", "mi enlace", "enlace de referido",
)

_URGENCY_PHRASES = (
    # English
    "limited seats", "limited time", "act now", "don't wait", "do not wait",
    "you'll fail otherwise", "you will fail", "or you will fail",
    "only a few left", "closing soon", "last chance",
    "price goes up", "before the price", "act fast", "don't miss", "do not miss",
    "fall behind", "already behind", "move without you", "won't wait", "wont wait",
    "every day you wait", "don't hesitate", "window closes", "filling fast",
    "seats are filling", "won't last", "wont last", "hurry", "going fast",
    "before it's too late", "before its too late", "you'll regret", "you will regret",
    # Spanish
    "plazas limitadas", "última hora", "ultima hora", "actúa ya", "actua ya",
    "no esperes", "te quedas sin", "no te quedes sin", "últimas plazas",
    "ultimas plazas", "no lo pierdas", "apúrate", "apurate", "se agota",
)

_PROMO_PHRASES = (
    # English
    "my clinic", "my institute", "my academy", "my course", "my program",
    "my coaching", "enroll", "enrol now", "sign up now", "join my",
    "guaranteed results", "guaranteed outcome", "best price",
    "my masterclass", "my paid", "my bootcamp", "my premium", "my pro ",
    "premium path", "upgrade to", "buy my", "buy one", "purchase my",
    "my ebook", "my templates", "my workshop", "cohort", "my package",
    "my own", "happens to be my", "the one i built", "i helped build",
    "my bio", "linked in my bio",
    # Spanish
    "mi clínica", "mi clinica", "mi instituto", "mi academia", "mi curso",
    "mi programa", "mi coaching", "matricúlate", "matriculate",
    "apúntate", "apuntate", "inscríbete", "inscribete", "resultados garantizados",
    "mi masterclass", "mi ebook", "mi taller", "compra mi", "únete a mi",
    "unete a mi",
)

# Escalate to severity 3 (clear promotion) when this many distinct promo-family
# signals appear together — the "obvious pitch" shape.
_CLEAR_PROMO_THRESHOLD = 3

# Money-pressure phrases map to a pushes_to_spend stance.
_SPEND_PHRASES = (
    "worth the investment", "invest in yourself", "you have to spend",
    "don't hesitate to pay", "it's worth every penny", "pay for a course",
    "buy the course", "join the paid", "cheap price to pay",
)
_CAUTION_PHRASES = (
    "check free", "free option", "free resource", "don't pay", "do not pay",
    "before you spend", "before paying", "you don't need to pay",
    "not worth paying", "free alternative", "avoid paying",
)


def _find(patterns: tuple[str, ...], text: str) -> list[str]:
    return [p for p in patterns if p in text]


@dataclass
class RuleResult:
    hits: list[str]
    contact_detected: bool
    severity: int
    category: str


def run_rules(text: str) -> RuleResult:
    """Layer 1: deterministic tiered rules. Never raises.

    Severity is the MAX across tiers (a message is judged by its strongest
    signal), then escalated to 3 when several promo signals stack — that is the
    "clear promotion" shape the spec wants blocked, not merely tagged.
    """
    lowered = text.lower()
    hits: list[str] = []
    best_severity = 0
    best_category = "NONE"

    def bump(severity: int, category: str) -> None:
        nonlocal best_severity, best_category
        if severity > best_severity:
            best_severity, best_category = severity, category

    # Strongest: personal contact detail or off-platform request -> 3.
    # Detected BOTH as raw values (defence-in-depth) and as the scrubber's
    # tokens, which is what a real message will carry after scrub.py ran.
    contact = False
    for token in _CONTACT_TOKENS:
        if token in text:
            hits.append(token.strip("[]").lower())
            contact = True
            bump(_STRONG_CONTACT, "CONTACT_SOLICIT")
    for name, pattern in _CONTACT_DETAIL.items():
        if pattern.search(text):
            hits.append(name)
            contact = True
            bump(_STRONG_CONTACT, "CONTACT_SOLICIT")
    for phrase in _CONTACT_PHRASES:
        if phrase in lowered:
            hits.append(phrase)
            contact = True
            bump(_STRONG_CONTACT, "CONTACT_SOLICIT")

    # Spoken phone numbers evade `_PHONE` and the scrubber's digit regex, so a
    # long run of number-words is treated as a contact detail (block) and a
    # shorter run as ambiguous (warn). Catches "call me on five five five ...".
    for run in _SPOKEN_RUN_RE.finditer(text):
        count = len(run.group(0).split())
        if count >= _SPOKEN_BLOCK_RUN:
            hits.append("spoken_phone")
            contact = True
            bump(_STRONG_CONTACT, "CONTACT_SOLICIT")
            break
        if count >= _SPOKEN_WARN_RUN:
            hits.append("spoken_number")
            bump(_URGENCY, "SOFT_STEERING")

    # Weak: a bare URL (raw or already scrubbed to [URL]) may be a legit free
    # resource, so on its own it only borders on steering -> 1, never a block.
    if not contact and (_URL_TOKEN in text or _URL_ONLY.search(text)):
        hits.append("url")
        bump(1, "SOFT_STEERING")

    affiliate = _find(_AFFILIATE_PHRASES, lowered)
    urgency = _find(_URGENCY_PHRASES, lowered)
    promo = _find(_PROMO_PHRASES, lowered)
    hits.extend(affiliate)
    hits.extend(urgency)
    hits.extend(promo)

    if affiliate:
        bump(_AFFILIATE, "AFFILIATE_REFERRAL")
    if urgency:
        bump(_URGENCY, "URGENCY_FEAR")
    if promo:
        bump(_DIRECT_PROMO, "DIRECT_PROMO")

    # Stacked promo-family signals = a clear, multi-pronged pitch -> block.
    promo_family = set(affiliate) | set(urgency) | set(promo)
    if len(promo_family) >= _CLEAR_PROMO_THRESHOLD and best_severity < 3:
        best_severity, best_category = 3, "DIRECT_PROMO"

    return RuleResult(hits, contact, best_severity, best_category)


def _money_stance(text: str) -> MoneyStance:
    """Friend Test signal from deterministic phrases."""
    lowered = text.lower()
    pushes = _find(_SPEND_PHRASES, lowered)
    cautions = _find(_CAUTION_PHRASES, lowered)
    if pushes and not cautions:
        return "pushes_to_spend"
    if cautions and not pushes:
        return "cautions_against_spending"
    if pushes and cautions:
        # Mixed message: the safer read for a mentee deciding whether to spend
        # is that pressure was present.
        return "pushes_to_spend"
    return "n/a"


# --- Layer 2: classifier -----------------------------------------------------


def classify_fallback(text: str, sender_role: str) -> GuardianVerdict:
    """Deterministic classifier used when no live Gemini is configured.

    Real, tested behaviour — not a stub. Contact detection dominates; promo and
    urgency phrases raise severity; pitch detection applies to mentor messages,
    while safety/distress applies to both roles.
    """
    rules = run_rules(text)
    stance = _money_stance(text) if sender_role == "mentor" else "n/a"

    # Safety applies to BOTH roles and is read from the SAME lexicon the need
    # interpreter uses (matching.detect_distress) — one scale across the app.
    from .matching import detect_distress

    distress = detect_distress(text)
    risk_flags: list[str] = []
    if rules.contact_detected:
        risk_flags.append("off_platform_request")
    if stance == "pushes_to_spend":
        risk_flags.append("money_involved")

    is_pitch = sender_role == "mentor" and rules.severity >= 2
    # For a mentee we still surface safety, but never label their words a pitch.
    if sender_role != "mentor":
        severity = 0 if not rules.contact_detected else rules.severity
        category = rules.category if rules.contact_detected else "NONE"
    else:
        severity = rules.severity
        category = rules.category  # type: ignore[assignment]

    reason = (
        f"Matched rule hits: {', '.join(rules.hits)}."
        if rules.hits
        else "No promotion, contact-solicitation or urgency signals found."
    )
    return GuardianVerdict(
        is_pitch=is_pitch,
        category=category,  # type: ignore[arg-type]
        severity=severity,
        evidence_span=_evidence_span(text, rules.hits),
        reason=reason,
        money_stance=stance,
        rule_hits=rules.hits,
        safety=GuardianSafety(distress=distress, risk_flags=risk_flags),
        source="fallback",
    )


def _evidence_span(text: str, hits: list[str]) -> str:
    """Shortest snippet justifying the hit — capped, never the whole message."""
    if not hits:
        return ""
    lowered = text.lower()
    for hit in hits:
        idx = lowered.find(hit)
        if idx >= 0:
            start = max(0, idx - 30)
            end = min(len(text), idx + len(hit) + 30)
            return text[start:end].strip()[:120]
    return ""


def _classify_with_gemini(
    client: GeminiClient, text: str, sender_role: str
) -> GuardianVerdict | None:
    """Live classifier. Returns None so callers fall back when unavailable.

    The user text is wrapped as DATA in the prompt (loaded from
    prompts/guardian.md) and the result is validated into GuardianVerdict.
    """
    result: GenerationResult = client.structured(
        "guardian",
        {"text": text, "sender_role": sender_role},
        GuardianVerdict,
    )
    if result.source != "gemini" or result.data is None:
        return None
    verdict = result.data
    # The model never decides pitch status for a mentee either.
    if sender_role != "mentor":
        verdict.is_pitch = False
    verdict.source = "gemini"
    return verdict


# --- Layer 3: deterministic action policy ------------------------------------
# Spec section 10.5: severity -> action. This is CODE, never the model.

SEVERITY_TO_ACTION = {
    0: "ALLOW",
    1: "ALLOW",
    2: "WARN",
    3: "BLOCK_AND_REDACT",
}

REDACTED_TEXT = "[Message removed: promotion or contact details]"
WARN_TAG = "Possible promotion"


def decide(verdict: GuardianVerdict, sender_role: str) -> GuardianDecision:
    """Map a verdict to an action. Pure deterministic code — fully testable.

    - severity 0/1 -> ALLOW (1 is logged but shown).
    - severity 2   -> WARN: shown, tagged "Possible promotion".
    - severity 3   -> BLOCK_AND_REDACT: replaced with a notice, strike +1.
    Only mentor strikes count toward ending a session (a mentee cannot be
    "struck" for their own distress or a mistyped number).
    """
    severity = max(0, min(3, verdict.severity))
    action = SEVERITY_TO_ACTION[severity]

    strike = action == "BLOCK_AND_REDACT" and sender_role == "mentor"
    ends = False

    if action == "BLOCK_AND_REDACT":
        display = REDACTED_TEXT
        tag = None
    elif action == "WARN":
        display = None  # original text shown; caller supplies it
        tag = WARN_TAG
    else:
        display = None
        tag = None

    return GuardianDecision(
        action=action,  # type: ignore[arg-type]
        final_severity=severity,
        strike_incurred=strike,
        ends_session=ends,
        display_text=display if display is not None else "",
        tag=tag,
    )


def screen_message(
    text: str,
    sender_role: str,
    gemini: GeminiClient | None = None,
) -> tuple[GuardianVerdict, GuardianDecision]:
    """Run the full pipeline on one message. Returns (verdict, decision).

    Layer 0 (Model Armor) is intentionally absent here: it is a cloud-only
    service with no local equivalent, so it is wired in when configured and
    simply skipped otherwise — the app never pretends it ran.
    """
    verdict: GuardianVerdict | None = None
    if gemini is not None:
        verdict = _classify_with_gemini(gemini, text, sender_role)
    if verdict is None:
        verdict = classify_fallback(text, sender_role)

    decision = decide(verdict, sender_role)
    # On ALLOW/WARN the recipient sees the original; on block, the notice.
    if decision.action != "BLOCK_AND_REDACT":
        decision.display_text = text
    return verdict, decision


__all__ = [
    "screen_message",
    "classify_fallback",
    "decide",
    "run_rules",
    "REDACTED_TEXT",
    "WARN_TAG",
]
