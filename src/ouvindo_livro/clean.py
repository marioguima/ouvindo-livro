from __future__ import annotations

import re
from collections import Counter

from ouvindo_livro.models import ExtractedBook

_PAGE_NUMBER_RE = re.compile(r"^\s*(?:pagina|page)?\s*\d{1,4}\s*$", re.IGNORECASE)
_DOT_LEADER_RE = re.compile(r"\.{3,}\s*\d{1,4}\s*$")


def clean_book_text(book: ExtractedBook) -> str:
    pages = book.pages if book.pages else [book.raw_text]
    repeated_lines = _detect_repeated_header_footer_lines(pages)

    cleaned_pages: list[str] = []
    for page in pages:
        cleaned_pages.append(_clean_page(page, repeated_lines))

    text = "\n\n".join(page for page in cleaned_pages if page.strip())
    text = _remove_probable_index(text)
    text = _fix_hyphenation(text)
    text = _normalize_text(text)
    return text.strip()


def _detect_repeated_header_footer_lines(pages: list[str]) -> set[str]:
    if len(pages) < 4:
        return set()

    candidates: list[str] = []
    for page in pages:
        lines = [_normalize_line(line) for line in page.splitlines() if _normalize_line(line)]
        if not lines:
            continue
        first = lines[:3]
        last = lines[-3:]
        candidates.extend(first + last)

    counts = Counter(candidates)
    minimum = max(3, int(len(pages) * 0.35))
    repeated = {line for line, count in counts.items() if count >= minimum and len(line) <= 120}
    return repeated


def _clean_page(page: str, repeated_lines: set[str]) -> str:
    lines: list[str] = []
    for raw_line in page.splitlines():
        line = _normalize_line(raw_line)
        if not line:
            lines.append("")
            continue
        if line in repeated_lines:
            continue
        if _PAGE_NUMBER_RE.match(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def _remove_probable_index(text: str) -> str:
    lines = text.splitlines()
    if len(lines) < 20:
        return text

    head_limit = min(len(lines), 220)
    head = lines[:head_limit]
    dot_leader_count = sum(1 for line in head if _DOT_LEADER_RE.search(line))
    summary_words = sum(
        1
        for line in head[:40]
        if line.strip().lower() in {"sumario", "sumário", "indice", "índice", "contents"}
    )

    if dot_leader_count < 5 and summary_words == 0:
        return text

    cut_at = 0
    for idx, line in enumerate(head):
        lower = line.strip().lower()
        if re.match(r"^(introducao|introdução|prefacio|prefácio|capitulo\s+1|capítulo\s+1|chapter\s+1)\b", lower):
            cut_at = idx
            break

    if cut_at > 0:
        return "\n".join(lines[cut_at:])
    return text


def _fix_hyphenation(text: str) -> str:
    text = re.sub(r"([A-Za-zÀ-ÿ])-\n([A-Za-zÀ-ÿ])", r"\1\2", text)
    text = re.sub(r"([^\n])\n([^\n])", r"\1 \2", text)
    return text


def _normalize_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


def _normalize_line(line: str) -> str:
    line = line.replace("\xa0", " ")
    line = re.sub(r"\s+", " ", line).strip()
    return line
