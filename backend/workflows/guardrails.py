"""Post-generation checks: a variant may inflate tone, never facts.

The model is told not to add numbers, employers, titles or names. This module verifies
it, because a post that invents a job or a statistic is the one failure that would
genuinely embarrass us on stage (requirements.md section 5).
"""

import re

# Capitalised words that start sentences or are too common to treat as a name.
_COMMON = {
    "a", "about", "after", "again", "all", "also", "and", "another", "any", "are", "as",
    "at", "be", "because", "before", "being", "best", "better", "but", "by", "can",
    "coffee", "day", "did", "do", "does", "doing", "done", "down", "each", "even",
    "every", "everyone", "everything", "first", "for", "friday", "from", "get", "go",
    "going", "good", "got", "great", "had", "has", "have", "he", "her", "here", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "just", "keep", "last", "learn",
    "learned", "lesson", "lessons", "let", "life", "like", "look", "made", "make",
    "many", "may", "maybe", "me", "meeting", "monday", "money", "more", "most", "much",
    "my", "never", "new", "next", "no", "not", "nobody", "now", "of", "off", "on",
    "once", "one", "only", "or", "other", "our", "out", "over", "own", "people",
    "really", "remember", "right", "said", "saturday", "say", "see", "she", "should",
    "so", "some", "someone", "something", "start", "started", "stop", "sunday", "take",
    "team", "than", "that", "the", "their", "them", "then", "there", "these", "they",
    "thing", "things", "think", "this", "those", "thursday", "time", "to", "today",
    "tomorrow", "too", "tuesday", "two", "unpopular", "up", "us", "use", "very", "was",
    "we", "wednesday", "week", "well", "went", "were", "what", "when", "where",
    "whether", "which", "while", "who", "why", "will", "with", "work", "working",
    "would", "year", "years", "yes", "yesterday", "you", "your",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december",
}

_DIGITS = re.compile(r"\d+")
_LIST_MARKER = re.compile(r"^\s*\d+[.)]\s", re.MULTILINE)
_CAP_WORD = re.compile(r"\b[A-Z][A-Za-z]{1,}\b")
# A capital is unremarkable at the start of a sentence, a line, a bullet, a numbered
# item, or after a colon. Only capitals elsewhere suggest an invented name.
_SENTENCE_START = re.compile(r"(?:^|[.!?:;]\s+|[\n\r]\s*(?:[-*•+]\s*|\d+[.)]\s*)?|[\"'“‘(\[]\s*)$")
# Hashtags are decoration, not factual claims, and #Hustle is not an invented employer.
_HASHTAG = re.compile(r"(?<!\w)#\w+")


def _digit_runs(text: str) -> set[str]:
    return set(_DIGITS.findall(text))


def check_variant(input_text: str, output_text: str) -> list[str]:
    """Return human-readable reasons the variant must be rejected. Empty means fine."""
    reasons: list[str] = []

    # Numbers: list markers like "1." are fine; anything else must come from the input.
    without_markers = _LIST_MARKER.sub("", output_text)
    new_numbers = _digit_runs(without_markers) - _digit_runs(input_text)
    if new_numbers:
        reasons.append(f"invented numbers: {', '.join(sorted(new_numbers))}")

    # Proper nouns: a capitalised word that is not sentence-initial and not in the input
    # is most likely an invented company, product or person.
    lowered_input = input_text.lower()
    invented: list[str] = []
    # Blank out hashtags first, keeping offsets so sentence-start detection still works.
    scannable = _HASHTAG.sub(lambda m: " " * len(m.group(0)), output_text)
    for match in _CAP_WORD.finditer(scannable):
        word = match.group(0)
        if word.lower() in _COMMON or word.lower() in lowered_input:
            continue
        if _SENTENCE_START.search(scannable[: match.start()]):
            continue
        invented.append(word)
    if invented:
        unique = sorted(set(invented))[:5]
        reasons.append(f"invented proper nouns: {', '.join(unique)}")

    return reasons
