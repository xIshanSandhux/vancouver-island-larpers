"""run_pipeline: the root task. M1 ships the minimal round trip; M2/M3 fill in the real stages."""

import logging
from typing import Any

from render import TaskContext

from workflows.events import post_event
from workflows.registry import app

log = logging.getLogger("workflows.pipeline")


@app.task
async def run_pipeline(ctx: TaskContext, req: dict[str, Any]) -> dict[str, str]:
    """req is a RunRequest dict plus run_id: {run_id, mode, text, demo_fail}."""
    run_id: str = req["run_id"]
    log.info("run_pipeline start run_id=%s mode=%s", run_id, req.get("mode"))
    try:
        await post_event(run_id, "run_started", {"mode": req["mode"], "input_text": req["text"]})
        # TODO(M2/M3/I2/M4): variants -> filter -> commenters -> rank -> reality.
        await post_event(run_id, "run_completed", {})
    except Exception as exc:
        log.exception("run_pipeline failed run_id=%s", run_id)
        await post_event(run_id, "run_failed", {"error": str(exc)})
        raise
    return {"run_id": run_id, "status": "completed"}
