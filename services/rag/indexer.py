import re
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from core.config import ChromaSettings


@dataclass(frozen=True)
class ComplianceChunk:
    doc_id: str
    text: str
    chunk_type: str
    section: str


class ComplianceIndexer:
    def __init__(self, settings: ChromaSettings) -> None:
        self._settings = settings
        self._client = chromadb.PersistentClient(path=str(settings.persist_dir))

    @property
    def collection(self) -> Collection:
        return self._client.get_or_create_collection(
            name=self._settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def is_indexed(self) -> bool:
        return self.collection.count() > 0

    def index_manual(self, manual_path: Path) -> int:
        text = manual_path.read_text(encoding="utf-8")
        chunks = self._build_chunks(text)
        if not chunks:
            return 0

        existing_ids = set(self.collection.get(include=[])["ids"])
        new_chunks = [chunk for chunk in chunks if chunk.doc_id not in existing_ids]
        if not new_chunks:
            return 0

        self.collection.add(
            ids=[chunk.doc_id for chunk in new_chunks],
            documents=[chunk.text for chunk in new_chunks],
            metadatas=[
                {
                    "chunk_type": chunk.chunk_type,
                    "section": chunk.section,
                    "source": "compliance_manual",
                }
                for chunk in new_chunks
            ],
        )
        return len(new_chunks)

    def _build_chunks(self, text: str) -> list[ComplianceChunk]:
        chunks: list[ComplianceChunk] = []
        sections = self._split_sections(text)

        for section_idx, (section_title, section_body) in enumerate(sections):
            paragraphs = [p.strip() for p in section_body.split("\n\n") if p.strip()]
            for paragraph_idx, paragraph in enumerate(paragraphs):
                chunks.append(
                    ComplianceChunk(
                        doc_id=f"section-{section_idx}-paragraph-{paragraph_idx}",
                        text=paragraph,
                        chunk_type="paragraph",
                        section=section_title,
                    )
                )

                sentences = self._split_sentences(paragraph)
                window_size = self._settings.sentence_window_size
                for sentence_idx, sentence in enumerate(sentences):
                    start = max(0, sentence_idx - window_size)
                    end = min(len(sentences), sentence_idx + window_size + 1)
                    window_text = " ".join(sentences[start:end])
                    chunks.append(
                        ComplianceChunk(
                            doc_id=f"section-{section_idx}-sentence-{paragraph_idx}-{sentence_idx}",
                            text=window_text,
                            chunk_type="sentence_window",
                            section=section_title,
                        )
                    )

        return chunks

    @staticmethod
    def _split_sections(text: str) -> list[tuple[str, str]]:
        parts = re.split(r"(?m)^##\s+", text)
        sections: list[tuple[str, str]] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            lines = part.splitlines()
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()
            sections.append((title, body))
        return sections

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        raw = re.split(r"(?<=[.!?])\s+", text.strip())
        return [sentence.strip() for sentence in raw if sentence.strip()]
