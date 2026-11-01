import json
from pathlib import Path

from app.models import CommentResult, CringeResult, PostScore, Variant
from workflows.ranking import filter_top3, post_score, rank

SAMPLES = Path(__file__).resolve().parents[2] / "data" / "samples"


def _comment(post_id: str, persona: str, action: str, appeal: int) -> CommentResult:
    return CommentResult(
        event_id=f"r:{post_id}:{persona}",
        post_id=post_id,
        persona_id=persona,
        persona_name="Persona",
        persona_label="Label",
        archetype="placeholder",
        action=action,
        comment="hi" if action == "comment" else None,
        appeal=appeal,
        cringe_flag=False,
    )


def test_ranking_matches_the_shared_fixture():
    """The same file drives frontend/lib/rank.test.ts, so the slider agrees with the server."""
    case = json.loads((SAMPLES / "ranking_case.json").read_text())
    scores = [PostScore.model_validate(s) for s in case["scores"]]
    for weight, expected in case["expected"].items():
        assert rank(scores, float(weight)) == expected, f"tone weight {weight}"


def test_tone_weight_changes_the_order():
    case = json.loads((SAMPLES / "ranking_case.json").read_text())
    scores = [PostScore.model_validate(s) for s in case["scores"]]
    assert rank(scores, 0.0) != rank(scores, 1.0)


def test_post_score_counts_likes_and_comments_as_engagement():
    comments = [
        _comment("v01", "p01", "like", 5),
        _comment("v01", "p02", "comment", 3),
        _comment("v01", "p03", "ignore", 1),
        _comment("v01", "p04", "report", 1),
    ]
    cringe = CringeResult(post_id="v01", rule_score=0, llm_score=None, score=0, reasons=[])
    score = post_score("v01", comments, persona_total=4, cringe=cringe)
    assert score.engagement_rate == 0.5
    assert score.appeal_mean == 2.5


def test_post_score_handles_an_empty_audience():
    cringe = CringeResult(post_id="v01", rule_score=0, llm_score=None, score=0, reasons=[])
    score = post_score("v01", [], persona_total=50, cringe=cringe)
    assert score.engagement_rate == 0.0
    assert score.appeal_mean == 3.0


def test_filter_top3_picks_distinct_voices():
    variants = [
        Variant(post_id="v01", voice_id="humblebrag", voice_label="A", text="a"),
        Variant(post_id="v02", voice_id="humblebrag", voice_label="A", text="b"),
        Variant(post_id="v03", voice_id="hot_take", voice_label="B", text="c"),
        Variant(post_id="v04", voice_id="story_time", voice_label="C", text="d"),
    ]
    hype = {"v01": 90.0, "v02": 85.0, "v03": 50.0, "v04": 10.0}
    assert filter_top3(variants, hype) == ["v01", "v03", "v04"]


def test_filter_top3_is_deterministic_when_every_score_ties():
    """The cringe stub scores everything 0, so ties must still resolve the same way."""
    variants = [
        Variant(post_id=f"v{i:02d}", voice_id=f"voice{i}", voice_label="L", text="t")
        for i in range(1, 6)
    ]
    hype = {v.post_id: 0.0 for v in variants}
    assert filter_top3(variants, hype) == filter_top3(variants, hype) == ["v01", "v02", "v03"]
