"""Cringe scoring. STUB created by M1 so imports work from day one.

Ishan replaces the bodies in task I3 (spec: architecture.md section 7). Keep these signatures.
"""

from app.models import CommentResult, CringeFeature, CringeResult


def features(text: str) -> list[CringeFeature]:
    """Rule-based, deterministic features found in the text."""
    return []


def rule_score(feats: list[CringeFeature]) -> float:
    """0..100 from rule features only."""
    return min(100.0, sum(f.points for f in feats))


def score(post_id: str, text: str, comments: list[CommentResult] | None = None) -> CringeResult:
    """Blended cringe result (0.6 rule + 0.4 share of commenters flagging cringe)."""
    feats = features(text)
    rule = rule_score(feats)
    llm: float | None = None
    if comments:
        flagged = sum(1 for c in comments if c.cringe_flag)
        llm = 100.0 * flagged / len(comments)
    blended = rule if llm is None else 0.6 * rule + 0.4 * llm
    return CringeResult(post_id=post_id, rule_score=rule, llm_score=llm, score=blended, reasons=feats[:5])


def hype_score(text: str) -> float:
    """How thought-leader-like the text is (higher is more). Used by filter_top3."""
    return float(rule_score(features(text)))
