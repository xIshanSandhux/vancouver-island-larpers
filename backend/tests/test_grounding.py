import pytest

from app.models import Variant
from workflows.grounding import review_grounding
from workflows.llm.anthropic_client import LLMError
from workflows.tasks.pipeline import write_variant_batch
from workflows.fallbacks import grounded_fallback
from workflows.data import load_voices
from workflows.guardrails import check_variant

POST = "I failed my midterm today. " + "An ordinary setback does not need to become a grand career story. " * 4
VARIANT = Variant(post_id="v01", voice_id="hot_take", voice_label="Hot take", text=POST)


@pytest.mark.parametrize("answer", [
    {}, {"verdicts": []},
    {"verdicts": [{"post_id": "v99", "grounded": True, "reason": ""}]},
    {"verdicts": [{"post_id": "v01", "grounded": "true", "reason": ""}]},
    {"verdicts": [{"post_id": "v01", "grounded": True, "reason": ""}] * 2},
])
async def test_incomplete_or_malformed_review_never_approves_a_post(monkeypatch, answer):
    async def call(**_):
        return answer
    monkeypatch.setattr("workflows.grounding.call_json", call)
    assert "v01" in await review_grounding("r", "I failed my midterm today", [VARIANT])


async def test_unsupported_study_habits_are_sent_back_for_revision(monkeypatch):
    prompts = []
    async def call(**kwargs):
        prompts.append(kwargs)
        return {"verdicts": [{"post_id": "v01", "unsupported_details": ["Invented skipped questions and study habits"], "grounded": False, "reason": "Unsupported"}]}
    monkeypatch.setattr("workflows.grounding.call_json", call)
    original = "I failed my chemistry midterm today"
    reasons = await review_grounding("r", original, [VARIANT])
    assert "study habits" in reasons["v01"]
    assert f"<source>{original}</source>" in prompts[0]["user"]
    assert original not in prompts[0]["system"]


async def test_unsupported_details_override_an_inconsistent_approval(monkeypatch):
    async def call(**_):
        return {"verdicts": [{"post_id": "v01", "unsupported_details": ["quiet room"], "grounded": True, "reason": ""}]}
    monkeypatch.setattr("workflows.grounding.call_json", call)
    assert await review_grounding("r", "An exam failed", [VARIANT]) == {"v01": "quiet room"}


async def test_review_outage_fails_closed(monkeypatch):
    async def call(**_):
        raise LLMError("unavailable")
    monkeypatch.setattr("workflows.grounding.call_json", call)
    assert "v01" in await review_grounding("r", "I failed my midterm today", [VARIANT])


async def test_batch_retries_semantically_rejected_posts_only_once(monkeypatch):
    attempts = []
    async def generate(**kwargs):
        attempts.append(kwargs["user"])
        return {"post": POST}
    async def reject(*_):
        return {"v01": "Invented study habits"}
    monkeypatch.setattr("workflows.tasks.pipeline.call_json", generate)
    monkeypatch.setattr("workflows.tasks.pipeline.review_grounding", reject)
    assignments = [{"post_id": "v01", "voice": {"id": "hot_take", "label": "Hot take", "instruction": "x"}}]
    result = await write_variant_batch.func(None, "r", "I failed my midterm today", assignments)
    assert len(result) == 1
    assert "grounded fallback" in result[0]["voice_label"]
    assert len(attempts) == 2
    assert "Invented study habits" in attempts[1]


@pytest.mark.parametrize("original", ["I folded a paper crane.", "Hi.", "a " * 139])
def test_fallbacks_keep_the_source_and_length_without_new_facts(original):
    for voice in load_voices():
        post = grounded_fallback("v", voice, original)
        assert original in post.text
        assert 40 <= len(post.text.split()) <= 140
        assert check_variant(original, post.text) == []
