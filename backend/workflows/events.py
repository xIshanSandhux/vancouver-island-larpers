"""Outgoing calls from workflow tasks to the API.

Task runs cannot receive connections, so progress is pushed here and the browser polls the API
(architecture.md section 1). Event ids make delivery idempotent: a retried task may re-send.
"""

import asyncio
import logging
from typing import Any

import httpx

from app.config import get_settings

log = logging.getLogger("workflows.events")

_TIMEOUT = 10.0
_ATTEMPTS = 3


def make_event_id(run_id: str, event_type: str, key: str = "") -> str:
    """Deterministic id so a retried task re-sends the same id. `key` distinguishes repeats."""
    return f"{run_id}:{event_type}:{key}" if key else f"{run_id}:{event_type}"


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {get_settings().workflow_event_secret}"}


def _url(run_id: str, suffix: str) -> str:
    return f"{get_settings().web_base_url.rstrip('/')}/internal/runs/{run_id}/{suffix}"


async def _post(url: str, body: dict[str, Any], client: httpx.AsyncClient | None) -> httpx.Response:
    owns = client is None
    client = client or httpx.AsyncClient(timeout=_TIMEOUT)
    try:
        last: Exception | None = None
        for attempt in range(_ATTEMPTS):
            try:
                res = await client.post(url, json=body, headers=_headers())
                if res.status_code < 500:
                    return res
                last = RuntimeError(f"{res.status_code} from {url}")
            except httpx.TransportError as exc:
                last = exc
            await asyncio.sleep(0.25 * (2**attempt))
        assert last is not None
        raise last
    finally:
        if owns:
            await client.aclose()


async def post_event(
    run_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    key: str = "",
    event_id: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Send one event to the API. Never raises for a 4xx: a bad event must not crash a run."""
    body = {
        "event_id": event_id or make_event_id(run_id, event_type, key),
        "type": event_type,
        "payload": payload or {},
    }
    res = await _post(_url(run_id, "events"), body, client)
    if res.status_code >= 400:
        log.warning("event rejected run_id=%s type=%s status=%s", run_id, event_type, res.status_code)


async def claim_demo_fail(run_id: str, *, client: httpx.AsyncClient | None = None) -> bool:
    """True exactly once per run with demo mode on (the API is the source of truth)."""
    res = await _post(_url(run_id, "demo-fail-claim"), {}, client)
    if res.status_code >= 400:
        log.warning("demo-fail-claim rejected run_id=%s status=%s", run_id, res.status_code)
        return False
    return bool(res.json().get("fail"))
