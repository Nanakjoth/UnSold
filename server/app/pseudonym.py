"""Server-side pseudonym generation.

Pseudonyms are generated from curated word lists with a random number. They are
never derived from user input, identity, email, or any real data (spec section
8), so this module deliberately accepts no text parameters at all.
"""

from __future__ import annotations

import random

_ADJECTIVES = (
    "calm", "steady", "bright", "quiet", "warm", "clear", "keen", "kind",
    "brave", "crisp", "fair", "gentle", "humble", "keen", "lively", "mellow",
    "nimble", "open", "patient", "plain", "rapid", "sage", "sharp", "sincere",
    "solid", "sunny", "thoughtful", "true", "wise", "young", "amber", "bold",
    "clever", "dawn", "eager", "fluent", "graceful", "honest", "independent",
    "joyful", "loyal", "modest", "noble", "optimistic", "practical", "reliable",
    "serene", "tolerant", "versatile", "watchful",
)

_ANIMALS = (
    "heron", "otter", "falcon", "badger", "crane", "dolphin", "elk", "finch",
    "gecko", "hummingbird", "ibex", "jay", "koala", "lynx", "macaw", "newt",
    "owl", "puffin", "quail", "rabbit", "seal", "tapir", "umbrellabird",
    "vicuna", "walrus", "yak", "zebra", "beaver", "camel", "dove", "egret",
    "fox", "giraffe", "hippo", "iguana", "jackal", "lemur", "mole", "nightingale",
    "orca", "parrot", "quokka", "raven", "sloth", "toucan", "urchin", "vulture",
    "wombat", "xenopus", "yowie",
)


def generate_pseudonym(rng: random.Random | None = None) -> str:
    """Return a fresh `adjective-animal-number` pseudonym."""
    source = rng or random
    return (
        f"{source.choice(_ADJECTIVES)}-{source.choice(_ANIMALS)}-{source.randint(100, 999)}"
    )
