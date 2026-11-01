import httpx
import pytest

from workflows.events import claim_demo_fail, make_event_id, post_event
from workflows.main import app
from workflows.tasks.pipeline import run_pipeline


def test_tasks_are_registered_with_retry():
    assert run_pipeline.name == "run_pipeline"
    assert "run_pipeline" in app._registry.get_task_names()


def test_event_ids_are_deterministic():
    assert make_event_id("r1", "stage", "variants") == "r1:stage:variants"
    assert make_event_id("r1", "run_started") == "r1:run_started"


def recording_client(responses: dict[str, dict]):
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        suffix = request.url.path.rsplit("/", 1)[-1]
        return httpx.Response(200, json=responses.get(suffix, {"ok": True}))

    return httpx.AsyncClient(transport=httpx.MockTransport(handler)), calls


@pytest.mark.asyncio
async def test_post_event_sends_auth_and_idempotency_key():
    client, calls = recording_client({})
    await post_event("r1", "stage", {"stage": "variants"}, key="variants", client=client)
    req = calls[0]
    assert req.url.path == "/internal/runs/r1/events"
    assert req.headers["authorization"].startswith("Bearer ")
    assert b'"event_id":"r1:stage:variants"' in req.content.replace(b" ", b"")


@pytest.mark.asyncio
async def test_claim_demo_fail_reads_the_api_answer():
    client, _ = recording_client({"demo-fail-claim": {"fail": True}})
    assert await claim_demo_fail("r1", client=client) is True
    client2, _ = recording_client({"demo-fail-claim": {"fail": False}})
    assert await claim_demo_fail("r1", client=client2) is False


@pytest.mark.asyncio
async def test_run_pipeline_round_trip_posts_started_then_completed(monkeypatch):
    sent: list[tuple[str, str]] = []

    async def fake_post_event(run_id, event_type, payload=None, **_):
        sent.append((run_id, event_type))

    monkeypatch.setattr("workflows.tasks.pipeline.post_event", fake_post_event)
    out = await run_pipeline.func(None, {"run_id": "r1", "mode": "generate", "text": "hi", "demo_fail": False})
    assert out["status"] == "completed"
    assert sent == [("r1", "run_started"), ("r1", "run_completed")]


@pytest.mark.asyncio
async def test_run_pipeline_reports_failure_and_reraises(monkeypatch):
    sent: list[str] = []

    async def fake_post_event(run_id, event_type, payload=None, **_):
        sent.append(event_type)
        if event_type == "run_started":
            raise RuntimeError("boom")

    monkeypatch.setattr("workflows.tasks.pipeline.post_event", fake_post_event)
    with pytest.raises(RuntimeError):
        await run_pipeline.func(None, {"run_id": "r1", "mode": "generate", "text": "hi", "demo_fail": False})
    assert sent[-1] == "run_failed"
