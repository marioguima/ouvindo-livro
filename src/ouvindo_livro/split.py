from __future__ import annotations

import re

from ouvindo_livro.models import Chapter
from ouvindo_livro.utils import count_words, slugify

_CHAPTER_RE = re.compile(
    r"^(#{1,3}\s+)?(cap[ií]tulo\s+\d+|chapter\s+\d+|parte\s+\d+|part\s+\d+|introdu[cç][aã]o|pref[aá]cio|conclus[aã]o|ep[ií]logo|pr[oó]logo)\b.*$",
    re.IGNORECASE,
)


def split_into_chapters(text: str, max_chars: int = 12000) -> list[Chapter]:
    detected = _split_by_headings(text)
    if detected:
        return _build_chapters(detected)
    return _split_by_size(text, max_chars=max_chars)


def _split_by_headings(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    heading_indexes: list[tuple[int, str]] = []

    for idx, line in enumerate(lines):
        candidate = line.strip()
        if not candidate or len(candidate) > 140:
            continue
        if _CHAPTER_RE.match(candidate):
            heading_indexes.append((idx, _clean_heading(candidate)))

    if len(heading_indexes) < 2:
        return []

    sections: list[tuple[str, str]] = []
    for pos, (start_idx, title) in enumerate(heading_indexes):
        end_idx = heading_indexes[pos + 1][0] if pos + 1 < len(heading_indexes) else len(lines)
        body = "\n".join(lines[start_idx + 1 : end_idx]).strip()
        if body:
            sections.append((title, body))

    return sections


def _split_by_size(text: str, max_chars: int) -> list[Chapter]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[tuple[str, str]] = []
    current: list[str] = []
    current_size = 0

    for paragraph in paragraphs:
        paragraph_size = len(paragraph)
        if current and current_size + paragraph_size > max_chars:
            title = f"Parte {len(chunks) + 1}"
            chunks.append((title, "\n\n".join(current)))
            current = []
            current_size = 0
        current.append(paragraph)
        current_size += paragraph_size

    if current:
        title = f"Parte {len(chunks) + 1}"
        chunks.append((title, "\n\n".join(current)))

    return _build_chapters(chunks)


def _build_chapters(items: list[tuple[str, str]]) -> list[Chapter]:
    chapters: list[Chapter] = []
    for index, (title, body) in enumerate(items, start=1):
        slug = f"{index:03d}-{slugify(title, fallback=f'capitulo-{index}') }"
        text = body.strip()
        chapters.append(
            Chapter(
                index=index,
                title=title.strip() or f"Capitulo {index}",
                slug=slug,
                text=text,
                char_count=len(text),
                word_count=count_words(text),
            )
        )
    return chapters


def _clean_heading(value: str) -> str:
    value = re.sub(r"^#{1,3}\s+", "", value.strip())
    value = re.sub(r"\s+", " ", value)
    return value
