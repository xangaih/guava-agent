"""Infer the caller's register from how they talk, so we can mirror it.

Nobody calling to book a trip wants to pick a voice from a menu. Instead we listen
to the caller's own words and match their register: someone who says "omg wait
that's so cute" gets the Gen Z Connie, someone who says "Good morning, I would like
to arrange a trip" gets the slow, careful one.

This is deliberately lexical rather than an LLM call: it runs on every utterance in
the hot path, so it has to be instant, free, and deterministic enough to unit test.
It is a nudge, not a verdict - `classify` returns None until the evidence is clear.
"""

import re

# Slang, fillers, and interjections that read as young/casual speech.
_GENZ_TERMS = {
    "literally", "lowkey", "highkey", "bestie", "vibe", "vibes", "obsessed", "slay",
    "deadass", "ngl", "tbh", "fr", "omg", "lol", "girl", "girlie", "dude", "bro",
    "cute", "iconic", "fire", "sick", "crazy", "insane", "wild", "vibing", "bet",
    "yeah", "yep", "yup", "nah", "kinda", "sorta", "wanna", "gonna", "gotta",
    "super", "totally", "honestly", "basically", "whatever", "cool", "hyped",
    "aesthetic", "chill", "broke", "cheap", "splurge",
}

# Formal / careful markers, plus signals the caller is struggling to follow.
_STEADY_TERMS = {
    "please", "thank", "thanks", "kindly", "certainly", "perhaps", "however",
    "regarding", "arrange", "arranging", "inquire", "inquiring", "assistance",
    "appreciate", "wonderful", "lovely", "pardon", "excuse", "sir", "maam",
    "madam", "afternoon", "morning", "evening", "would", "could", "shall", "may",
    "repeat", "slower", "slowly", "again", "hear", "understand", "confused",
}

# Phrases that outweigh single words.
_GENZ_PHRASES = ("oh my god", "no way", "so cute", "for real", "i'm dead", "im dead",
                 "that's fire", "thats fire", "kind of", "like a lot")
_STEADY_PHRASES = ("i would like", "i would prefer", "good morning", "good afternoon",
                   "good evening", "could you please", "would you mind", "thank you very much",
                   "say that again", "one moment", "i beg your pardon", "speak up")

# Words that mark a register almost on their own - one is worth several ordinary hits,
# and enough of them lets us decide before the caller has said much.
_GENZ_STRONG = {
    "yo", "yoo", "sup", "wassup", "bestie", "girl", "girlie", "girlies", "omg", "deadass",
    "ngl", "fr", "lowkey", "highkey", "slay", "bruh", "bro", "dude", "vibes", "obsessed",
}
_STEADY_STRONG = {
    "pardon", "kindly", "madam", "maam", "sir", "certainly", "inquire", "inquiring",
    "assistance", "regarding", "shall",
}

_ELONGATION = re.compile(r"([a-z])\1{2,}")        # heyyy, sooo, girllll
_WORD = re.compile(r"[a-z']+")

# How much evidence before we act, and how far ahead the winner must be.
MIN_WORDS = 8          # ordinary evidence: wait for roughly a full sentence
MIN_STRONG_WORDS = 4   # a strong marker ("yo", "pardon") can decide it sooner
MIN_MARGIN = 2.0       # ordinary evidence must clearly beat the neutral default
STRONG_MARGIN = 1.0    # a strong marker is reliable enough to need less of a lead


def score(text: str) -> dict[str, float]:
    """Weighted evidence for each style from one blob of caller speech."""
    low = (text or "").lower()
    words = _WORD.findall(low)
    scores = {"genz": 0.0, "steady": 0.0, "friendly": 0.0}
    if not words:
        return scores

    strong = 0.0
    for w in words:
        if w in _GENZ_STRONG:
            scores["genz"] += 2.0
            strong += 2.0
        elif w in _GENZ_TERMS:
            scores["genz"] += 1.0
        if w in _STEADY_STRONG:
            scores["steady"] += 2.0
            strong += 2.0
        elif w in _STEADY_TERMS:
            scores["steady"] += 1.0
    scores["_strong"] = strong

    scores["genz"] += 2.0 * len(_ELONGATION.findall(low))          # sooo, girllll
    scores["genz"] += 1.5 * sum(low.count(p) for p in _GENZ_PHRASES)
    scores["steady"] += 2.0 * sum(low.count(p) for p in _STEADY_PHRASES)

    # Apostrophe-free formality ("I am" / "do not" / "cannot") vs contractions.
    contractions = sum(1 for w in words if "'" in w)
    scores["genz"] += 0.5 * contractions
    if contractions == 0 and len(words) >= 10 and scores["steady"] > 0:
        scores["steady"] += 1.5

    # Long, complete sentences read as measured; clipped ones read as casual.
    avg_sentence = len(words) / max(1, len(re.findall(r"[.!?]+", low)) or 1)
    if avg_sentence >= 14:
        scores["steady"] += 1.0
    elif avg_sentence <= 5:
        scores["genz"] += 0.5

    scores["friendly"] = 1.0  # the middle register is the standing default
    return scores


def classify(utterances: list[str]) -> str | None:
    """Best style for this caller, or None if the evidence is not yet clear."""
    text = " ".join(utterances)
    word_count = len(_WORD.findall(text.lower()))
    if word_count < MIN_STRONG_WORDS:
        return None

    scores = score(text)
    has_strong = scores.pop("_strong", 0.0) >= 2.0
    if word_count < MIN_WORDS and not has_strong:
        return None

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    (top, top_score), (_, second_score) = ranked[0], ranked[1]
    if top == "friendly":
        return "friendly"
    margin = STRONG_MARGIN if has_strong else MIN_MARGIN
    if top_score - second_score < margin:
        return None  # ambiguous - stay where we are rather than guess
    return top
