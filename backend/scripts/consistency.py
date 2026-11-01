"""Measure commenter ranking consistency and rule-score separation.

The live invocation intentionally makes 3 posts x 50 personas x 2 runs = 300 Claude
commenter calls. It is an evidence script, not part of the request path.
"""

import asyncio
import os
from collections.abc import Sequence
from pathlib import Path

from dotenv import dotenv_values

import cringe
from app.models import CommentResult, Variant
from workflows.data import persona_ids
from workflows.ranking import post_score, rank
from workflows.tasks.commenters import react_persona

FINALISTS = [
    Variant(post_id="finalist-a", voice_id="v01", voice_label="Quiet operator", text="I made one small improvement to our weekly process, and the team kept it going."),
    Variant(post_id="finalist-b", voice_id="v02", voice_label="Clear teacher", text="The useful lesson was simple: listen closely, test one change, and keep showing up."),
    Variant(post_id="finalist-c", voice_id="v03", voice_label="Reflective builder", text="Progress looked less like a breakthrough and more like a habit we could repeat."),
]

KNOWN_CRINGE = [
    "Stop scrolling. This changed everything. #leadership #mindset #success #growth",
    "I failed publicly so you don't have to. Here are 5 things I learned. 🔥🚀💯",
    "Unpopular opinion: synergy and disruption are the keys to unlocking scalable impact.",
    "My humblebrag is that our team went viral. Agree? Comment YES below!",
    "I woke up at 4am and it reminded me that greatness is a choice. #hustle #winning",
    "Nobody talks about this secret: 3 lessons from my journey to transformational leadership.",
    "I was vulnerable with my team, but the real lesson was my relentless growth mindset.",
    "If you're not building your personal brand, you're already behind. Tag a leader.",
    "This one framework unlocked massive value and next-level innovation overnight.",
    "I almost quit, then I remembered that winners embrace the uncomfortable journey.",
]

PLAIN = [
    "We moved the weekly meeting to Tuesday and shared notes afterward.",
    "The customer interview surfaced two questions we had not considered.",
    "I updated the checklist and asked a teammate to try it next week.",
    "The report is shorter now because we removed two repeated sections.",
    "We tested the new form with three people and fixed the confusing field.",
    "Our team agreed to review the draft before sending it to the client.",
    "I wrote down the decision and the reason so we can revisit it later.",
    "The first version was incomplete, but it gave us something concrete to discuss.",
    "We noticed the handoff was slow and measured it for five working days.",
    "A quiet change to the calendar made it easier to protect focus time.",
]


def spearman(first: Sequence[str], second: Sequence[str]) -> float:
    """Spearman correlation for two complete rankings with the same unique IDs."""
    if len(first) != len(second) or len(first) < 2 or set(first) != set(second):
        raise ValueError("rankings must contain the same at least two unique IDs")
    left = {item: index for index, item in enumerate(first)}
    right = {item: index for index, item in enumerate(second)}
    n = len(first)
    squared = sum((left[item] - right[item]) ** 2 for item in first)
    return 1.0 - (6 * squared) / (n * (n * n - 1))


async def _commenter_run(run_number: int) -> tuple[list[list[str]], int, int]:
    ids = persona_ids()
    all_scores = []
    calls = 0
    fallbacks = 0
    for finalist in FINALISTS:
        outcomes = await asyncio.gather(
            *(react_persona(f"consistency-{run_number}", finalist.model_dump(), persona_id) for persona_id in ids)
        )
        comments: list[CommentResult] = []
        for result, used_fallback in outcomes:
            comments.append(result)
            calls += 1
            fallbacks += int(used_fallback)
        scored = cringe.score(finalist.post_id, finalist.text, comments)
        all_scores.append(post_score(finalist.post_id, comments, len(ids), scored))
    return [rank(all_scores)], calls, fallbacks


async def main() -> None:
    local_env = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY") or local_env.get("ANTHROPIC_API_KEY")
    commenter_model = os.getenv("COMMENTER_MODEL") or local_env.get("COMMENTER_MODEL")
    if not anthropic_key or not commenter_model:
        raise SystemExit("Set ANTHROPIC_API_KEY and COMMENTER_MODEL in backend/.env before running consistency.")
    results = await asyncio.gather(_commenter_run(1), _commenter_run(2))
    first, second = results
    correlation = spearman(first[0][0], second[0][0])
    cringe_scores = [cringe.hype_score(text) for text in KNOWN_CRINGE]
    plain_scores = [cringe.hype_score(text) for text in PLAIN]
    separation = min(cringe_scores) > max(plain_scores)
    print(f"spearman={correlation:.3f}")
    print(f"known_cringe_mean={sum(cringe_scores) / len(cringe_scores):.2f} min={min(cringe_scores):.2f} max={max(cringe_scores):.2f}")
    print(f"plain_mean={sum(plain_scores) / len(plain_scores):.2f} min={min(plain_scores):.2f} max={max(plain_scores):.2f}")
    print(f"separation_margin={min(cringe_scores) - max(plain_scores):.2f} separation={'PASS' if separation else 'FAIL'}")
    print(f"model_calls={first[1] + second[1]} fallback_count={first[2] + second[2]}")


if __name__ == "__main__":
    asyncio.run(main())
