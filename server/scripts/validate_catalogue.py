"""One-off validation of catalogue_entries.py before wiring it into the app."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.catalogue_entries import EDGES, ENTRIES  # noqa: E402

errors: list[str] = []

# --- Entries ---------------------------------------------------------------
slugs = [e["slug"] for e in ENTRIES]
print(f"entries: {len(ENTRIES)}")
if not (80 <= len(ENTRIES) <= 120):
    errors.append(f"entry count {len(ENTRIES)} outside 80-120")
if len(set(slugs)) != len(slugs):
    dupes = {s for s in slugs if slugs.count(s) > 1}
    errors.append(f"duplicate slugs: {dupes}")

slug_set = set(slugs)
categories: dict[str, int] = {}
REQUIRED = (
    "slug", "title", "category", "short_description", "long_description",
    "beginner_step", "tags", "skills", "materials", "ways_of_thinking",
    "accessibility_notes", "solo_or_group", "online_or_in_person",
    "languages", "source_notes", "is_sample_content",
)
for e in ENTRIES:
    for key in REQUIRED:
        if key not in e or e[key] is None or e[key] == []:
            if key not in ("time_commitment", "difficulty"):
                if not e.get(key):
                    errors.append(f"{e.get('slug', '?')}: missing {key}")
    categories[e["category"]] = categories.get(e["category"], 0) + 1
    if e["languages"] != ["en"]:
        errors.append(f"{e['slug']}: languages != ['en']")
    if e["is_sample_content"] is not True:
        errors.append(f"{e['slug']}: is_sample_content not True")
    for v in e["solo_or_group"]:
        if v not in ("solo", "group"):
            errors.append(f"{e['slug']}: bad solo value {v!r}")
    for v in e["online_or_in_person"]:
        if v not in ("online", "in_person"):
            errors.append(f"{e['slug']}: bad mode value {v!r}")
    if e["difficulty"] not in (None, "beginner", "intermediate"):
        errors.append(f"{e['slug']}: bad difficulty {e['difficulty']!r}")
    if " " in e["slug"] or e["slug"] != e["slug"].lower():
        errors.append(f"{e['slug']}: malformed slug")

print(f"categories ({len(categories)}):")
for name, count in sorted(categories.items()):
    print(f"  {count:2d}  {name}")

# --- Edges ----------------------------------------------------------------
print(f"edges: {len(EDGES)}")
TYPES = {
    "shares_material", "shares_technique", "shares_skill",
    "shares_way_of_thinking", "related_culture_or_context",
    "complementary_activity", "prerequisite_for", "contrasts_with",
}
seen_pairs: set[tuple[str, str]] = set()
used_types: set[str] = set()
participation: dict[str, int] = {s: 0 for s in slug_set}
for edge in EDGES:
    if len(edge) not in (3, 4):
        errors.append(f"bad edge arity: {edge}")
        continue
    frm, to, kind = edge[0], edge[1], edge[2]
    if frm not in slug_set:
        errors.append(f"edge from unknown slug: {frm}")
    if to not in slug_set:
        errors.append(f"edge to unknown slug: {to}")
    if kind not in TYPES:
        errors.append(f"bad edge type: {kind}")
    if (frm, to) in seen_pairs:
        errors.append(f"duplicate edge pair: {frm} -> {to}")
    seen_pairs.add((frm, to))
    used_types.add(kind)
    participation[frm] = participation.get(frm, 0) + 1
    participation[to] = participation.get(to, 0) + 1

under = sorted(s for s, n in participation.items() if n < 2)
if under:
    errors.append(f"{len(under)} slugs with <2 edge participation: {under}")
unused_types = TYPES - used_types
if unused_types:
    errors.append(f"relationship types never used: {unused_types}")
print(f"types used: {len(used_types)}/8; min participation: {min(participation.values())}")

# --- Result ---------------------------------------------------------------
if errors:
    print(f"\nFAILED with {len(errors)} problems:")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
print("\nOK: catalogue validates cleanly.")
