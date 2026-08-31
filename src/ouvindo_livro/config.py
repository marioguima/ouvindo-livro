from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    tts_command: str | None
    tts_output_extension: str
    tts_max_chars_per_chapter: int
    book_language: str


_PROJECT_ROOT = Path.cwd()


def load_settings() -> Settings:
    load_dotenv(_PROJECT_ROOT / ".env")

    raw_command = os.getenv("TTS_COMMAND", "").strip()
    output_extension = os.getenv("TTS_OUTPUT_EXTENSION", "mp3").strip().lstrip(".") or "mp3"

    try:
        max_chars = int(os.getenv("TTS_MAX_CHARS_PER_CHAPTER", "18000"))
    except ValueError:
        max_chars = 18000

    return Settings(
        tts_command=raw_command or None,
        tts_output_extension=output_extension,
        tts_max_chars_per_chapter=max_chars,
        book_language=os.getenv("BOOK_LANGUAGE", "pt-BR").strip() or "pt-BR",
    )
