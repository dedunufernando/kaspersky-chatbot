"""
Retrieves the most relevant KB chunks for a user query.
Uses hybrid search: semantic (pgvector cosine) + keyword boost.
Embeddings generated locally via sentence-transformers (free).
"""
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg
from sentence_transformers import SentenceTransformer

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    DATABASE_URL,
    EMBEDDING_MODEL,
    RETRIEVAL_TOP_K, CONFIDENCE_THRESHOLD,
)

# Load once at import time (cached for the session)
_embedder = SentenceTransformer(EMBEDDING_MODEL)


@dataclass
class Chunk:
    url: str
    title: str
    content: str
    score: float
    last_modified: str


def _embed_query(text: str) -> list[float]:
    vec = _embedder.encode([text], normalize_embeddings=True)
    return vec[0].tolist()


def _preprocess_query(query: str) -> str:
    query = re.sub(r"0x\s*([0-9a-fA-F]+)", lambda m: "0x" + m.group(1).upper(), query)
    replacements = {
        "won't": "does not",
        "doesn't": "does not",
        "can't": "cannot",
        "kes": "Kaspersky Endpoint Security",
        "ksc": "Kaspersky Security Center",
    }
    for k, v in replacements.items():
        query = query.replace(k, v)
    return query


def _extract_keywords(query: str) -> list[str]:
    codes = re.findall(r"0x[0-9a-fA-F]+|\d{4,}", query)
    products = ["endpoint security", "security center", "total security",
                "standard", "premium", "plus", "kaspersky vpn", "safe kids"]
    found = [p for p in products if p in query.lower()]
    return codes + found


def retrieve(query: str) -> list[Chunk]:
    """
    Returns ranked chunks above CONFIDENCE_THRESHOLD.
    Returns empty list if nothing qualifies → triggers escalation in pipeline.
    """
    query = _preprocess_query(query)
    vec = _embed_query(query)
    vec_str = str(vec)

    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT url, title, content, last_modified,
               1 - (embedding <=> %s::vector) AS score
        FROM kb_chunks
        WHERE 1 - (embedding <=> %s::vector) >= %s
        ORDER BY score DESC
        LIMIT %s
        """,
        (vec_str, vec_str, CONFIDENCE_THRESHOLD, RETRIEVAL_TOP_K * 2),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    keyword_terms = _extract_keywords(query)
    results: list[Chunk] = []
    seen: set[str] = set()

    for url, title, content, last_modified, score in rows:
        boost = sum(0.05 for kw in keyword_terms if kw.lower() in content.lower())
        final_score = min(score + boost, 1.0)
        key = f"{url}:{content[:50]}"
        if key not in seen:
            seen.add(key)
            results.append(Chunk(url=url, title=title, content=content,
                                 score=final_score, last_modified=last_modified))

    results.sort(key=lambda c: c.score, reverse=True)
    return results[:RETRIEVAL_TOP_K]
