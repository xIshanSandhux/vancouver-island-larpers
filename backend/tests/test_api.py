"""API route tests. Render is stubbed, so nothing here starts a real task run."""

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.guard import limiter
from app.main import app
from app.render_client import RenderUnavailable
from app.store import store


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    """Each test gets an empty store, a fresh limiter and a stubbed Render."""
    store._runs.clear()
    store._seen_events.clear()
    store._demo_fail_claimed.clear()
    limiter._per_ip.clear()
    limiter._global.clear()

    async def fake_start_run(task_name, payload, *, run_id):
        return "trn-test"

    monkeypatch.setattr("app.routes.runs.start_run", fake_start_run)
    monkeypatch.setattr("app.routes.tone_down.start_run", fake_start_run)
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def secret_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {get_settings().workflow_event_secret}"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_creating_a_run_returns_an_id(client):
    res = client.post("/api/runs", json={"mode": "generate", "text": "i got a coffee"})
    assert res.status_code == 200
    run_id = res.json()["run_id"]
    state = client.get(f"/api/runs/{run_id}").json()
    assert state["status"] == "queued"
    assert state["task_run_id"] == "trn-test"


def test_unknown_run_is_a_404_with_the_error_contract(client):
    res = client.get("/api/runs/nope")
    assert res.status_code == 404
    assert res.json()["code"] == "not_found"


def test_over_length_generate_text_is_rejected_before_render(client):
    res = client.post("/api/runs", json={"mode": "generate", "text": "x" * 281})
    assert res.status_code == 422  # the contract's own length rule


def test_empty_text_is_rejected(client):
    res = client.post("/api/runs", json={"mode": "generate", "text": "   "})
    assert res.status_code == 422


def test_check_mode_allows_a_longer_draft(client):
    res = client.post("/api/runs", json={"mode": "check", "text": "x" * 1000})
    assert res.status_code == 200


def test_too_many_active_runs_gets_a_friendly_busy(client, monkeypatch):
    limit = get_settings().max_active_runs
    for i in range(limit):
        assert client.post(
            "/api/runs",
            json={"mode": "generate", "text": f"run {i}"},
            headers={"X-Forwarded-For": f"10.0.0.{i}"},
        ).status_code == 200

    res = client.post(
        "/api/runs", json={"mode": "generate", "text": "one too many"}, headers={"X-Forwarded-For": "10.0.0.99"}
    )
    assert res.status_code == 429
    assert res.json()["code"] == "busy"


def test_render_failure_marks_the_run_failed(client, monkeypatch):
    async def boom(task_name, payload, *, run_id):
        raise RenderUnavailable("no workflow slug")

    monkeypatch.setattr("app.routes.runs.start_run", boom)
    res = client.post("/api/runs", json={"mode": "generate", "text": "i got a coffee"})
    assert res.status_code == 502
    assert res.json()["code"] == "render_unavailable"


def test_events_require_the_shared_secret(client):
    run_id = client.post("/api/runs", json={"mode": "generate", "text": "hi"}).json()["run_id"]
    body = {"event_id": "e1", "type": "run_completed", "payload": {}}

    assert client.post(f"/internal/runs/{run_id}/events", json=body).status_code == 401
    assert client.post(f"/internal/runs/{run_id}/events", json=body, headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.post(f"/internal/runs/{run_id}/events", json=body, headers=secret_headers()).status_code == 200


def test_an_event_updates_the_polled_state(client):
    run_id = client.post("/api/runs", json={"mode": "generate", "text": "hi"}).json()["run_id"]
    client.post(
        f"/internal/runs/{run_id}/events",
        json={"event_id": "e1", "type": "ranking_ready", "payload": {"ranking": ["v07"]}},
        headers=secret_headers(),
    )
    assert client.get(f"/api/runs/{run_id}").json()["ranking"] == ["v07"]


def test_duplicate_events_are_reported_as_duplicates(client):
    run_id = client.post("/api/runs", json={"mode": "generate", "text": "hi"}).json()["run_id"]
    body = {"event_id": "e1", "type": "run_completed", "payload": {}}
    first = client.post(f"/internal/runs/{run_id}/events", json=body, headers=secret_headers()).json()
    second = client.post(f"/internal/runs/{run_id}/events", json=body, headers=secret_headers()).json()
    assert first == {"ok": True, "duplicate": False}
    assert second == {"ok": True, "duplicate": True}


def test_demo_fail_claim_answers_once(client):
    run_id = client.post(
        "/api/runs", json={"mode": "generate", "text": "hi", "demo_fail": True}
    ).json()["run_id"]
    url = f"/internal/runs/{run_id}/demo-fail-claim"
    assert client.post(url, headers=secret_headers()).json() == {"fail": True}
    assert client.post(url, headers=secret_headers()).json() == {"fail": False}


def test_demo_fail_claim_needs_the_secret(client):
    run_id = client.post("/api/runs", json={"mode": "generate", "text": "hi", "demo_fail": True}).json()["run_id"]
    assert client.post(f"/internal/runs/{run_id}/demo-fail-claim").status_code == 401


def test_tone_down_requires_a_completed_check_run(client):
    unknown = client.post("/api/runs/nope/tone-down")
    assert unknown.status_code == 404
    run_id = client.post("/api/runs", json={"mode": "generate", "text": "hi"}).json()["run_id"]
    wrong_mode = client.post(f"/api/runs/{run_id}/tone-down")
    assert wrong_mode.status_code == 400


def test_tone_down_starts_for_a_scored_completed_draft(client):
    run_id = client.post("/api/runs", json={"mode": "check", "text": "A useful draft."}).json()["run_id"]
    headers = secret_headers()
    client.post(
        f"/internal/runs/{run_id}/events",
        json={"event_id": "started", "type": "run_started", "payload": {"mode": "check", "input_text": "A useful draft."}},
        headers=headers,
    )
    client.post(
        f"/internal/runs/{run_id}/events",
        json={"event_id": "finalists", "type": "finalists_selected", "payload": {"finalist_ids": ["draft"]}},
        headers=headers,
    )
    client.post(
        f"/internal/runs/{run_id}/events",
        json={
            "event_id": "score",
            "type": "cringe_scored",
            "payload": {
                "post_id": "draft",
                "engagement_rate": 0.5,
                "appeal_mean": 3,
                "cringe": {"post_id": "draft", "rule_score": 20, "llm_score": None, "score": 20, "reasons": []},
                "base_score": 50,
            },
        },
        headers=headers,
    )
    client.post(f"/internal/runs/{run_id}/events", json={"event_id": "done", "type": "run_completed", "payload": {}}, headers=headers)
    response = client.post(f"/api/runs/{run_id}/tone-down")
    assert response.status_code == 202
    assert response.json() == {"ok": True}
