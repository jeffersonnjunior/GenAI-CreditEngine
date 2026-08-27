"""Chroma-backed compliance policy store."""

from __future__ import annotations

from pathlib import Path

import chromadb

from credit_engine.core.config import EnvEnum, settings
from credit_engine.rag.chunking import (
    PolicyChunk,
    load_policy_chunks,
    window_chunks,
)
from credit_engine.rag.embeddings import HashingEmbeddingFunction
from credit_engine.rag.lexical import rank_ids_by_lexical
from credit_engine.rag.rrf import reciprocal_rank_fusion

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
        base_name = collection_name or settings.COLLECTION_NAME
        # Separate collection when sentence-window indexing is on (schema differs).
        if settings.SENTENCE_WINDOW and collection_name is None:
            base_name = f"{base_name}_sw"
        self._collection_name = base_name
        self._embedder = HashingEmbeddingFunction()
        self._parent_texts: dict[str, str] = {}

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
            if not self._parent_texts:
                self._hydrate_parents_from_policy()
            return self._collection.count()
        sections = load_policy_chunks(self._policy_path)
        self._parent_texts = {
            section.chunk_id: section.text for section in sections
        }
        if settings.SENTENCE_WINDOW:
            chunks = window_chunks(
                sections,
                window_sentences=settings.WINDOW_SENTENCES,
                overlap=settings.WINDOW_OVERLAP,
            )
        else:
            chunks = sections
        self.index_chunks(chunks)
        return len(chunks)

    def _hydrate_parents_from_policy(self) -> None:
        sections = load_policy_chunks(self._policy_path)
        self._parent_texts = {
            section.chunk_id: section.text for section in sections
        }

    def index_chunks(self, chunks: list[PolicyChunk]) -> None:
        """Upsert policy chunks into the collection."""
        if not chunks:
            return
        for chunk in chunks:
            if chunk.parent_id is None:
                self._parent_texts.setdefault(chunk.chunk_id, chunk.text)
            elif chunk.parent_id not in self._parent_texts:
                self._parent_texts[chunk.parent_id] = chunk.text

        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "title": chunk.title,
                    "parent_id": chunk.parent_id or chunk.chunk_id,
                }
                for chunk in chunks
            ],
        )

    def query(self, text: str, *, top_k: int | None = None) -> list[str]:
        """Return the top-k most relevant policy excerpts (parent sections)."""
        self.ensure_indexed()
        k = top_k if top_k is not None else settings.TOP_K
        total = max(1, self._collection.count())
        k = max(1, min(k, total))
        fetch_n = k
        if settings.RRF_ENABLED or settings.SENTENCE_WINDOW:
            fetch_n = max(k, min(settings.RRF_CANDIDATES, total))

        result = self._collection.query(
            query_texts=[text],
            n_results=fetch_n,
            include=["documents", "metadatas"],
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        if not ids:
            return []

        vector_ranked = list(ids)
        if settings.RRF_ENABLED and len(ids) > 1:
            lexical_ranked = rank_ids_by_lexical(
                text,
                ids=ids,
                documents=documents,
            )
            ordered_ids = reciprocal_rank_fusion(
                [vector_ranked, lexical_ranked],
                k=settings.RRF_K,
            )
        else:
            ordered_ids = vector_ranked

        meta_by_id = {
            doc_id: (meta or {})
            for doc_id, meta in zip(ids, metadatas, strict=True)
        }
        doc_by_id = {
            doc_id: doc
            for doc_id, doc in zip(ids, documents, strict=True)
        }

        excerpts: list[str] = []
        seen_parents: set[str] = set()
        for doc_id in ordered_ids:
            meta = meta_by_id.get(doc_id) or {}
            parent_id = str(meta.get("parent_id") or doc_id)
            if parent_id in seen_parents:
                continue
            seen_parents.add(parent_id)
            excerpt = self._parent_texts.get(parent_id) or doc_by_id.get(doc_id)
            if excerpt:
                excerpts.append(excerpt)
            if len(excerpts) >= k:
                break
        return excerpts


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
