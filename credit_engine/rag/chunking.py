"""Split compliance markdown into retrieval chunks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PolicyChunk:
    """One section of the compliance manual."""

    chunk_id: str
    title: str
    text: str


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


def load_policy_chunks(path: Path) -> list[PolicyChunk]:
    """Read a markdown policy file and return section chunks."""
    markdown = path.read_text(encoding="utf-8")
    return chunk_markdown_sections(markdown, source=path.stem)
