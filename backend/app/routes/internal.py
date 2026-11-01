"""Endpoints only the workflow tasks call. Shared-secret protected.

Task runs cannot receive incoming connections, so progress travels this way: tasks POST
here, the browser polls the public endpoints.
"""

import logging
import secrets

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models import RunEvent
from app.store import store

log = logging.getLogger("app.internal")
router = APIRouter(prefix="/internal")


def _authorized(authorization: str | None) -> bool:
    expected = get_settings().workflow_event_secret
    if not authorization or not authorization.startswith("Bearer "):
        return False
    return secrets.compare_digest(authorization[7:], expected)


@router.post("/runs/{run_id}/events")
async def ingest_event(
    run_id: str, event: RunEvent, authorization: str | None = Header(default=None)
) -> JSONResponse:
    if not _authorized(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized", "code": "not_found"})

    known, duplicate = await store.apply_event(run_id, event)
    if not known:
        return JSONResponse(status_code=404, content={"error": "unknown run", "code": "not_found"})
    if not duplicate:
        log.info("event run_id=%s type=%s", run_id, event.type)
    return JSONResponse({"ok": True, "duplicate": duplicate})


@router.post("/runs/{run_id}/demo-fail-claim")
async def demo_fail_claim(
    run_id: str, request: Request, authorization: str | None = Header(default=None)
) -> JSONResponse:
    if not _authorized(authorization):
        return JSONResponse(status_code=401, content={"error": "unauthorized", "code": "not_found"})
    del request
    fail = await store.claim_demo_fail(run_id)
    if fail:
        log.info("demo failure claimed run_id=%s", run_id)
    return JSONResponse({"fail": fail})
