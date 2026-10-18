"""PII scrubbing tests (spec section 8)."""

from __future__ import annotations

from app.scrub import scrub


def test_email_is_scrubbed() -> None:
    result = scrub("reach me at jane.doe+work@example.com please")
    assert "[EMAIL]" in result.text
    assert "jane.doe" not in result.text
    assert result.counts["email"] == 1


def test_multiple_emails_counted() -> None:
    result = scrub("a@b.com and c@d.org and e@f.io")
    assert result.counts["email"] == 3
    assert "@" not in result.text.replace("[EMAIL]", "")


def test_international_phone_is_scrubbed() -> None:
    result = scrub("call me on +91 98765 43210 anytime")
    assert "[PHONE]" in result.text
    assert "98765" not in result.text


def test_phone_with_parentheses_and_dashes() -> None:
    result = scrub("office line (022) 4001-2345 is best")
    assert "[PHONE]" in result.text
    assert "4001" not in result.text


def test_url_is_scrubbed() -> None:
    result = scrub("see https://example.com/path?q=1 or www.example.org/x")
    assert "[URL]" in result.text
    assert "https://" not in result.text
    assert "www.example.org" not in result.text


def test_bare_domain_is_scrubbed() -> None:
    result = scrub("check myprofile.com for details")
    assert "[URL]" in result.text
    assert "myprofile.com" not in result.text


def test_social_handle_is_scrubbed() -> None:
    result = scrub("i'm @jane_doe on there")
    assert "[HANDLE]" in result.text
    assert "@jane_doe" not in result.text


def test_off_platform_request_detected_and_tokenised() -> None:
    result = scrub(" whatsapp me later")
    assert "[OFF_PLATFORM_REQUEST]" in result.text
    assert result.contact_request_detected is True
    assert result.counts["off_platform_request"] >= 1


def test_telegram_and_dm_variants() -> None:
    for phrase in ("telegram me", "dm me", "DM me your number", "ping me"):
        result = scrub(phrase)
        assert result.contact_request_detected is True, phrase


def test_visit_clinic_variant() -> None:
    result = scrub("you should visit our clinic in person")
    assert "[OFF_PLATFORM_REQUEST]" in result.text
    assert result.contact_request_detected is True


def test_name_in_identifying_phrase_is_scrubbed() -> None:
    result = scrub("hi, my name is John Smith and I need help")
    assert "[PERSON]" in result.text
    assert "John Smith" not in result.text


def test_call_me_name_variant() -> None:
    result = scrub("call me Alex when you can")
    # 'call me' is also an off-platform phrase; both effects are acceptable,
    # but the name must not survive.
    assert "Alex" not in result.text


def test_ordinary_sentence_is_unchanged() -> None:
    text = "I'm deciding whether to take a senior product role in fintech."
    result = scrub(text)
    assert result.text == text
    assert result.changed is False


def test_no_double_scrubbing_of_email_interior() -> None:
    result = scrub("mail me at a.b@c.com")
    assert result.counts.get("phone", 0) == 0
    assert result.counts["email"] == 1


def test_very_long_input_is_capped() -> None:
    result = scrub("x" * 50_000)
    assert len(result.text) <= 20_000


def test_none_input_is_safe() -> None:
    result = scrub(None)  # type: ignore[arg-type]
    assert result.text == ""


def test_scrubbed_text_never_contains_matched_values() -> None:
    """The counts-only helper must not leak content (spec section 15)."""
    result = scrub("secret person named Alice at alice@example.com")
    assert "alice" not in str(result.counts)
    assert result.counts == {"email": 1, "person": 1}
