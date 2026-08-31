from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ouvindo_livro import __version__
from ouvindo_livro.processor import process_book

console = Console()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "processar":
        return _process_command(args)

    parser.print_help()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ouvindo-livro",
        description="Transforma livros em texto limpo, estudo inteligente e audio por capitulo.",
    )
    parser.add_argument("--version", action="version", version=f"ouvindo-livro {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    processar = subparsers.add_parser("processar", help="Processa um PDF, EPUB, TXT ou Markdown")
    processar.add_argument("arquivo", type=Path, help="Caminho do livro de entrada")
    processar.add_argument("--saida", type=Path, default=Path("saida"), help="Pasta raiz de saida")
    processar.add_argument("--sem-audio", action="store_true", help="Gera somente textos e narracao")
    processar.add_argument(
        "--limite-capitulos",
        type=int,
        default=None,
        help="Limita a quantidade de capitulos para teste rapido",
    )
    return parser


def _process_command(args: argparse.Namespace) -> int:
    input_path = args.arquivo
    output_root = args.saida

    try:
        console.print(Panel.fit(f"Processando: {input_path}", title="Ouvindo Livro"))
        processed = process_book(
            input_path=input_path,
            output_root=output_root,
            skip_audio=args.sem_audio,
            chapter_limit=args.limite_capitulos,
        )
    except Exception as exc:
        console.print(f"[bold red]Erro:[/bold red] {exc}")
        return 1

    table = Table(title="Resultado")
    table.add_column("Item")
    table.add_column("Valor")
    table.add_row("Livro", processed.title)
    table.add_row("Capitulos", str(len(processed.chapters)))
    table.add_row("Saida", str(processed.output_dir))
    table.add_row("Resumo", str(processed.output_dir / "resumo.md"))
    table.add_row("Estudo", str(processed.output_dir / "estudo.md"))
    table.add_row("Audiobookshelf", "docker compose up -d")
    console.print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
