# TokenMark v0.9.4 Enterprise Localization & Documentation Engine

TokenMark is a **Markdown-first localization, documentation, and composition engine** for modern Doc-as-Code workflows.

It keeps Markdown as the human-readable source, then derives stable semantic tokens, translation catalogs, structure models, localized HTML/PDF/Markdown output, Translation Memory, QA reports, dashboards, and a local browser-based Studio.

**Current version:** `0.9.4`

---

## What TokenMark does

TokenMark turns this:

```text
Markdown / meeting notes / technical docs
```

into this:

```text
stable content tokens
translation catalogs
document IR
localized Markdown
HTML / PDF
Translation Memory
QA reports
i18n dashboard
Studio review workflow
generated documentation from notes
```

Core principle:

```text
Markdown remains the source of truth.
TokenMark adds structure, localization, QA, and controlled generation around it.
```

---

## Key features in v0.9.4

### Markdown-first compiler

- Parses Markdown files from `docs/`
- Segments content into semantic units
- Generates stable token IDs
- Preserves code blocks and frozen technical structures
- Renders HTML, PDF, and localized Markdown
- Mirrors nested docs paths into `build/`

Example:

```text
docs/generated/index.md
        ↓
build/generated/index.html
```

### Localization engine

- JSON translation catalogs
- PO/XLIFF support
- Segment status: `missing`, `needs_review`, `translated`, `frozen`, `stale`
- Glossary support
- Localized Markdown export
- SSG export for MkDocs, Docusaurus, Hugo, Nextra, etc.

### AI translation providers

Supported providers:

```text
mock
identity
openai
gemini
deepl
lmstudio
```

LM Studio support uses the OpenAI-compatible local API.

### Translation Memory

- SQLite backend at `locales/tm.sqlite`
- TM backfill from existing catalogs
- Fuzzy suggestions
- Hybrid lexical/vector matching
- Audit/history support
- Studio TM suggestions

### Studio

Local browser-based review interface:

```text
http://127.0.0.1:8000/__tokenmark/studio
```

Studio supports:

- live preview
- source/target editing
- token inspection
- TM suggestions
- AI mock
- **AI LM Studio** one-segment translation
- save-to-catalog
- save-to-TM

Important distinction:

```text
TM suggestions = reuse existing translations from the Translation Memory
AI LM Studio   = generate a new translation with the local LM Studio model
```

### Compose engine

TokenMark can now generate structured documentation from unstructured notes.

Pipeline:

```text
Unstructured ideas
    ↓
semantic ordering
    ↓
Intent Graph
    ↓
documentation plan
    ↓
controlled Markdown generation
    ↓
normal TokenMark build / QA / i18n / PDF
```

Example:

```powershell
tokenmark compose docs\meeting_notes.md `
  --provider lmstudio `
  --type technical-guide `
  --audience developers `
  --outdir docs\generated `
  --build
```

Generated files:

```text
docs/generated/index.md
docs/generated/overview.md
docs/generated/concepts.md
docs/generated/open_questions.md

build/compose.intent.json
build/compose.trace.json
build/compose.open_questions.md
```

### QA and dashboard

- Markdown structure linter
- Link/URL/placeholder checks
- Inline code checks
- MDX/JSX safety checks
- Text expansion warnings
- Visual QA
- Lint auto-fix
- Static i18n dashboard

Dashboard:

```text
build/i18n-dashboard.html
```

Open locally:

```text
http://127.0.0.1:8000/i18n-dashboard.html
```

---

## Installation

From the TokenMark project folder:

```powershell
cd D:\tm

python -m pip uninstall -y tokenmark
python -m pip install -e . --force-reinstall

tokenmark doctor
```

Expected:

```text
version: 0.9.4
```

Optional PDF support:

```powershell
python -m pip install -e ".[pdf]"
```

Optional server/vector extras:

```powershell
python -m pip install -e ".[server,vector]"
```

---

## Project structure

Typical TokenMark project:

```text
project/
  .tokenmark.json
  docs/
    intro.md
    guide.md
    generated/
      index.md
  locales/
    de/
      intro.catalog.json
    en/
      intro.catalog.json
    glossary.json
    tm.sqlite
  themes/
    default.css
  build/
    intro.html
    intro.en.html
    generated/
      index.html
    site_index.json
    i18n-dashboard.html
```

---

## Configuration

Example `.tokenmark.json`:

```json
{
  "source_lang": "de",
  "docs_dir": "docs",
  "locales_dir": "locales",
  "build_dir": "build",
  "theme": "themes/default.css",
  "tm_path": "locales/tm.sqlite",
  "plugins": ["tokenmark.plugins.mermaid"],
  "mdx_translatable_props": [
    "title",
    "label",
    "description",
    "alt",
    "aria-label",
    "placeholder"
  ]
}
```

---

## Basic workflow

```powershell
cd D:\tm

tokenmark build --force --dashboard
tokenmark extract --lang en
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
tokenmark render --lang en --format html
tokenmark tm-backfill --lang en
tokenmark lint --lang en --fix
tokenmark visual-qa --lang en
tokenmark dashboard --lang en
tokenmark serve --port 8000 --inspect
```

Open:

```text
http://127.0.0.1:8000/__tokenmark/studio
```

---

## LM Studio workflow

Start LM Studio server first. It should expose an OpenAI-compatible endpoint like:

```text
http://127.0.0.1:1234/v1
```

Set environment variables:

```powershell
$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"
```

Run translation:

```powershell
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
```

Recommended for local models:

```text
--batch-size 1
```

This is slower but more robust because local models often produce cleaner JSON for one segment at a time.

---

## Gemini workflow

```powershell
Remove-Item Env:GOOGLE_API_KEY -ErrorAction SilentlyContinue
$env:GEMINI_API_KEY="YOUR_GEMINI_KEY"
$env:TOKENMARK_GEMINI_MODEL="gemini-2.5-flash-lite"

tokenmark auto-translate --lang en --provider gemini --batch-size 1
```

If Gemini returns temporary overload errors, reduce the batch size or retry later.

---

## OpenAI workflow

```powershell
$env:OPENAI_API_KEY="YOUR_OPENAI_KEY"

tokenmark auto-translate --lang en --provider openai --batch-size 3
```

---

## DeepL workflow

```powershell
$env:DEEPL_API_KEY="YOUR_DEEPL_KEY"

tokenmark auto-translate --lang en --provider deepl --batch-size 10
```

---

## Compose workflow

Create meeting notes:

```powershell
New-Item -ItemType Directory docs -Force | Out-Null
New-Item -ItemType Directory docs\generated -Force | Out-Null

@"
# Meeting Notes

- TokenMark soll chaotische Bullet Points in Dokumentation verwandeln
- Zielgruppe: Entwickler und technische Autoren
- Pipeline: Notizen -> Intent Graph -> Markdown -> QA -> i18n -> PDF
- Risiko: KI darf keine Fakten erfinden
- Wie markieren wir offene Fragen?
- LM Studio soll lokal nutzbar sein
"@ | Set-Content docs\meeting_notes.md -Encoding UTF8
```

Compose with heuristic provider:

```powershell
tokenmark compose docs\meeting_notes.md `
  --provider heuristic `
  --type technical-guide `
  --audience developers `
  --outdir docs\generated `
  --build
```

Compose with LM Studio:

```powershell
$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"

tokenmark compose docs\meeting_notes.md `
  --provider lmstudio `
  --type technical-guide `
  --audience developers `
  --outdir docs\generated `
  --build
```

Build and serve:

```powershell
tokenmark build --force --dashboard
tokenmark serve --port 8000 --inspect
```

Open:

```text
http://127.0.0.1:8000/generated/index.html
```

---

## Working with `tokenmark_whitepaper_v0_9_4.md`

Place the whitepaper into `docs/`:

```powershell
Copy-Item .\tokenmark_whitepaper_v0_9_4.md docs\tokenmark_whitepaper.md
```

Build:

```powershell
tokenmark build --force --dashboard
```

Open:

```text
http://127.0.0.1:8000/tokenmark_whitepaper.html
```

Extract English catalog:

```powershell
tokenmark extract docs\tokenmark_whitepaper.md --lang en
```

Translate with LM Studio:

```powershell
$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"

tokenmark auto-translate docs\tokenmark_whitepaper.md --lang en --provider lmstudio --batch-size 1
```

Render English HTML:

```powershell
tokenmark render docs\tokenmark_whitepaper.md --lang en --format html
```

Open:

```text
http://127.0.0.1:8000/tokenmark_whitepaper.en.html
```

Create PDF:

```powershell
python -m pip install -e ".[pdf]"
tokenmark render docs\tokenmark_whitepaper.md --lang en --format pdf
```

Open PDF:

```powershell
start build\tokenmark_whitepaper.en.pdf
```

---

## PDF generation

Install PDF dependencies:

```powershell
python -m pip install -e ".[pdf]"
```

Render all English PDFs:

```powershell
tokenmark render --lang en --format pdf
```

Render one file:

```powershell
tokenmark render docs\tokenmark_whitepaper.md --lang en --format pdf
```

List PDFs:

```powershell
dir build\*.pdf
```

---

## Translation Memory commands

Backfill TM from existing catalogs:

```powershell
tokenmark tm-backfill --lang en
```

Suggest translations:

```powershell
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode hybrid
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode lexical
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode vector
```

Show history:

```powershell
tokenmark tm-history --lang en --id <token-id>
```

---

## Neural embeddings

Default vector matching is offline and deterministic.

Optional local neural embeddings:

```powershell
python -m pip install -e ".[vector]"
$env:TOKENMARK_EMBEDDING_BACKEND="sentence-transformers"

tokenmark tm-backfill --lang en
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode vector
```

OpenAI embeddings:

```powershell
$env:OPENAI_API_KEY="YOUR_OPENAI_KEY"
$env:TOKENMARK_EMBEDDING_BACKEND="openai"

tokenmark tm-backfill --lang en
```

---

## QA and linting

Run linter:

```powershell
tokenmark lint --lang en
```

Run AI/semantic linter:

```powershell
tokenmark lint --lang en --ai
```

Auto-fix conservative Markdown structure errors:

```powershell
tokenmark lint --lang en --fix
```

Visual QA:

```powershell
tokenmark visual-qa --lang en
```

Strict CI check:

```powershell
tokenmark check --lang en --strict --lint
```

---

## Dashboard and CI

Generate dashboard:

```powershell
tokenmark dashboard --lang en
```

or:

```powershell
tokenmark build --force --dashboard
```

Open:

```text
http://127.0.0.1:8000/i18n-dashboard.html
```

CI report:

```powershell
tokenmark ci-report --lang en
```

CI automation:

```powershell
tokenmark ci --lang en --provider lmstudio
```

Cross-branch sync:

```powershell
tokenmark sync-branches --from main --lang en --dry-run
```

---

## Studio

Start:

```powershell
tokenmark serve --port 8000 --inspect
```

Open:

```text
http://127.0.0.1:8000/__tokenmark/studio
```

Important Studio buttons:

```text
TM suggestions
  Search existing translations in the SQLite Translation Memory.

AI mock
  Generate a fake test target: [en] Source.

AI LM Studio
  Ask the local LM Studio model to translate the selected segment.

Save
  Save target to catalog and synchronize it into the Translation Memory.
```

---

## FastAPI/WebSocket server

Optional collaborative server:

```powershell
python -m pip install -e ".[server]"

tokenmark serve --fastapi --port 8000 --inspect
```

Open:

```text
http://127.0.0.1:8000/__tokenmark/studio
```

---

## Useful troubleshooting

### `doctor` shows old config version

If `tokenmark doctor` shows:

```text
version: 0.9.4
config_version: 0.9.1
```

that is okay. `version` is the installed package. `config_version` may come from the project config.

### `generated/index.html` exists but browser returns 404

Make sure the server is started in the same project root:

```powershell
cd D:\tm
tokenmark serve --port 8000 --inspect
```

Check:

```powershell
dir build\generated\index.html
```

Open:

```text
http://127.0.0.1:8000/generated/index.html
```

### Studio shows no TM suggestions

Backfill the Translation Memory:

```powershell
tokenmark tm-backfill --lang en
```

Then restart the server.

### LM Studio translates but TokenMark does not save

Check the provider output. Local models sometimes return invalid JSON. v0.8.3+ repairs common cases such as trailing commas:

```json
["translation",]
```

Recommended:

```powershell
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
```

### Check whether targets are filled

```powershell
Select-String -Path locales\en\*.catalog.json -Pattern '"target": "[^"]' | Select-Object -First 20
```

Count empty targets:

```powershell
Select-String -Path locales\en\*.catalog.json -Pattern '"target": ""' | Measure-Object
```

Check for old mock translations:

```powershell
Select-String -Path locales\en\*.catalog.json -Pattern "\[en\]"
```

### Rebuild from scratch

```powershell
Remove-Item locales\en -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item locales\tm.sqlite -Force -ErrorAction SilentlyContinue
Remove-Item build -Recurse -Force -ErrorAction SilentlyContinue

tokenmark build --force --dashboard
tokenmark extract --lang en
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
tokenmark render --lang en --format html
tokenmark tm-backfill --lang en
tokenmark dashboard --lang en
tokenmark serve --port 8000 --inspect
```

---

## Important commands overview

```powershell
tokenmark doctor
tokenmark init --force
tokenmark build --force --dashboard
tokenmark extract --lang en
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
tokenmark render --lang en --format html
tokenmark render --lang en --format markdown
tokenmark render --lang en --format pdf
tokenmark lint --lang en --fix
tokenmark visual-qa --lang en
tokenmark tm-backfill --lang en
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode hybrid
tokenmark dashboard --lang en
tokenmark ci-report --lang en
tokenmark compose docs\meeting_notes.md --provider lmstudio --type technical-guide --audience developers --outdir docs\generated --build
tokenmark serve --port 8000 --inspect
```

---

## Short positioning

**TokenMark is not a new Markdown. TokenMark is the control layer that makes Markdown enterprise-ready.**
