from __future__ import annotations

import re
import unicodedata
from pathlib import Path


def slugify(value: str, fallback: str = "livro") -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or fallback


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def count_words(text: str) -> int:
    return len(re.findall(r"\w+", text, flags=re.UNICODE))


def limit_text(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    paragraph_break = cut.rfind("\n\n")
    if paragraph_break > 1000:
        return cut[:paragraph_break].strip()
    sentence_break = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if sentence_break > 1000:
        return cut[: sentence_break + 1].strip()
    return cut.strip()
