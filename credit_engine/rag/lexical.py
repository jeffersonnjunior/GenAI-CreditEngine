"""Lightweight lexical ranking for RRF (no external search engine)."""

from __future__ import annotations

import re
from collections.abc import Sequence

_TOKEN_RE = re.compile(r"[a-z0-9à-ü]+", re.IGNORECASE)


def tokenize(text: str) -> set[str]:
    """Lowercased alphanumeric tokens."""
    return {token.lower() for token in _TOKEN_RE.findall(text)}


def lexical_overlap_score(query: str, document: str) -> float:
    """Jaccard overlap between query and document token sets."""
    query_tokens = tokenize(query)
    doc_tokens = tokenize(document)
    if not query_tokens or not doc_tokens:
        return 0.0
    intersection = query_tokens & doc_tokens
    union = query_tokens | doc_tokens
    return len(intersection) / len(union)


def rank_ids_by_lexical(
    query: str,
    *,
    ids: Sequence[str],
    documents: Sequence[str],
) -> list[str]:
    """Return ids sorted by descending lexical overlap with the query."""
    if len(ids) != len(documents):
        msg = "ids and documents must have the same length"
        raise ValueError(msg)

    scored = [
        (lexical_overlap_score(query, document), index, doc_id)
        for index, (doc_id, document) in enumerate(
            zip(ids, documents, strict=True)
        )
    ]
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [doc_id for _, _, doc_id in scored]
