"""Deterministic hashing embeddings (offline-friendly for CI/dev)."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

_TOKEN_RE = re.compile(r"[a-z0-9à-ü]+", re.IGNORECASE)


class HashingEmbeddingFunction(EmbeddingFunction[Documents]):
    """Bag-of-tokens hashing embedder — no model download required."""

    def __init__(self, dimensions: int = 256) -> None:
        self._dimensions = dimensions

    @staticmethod
    def name() -> str:
        return "hashing_embedding"

    def get_config(self) -> dict[str, Any]:
        return {"dimensions": self._dimensions}

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> HashingEmbeddingFunction:
        return HashingEmbeddingFunction(dimensions=int(config.get("dimensions", 256)))

    def __call__(self, input: Documents) -> Embeddings:
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        tokens = _TOKEN_RE.findall(text.lower())
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
