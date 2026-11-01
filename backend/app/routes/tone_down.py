"""Start the asynchronous tone-down task for a completed Check run."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models import ApiError
from app.render_client import RenderUnavailable, start_run
from app.store import store

router = APIRouter(prefix="/api")


def _error(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(status_code=status, content=ApiError(error=message, code=code).model_dump())


@router.post("/runs/{run_id}/tone-down", status_code=202)
async def tone_down(run_id: str) -> JSONResponse:
    run = await store.get(run_id)
    if run is None:
        return _error("not_found", "That run has expired or never existed.", 404)
    if run.mode != "check" or run.status != "completed" or run.rewrite is not None:
        return _error("invalid_input", "Tone down is available only after a Check score completes.", 400)
    score = next((item for item in run.scores if item.post_id == "draft"), None)
    if score is None:
        return _error("invalid_input", "This run does not have a completed draft score yet.", 400)
    payload = {
        "run_id": run_id,
        "draft": run.input_text,
        "cringe_result": score.cringe.model_dump(),
    }
    try:
        await start_run("run_tone_down", payload, run_id=run_id)
    except RenderUnavailable:
        return _error("render_unavailable", "Could not reach the workflow service.", 502)
    return JSONResponse(status_code=202, content={"ok": True})
