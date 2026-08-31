from __future__ import annotations

import re
from pathlib import Path

import fitz
from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT, epub

from ouvindo_livro.models import ExtractedBook

SUPPORTED_EXTENSIONS = {".pdf", ".epub", ".txt", ".md"}


def extract_book(path: Path) -> ExtractedBook:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Formato nao suportado: {suffix}. Suportados: {supported}")

    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix == ".epub":
        return _extract_epub(path)
    return _extract_plain_text(path)


def _extract_pdf(path: Path) -> ExtractedBook:
    document = fitz.open(path)
    pages: list[str] = []
    metadata = {k: str(v) for k, v in (document.metadata or {}).items() if v}

    for page in document:
        text = page.get_text("text", sort=True)
        pages.append(text or "")

    title = _pick_title(metadata.get("title"), path.stem)
    return ExtractedBook(
        title=title,
        source_path=str(path),
        source_type="pdf",
        pages=pages,
        raw_text="\n\n".join(pages),
        metadata=metadata,
    )


def _extract_epub(path: Path) -> ExtractedBook:
    book = epub.read_epub(str(path))
    metadata = _epub_metadata(book)
    pages: list[str] = []

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
        if text.strip():
            pages.append(text)

    title = _pick_title(metadata.get("title"), path.stem)
    return ExtractedBook(
        title=title,
        source_path=str(path),
        source_type="epub",
        pages=pages,
        raw_text="\n\n".join(pages),
        metadata=metadata,
    )


def _extract_plain_text(path: Path) -> ExtractedBook:
    text = path.read_text(encoding="utf-8", errors="ignore")
    title = _pick_title(None, path.stem)
    return ExtractedBook(
        title=title,
        source_path=str(path),
        source_type=path.suffix.lower().lstrip("."),
        pages=[text],
        raw_text=text,
        metadata={"title": title},
    )


def _epub_metadata(book: epub.EpubBook) -> dict[str, str]:
    result: dict[str, str] = {}
    title = book.get_metadata("DC", "title")
    creator = book.get_metadata("DC", "creator")
    language = book.get_metadata("DC", "language")

    if title:
        result["title"] = str(title[0][0])
    if creator:
        result["author"] = str(creator[0][0])
    if language:
        result["language"] = str(language[0][0])
    return result


def _pick_title(candidate: str | None, fallback: str) -> str:
    cleaned = (candidate or "").strip()
    if not cleaned or cleaned.lower() in {"untitled", "unknown"}:
        cleaned = fallback
    cleaned = cleaned.replace("_", "-")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned
