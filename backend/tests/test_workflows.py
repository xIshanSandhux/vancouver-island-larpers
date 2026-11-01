"""Workflow task tests.

Tasks are exercised by calling their bodies directly (`task.func`) with a fake context,
so none of this needs Render or a model key.
"""

import httpx
import pytest
from anthropic import APITimeoutError

from workflows.data import chunk
from workflows.demo_fail import SimulatedFailure, designated_batch_id
from workflows.events import claim_demo_fail, make_event_id, post_event
from workflows.llm.anthropic_client import LLMError, call_json, extract_json
from workflows.main import app
from workflows.tasks.commenters import MAX_COMMENT_CHARS, PersonaReaction, run_commenter_batch
from workflows.tasks.pipeline import run_pipeline, write_variant_batch
from workflows.tasks.reality import translate_reality
from workflows.tasks.tone_down import run_tone_down


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

    for module in ("pipeline", "commenters", "reality", "tone_down"):
        monkeypatch.setattr(f"workflows.tasks.{module}.post_event", fake_post_event, raising=False)
    async def fake_commenter_call_json(*, system, user, schema=None, max_tokens=1024, model=None):
        return {"action": "comment", "comment": "A useful reminder to keep it practical.", "appeal": 4, "cringe_flag": False}

    monkeypatch.setattr("workflows.tasks.commenters.call_json", fake_commenter_call_json)
    monkeypatch.setattr("workflows.demo_fail.post_event", fake_post_event)
    return captured


@pytest.fixture
def fake_llm(monkeypatch):
    """A model that always returns a clean, guardrail-safe post."""

    async def fake_call_json(*, system, user, schema=None, max_tokens=1024, model=None):
        if "original" in user:  # the reality translation prompt
            return {"translation": "It was a coffee.", "inflations": ["a mindset"]}
        opening = "Unpopular opinion: " if "Voice: Unpopular opinion." in user else ""
        return {"post": opening + "i got a coffee.\n\nthat is the whole story. an ordinary event does not need an extraordinary backstory. perhaps the real thought leadership is letting a small moment stay small, even when the urge to turn it into a grand lesson is very strong."}

    async def grounded(*_):
        return {}

    monkeypatch.setattr("workflows.tasks.pipeline.call_json", fake_call_json)
    monkeypatch.setattr("workflows.tasks.reality.call_json", fake_call_json)
    monkeypatch.setattr("workflows.tasks.pipeline.review_grounding", grounded)


def test_tasks_are_registered():
    names = app._registry.get_task_names()
    for task in ("run_pipeline", "write_variant_batch", "run_commenter_batch", "translate_reality", "run_tone_down"):
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


async def test_write_variant_batch_replaces_a_variant_that_invents_facts(monkeypatch):
    async def inventing(*, system, user, schema=None, max_tokens=1024, model=None):
        return {"post": "I joined Microsoft and raised 40 million dollars."}

    monkeypatch.setattr("workflows.tasks.pipeline.call_json", inventing)
    assignments = [{"post_id": "v01", "voice": {"id": "v", "label": "V", "instruction": "x"}}]
    out = await write_variant_batch.func(FakeCtx(), "r1", "i got a coffee.", assignments)
    assert len(out) == 1
    assert "Microsoft" not in out[0]["text"]
    assert "40 million" not in out[0]["text"]
    assert "grounded fallback" in out[0]["voice_label"]


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


async def test_tone_down_emits_rewrite_failure_without_run_failure(events, monkeypatch):
    async def malformed(**_):
        return {}

    monkeypatch.setattr("workflows.tasks.tone_down.call_json", malformed)
    with pytest.raises(RuntimeError):
        await run_tone_down.func(
            FakeCtx(),
            {
                "run_id": "r-tone",
                "draft": "I got a coffee and went to a meeting.",
                "cringe_result": {"rule_score": 10, "reasons": []},
            },
        )
    assert events[-1][0] == "rewrite_failed"


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


async def test_model_timeout_gets_one_explicit_retry(monkeypatch):
    attempts = 0

    class Messages:
        async def create(self, **_):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise APITimeoutError(request=httpx.Request("POST", "https://api.anthropic.com"))
            block = type("Block", (), {"type": "text", "text": '{"ok": true}'})()
            return type("Message", (), {"stop_reason": None, "content": [block]})()

    client = type("Client", (), {"messages": Messages()})()
    monkeypatch.setattr("workflows.llm.anthropic_client.get_client", lambda: client)
    out = await call_json(system="test", user="test", schema=None)
    assert out == {"ok": True}
    assert attempts == 2


def _async(value):
    async def inner():
        return value

    return inner()


class TestPersonaReactionNormalisation:
    """Claude's reply is reconciled rather than rejected.

    Regression test for a bug found by running the real model: roughly one reply in
    six chose "like" *and* wrote a comment, which the validator refused. Those were
    replaced by a neutral "ignore", which discarded the liveliest reactions and their
    cringe flags.
    """

    def test_a_like_keeps_its_action_and_discards_stray_comment_text(self):
        reaction = PersonaReaction.model_validate(
            {"action": "like", "comment": "Love this! 🎉", "appeal": 3, "cringe_flag": True}
        )
        assert reaction.action == "like"
        assert reaction.comment is None
        assert reaction.cringe_flag is True

    def test_a_comment_with_no_text_becomes_an_ignore(self):
        reaction = PersonaReaction.model_validate(
            {"action": "comment", "comment": "   ", "appeal": 2, "cringe_flag": False}
        )
        assert reaction.action == "ignore"
        assert reaction.comment is None

    @pytest.mark.parametrize("action", ["ignore", "report"])
    def test_text_is_dropped_when_the_persona_scrolled_past(self, action):
        reaction = PersonaReaction.model_validate(
            {"action": action, "comment": "why am I talking", "appeal": 1, "cringe_flag": True}
        )
        assert reaction.action == action
        assert reaction.comment is None

    def test_well_formed_replies_are_untouched(self):
        for raw in (
            {"action": "comment", "comment": "Great post!", "appeal": 4, "cringe_flag": False},
            {"action": "like", "comment": None, "appeal": 5, "cringe_flag": False},
            {"action": "ignore", "comment": None, "appeal": 2, "cringe_flag": False},
        ):
            reaction = PersonaReaction.model_validate(raw)
            assert reaction.action == raw["action"]
            assert reaction.comment == raw["comment"]

    def test_the_invariant_the_feed_relies_on_always_holds(self):
        """Whatever Claude sends, comment text exists if and only if action is comment."""
        for action in ("like", "comment", "ignore", "report"):
            for comment in (None, "", "   ", "something"):
                reaction = PersonaReaction.model_validate(
                    {"action": action, "comment": comment, "appeal": 3, "cringe_flag": False}
                )
                assert (reaction.comment is not None) == (reaction.action == "comment")


def test_schemas_sent_to_the_api_avoid_unsupported_keywords():
    """Structured outputs reject some JSON Schema keywords with a 400.

    A `maxItems` on the reality schema made every real call fail and fall back
    silently, so the feature looked fine in tests and was dead in production.
    Caps belong in the Pydantic models instead.
    """
    import json

    from workflows.tasks.commenters import PersonaReaction
    from workflows.tasks.pipeline import _VARIANT_SCHEMA
    from workflows.tasks.reality import _SCHEMA

    unsupported = ("maxItems", "minItems")
    for name, schema in (
        ("reality", _SCHEMA),
        ("variant", _VARIANT_SCHEMA),
        ("persona reaction", PersonaReaction.model_json_schema()),
    ):
        serialised = json.dumps(schema)
        for keyword in unsupported:
            assert keyword not in serialised, f"{name} schema still sends {keyword}"


async def test_reality_caps_inflations_without_relying_on_the_schema(monkeypatch):
    """The cap moved out of the schema, so prove it is still enforced."""

    async def five_inflations(**kwargs):
        return {"translation": "inflated a coffee", "inflations": [f"p{i}" for i in range(5)]}

    monkeypatch.setattr("workflows.tasks.reality.call_json", five_inflations)
    out = await translate_reality.func(
        FakeCtx(), "r1", "i got a coffee.", {"post_id": "v01", "text": "x"}
    )
    assert len(out["inflations"]) == 3
    assert out["translation"] == "inflated a coffee"


class TestOverLongComments:
    """Pydantic rejected comments over 140 chars, discarding the whole reaction.

    That showed up as intermittent fallbacks in real runs, worst on posts that invite
    longer replies. Trimming keeps the persona's reaction and its cringe flag.
    """

    LONG = (
        "This is a genuinely thoughtful reply about coffee rituals and meeting culture "
        "that simply runs well past the limit the prompt asked the model to respect."
    )

    def test_a_long_comment_is_trimmed_not_discarded(self):
        reaction = PersonaReaction.model_validate(
            {"action": "comment", "comment": self.LONG, "appeal": 4, "cringe_flag": True}
        )
        assert reaction.action == "comment"
        assert reaction.comment is not None
        assert len(reaction.comment) <= MAX_COMMENT_CHARS
        assert reaction.comment.endswith("…")
        assert reaction.cringe_flag is True

    def test_trimming_happens_at_a_word_boundary(self):
        reaction = PersonaReaction.model_validate(
            {"action": "comment", "comment": self.LONG, "appeal": 3, "cringe_flag": False}
        )
        assert "  " not in reaction.comment
        assert self.LONG.startswith(reaction.comment.rstrip("…"))

    def test_a_comment_at_the_limit_is_untouched(self):
        exact = "x" * MAX_COMMENT_CHARS
        reaction = PersonaReaction.model_validate(
            {"action": "comment", "comment": exact, "appeal": 3, "cringe_flag": False}
        )
        assert reaction.comment == exact

    def test_a_long_comment_on_a_like_does_not_convert_the_action(self):
        """Over-length text plus the like/comment mismatch, together."""
        reaction = PersonaReaction.model_validate(
            {"action": "like", "comment": self.LONG, "appeal": 5, "cringe_flag": True}
        )
        assert reaction.action == "like"
        assert reaction.comment is None
