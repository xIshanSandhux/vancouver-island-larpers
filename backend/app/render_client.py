"""Starting workflow runs from the API (architecture.md section 4).

`start_task` hands back the task run id immediately and the run keeps going on Render.
We also watch it in the background: if the root task dies without posting `run_failed`,
nothing else would ever update the run and the browser would poll a frozen page.
"""

import asyncio
import logging
from typing import Any

from render import RenderAsync

from app.config import get_settings
from app.store import store

log = logging.getLogger("app.render")


class RenderUnavailable(Exception):
    """Render could not start the run."""


_client: RenderAsync | None = None
_watchers: set[asyncio.Task] = set()


def get_client() -> RenderAsync:
    global _client
    if _client is None:
        settings = get_settings()
        _client = RenderAsync(token=settings.render_api_key or None)
    return _client


def task_slug(task_name: str) -> str:
    slug = get_settings().render_workflow_slug
    if not slug:
        raise RenderUnavailable("RENDER_WORKFLOW_SLUG is not set")
    return f"{slug}/{task_name}"


async def start_run(task_name: str, payload: dict[str, Any], *, run_id: str) -> str:
    """Start a root task run and watch it. Returns the Render task run id."""
    try:
        awaitable = await get_client().workflows.start_task(
            task_slug(task_name), [payload], idempotency_key=f"{run_id}:{task_name}"
        )
    except RenderUnavailable:
        raise
    except Exception as exc:  # the SDK raises several error types; all mean "no run"
        log.exception("start_task failed run_id=%s", run_id)
        raise RenderUnavailable(str(exc)) from exc

    watcher = asyncio.create_task(_watch(run_id, awaitable))
    _watchers.add(watcher)
    watcher.add_done_callback(_watchers.discard)
    return awaitable.id


async def _watch(run_id: str, awaitable: Any) -> None:
    """Awaiting the run raises if it ultimately fails, including after its retries."""
    try:
        await awaitable
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        log.warning("task run failed run_id=%s: %s", run_id, exc)
        await store.mark_failed(run_id, f"workflow run failed: {exc}")
