"""Log hygiene tests: no free text can leak into structured logs."""

from __future__ import annotations

import json

from app.observability import log_event, new_request_id


def test_log_event_emits_json_line(capsys) -> None:
    log_event("guardian_decision", session_id="s_1", severity=2, action="WARN")
    line = capsys.readouterr().out.strip()
    record = json.loads(line)
    assert record["event"] == "guardian_decision"
    assert record["session_id"] == "s_1"
    assert record["severity"] == 2
    assert record["ts"].endswith("Z")


def test_long_values_are_truncated(capsys) -> None:
    user_content = "this looks like message text " * 20  # > 120 chars
    log_event("oops", detail=user_content)
    record = json.loads(capsys.readouterr().out.strip())
    assert record["detail"].startswith("[truncated:")
    assert "message text" not in record["detail"]


def test_request_id_appears_when_provided(capsys) -> None:
    rid = new_request_id()
    assert len(rid) == 12
    log_event("api_request", request_id=rid, status=200)
    record = json.loads(capsys.readouterr().out.strip())
    assert record["request_id"] == rid


def test_log_lines_have_no_newlines(capsys) -> None:
    log_event("api_request", path="/api/needs", latency_ms=42)
    out = capsys.readouterr().out
    assert out.count("\n") == 1
