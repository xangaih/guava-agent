"""Small, targeted embedding similarity - not a RAG pipeline.

Matches free-form caller text (a destination, a list of interests) against a
tiny fixed catalog (6 cities, ~125 hotels/restaurants/experiences) by cosine
similarity instead of exact string/tag equality. At this scale a vector
database is unnecessary overhead - comparing a query embedding against a
few hundred stored ones directly is effectively instant.
"""

import math
import os

from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"

KNOWN_CITIES = ["Kyoto", "Paris", "Rome", "Barcelona", "Tokyo", "Bangkok"]

# Below this cosine similarity, a destination isn't considered a real match
# to any known city - better to say so than silently guess wrong.
CITY_MATCH_THRESHOLD = 0.3

_client: OpenAI | None = None
_city_embeddings: dict[str, list[float]] | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def embed(text: str) -> list[float]:
    return embed_batch([text])[0]


def embed_batch(texts: list[str]) -> list[list[float]]:
    response = _get_client().embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def match_city(text: str) -> str | None:
    """Best known city for free-form destination text, or None if nothing is close."""
    global _city_embeddings
    if _city_embeddings is None:
        vectors = embed_batch(KNOWN_CITIES)
        _city_embeddings = dict(zip(KNOWN_CITIES, vectors))

    query = embed(text)
    best_city, best_score = None, CITY_MATCH_THRESHOLD
    for city, vec in _city_embeddings.items():
        score = cosine_similarity(query, vec)
        if score > best_score:
            best_city, best_score = city, score
    return best_city


def rank_by_similarity(query_text: str, items: list[dict], limit: int) -> list[dict]:
    """Rank items with an `embedding` field by similarity to query_text."""
    if not items:
        return items
    query_vec = embed(query_text)
    scored = [
        (cosine_similarity(query_vec, item["embedding"]), item)
        for item in items
        if item.get("embedding")
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]
