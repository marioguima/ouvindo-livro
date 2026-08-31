from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from ouvindo_livro.config import Settings
from ouvindo_livro.models import Chapter
from ouvindo_livro.utils import ensure_dir, limit_text, write_text


@dataclass(frozen=True)
class TTSResult:
    chapter: Chapter
    narration_path: Path
    audio_path: Path | None
    status: str
    error: str | None = None


def generate_audio(
    chapters: list[Chapter],
    output_dir: Path,
    settings: Settings,
    skip_audio: bool = False,
) -> list[TTSResult]:
    narration_dir = ensure_dir(output_dir / "narracao")
    audio_dir = ensure_dir(output_dir / "audio")
    results: list[TTSResult] = []

    if skip_audio or not settings.tts_command:
        _write_pending_tts_readme(audio_dir)

    for chapter in chapters:
        narration_text = _build_narration_text(chapter, settings.tts_max_chars_per_chapter)
        narration_path = narration_dir / f"{chapter.slug}.txt"
        write_text(narration_path, narration_text)

        if skip_audio or not settings.tts_command:
            results.append(
                TTSResult(
                    chapter=chapter,
                    narration_path=narration_path,
                    audio_path=None,
                    status="tts-pendente",
                )
            )
            continue

        audio_path = audio_dir / f"{chapter.slug}.{settings.tts_output_extension}"
        command = _render_command(
            settings.tts_command,
            input_path=narration_path,
            output_path=audio_path,
            chapter=chapter,
        )

        try:
            completed = subprocess.run(command, shell=True, check=False, text=True, capture_output=True)
            if completed.returncode != 0:
                results.append(
                    TTSResult(
                        chapter=chapter,
                        narration_path=narration_path,
                        audio_path=audio_path,
                        status="erro",
                        error=(completed.stderr or completed.stdout or "Erro desconhecido").strip(),
                    )
                )
                continue
            results.append(
                TTSResult(
                    chapter=chapter,
                    narration_path=narration_path,
                    audio_path=audio_path,
                    status="ok" if audio_path.exists() else "comando-executado-audio-nao-encontrado",
                )
            )
        except Exception as exc:
            results.append(
                TTSResult(
                    chapter=chapter,
                    narration_path=narration_path,
                    audio_path=audio_path,
                    status="erro",
                    error=str(exc),
                )
            )
    return results


def _build_narration_text(chapter: Chapter, max_chars: int) -> str:
    text = limit_text(chapter.text.strip(), max_chars)
    return f"{chapter.title}\n\n{text}\n"


def _render_command(command: str, input_path: Path, output_path: Path, chapter: Chapter) -> str:
    replacements = {
        "input": str(input_path),
        "output": str(output_path),
        "title": chapter.title,
        "slug": chapter.slug,
        "index": f"{chapter.index:03d}",
    }
    rendered = command
    for key, value in replacements.items():
        rendered = rendered.replace("{" + key + "}", value)
    return rendered


def _write_pending_tts_readme(audio_dir: Path) -> None:
    content = """# TTS pendente

O projeto gerou os arquivos em `narracao/`, mas nao gerou audio porque `TTS_COMMAND` nao foi configurado ou porque o comando foi executado com `--sem-audio`.

Configure o `.env` com seu motor de TTS, por exemplo:

```env
TTS_COMMAND=python caminho/tts.py --input "{input}" --output "{output}"
TTS_OUTPUT_EXTENSION=mp3
```

Use aspas nos placeholders se seus caminhos puderem conter espacos.
"""
    write_text(audio_dir / "README_TTS_PENDENTE.md", content)
