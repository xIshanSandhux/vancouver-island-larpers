"""Workflow task tests.

Tasks are exercised by calling their bodies directly (`task.func`) with a fake context,
so none of this needs Render or a model key.
"""

import httpx
import pytest

from workflows.data import chunk
from workflows.demo_fail import SimulatedFailure, designated_batch_id
from workflows.events import claim_demo_fail, make_event_id, post_event
from workflows.llm.anthropic_client import LLMError, extract_json
from workflows.main import app
from workflows.tasks.commenters import run_commenter_batch
from workflows.tasks.pipeline import run_pipeline, write_variant_batch
from workflows.tasks.reality import translate_reality


class FakeCtx:
    """Runs child tasks in-process instead of on Render."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def run(self, task, *args, **kwargs):
        self.calls.append(task.name)
        return await task.func(self, *args, **kwargs)


@pytest.fixture
def events(monkeypatch):
    """Capture every event the tasks post, from all three task modules."""
    captured: list[tuple[str, str]] = []

    async def fake_post_event(run_id, event_type, payload=None, **_):
        captured.append((event_type, payload or {}))

    for module in ("pipeline", "commenters", "reality"):
        monkeypatch.setattr(f"workflows.tasks.{module}.post_event", fake_post_event, raising=False)
    monkeypatch.setattr("workflows.demo_fail.post_event", fake_post_event)
    return captured


@pytest.fixture
def fake_llm(monkeypatch):
    """A model that always returns a clean, guardrail-safe post."""

    async def fake_call_json(*, system, user, schema=None, max_tokens=1024, model=None):
        if "original" in user:  # the reality translation prompt
            return {"translation": "It was a coffee.", "inflations": ["a mindset"]}
        return {"post": "i got a coffee and went to a meeting.\n\nthat is the whole story."}

    monkeypatch.setattr("workflows.tasks.pipeline.call_json", fake_call_json)
    monkeypatch.setattr("workflows.tasks.reality.call_json", fake_call_json)


def test_tasks_are_registered():
    names = app._registry.get_task_names()
    for task in ("run_pipeline", "write_variant_batch", "run_commenter_batch", "translate_reality"):
        assert task in names


def test_event_ids_are_deterministic():
    assert make_event_id("r1", "stage", "variants") == "r1:stage:variants"
    assert make_event_id("r1", "run_started") == "r1:run_started"


def test_chunk_splits_evenly_and_never_returns_empty():
    assert chunk(list(range(50)), 2) == [list(range(25)), list(range(25, 50))]
    assert chunk([], 4) == [[]]
    assert chunk([1], 4) == [[1]]


def test_extract_json_tolerates_fences_and_prose():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": 2} hope that helps') == {"a": 2}
    with pytest.raises(LLMError):
        extract_json("no json here")


def recording_client(responses: dict[str, dict]):
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        suffix = request.url.path.rsplit("/", 1)[-1]
        return httpx.Response(200, json=responses.get(suffix, {"ok": True}))

    return httpx.AsyncClient(transport=httpx.MockTransport(handler)), calls


async def test_post_event_sends_auth_and_idempotency_key():
    client, calls = recording_client({})
    await post_event("r1", "stage", {"stage": "variants"}, key="variants", client=client)
    req = calls[0]
    assert req.url.path == "/internal/runs/r1/events"
    assert req.headers["authorization"].startswith("Bearer ")
    assert b'"event_id":"r1:stage:variants"' in req.content.replace(b" ", b"")


async def test_claim_demo_fail_reads_the_api_answer():
    client, _ = recording_client({"demo-fail-claim": {"fail": True}})
    assert await claim_demo_fail("r1", client=client) is True
    client2, _ = recording_client({"demo-fail-claim": {"fail": False}})
    assert await claim_demo_fail("r1", client=client2) is False


async def test_write_variant_batch_returns_one_variant_per_voice(fake_llm):
    assignments = [
        {"post_id": "v01", "voice": {"id": "humblebrag", "label": "Humblebrag", "instruction": "x"}},
        {"post_id": "v02", "voice": {"id": "hot_take", "label": "Hot take", "instruction": "y"}},
    ]
    out = await write_variant_batch.func(FakeCtx(), "r1", "i got a coffee and went to a meeting.", assignments)
    assert [v["post_id"] for v in out] == ["v01", "v02"]
    assert out[0]["voice_id"] == "humblebrag"


async def test_write_variant_batch_drops_a_variant_that_invents_facts(monkeypatch):
    async def inventing(*, system, user, schema=None, max_tokens=1024, model=None):
        return {"post": "I joined Microsoft and raised 40 million dollars."}

    monkeypatch.setattr("workflows.tasks.pipeline.call_json", inventing)
    assignments = [{"post_id": "v01", "voice": {"id": "v", "label": "V", "instruction": "x"}}]
    assert await write_variant_batch.func(FakeCtx(), "r1", "i got a coffee.", assignments) == []


async def test_generate_run_reaches_completion_and_ranks(events, fake_llm):
    ctx = FakeCtx()
    out = await run_pipeline.func(
        ctx, {"run_id": "r1", "mode": "generate", "text": "i got a coffee.", "demo_fail": False}
    )
    assert out["status"] == "completed"
    kinds = [k for k, _ in events]
    assert kinds[0] == "run_started" and kinds[-1] == "run_completed"
    for required in ("variants_ready", "finalists_selected", "comment", "cringe_scored", "ranking_ready", "reality_ready"):
        assert required in kinds, required
    ranking = next(p["ranking"] for k, p in events if k == "ranking_ready")
    assert len(ranking) == 3
    assert ctx.calls.count("translate_reality") == 1


async def test_check_run_skips_variants_and_reality(events, fake_llm):
    out = await run_pipeline.func(
        ctx := FakeCtx(), {"run_id": "r2", "mode": "check", "text": "my real draft", "demo_fail": False}
    )
    assert out["status"] == "completed"
    kinds = [k for k, _ in events]
    assert "variants_ready" not in kinds
    assert "reality_ready" not in kinds
    assert "translate_reality" not in ctx.calls
    assert next(p["finalist_ids"] for k, p in events if k == "finalists_selected") == ["draft"]


async def test_run_failed_is_posted_and_reraised(events, monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("model down")

    monkeypatch.setattr("workflows.tasks.pipeline.call_json", boom)
    monkeypatch.setattr("workflows.data.load_voices", lambda: [])
    with pytest.raises(Exception):
        await run_pipeline.func(
            FakeCtx(), {"run_id": "r3", "mode": "generate", "text": "x", "demo_fail": False}
        )
    assert [k for k, _ in events][-1] == "run_failed"


async def test_demo_mode_fails_the_designated_batch_once(events, monkeypatch):
    """The API decides; the batch obeys. First claim fails, the retry succeeds."""
    answers = iter([True, False])
    monkeypatch.setattr("workflows.demo_fail.claim_demo_fail", lambda run_id: _async(next(answers)))

    designated = designated_batch_id(["v01"])
    post = {"post_id": "v01", "voice_id": "v", "voice_label": "V", "text": "t"}

    with pytest.raises(SimulatedFailure):
        await run_commenter_batch.func(FakeCtx(), "r1", post, ["p01"], designated, True, designated)

    # Render retries the same batch; this time it runs normally.
    out = await run_commenter_batch.func(FakeCtx(), "r1", post, ["p01"], designated, True, designated)
    assert len(out) == 1
    assert ("demo_failure_triggered", {"batch_id": "v01-b1"}) in events


async def test_other_batches_never_fail_in_demo_mode(events):
    post = {"post_id": "v01", "voice_id": "v", "voice_label": "V", "text": "t"}
    out = await run_commenter_batch.func(FakeCtx(), "r1", post, ["p01"], "v01-b2", True, "v01-b1")
    assert len(out) == 1


async def test_reality_falls_back_instead_of_failing_the_run(monkeypatch):
    async def boom(**kwargs):
        raise LLMError("nope")

    monkeypatch.setattr("workflows.tasks.reality.call_json", boom)
    out = await translate_reality.func(FakeCtx(), "r1", "i got a coffee.", {"post_id": "v01", "text": "x"})
    assert "i got a coffee." in out["translation"]


def _async(value):
    async def inner():
        return value

    return inner()
