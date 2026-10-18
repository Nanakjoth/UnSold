"""Validate each sample scenario surfaces its intended mentor as the top match.

Runs the deterministic interpreter + matcher over every scenario's text (after
scrubbing, exactly as /api/needs does) and reports the intended mentor's rank.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from app.mentor_corpus import MENTORS
from app.matching import interpret_need, match_mentors
from app.sample_scenarios import SCENARIOS
from app.scrub import scrub

fails = 0
for sc in SCENARIOS:
    cleaned = scrub(sc.text).text
    intent, _ = interpret_need(cleaned, money_involved=sc.money_involved)
    matches, no_strong, _src = match_mentors(MENTORS, intent, cleaned, top_n=5)
    ids = [m.mentor.id for m in matches]
    rank = ids.index(sc.intended_mentor_id) + 1 if sc.intended_mentor_id in ids else None
    fit = next((m.fit_score for m in matches if m.mentor.id == sc.intended_mentor_id), None)
    ok = rank == 1
    if not ok:
        fails += 1
    status = "OK  " if ok else "MISS"
    print(f"{status} {sc.id:<28} domain={sc.domain:<16} rank={rank} fit={fit} no_strong={no_strong} top={ids[0] if ids else None}")

print(f"\n{len(SCENARIOS)-fails}/{len(SCENARIOS)} scenarios have their intended mentor ranked #1")
sys.exit(1 if fails else 0)
