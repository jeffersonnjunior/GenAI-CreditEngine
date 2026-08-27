"""Split compliance markdown into retrieval chunks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?])\s+|(?:\n(?=\s*[-*]\s))|\n{2,}",
)


@dataclass(frozen=True, slots=True)
class PolicyChunk:
    """One retrieval unit (section or sentence window)."""

    chunk_id: str
    title: str
    text: str
    parent_id: str | None = None
    """Section id when this chunk is a sentence window; None for root sections."""


def chunk_markdown_sections(
    markdown: str,
    *,
    source: str = "policy",
) -> list[PolicyChunk]:
    """Split on level-2 headings (##), keeping title + body together."""
    lines = markdown.replace("\r\n", "\n").split("\n")
    sections: list[tuple[str, list[str]]] = []
    current_title = "intro"
    current_body: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_body and any(part.strip() for part in current_body):
                sections.append((current_title, current_body))
            current_title = line[3:].strip() or "section"
            current_body = [line]
        else:
            current_body.append(line)

    if current_body and any(part.strip() for part in current_body):
        sections.append((current_title, current_body))

    chunks: list[PolicyChunk] = []
    for index, (title, body_lines) in enumerate(sections):
        text = "\n".join(body_lines).strip()
        if not text:
            continue
        chunks.append(
            PolicyChunk(
                chunk_id=f"{source}-{index}",
                title=title,
                text=text,
            )
        )
    return chunks


def split_into_sentences(text: str) -> list[str]:
    """Split policy text into sentence-like units (incl. bullet lines)."""
    parts = _SENTENCE_SPLIT_RE.split(text.strip())
    return [part.strip() for part in parts if part and part.strip()]


def window_chunks(
    sections: list[PolicyChunk],
    *,
    window_sentences: int = 2,
    overlap: int = 0,
) -> list[PolicyChunk]:
    """Build overlapping sentence windows that point back to parent sections."""
    if window_sentences < 1:
        msg = "window_sentences must be >= 1"
        raise ValueError(msg)
    if overlap < 0 or overlap >= window_sentences:
        msg = "overlap must be >= 0 and < window_sentences"
        raise ValueError(msg)

    step = window_sentences - overlap
    windows: list[PolicyChunk] = []

    for section in sections:
        sentences = split_into_sentences(section.text)
        if not sentences:
            continue
        if len(sentences) <= window_sentences:
            windows.append(
                PolicyChunk(
                    chunk_id=f"{section.chunk_id}-w0",
                    title=section.title,
                    text=section.text,
                    parent_id=section.chunk_id,
                )
            )
            continue

        window_index = 0
        start = 0
        while start < len(sentences):
            end = min(start + window_sentences, len(sentences))
            piece = " ".join(sentences[start:end]).strip()
            if piece:
                windows.append(
                    PolicyChunk(
                        chunk_id=f"{section.chunk_id}-w{window_index}",
                        title=section.title,
                        text=piece,
                        parent_id=section.chunk_id,
                    )
                )
                window_index += 1
            if end >= len(sentences):
                break
            start += step

    return windows


def load_policy_chunks(path: Path) -> list[PolicyChunk]:
    """Read a markdown policy file and return section chunks."""
    markdown = path.read_text(encoding="utf-8")
    return chunk_markdown_sections(markdown, source=path.stem)
