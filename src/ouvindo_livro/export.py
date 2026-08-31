from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ouvindo_livro.models import Chapter, ProcessedBook
from ouvindo_livro.tts import TTSResult
from ouvindo_livro.utils import ensure_dir, write_text


def export_processed_book(book: ProcessedBook, tts_results: list[TTSResult]) -> None:
    output_dir = ensure_dir(book.output_dir)
    chapters_dir = ensure_dir(output_dir / "capitulos")

    write_text(output_dir / "livro-limpo.md", _build_clean_book_markdown(book))
    write_text(output_dir / "resumo.md", book.summary_markdown)
    write_text(output_dir / "estudo.md", book.study_markdown)

    for chapter in book.chapters:
        write_text(chapters_dir / f"{chapter.slug}.md", _chapter_markdown(chapter))

    manifest = _build_manifest(book, tts_results)
    write_text(output_dir / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))


def _build_clean_book_markdown(book: ProcessedBook) -> str:
    lines = [f"# {book.title}", ""]
    for chapter in book.chapters:
        lines.append(f"## {chapter.title}")
        lines.append("")
        lines.append(chapter.text.strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _chapter_markdown(chapter: Chapter) -> str:
    return f"# {chapter.title}\n\n{chapter.text.strip()}\n"


def _build_manifest(book: ProcessedBook, tts_results: list[TTSResult]) -> dict:
    return {
        "title": book.title,
        "slug": book.slug,
        "source_path": book.source_path,
        "output_dir": str(book.output_dir),
        "processed_at": datetime.now().isoformat(timespec="seconds"),
        "metadata": book.metadata,
        "chapters": [
            {
                "index": chapter.index,
                "title": chapter.title,
                "slug": chapter.slug,
                "char_count": chapter.char_count,
                "word_count": chapter.word_count,
                "score": chapter.score,
                "chapter_file": f"capitulos/{chapter.slug}.md",
                "narration_file": f"narracao/{chapter.slug}.txt",
                "audio_file": _find_audio_file(chapter, tts_results),
                "tts_status": _find_tts_status(chapter, tts_results),
            }
            for chapter in book.chapters
        ],
    }


def _find_audio_file(chapter: Chapter, results: list[TTSResult]) -> str | None:
    for result in results:
        if result.chapter.index == chapter.index and result.audio_path:
            return str(result.audio_path.relative_to(result.audio_path.parents[1]))
    return None


def _find_tts_status(chapter: Chapter, results: list[TTSResult]) -> str:
    for result in results:
        if result.chapter.index == chapter.index:
            return result.status
    return "nao-executado"
