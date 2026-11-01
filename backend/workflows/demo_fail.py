"""The demo failure switch (M7, architecture.md section 6).

Render retries a failed task automatically, and the dashboard shows the failed attempt
followed by the successful one. That is our durability proof, but a real failure cannot
be scheduled, so demo mode injects exactly one.

The SDK does not expose the attempt number, so the API decides: it answers "fail" to the
first claim for a run and "do not fail" to every later one. The retry therefore succeeds.
"""

import logging

from workflows.events import claim_demo_fail, post_event

log = logging.getLogger("workflows.demo_fail")


class SimulatedFailure(RuntimeError):
    """Raised on purpose in demo mode so Render retries the task."""


def designated_batch_id(finalist_ids: list[str]) -> str | None:
    """The one batch allowed to fail: the first commenter batch of the first finalist."""
    return f"{finalist_ids[0]}-b1" if finalist_ids else None


async def maybe_fail(run_id: str, batch_id: str, demo_fail: bool, designated: str | None) -> None:
    """Call at the top of a commenter batch. Raises once per run when demo mode is on."""
    if not demo_fail or batch_id != designated:
        return
    if not await claim_demo_fail(run_id):
        log.info("demo failure already used run_id=%s batch=%s", run_id, batch_id)
        return
    log.info("injecting simulated failure run_id=%s batch=%s", run_id, batch_id)
    await post_event(run_id, "demo_failure_triggered", {"batch_id": batch_id}, key=batch_id)
    raise SimulatedFailure("simulated failure (demo mode)")
