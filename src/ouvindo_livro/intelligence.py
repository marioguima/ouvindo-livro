from __future__ import annotations

import math
import re
from collections import Counter

from ouvindo_livro.models import Chapter

_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos", "em", "no", "na",
    "nos", "nas", "por", "para", "com", "sem", "que", "se", "e", "ou", "mas", "como", "mais", "menos",
    "muito", "muita", "muitos", "muitas", "quando", "onde", "porque", "tambem", "também", "sobre",
    "entre", "isso", "isto", "essa", "esse", "estas", "estes", "aquela", "aquele", "aquelas", "aqueles",
    "ser", "ter", "foi", "sao", "são", "era", "eram", "tem", "têm", "sua", "seu", "suas", "seus",
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were", "have", "has", "not",
}
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]{4,}")


def enrich_chapter_scores(chapters: list[Chapter]) -> list[Chapter]:
    corpus_frequency = _word_frequency("\n".join(chapter.text for chapter in chapters))
    scored: list[Chapter] = []
    for chapter in chapters:
        chapter.score = _score_text(chapter.text, corpus_frequency)
        scored.append(chapter)
    return scored


def build_summary(title: str, chapters: list[Chapter], max_sentences: int = 14) -> str:
    if not chapters:
        return f"# Resumo\n\nNao foi possivel detectar conteudo relevante para `{title}`.\n"

    frequency = _word_frequency("\n".join(chapter.text for chapter in chapters))
    sentences = _rank_sentences(chapters, frequency)
    selected = [sentence for _score, sentence, _chapter in sentences[:max_sentences]]
    concepts = _top_terms(frequency, limit=18)
    essential = sorted(chapters, key=lambda chapter: chapter.score, reverse=True)[: min(5, len(chapters))]

    lines = [
        "# Resumo inteligente",
        "",
        f"Livro: **{title}**",
        "",
        "## Ideia central aproximada",
        "",
    ]

    if selected:
        lines.append(selected[0])
    else:
        lines.append("O texto foi extraido, mas ainda nao houve frases suficientes para resumir com seguranca.")

    lines.extend([
        "",
        "## Ideias fortes detectadas",
        "",
    ])
    for sentence in selected[1:]:
        lines.append(f"- {sentence}")

    lines.extend([
        "",
        "## Conceitos recorrentes",
        "",
        ", ".join(concepts) if concepts else "Nenhum conceito recorrente detectado com seguranca.",
        "",
        "## Capitulos mais importantes para comecar",
        "",
    ])
    for chapter in essential:
        lines.append(f"- {chapter.index:03d}. {chapter.title} ({chapter.word_count} palavras)")

    lines.extend([
        "",
        "## Observacao",
        "",
        "Este resumo usa heuristica local no MVP. A proxima evolucao natural e plugar um LLM local ou remoto para interpretar intencao, tese, exemplos e aplicacao pratica com mais profundidade.",
    ])
    return "\n".join(lines).strip() + "\n"


def build_study_job(title: str, chapters: list[Chapter]) -> str:
    if not chapters:
        return f"# Estudo\n\nNao foi possivel montar um estudo para `{title}`.\n"

    ordered = sorted(chapters, key=lambda chapter: chapter.score, reverse=True)
    essential = ordered[: min(6, len(ordered))]
    lighter = [chapter for chapter in chapters if chapter not in essential]
    total_words = sum(chapter.word_count for chapter in chapters)
    estimated_minutes = max(1, math.ceil(total_words / 145))

    lines = [
        "# Job de estudo",
        "",
        f"Livro: **{title}**",
        "",
        "## Objetivo",
        "",
        "Transformar o livro em aprendizado escutavel, separando o que provavelmente carrega mais densidade de ideia do que pode ser revisado depois.",
        "",
        "## Estimativa de escuta",
        "",
        f"- Palavras detectadas: {total_words}",
        f"- Tempo aproximado a 145 palavras por minuto: {estimated_minutes} min",
        "",
        "## Ordem sugerida para ouvir primeiro",
        "",
    ]

    for chapter in essential:
        lines.append(f"1. {chapter.title} - {chapter.word_count} palavras")

    lines.extend([
        "",
        "## Capitulos para segunda passada",
        "",
    ])

    if lighter:
        for chapter in lighter[:10]:
            lines.append(f"- {chapter.title}")
    else:
        lines.append("Todos os capitulos entraram como essenciais neste primeiro processamento.")

    lines.extend([
        "",
        "## Perguntas de reflexao",
        "",
        "- Qual e a tese que o autor esta tentando provar?",
        "- Que decisao minha mudaria se eu levasse essa tese a serio?",
        "- Quais exemplos sao apenas apoio e quais carregam a ideia principal?",
        "- O que eu posso aplicar em ate 7 dias?",
        "- Que conceito merece virar uma anotacao permanente?",
        "",
        "## Criterio para pular partes",
        "",
        "Pule ou acelere trechos que apenas repetem a mesma ideia, listas editoriais, agradecimentos longos, indice, referencias extensas e historias que nao mudam o entendimento da tese central.",
        "",
        "## Proxima melhoria",
        "",
        "Rodar uma segunda etapa com LLM para classificar cada bloco como tese, argumento, exemplo, historia, exercicio, referencia ou ruido. Isso permitira gerar uma versao ainda mais enxuta do audiobook.",
    ])
    return "\n".join(lines).strip() + "\n"


def _word_frequency(text: str) -> Counter[str]:
    words = []
    for match in _WORD_RE.finditer(text.lower()):
        word = match.group(0)
        if word not in _STOPWORDS:
            words.append(word)
    return Counter(words)


def _score_text(text: str, frequency: Counter[str]) -> float:
    words = [word for word in _WORD_RE.findall(text.lower()) if word not in _STOPWORDS]
    if not words:
        return 0.0
    raw = sum(frequency.get(word, 0) for word in words)
    density = raw / max(1, len(words))
    length_factor = min(1.0, len(words) / 1200)
    return density * (0.35 + length_factor)


def _rank_sentences(chapters: list[Chapter], frequency: Counter[str]) -> list[tuple[float, str, Chapter]]:
    ranked: list[tuple[float, str, Chapter]] = []
    for chapter in chapters:
        sentences = [s.strip() for s in _SENTENCE_RE.split(chapter.text) if 80 <= len(s.strip()) <= 420]
        for sentence in sentences:
            score = _score_text(sentence, frequency) + (chapter.score * 0.1)
            ranked.append((score, sentence, chapter))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return _dedupe_ranked_sentences(ranked)


def _dedupe_ranked_sentences(ranked: list[tuple[float, str, Chapter]]) -> list[tuple[float, str, Chapter]]:
    result: list[tuple[float, str, Chapter]] = []
    seen_roots: set[str] = set()
    for score, sentence, chapter in ranked:
        root = " ".join(_WORD_RE.findall(sentence.lower())[:8])
        if root in seen_roots:
            continue
        seen_roots.add(root)
        result.append((score, sentence, chapter))
    return result


def _top_terms(frequency: Counter[str], limit: int) -> list[str]:
    return [word for word, _count in frequency.most_common(limit)]
