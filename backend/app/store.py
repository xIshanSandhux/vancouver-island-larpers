"""In-memory run state (architecture.md section 4).

There is no database on purpose. That buys simplicity and costs us one constraint: the
API must run as a single instance with one worker, or two browsers will see two
different halves of a run.

Events arrive from workflow task runs and are idempotent by `event_id`, because Render
retries failed tasks and a retried task re-sends what it already sent.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.models import (
    CommentResult,
    PostScore,
    Reality,
    RunEvent,
    RunState,
    Rewrite,
    Variant,
)

RUN_TTL = timedelta(hours=1)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[str, RunState] = {}
        self._seen_events: dict[str, set[str]] = {}
        self._demo_fail_claimed: set[str] = set()
        self._lock = asyncio.Lock()

    async def create(self, mode: str, text: str, demo_fail: bool) -> RunState:
        run = RunState(
            run_id=f"run-{uuid.uuid4().hex[:12]}",
            mode=mode,
            status="queued",
            stage="queued",
            input_text=text,
            demo_fail=demo_fail,
            started_at=_now(),
            updated_at=_now(),
        )
        async with self._lock:
            self._purge_locked()
            self._runs[run.run_id] = run
            self._seen_events[run.run_id] = set()
        return run

    async def get(self, run_id: str) -> RunState | None:
        async with self._lock:
            return self._runs.get(run_id)

    async def active_count(self) -> int:
        async with self._lock:
            self._purge_locked()
            return sum(1 for r in self._runs.values() if r.status in ("queued", "running"))

    async def set_task_run_id(self, run_id: str, task_run_id: str) -> None:
        async with self._lock:
            run = self._runs.get(run_id)
            if run:
                run.task_run_id = task_run_id
                run.updated_at = _now()

    async def mark_failed(self, run_id: str, error: str) -> None:
        async with self._lock:
            run = self._runs.get(run_id)
            # A run that already finished keeps its result; a late watcher error is noise.
            if run and run.status not in ("completed", "failed"):
                run.status = "failed"
                run.error = error
                run.updated_at = _now()

    async def claim_demo_fail(self, run_id: str) -> bool:
        """True exactly once per run, and only when the run asked for demo mode."""
        async with self._lock:
            run = self._runs.get(run_id)
            if not run or not run.demo_fail or run_id in self._demo_fail_claimed:
                return False
            self._demo_fail_claimed.add(run_id)
            return True

    async def apply_event(self, run_id: str, event: RunEvent) -> tuple[bool, bool]:
        """Returns (known_run, duplicate)."""
        async with self._lock:
            run = self._runs.get(run_id)
            if run is None:
                return False, False
            seen = self._seen_events.setdefault(run_id, set())
            if event.event_id in seen:
                return True, True
            seen.add(event.event_id)
            run.last_seq += 1
            event.seq = run.last_seq
            self._apply_locked(run, event)
            run.updated_at = _now()
            return True, False

    def _apply_locked(self, run: RunState, event: RunEvent) -> None:
        payload: dict[str, Any] = event.payload
        kind = event.type

        if kind == "run_started":
            run.status = "running"
        elif kind == "stage":
            run.stage = payload["stage"]
        elif kind == "variants_ready":
            run.variants = [Variant.model_validate(v) for v in payload["variants"]]
        elif kind == "finalists_selected":
            run.finalist_ids = list(payload["finalist_ids"])
            if not run.variants:  # check mode has no variant stage
                run.variants = [
                    Variant(post_id="draft", voice_id="user", voice_label="Your draft", text=run.input_text)
                ]
        elif kind == "comment":
            run.comments.append(CommentResult.model_validate(payload))
        elif kind == "cringe_scored":
            score = PostScore.model_validate(payload)
            run.scores = [s for s in run.scores if s.post_id != score.post_id] + [score]
        elif kind == "ranking_ready":
            run.ranking = list(payload["ranking"])
        elif kind == "reality_ready":
            run.reality = Reality.model_validate(payload)
        elif kind == "rewrite_ready":
            run.rewrite = Rewrite.model_validate(payload)
        elif kind == "demo_failure_triggered":
            run.retries_seen += 1
        elif kind == "run_completed":
            run.status = "completed"
            run.stage = "done"
        elif kind == "run_failed":
            run.status = "failed"
            run.error = str(payload.get("error", "unknown error"))

    def _purge_locked(self) -> None:
        cutoff = datetime.now(timezone.utc) - RUN_TTL
        stale = [
            rid
            for rid, run in self._runs.items()
            if datetime.fromisoformat(run.started_at) < cutoff
        ]
        for rid in stale:
            self._runs.pop(rid, None)
            self._seen_events.pop(rid, None)
            self._demo_fail_claimed.discard(rid)


store = RunStore()
