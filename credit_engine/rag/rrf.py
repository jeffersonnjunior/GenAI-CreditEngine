"""Reciprocal Rank Fusion for multi-ranker retrieval."""

from __future__ import annotations

from collections.abc import Sequence


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[str]],
    *,
    k: int = 60,
) -> list[str]:
    """Merge ranked id lists with classic RRF: sum 1/(k + rank).

    Rank is 1-based. Ids missing from a list contribute 0 for that list.
    Stable tie-break: first appearance order across inputs, then id.
    """
    if k < 1:
        msg = "RRF k must be >= 1"
        raise ValueError(msg)

    scores: dict[str, float] = {}
    first_seen: dict[str, tuple[int, int]] = {}

    for list_index, ranked in enumerate(ranked_lists):
        for rank_zero, doc_id in enumerate(ranked):
            rank = rank_zero + 1
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            if doc_id not in first_seen:
                first_seen[doc_id] = (list_index, rank_zero)

    return sorted(
        scores.keys(),
        key=lambda doc_id: (-scores[doc_id], first_seen[doc_id], doc_id),
    )
