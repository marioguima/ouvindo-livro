# Ouvindo Livro

Projeto separado e enxuto para transformar livros em material de aprendizado por audio.

A prioridade deste repositório é velocidade: receber um PDF, EPUB, TXT ou Markdown, extrair o conteúdo, limpar ruídos, separar capítulos, gerar resumo/estudo inteligente e preparar audio por capítulo para ouvir no celular.

## O que este MVP faz

- Processa arquivos `.pdf`, `.epub`, `.txt` e `.md`.
- Extrai texto de PDFs com PyMuPDF.
- Extrai texto de EPUB com ebooklib e BeautifulSoup.
- Remove cabeçalhos e rodapés repetidos por heurística.
- Remove numeração de página isolada.
- Corrige hifenização de quebra de linha.
- Normaliza espaços, quebras e linhas vazias.
- Detecta capítulos por padrões como `Capítulo`, `Parte`, `Introdução`, `Chapter` e headings Markdown.
- Gera capítulos em Markdown.
- Gera `livro-limpo.md`.
- Gera `resumo.md` com extração heurística das ideias mais fortes.
- Gera `estudo.md` com ordem de escuta, capítulos essenciais e perguntas de reflexão.
- Gera `manifest.json` com metadados do processamento.
- Prepara audio por capítulo usando um comando externo de TTS configurado no `.env`.
- Sobe Audiobookshelf por Docker para ouvir no celular.

## O que este MVP ainda não tenta resolver

- Não tem painel web.
- Não tem login.
- Não tem banco.
- Não baixa livros automaticamente.
- Não burla proteção, DRM ou direitos autorais.
- Não tenta ser perfeito na primeira extração.
- Não cria player próprio.

## Instalação local

Requisitos:

- Python 3.11 ou superior
- uv
- ffmpeg, quando seu TTS precisar juntar ou converter audio
- Docker, para subir Audiobookshelf

```bash
uv sync
cp .env.example .env
```

## Uso rápido

Coloque um livro em `entrada/`.

```bash
uv run ouvindo-livro processar entrada/seu-livro.pdf
```

A saída será criada em `saida/<nome-do-livro>/`.

Exemplo:

```txt
saida/meu-livro/
  livro-limpo.md
  resumo.md
  estudo.md
  manifest.json
  capitulos/
    001-introducao.md
    002-capitulo-1.md
  narracao/
    001-introducao.txt
    002-capitulo-1.txt
  audio/
    001-introducao.mp3
    002-capitulo-1.mp3
```

## TTS

O projeto não prende você a um motor de voz. Ele chama um comando externo configurável.

No `.env`, configure:

```env
TTS_COMMAND=python caminho/para/seu_tts.py --input "{input}" --output "{output}"
TTS_OUTPUT_EXTENSION=mp3
```

Placeholders disponíveis:

- `{input}`: arquivo `.txt` com o texto do capítulo.
- `{output}`: caminho final do audio esperado.
- `{title}`: título do capítulo.
- `{slug}`: slug do capítulo.
- `{index}`: número do capítulo com 3 dígitos.

Se `TTS_COMMAND` estiver vazio, o projeto gera os arquivos de narração em `narracao/` e cria um aviso em `audio/README_TTS_PENDENTE.md`.

Isso permite começar sem amarrar o MVP ao Chatterbox, OmniVoice, Kokoro ou qualquer outro engine.

## Audiobookshelf

Suba o servidor:

```bash
docker compose up -d
```

Depois abra:

```txt
http://localhost:13378
```

Configure a biblioteca apontando para `/audiobooks` dentro do container. A pasta `./saida` do projeto já fica montada nesse caminho.

## Comandos úteis

Processar sem gerar audio:

```bash
uv run ouvindo-livro processar entrada/livro.pdf --sem-audio
```

Limitar quantidade de capítulos para teste rápido:

```bash
uv run ouvindo-livro processar entrada/livro.pdf --limite-capitulos 2
```

Escolher pasta de saída:

```bash
uv run ouvindo-livro processar entrada/livro.pdf --saida /caminho/saida
```

## Estratégia do projeto

A primeira vitória não é criar um produto bonito. A primeira vitória é processar um livro real e gerar algo que você consiga ouvir.

Ordem de evolução recomendada:

1. Validar com 1 PDF simples.
2. Validar com 1 EPUB.
3. Ajustar limpeza de cabeçalho/rodapé com casos reais.
4. Plugar Chatterbox ou OmniVoice via `TTS_COMMAND`.
5. Subir Audiobookshelf e ouvir pelo celular.
6. Adicionar MinerU somente quando encontrar PDF difícil.
7. Adicionar Cloudflare R2 somente quando precisar publicar fora da máquina.
8. Adicionar busca de livros depois que o pipeline estiver gerando valor.

## Licença

Projeto pessoal em fase inicial.
