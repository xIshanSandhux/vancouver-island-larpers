import json
from pathlib import Path

import cringe
import pytest
from app.models import CommentResult


def test_personas_have_required_distribution_and_ranges():
    personas = json.loads((Path(__file__).parents[2] / "data" / "personas.json").read_text())
    assert len(personas) == 50
    assert [item["id"] for item in personas] == [f"p{i:02d}" for i in range(1, 51)]
    assert {item["archetype"] for item in personas} == {
        "recruiter",
        "agree_guy",
        "ai_pivot_bro",
        "great_post_bot",
        "skeptical_senior_eng",
        "laid_off_job_seeker",
        "hustle_founder",
        "hr_people_ops",
        "quiet_lurker",
        "corporate_comms_exec",
    }
    for persona in personas:
        # Both traits are integers on a 0-5 scale. Zero is a real value, not a slip:
        # three of the great_post_bot personas have no cynicism at all, which is the
        # point of that archetype.
        assert isinstance(persona["hype_tolerance"], int)
        assert isinstance(persona["cynicism"], int)
        assert 0 <= persona["hype_tolerance"] <= 5
        assert 0 <= persona["cynicism"] <= 5
        assert 0 <= persona["like_bias"] <= 1
        assert all(persona[field] for field in ("name", "label", "industry", "bio", "comment_style"))


def test_cringe_features_are_case_insensitive_and_capped():
    text = "STOP SCROLLING — this changed everything!\n\n#one #two #three #four #five 🔥🚀💯✨"
    found = {feature.id: feature for feature in cringe.features(text)}
    assert found["hook_phrase"].points == 10
    assert found["hashtags"].points == 2
    assert found["emoji_overload"].points == 1
    assert cringe.rule_score(cringe.features(text)) <= 100


def test_cringe_reasons_are_stable_and_blend_comment_flags():
    text = "Here are 3 lessons: stop scrolling and unlock synergy."
    one = cringe.features(text)
    two = cringe.features(text)
    assert [item.model_dump() for item in one] == [item.model_dump() for item in two]
    comments = [
        CommentResult(event_id="1", post_id="p", persona_id="p01", persona_name="A", persona_label="A", archetype="x", action="comment", comment="x", appeal=3, cringe_flag=True),
        CommentResult(event_id="2", post_id="p", persona_id="p02", persona_name="B", persona_label="B", archetype="x", action="like", appeal=3, cringe_flag=False),
    ]
    result = cringe.score("p", text, comments)
    assert result.score == pytest.approx(0.6 * result.rule_score + 0.4 * 50)
    assert result.reasons == one[:5]
