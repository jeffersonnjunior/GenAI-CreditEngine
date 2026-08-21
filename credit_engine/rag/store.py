"""Chroma-backed compliance policy store."""

from __future__ import annotations

from pathlib import Path

import chromadb

from credit_engine.core.config import EnvEnum, settings
from credit_engine.rag.chunking import PolicyChunk, load_policy_chunks
from credit_engine.rag.embeddings import HashingEmbeddingFunction

_DEFAULT_POLICY = (
    Path(__file__).resolve().parent / "policies" / "credit_policy_pt.md"
)


class ComplianceStore:
    """Indexes and retrieves compliance chunks via Chroma."""

    def __init__(
        self,
        *,
        persist_dir: str | None = None,
        collection_name: str | None = None,
        policy_path: Path | None = None,
        ephemeral: bool = False,
    ) -> None:
        configured = settings.POLICY_PATH.strip()
        self._policy_path = policy_path or Path(configured or _DEFAULT_POLICY)
        self._collection_name = collection_name or settings.COLLECTION_NAME
        self._embedder = HashingEmbeddingFunction()

        if ephemeral:
            self._client = chromadb.EphemeralClient()
        else:
            path = persist_dir or settings.PERSIST_DIR
            Path(path).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=path)

        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            embedding_function=self._embedder,
            metadata={"hnsw:space": "cosine"},
        )

    def ensure_indexed(self) -> int:
        """Load the policy file into Chroma if the collection is empty."""
        if self._collection.count() > 0:
            return self._collection.count()
        chunks = load_policy_chunks(self._policy_path)
        self.index_chunks(chunks)
        return len(chunks)

    def index_chunks(self, chunks: list[PolicyChunk]) -> None:
        """Upsert policy chunks into the collection."""
        if not chunks:
            return
        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[{"title": chunk.title} for chunk in chunks],
        )

    def query(self, text: str, *, top_k: int | None = None) -> list[str]:
        """Return the top-k most similar policy excerpts."""
        self.ensure_indexed()
        k = top_k if top_k is not None else settings.TOP_K
        k = max(1, min(k, max(1, self._collection.count())))
        result = self._collection.query(query_texts=[text], n_results=k)
        documents = (result.get("documents") or [[]])[0]
        return [doc for doc in documents if doc]


_store: ComplianceStore | None = None


def get_compliance_store(*, ephemeral: bool | None = None) -> ComplianceStore:
    """Return a process-wide compliance store."""
    global _store
    if ephemeral is True:
        return ComplianceStore(ephemeral=True)
    if _store is None:
        use_ephemeral = settings.ENV is EnvEnum.TEST
        _store = ComplianceStore(ephemeral=use_ephemeral)
    return _store


def reset_compliance_store() -> None:
    """Clear the cached store (tests)."""
    global _store
    _store = None
