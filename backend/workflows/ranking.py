"""Scoring and ranking (architecture.md section 8).

frontend/lib/rank.ts mirrors `final_score` and `rank` so the tone slider re-orders in the
browser without a round trip. data/samples/ranking_case.json pins both to the same numbers.
"""

from app.models import CommentResult, CringeResult, PostScore, Variant

DEFAULT_TONE_WEIGHT = 0.5


def post_score(post_id: str, comments: list[CommentResult], persona_total: int, cringe: CringeResult) -> PostScore:
    """Turn one finalist's persona reactions into its score."""
    engaged = sum(1 for c in comments if c.action in ("like", "comment"))
    engagement_rate = engaged / persona_total if persona_total else 0.0
    appeal_mean = sum(c.appeal for c in comments) / len(comments) if comments else 3.0
    appeal_norm = (appeal_mean - 1) / 4
    base = 100 * (0.5 * engagement_rate + 0.5 * appeal_norm)
    return PostScore(
        post_id=post_id,
        engagement_rate=min(1.0, engagement_rate),
        appeal_mean=appeal_mean,
        cringe=cringe,
        base_score=base,
    )


def final_score(score: PostScore, tone_weight: float = DEFAULT_TONE_WEIGHT) -> float:
    """Higher is better. Raising tone_weight punishes cringe harder."""
    return score.base_score - tone_weight * score.cringe.score


def rank(scores: list[PostScore], tone_weight: float = DEFAULT_TONE_WEIGHT) -> list[str]:
    """Post ids, best first. post_id breaks ties so the order never wobbles."""
    return [s.post_id for s in sorted(scores, key=lambda s: (-final_score(s, tone_weight), s.post_id))]


def filter_top3(variants: list[Variant], hype_scores: dict[str, float], limit: int = 3) -> list[str]:
    """The most thought-leader-ish variants, one per voice so the finalists read differently."""
    ordered = sorted(variants, key=lambda v: (-hype_scores.get(v.post_id, 0.0), v.post_id))
    chosen: list[str] = []
    seen_voices: set[str] = set()
    for variant in ordered:
        if variant.voice_id in seen_voices:
            continue
        seen_voices.add(variant.voice_id)
        chosen.append(variant.post_id)
        if len(chosen) == limit:
            break
    return chosen
