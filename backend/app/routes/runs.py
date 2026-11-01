"""Public run endpoints: start a run, then poll it."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.guard import GuardError, check_text, client_ip, limiter
from app.models import ApiError, RunRequest, RunState
from app.render_client import RenderUnavailable, start_run
from app.store import store

log = logging.getLogger("app.runs")
router = APIRouter(prefix="/api")


def _error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content=ApiError(error=message, code=code).model_dump())


@router.post("/runs")
async def create_run(req: RunRequest, request: Request) -> JSONResponse:
    settings = get_settings()
    try:
        text = check_text(req.mode, req.text)
        limiter.check(client_ip(request.headers.get("x-forwarded-for"), request.client.host if request.client else None))
    except GuardError as exc:
        return _error(exc.code, exc.message, exc.status)

    if await store.active_count() >= settings.max_active_runs:
        return _error("busy", "Both demo slots are busy, try again in a few seconds.", 429)

    run = await store.create(req.mode, text, req.demo_fail)
    payload = {"run_id": run.run_id, "mode": req.mode, "text": text, "demo_fail": req.demo_fail}
    try:
        task_run_id = await start_run("run_pipeline", payload, run_id=run.run_id)
    except RenderUnavailable as exc:
        await store.mark_failed(run.run_id, str(exc))
        return _error("render_unavailable", "Could not reach the workflow service.", 502)

    await store.set_task_run_id(run.run_id, task_run_id)
    log.info("run started run_id=%s task_run_id=%s", run.run_id, task_run_id)
    return JSONResponse({"run_id": run.run_id})


@router.get("/runs/{run_id}", response_model=None)
async def get_run(run_id: str) -> JSONResponse | RunState:
    run = await store.get(run_id)
    if run is None:
        return _error("not_found", "That run has expired or never existed.", 404)
    return run
