import pytest

from app.models import RunEvent
from app.store import RunStore


@pytest.fixture
def store() -> RunStore:
    return RunStore()


def event(event_id: str, kind: str, payload: dict | None = None) -> RunEvent:
    return RunEvent(event_id=event_id, type=kind, payload=payload or {})


async def test_a_new_run_starts_queued(store):
    run = await store.create("generate", "hello", demo_fail=False)
    assert run.status == "queued" and run.stage == "queued"
    assert (await store.get(run.run_id)).run_id == run.run_id


async def test_events_drive_the_run_to_completion(store):
    run = await store.create("generate", "hello", demo_fail=False)
    await store.apply_event(run.run_id, event("e1", "run_started", {"mode": "generate", "input_text": "hello"}))
    await store.apply_event(run.run_id, event("e2", "stage", {"stage": "commenting"}))
    await store.apply_event(run.run_id, event("e3", "ranking_ready", {"ranking": ["v07", "v01"]}))
    await store.apply_event(run.run_id, event("e4", "run_completed"))

    state = await store.get(run.run_id)
    assert state.status == "completed"
    assert state.stage == "done"
    assert state.ranking == ["v07", "v01"]
    assert state.last_seq == 4


async def test_repeated_event_ids_are_ignored(store):
    """A retried task re-sends what it already sent; the comment must not double up."""
    run = await store.create("generate", "hello", demo_fail=False)
    comment = {
        "event_id": f"{run.run_id}:v01:p01",
        "post_id": "v01",
        "persona_id": "p01",
        "persona_name": "Dana",
        "persona_label": "Recruiter",
        "archetype": "recruiter",
        "action": "comment",
        "comment": "Great post!",
        "appeal": 4,
        "cringe_flag": False,
    }
    first = await store.apply_event(run.run_id, event(comment["event_id"], "comment", comment))
    second = await store.apply_event(run.run_id, event(comment["event_id"], "comment", comment))

    assert first == (True, False)
    assert second == (True, True)
    state = await store.get(run.run_id)
    assert len(state.comments) == 1
    assert state.last_seq == 1


async def test_cringe_scores_replace_rather_than_accumulate(store):
    run = await store.create("generate", "hello", demo_fail=False)
    score = {
        "post_id": "v01",
        "engagement_rate": 0.5,
        "appeal_mean": 3.0,
        "base_score": 40.0,
        "cringe": {"post_id": "v01", "rule_score": 10, "llm_score": None, "score": 10, "reasons": []},
    }
    await store.apply_event(run.run_id, event("s1", "cringe_scored", score))
    await store.apply_event(run.run_id, event("s2", "cringe_scored", {**score, "base_score": 55.0}))
    state = await store.get(run.run_id)
    assert len(state.scores) == 1 and state.scores[0].base_score == 55.0


async def test_events_for_an_unknown_run_are_reported(store):
    assert await store.apply_event("nope", event("e1", "run_completed")) == (False, False)


async def test_demo_fail_is_claimable_once_and_only_in_demo_mode(store):
    on = await store.create("generate", "hello", demo_fail=True)
    assert await store.claim_demo_fail(on.run_id) is True
    assert await store.claim_demo_fail(on.run_id) is False

    off = await store.create("generate", "hello", demo_fail=False)
    assert await store.claim_demo_fail(off.run_id) is False


async def test_retries_seen_counts_injected_failures(store):
    run = await store.create("generate", "hello", demo_fail=True)
    await store.apply_event(run.run_id, event("d1", "demo_failure_triggered", {"batch_id": "v01-b1"}))
    assert (await store.get(run.run_id)).retries_seen == 1


async def test_a_finished_run_is_not_overwritten_by_a_late_watcher(store):
    run = await store.create("generate", "hello", demo_fail=False)
    await store.apply_event(run.run_id, event("e1", "run_completed"))
    await store.mark_failed(run.run_id, "watcher noticed later")
    assert (await store.get(run.run_id)).status == "completed"


async def test_active_count_tracks_unfinished_runs(store):
    a = await store.create("generate", "a", demo_fail=False)
    await store.create("generate", "b", demo_fail=False)
    assert await store.active_count() == 2
    await store.apply_event(a.run_id, event("e1", "run_completed"))
    assert await store.active_count() == 1
