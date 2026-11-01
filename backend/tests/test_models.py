import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import RunEvent, RunRequest, RunState, validate_payload

SAMPLES = Path(__file__).resolve().parents[2] / "data" / "samples"


def load(name: str):
    return json.loads((SAMPLES / name).read_text())


def test_sample_run_state_parses():
    state = RunState.model_validate(load("run_state.json"))
    assert state.run_id == "run-sample-0001"
    assert state.ranking == ["v07", "v01", "v12"]
    assert len(state.comments) == 12


def test_every_sample_event_parses_with_its_payload_model():
    events = load("events.json")
    seen = set()
    for raw in events:
        event = RunEvent.model_validate(raw)
        validate_payload(event.type, event.payload)
        seen.add(event.type)
    assert "comment" in seen and "run_failed" in seen


def test_sample_request_parses():
    assert RunRequest.model_validate(load("run_request.json")).mode == "generate"


def test_request_length_limits_depend_on_mode():
    with pytest.raises(ValidationError):
        RunRequest(mode="generate", text="x" * 281)
    assert RunRequest(mode="check", text="x" * 281).mode == "check"
    with pytest.raises(ValidationError):
        RunRequest(mode="generate", text="   ")


def test_unknown_event_type_is_rejected():
    with pytest.raises(ValidationError):
        RunEvent.model_validate({"event_id": "a", "type": "nope", "payload": {}})
