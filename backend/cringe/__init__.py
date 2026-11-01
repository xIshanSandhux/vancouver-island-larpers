"""Deterministic cringe and hype scoring for Thought Leadr."""

import json
import re
from functools import lru_cache
from pathlib import Path

from app.models import CommentResult, CringeFeature, CringeResult

_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "cringe_lexicon.json"
_WORD_RE = re.compile(r"\b\w+[’'-]?\w*\b")
_HASHTAG_RE = re.compile(r"(?<!\w)#\w+")
_NUMBERED_LINE_RE = re.compile(r"^\s*\d+[.)]\s+", re.MULTILINE)
_EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001FAFF\u2600-\u27BF]"
)

_LABELS = {
    "one_line_paragraphs": "One-line paragraphs",
    "hook_phrase": "Hook phrase",
    "engagement_bait": "Engagement-bait ending",
    "humblebrag": "Humblebrag phrases",
    "hashtags": "Excessive hashtags",
    "emoji_overload": "Emoji overload",
    "buzzwords": "Corporate buzzwords",
    "listicle": "Listicle format",
    "fake_vulnerability": "Vulnerability phrasing",
    "over_length": "Overly long post",
}


@lru_cache
def _lexicon() -> dict[str, list[str]]:
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


def _count_phrases(text: str, phrases: list[str]) -> int:
    lowered = text.casefold()
    return sum(lowered.count(phrase.casefold()) for phrase in phrases)


def _feature(feature_id: str, count: int, points: float) -> CringeFeature | None:
    if count <= 0 or points <= 0:
        return None
    return CringeFeature(
        id=feature_id,
        label=_LABELS[feature_id],
        count=count,
        points=round(points, 2),
    )


def features(text: str) -> list[CringeFeature]:
    """Return all triggered rule features in stable score order."""
    lexicon = _lexicon()
    lowered = text.casefold()
    found: list[CringeFeature] = []

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    short_single_line = sum(
        1 for paragraph in paragraphs
        if "\n" not in paragraph and len(_WORD_RE.findall(paragraph)) <= 12
    )
    if paragraphs:
        one_line = _feature(
            "one_line_paragraphs",
            short_single_line,
            12 * short_single_line / len(paragraphs),
        )
        if one_line:
            found.append(one_line)

    hook_count = _count_phrases(text, lexicon["hook_phrase"])
    hook = _feature("hook_phrase", hook_count, 10)
    if hook:
        found.append(hook)

    ending = re.sub(r"[^\w?!.'\s]", "", paragraphs[-1].casefold().replace("’", "'") if paragraphs else "").strip()
    engagement_count = sum(
        1 for phrase in lexicon["engagement_bait"]
        if ending.endswith(phrase.casefold())
    )
    engagement_count += bool(re.search(
        r"(?:agree or disagree|what do you think|share your (?:story|thoughts)|"
        r"what(?:'s| is) your\b|what(?:'s| is) a\b.*\byou\b|"
        r"what\b.*\bwould you\b|have you ever|let me know|"
        r"repost if\b|follow for more\b)", ending
    ))
    engagement = _feature("engagement_bait", engagement_count, 10)
    if engagement:
        found.append(engagement)

    humblebrag_count = _count_phrases(text, lexicon["humblebrag"])
    humblebrag = _feature("humblebrag", humblebrag_count, min(12, humblebrag_count * 2))
    if humblebrag:
        found.append(humblebrag)

    hashtag_count = len(_HASHTAG_RE.findall(text))
    hashtags = _feature("hashtags", max(0, hashtag_count - 3), min(8, max(0, hashtag_count - 3)))
    if hashtags:
        found.append(hashtags)

    emoji_count = len(_EMOJI_RE.findall(text))
    emojis = _feature("emoji_overload", max(0, emoji_count - 3), min(8, max(0, emoji_count - 3)))
    if emojis:
        found.append(emojis)

    buzzword_count = _count_phrases(text, lexicon["buzzwords"])
    buzzwords = _feature("buzzwords", buzzword_count, min(10, buzzword_count * 2))
    if buzzwords:
        found.append(buzzwords)

    listicle_count = len(_NUMBERED_LINE_RE.findall(text)) + sum(
        1 for phrase in ("3 lessons", "5 things") if phrase in lowered
    )
    listicle = _feature("listicle", listicle_count, 6)
    if listicle:
        found.append(listicle)

    vulnerability_count = _count_phrases(text, [
        phrase for phrase in lexicon["fake_vulnerability"] if phrase.casefold() != "broke down"
    ])
    vulnerability_count += len(re.findall(r"\b(?:i|we)\s+(?:just\s+)?broke down\b", lowered))
    vulnerability = _feature("fake_vulnerability", vulnerability_count, 8)
    if vulnerability:
        found.append(vulnerability)

    over_length = _feature("over_length", 1 if len(text) > 1300 else 0, 6)
    if over_length:
        found.append(over_length)

    return sorted(found, key=lambda item: (-item.points, item.id))


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
