"""Fact-preserving defaults when a generated draft cannot pass review."""

from app.models import Variant

_OPENINGS = {
    "humblebrag": "Humbled to present an ordinary event without an extraordinary backstory.",
    "hot_take": "Hot take: an ordinary event does not need a heroic backstory.",
    "story_time": "Story time. Here is the entire plot, without the dramatic soundtrack.",
    "lessons_learned": "Three reminders:\n1. Keep the facts.\n2. Inflate the framing.\n3. Question the lesson.",
    "unpopular_opinion": "Unpopular opinion: ordinary events deserve smaller narratives.",
    "gratitude": "Grateful for the ordinary. Even more grateful for a little perspective.",
    "nobody_talks": "Nobody talks about how much framing an ordinary event can carry.",
    "leadership_lens": "Leadership lens: a bigger narrative does not make a bigger event.",
    "startup_grind": "The grind never stops. Neither, apparently, does the urge to narrate it.",
    "vulnerable_share": "A vulnerable thought: perhaps the ordinary can simply be ordinary.",
    "data_driven": "The input is an event. The output is a suspicious amount of significance.",
    "mentor_voice": "A little advice: let the facts do the talking before the lesson takes over.",
    "plot_twist": "An ordinary event.\n\nThe plot twist? It can stay ordinary.",
    "industry_prediction": "A prediction: ordinary moments will continue inspiring extraordinary amounts of commentary.",
    "quiet_flex": "No grand reveal. No heroic arc. Just the event.",
    "checklist": "A checklist for perspective:\n- Keep the event.\n- Question the framing.\n- Leave room for the ordinary.",
    "reframe": "The reframe: perhaps the event is smaller than the story around it.",
    "coach_energy": "Keep the facts. Bring the energy. Resist the imaginary comeback montage.",
    "philosopher": "An ordinary event is a small window. How large a meaning should fit through it?",
    "thread_opener": "A thread about the gap between an ordinary event and an extraordinary caption.",
}
_REFLECTION = (
    "Perhaps the real lesson is about perspective. A small moment can carry a grand metaphor "
    "without acquiring an imaginary backstory. Call it growth, call it a journey, or simply "
    "let the event speak for itself. The framing can get louder while the facts stay exactly "
    "where they started. How much meaning would you put around it?"
)


def grounded_fallback(post_id: str, voice: dict, original: str) -> Variant:
    opening = _OPENINGS.get(voice["id"], "An ordinary event, with room for perspective.")
    text = f"{opening}\n\nThe original event:\n{original}"
    if len(text.split()) > 140:
        text = original
    if len(text.split()) + len(_REFLECTION.split()) <= 140:
        text += f"\n\n{_REFLECTION}"
    return Variant(post_id=post_id, voice_id=voice["id"],
                   voice_label=f"{voice['label']} · grounded fallback", text=text)
