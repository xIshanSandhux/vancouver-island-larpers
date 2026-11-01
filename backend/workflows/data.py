"""Loaders for the static JSON in data/.

Files owned by different people land at different times, so every loader degrades to a
usable default instead of raising. That keeps the pipeline runnable before I1 lands.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path

log = logging.getLogger("workflows.data")

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PERSONA_TOTAL = 50


@lru_cache
def load_voices() -> list[dict]:
    """The 20 post voices (M2). Each: {id, label, instruction}."""
    path = DATA_DIR / "voices.json"
    if not path.exists():
        log.error("voices.json missing at %s", path)
        return []
    return json.loads(path.read_text())


@lru_cache
def load_personas() -> list[dict]:
    """The 50 commenter personas (Ishan, I1). Empty until that file lands."""
    path = DATA_DIR / "personas.json"
    if not path.exists():
        log.warning("personas.json missing; using placeholder persona ids")
        return []
    return json.loads(path.read_text())


def persona_ids() -> list[str]:
    """Ids to fan the commenter batches over, whether or not personas.json exists yet."""
    personas = load_personas()
    if personas:
        return [p["id"] for p in personas]
    return [f"p{i:02d}" for i in range(1, PERSONA_TOTAL + 1)]


def chunk(items: list, parts: int) -> list[list]:
    """Split into `parts` near-even chunks, dropping empties. Used for task fan-out."""
    if not items:
        return [[]]
    parts = max(1, min(parts, len(items)))
    size = -(-len(items) // parts)  # ceiling division
    return [items[i : i + size] for i in range(0, len(items), size)]
