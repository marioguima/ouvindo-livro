from __future__ import annotations

from pathlib import Path

from ouvindo_livro.clean import clean_book_text
from ouvindo_livro.config import load_settings
from ouvindo_livro.export import export_processed_book
from ouvindo_livro.extract import extract_book
from ouvindo_livro.intelligence import build_study_job, build_summary, enrich_chapter_scores
from ouvindo_livro.models import ProcessedBook
from ouvindo_livro.split import split_into_chapters
from ouvindo_livro.tts import generate_audio
from ouvindo_livro.utils import ensure_dir, slugify


def process_book(
    input_path: Path,
    output_root: Path,
    skip_audio: bool = False,
    chapter_limit: int | None = None,
) -> ProcessedBook:
    settings = load_settings()

    extracted = extract_book(input_path)
    clean_text = clean_book_text(extracted)
    chapters = split_into_chapters(clean_text)

    if chapter_limit is not None and chapter_limit > 0:
        chapters = chapters[:chapter_limit]

    chapters = enrich_chapter_scores(chapters)

    book_slug = slugify(extracted.title)
    output_dir = ensure_dir(output_root / book_slug)

    summary = build_summary(extracted.title, chapters)
    study = build_study_job(extracted.title, chapters)

    processed = ProcessedBook(
        title=extracted.title,
        slug=book_slug,
        source_path=str(input_path),
        output_dir=output_dir,
        clean_text=clean_text,
        chapters=chapters,
        summary_markdown=summary,
        study_markdown=study,
        metadata={**extracted.metadata, "source_type": extracted.source_type, "language": settings.book_language},
    )

    tts_results = generate_audio(chapters, output_dir, settings, skip_audio=skip_audio)
    export_processed_book(processed, tts_results)
    return processed
