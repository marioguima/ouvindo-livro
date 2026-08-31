from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ExtractedBook(BaseModel):
    title: str
    source_path: str
    source_type: str
    pages: list[str] = Field(default_factory=list)
    raw_text: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)


class Chapter(BaseModel):
    index: int
    title: str
    slug: str
    text: str
    char_count: int
    word_count: int
    score: float = 0.0


class ProcessedBook(BaseModel):
    title: str
    slug: str
    source_path: str
    output_dir: Path
    clean_text: str
    chapters: list[Chapter]
    summary_markdown: str
    study_markdown: str
    metadata: dict[str, str] = Field(default_factory=dict)
