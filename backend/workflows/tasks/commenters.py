"""run_commenter_batch - the simulated audience.

STUB. Ishan replaces the body in task I2 with real Anthropic calls, one per persona,
validated against the JSON schema in architecture.md section 11. Until then this returns
deterministic fake reactions so the rest of the pipeline runs end to end.

Two things must survive the rewrite:
  * the `maybe_fail` call at the top (the demo failure switch, M7), and
  * posting one "comment" event per persona as it finishes, so the UI streams.
"""

import logging
import zlib
from typing import Any

from render import TaskContext

from app.models import CommentResult
from workflows.data import load_personas
from workflows.demo_fail import maybe_fail
from workflows.events import post_event
from workflows.registry import app

log = logging.getLogger("workflows.commenters")

_FALLBACK_LABELS = ["Recruiter", "Growth Lead", "Founder", "Engineer", "People Ops"]


def persona_info(persona_id: str) -> dict[str, str]:
    """Persona display fields, with a placeholder shape until personas.json lands."""
    for persona in load_personas():
        if persona["id"] == persona_id:
            return persona
    index = int("".join(c for c in persona_id if c.isdigit()) or 0)
    return {
        "id": persona_id,
        "name": f"Persona {index}",
        "label": _FALLBACK_LABELS[index % len(_FALLBACK_LABELS)],
        "archetype": "placeholder",
    }


@app.task
async def run_commenter_batch(
    ctx: TaskContext,
    run_id: str,
    post: dict[str, Any],
    persona_ids: list[str],
    batch_id: str,
    demo_fail: bool = False,
    designated_batch: str | None = None,
) -> list[dict[str, Any]]:
    """One slice of the audience reacting to one post."""
    await maybe_fail(run_id, batch_id, demo_fail, designated_batch)

    post_id = post["post_id"]
    results: list[CommentResult] = []
    for persona_id in persona_ids:
        persona = persona_info(persona_id)
        # Deterministic placeholder reactions; I2 replaces this with model calls.
        # crc32, not hash(): Python randomises string hashes per process.
        bucket = zlib.crc32(f"{post_id}:{persona_id}".encode()) % 4
        action = ("like", "comment", "ignore", "comment")[bucket]
        comment = f"Placeholder reaction from {persona['label']}." if action == "comment" else None
        result = CommentResult(
            event_id=f"{run_id}:{post_id}:{persona_id}",
            post_id=post_id,
            persona_id=persona_id,
            persona_name=persona["name"],
            persona_label=persona["label"],
            archetype=persona.get("archetype", "placeholder"),
            action=action,
            comment=comment,
            appeal=(bucket % 5) + 1,
            cringe_flag=bucket == 2,
        )
        results.append(result)
        await post_event(run_id, "comment", result.model_dump(), event_id=result.event_id)

    log.info("commenter batch done run_id=%s batch=%s n=%s", run_id, batch_id, len(results))
    return [r.model_dump() for r in results]
