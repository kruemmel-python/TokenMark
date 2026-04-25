# TokenMark Commands

**Version:** TokenMark v0.9.4  
**Ziel:** Zentrale Befehlsreferenz für lokale Entwicklung, Dokumentationserzeugung, Übersetzung, QA, PDF, Studio, Compose und LM Studio.

> Hinweis: Die Beispiele sind primär für **PowerShell unter Windows** geschrieben, weil die bisherigen Workflows unter `D:\tm` und `D:\tokenmark_project` liefen. Wo sinnvoll, sind Bash/macOS/Linux-Varianten ergänzt.

---

## 1. Projektordner öffnen

### PowerShell

```powershell
cd D:\tm
```

Oder, falls dein Projekt dort liegt:

```powershell
cd D:\tokenmark_project
```

### Bash

```bash
cd /path/to/tokenmark_project
```

---

## 2. TokenMark installieren oder aktualisieren

### PowerShell

```powershell
cd D:\tm

python -m pip uninstall -y tokenmark
python -m pip install -e . --force-reinstall

tokenmark doctor
```

Erwartet:

```text
version: 0.9.4
```

### Bash

```bash
cd /path/to/tokenmark_project

python -m pip uninstall -y tokenmark
python -m pip install -e . --force-reinstall

tokenmark doctor
```

---

## 3. Optionale Abhängigkeiten installieren

### PDF-Unterstützung

```powershell
python -m pip install -e ".[pdf]"
```

### Server-/FastAPI-Unterstützung

```powershell
python -m pip install -e ".[server]"
```

### Neural Embeddings / Vector TM

```powershell
python -m pip install -e ".[vector]"
```

### MkDocs-Integration

```powershell
python -m pip install -e ".[mkdocs]"
```

### Alles zusammen

```powershell
python -m pip install -e ".[pdf,server,vector,mkdocs]"
```

### Gemini SDK

```powershell
python -m pip install google-genai
```

---

## 4. Projekt initialisieren

```powershell
tokenmark init
```

Mit Überschreiben vorhandener Projektdateien:

```powershell
tokenmark init --force
```

Danach prüfen:

```powershell
tokenmark doctor
```

---

## 5. Empfohlene Projektstruktur

```text
project/
  .tokenmark.json
  docs/
    tokenmark_whitepaper_v0_9_4.md
    meeting_notes.md
  docs/generated/
    index.md
    overview.md
  locales/
    de/
    en/
    glossary.json
    tm.sqlite
  themes/
    default.css
  build/
    tokenmark_whitepaper_v0_9_4.html
    tokenmark_whitepaper_v0_9_4.en.html
    generated/index.html
    i18n-dashboard.html
```

---

## 6. Markdown-Dateien in `docs` ablegen

Beispiel: `tokenmark_whitepaper_v0_9_4.md` in den Projektordner kopieren.

### PowerShell

```powershell
cd D:\tm

New-Item -ItemType Directory docs -Force | Out-Null

Copy-Item D:\Downloads\tokenmark_whitepaper_v0_9_4.md docs\tokenmark_whitepaper_v0_9_4.md -Force
```

Oder direkt eine Datei öffnen:

```powershell
notepad docs\tokenmark_whitepaper_v0_9_4.md
```

### Bash

```bash
mkdir -p docs
cp ~/Downloads/tokenmark_whitepaper_v0_9_4.md docs/tokenmark_whitepaper_v0_9_4.md
```

---

## 7. Projekt bauen

Alle Markdown-Dateien aus `docs/` bauen:

```powershell
tokenmark build --force
```

Mit Dashboard:

```powershell
tokenmark build --force --dashboard
```

Erzeugt typischerweise:

```text
build/*.html
build/site_index.json
build/i18n-dashboard.html
build/**/*.tokens.txt
build/**/*.ir.json
build/**/*.tokens.manifest.json
```

---

## 8. Einzelne Markdown-Datei bauen

Beispiel: Whitepaper bauen.

```powershell
tokenmark build docs\tokenmark_whitepaper_v0_9_4.md `
  --out build\tokenmark_whitepaper_v0_9_4.html `
  --tokens build\tokenmark_whitepaper_v0_9_4.tokens.txt `
  --catalog build\tokenmark_whitepaper_v0_9_4.catalog.json `
  --ir build\tokenmark_whitepaper_v0_9_4.ir.json `
  --manifest build\tokenmark_whitepaper_v0_9_4.tokens.manifest.json
```

Bash:

```bash
tokenmark build docs/tokenmark_whitepaper_v0_9_4.md \
  --out build/tokenmark_whitepaper_v0_9_4.html \
  --tokens build/tokenmark_whitepaper_v0_9_4.tokens.txt \
  --catalog build/tokenmark_whitepaper_v0_9_4.catalog.json \
  --ir build/tokenmark_whitepaper_v0_9_4.ir.json \
  --manifest build/tokenmark_whitepaper_v0_9_4.tokens.manifest.json
```

---

## 9. Ausgabe prüfen

### PowerShell

```powershell
dir build
dir build -Recurse *.html
dir build -Recurse *.pdf
dir locales
```

### Bash

```bash
ls build
find build -name "*.html"
find build -name "*.pdf"
find locales -maxdepth 3 -type f
```

---

## 10. HTML im Browser öffnen

### Datei direkt öffnen

```powershell
start build\tokenmark_whitepaper_v0_9_4.html
```

### Über TokenMark Server öffnen

```powershell
tokenmark serve --port 8000 --inspect
```

Dann:

```text
http://127.0.0.1:8000/tokenmark_whitepaper_v0_9_4.html
```

---

## 11. TokenMark Studio starten

```powershell
tokenmark serve --port 8000 --inspect
```

Öffnen:

```text
http://127.0.0.1:8000/__tokenmark/studio
```

Studio-Funktionen:

```text
Source/Target-Ansicht
Live Preview
Save
AI mock
AI LM Studio
TM suggestions
Statusfilter
Segmentauswahl
```

---

## 12. FastAPI/WebSocket Studio starten

Falls installiert:

```powershell
python -m pip install -e ".[server]"
```

Dann:

```powershell
tokenmark serve --fastapi --port 8000 --inspect
```

Öffnen:

```text
http://127.0.0.1:8000/__tokenmark/studio
```

---

## 13. Kataloge extrahieren

Englische Kataloge aus allen Markdown-Dateien erzeugen:

```powershell
tokenmark extract --lang en
```

Nur eine Datei:

```powershell
tokenmark extract docs\tokenmark_whitepaper_v0_9_4.md --lang en
```

---

## 14. Kataloge anzeigen

```powershell
dir locales\en
type locales\en\tokenmark_whitepaper_v0_9_4.catalog.json
```

Leere Targets zählen:

```powershell
Select-String -Path locales\en\*.catalog.json -Pattern '"target": ""' | Measure-Object
```

Gefüllte Targets anzeigen:

```powershell
Select-String -Path locales\en\*.catalog.json -Pattern '"target": "[^"]' | Select-Object -First 20
```

Mock-Texte finden:

```powershell
Select-String -Path locales\en\*.catalog.json -Pattern "\[en\]"
```

---

## 15. Mock-Übersetzung

Nur zum Testen, keine echte Übersetzung:

```powershell
tokenmark auto-translate --lang en --provider mock
```

Erzeugt ungefähr:

```text
[en] Originaltext
```

---

## 16. Identity-Übersetzung

Target entspricht Source:

```powershell
tokenmark auto-translate --lang en --provider identity
```

---

## 17. LM Studio verwenden

LM Studio muss laufen und einen OpenAI-kompatiblen Server bereitstellen.

Typisch:

```text
http://127.0.0.1:1234/v1
```

Oder im LAN:

```text
http://192.168.178.62:1234/v1
```

### Modelle prüfen

```powershell
Invoke-RestMethod http://127.0.0.1:1234/v1/models
```

### Umgebungsvariablen setzen

```powershell
Remove-Item Env:GOOGLE_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue

$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"
```

### Mit LM Studio übersetzen

```powershell
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
```

Nur eine Datei:

```powershell
tokenmark auto-translate docs\tokenmark_whitepaper_v0_9_4.md --lang en --provider lmstudio --batch-size 1
```

`--batch-size 1` ist bei lokalen Modellen am stabilsten.

---

## 18. Vollständiger LM-Studio-Lauf

```powershell
cd D:\tm

python -m pip uninstall -y tokenmark
python -m pip install -e . --force-reinstall

tokenmark doctor

Remove-Item Env:GOOGLE_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue

$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"

tokenmark build --force --dashboard
tokenmark extract --lang en
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
tokenmark render --lang en --format html
tokenmark tm-backfill --lang en
tokenmark status --lang en
tokenmark lint --lang en --fix
tokenmark visual-qa --lang en
tokenmark dashboard --lang en
tokenmark serve --port 8000 --inspect
```

Öffnen:

```text
http://127.0.0.1:8000/__tokenmark/studio
```

---

## 19. Gemini verwenden

### Installation

```powershell
python -m pip install google-genai
```

### Umgebungsvariablen

```powershell
Remove-Item Env:GOOGLE_API_KEY -ErrorAction SilentlyContinue
$env:GEMINI_API_KEY="DEIN_GEMINI_API_KEY"
$env:TOKENMARK_GEMINI_MODEL="gemini-2.5-flash-lite"
```

### Übersetzen

```powershell
tokenmark auto-translate --lang en --provider gemini --batch-size 1
```

Nur eine Datei:

```powershell
tokenmark auto-translate docs\tokenmark_whitepaper_v0_9_4.md --lang en --provider gemini --batch-size 1
```

---

## 20. OpenAI verwenden

```powershell
$env:OPENAI_API_KEY="DEIN_OPENAI_API_KEY"

tokenmark auto-translate --lang en --provider openai --batch-size 3
```

---

## 21. DeepL verwenden

```powershell
$env:DEEPL_API_KEY="DEIN_DEEPL_KEY"

tokenmark auto-translate --lang en --provider deepl --batch-size 5
```

---

## 22. HTML rendern

Alle englischen HTML-Dateien:

```powershell
tokenmark render --lang en --format html
```

Eine Datei:

```powershell
tokenmark render docs\tokenmark_whitepaper_v0_9_4.md --lang en --format html
```

Default-Sprache:

```powershell
tokenmark render --format html
```

---

## 23. PDF erzeugen

### PDF-Abhängigkeiten installieren

```powershell
python -m pip install -e ".[pdf]"
```

### Alle englischen PDFs erzeugen

```powershell
tokenmark render --lang en --format pdf
```

### Eine PDF erzeugen

```powershell
tokenmark render docs\tokenmark_whitepaper_v0_9_4.md --lang en --format pdf
```

### Deutsche/default PDFs

```powershell
tokenmark render --format pdf
```

### PDF öffnen

```powershell
dir build\*.pdf
start build\tokenmark_whitepaper_v0_9_4.en.pdf
```

Falls Pfad gespiegelt wird:

```powershell
dir build -Recurse *.pdf
```

---

## 24. Lokalisiertes Markdown erzeugen

```powershell
tokenmark render --lang en --format markdown
```

Eine Datei:

```powershell
tokenmark render docs\tokenmark_whitepaper_v0_9_4.md --lang en --format markdown
```

---

## 25. SSG-Export

```powershell
tokenmark export-ssg --lang en --outdir build\ssg\en
```

Bash:

```bash
tokenmark export-ssg --lang en --outdir build/ssg/en
```

---

## 26. Dashboard erzeugen

```powershell
tokenmark dashboard --lang en
```

Oder beim Build:

```powershell
tokenmark build --force --dashboard
```

Öffnen:

```text
http://127.0.0.1:8000/i18n-dashboard.html
```

Oder lokal:

```powershell
start build\i18n-dashboard.html
```

---

## 27. Status prüfen

```powershell
tokenmark status --lang en
```

Beispiel:

```text
docs/tokenmark_whitepaper_v0_9_4.md: 120 translated, 20 missing, 40 needs_review, 180 total
```

---

## 28. Strict Check für CI

```powershell
tokenmark check --lang en --strict
```

Mit Lint:

```powershell
tokenmark check --lang en --strict --lint
```

---

## 29. Linting

```powershell
tokenmark lint --lang en
```

Mit AI-Heuristik:

```powershell
tokenmark lint --lang en --ai
```

Mit Auto-Fix:

```powershell
tokenmark lint --lang en --fix
```

Nur eine Datei:

```powershell
tokenmark lint docs\tokenmark_whitepaper_v0_9_4.md --lang en --fix
```

---

## 30. Visual QA

```powershell
tokenmark visual-qa --lang en
```

---

## 31. Translation Memory befüllen

```powershell
tokenmark tm-backfill --lang en
```

Ohne Sprachangabe:

```powershell
tokenmark tm-backfill
```

---

## 32. TM Suggestions per CLI

```powershell
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en
```

Mit Modus:

```powershell
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode lexical
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode vector
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode hybrid
```

---

## 33. Neural Embeddings aktivieren

### Lokales sentence-transformers Backend

```powershell
python -m pip install -e ".[vector]"

$env:TOKENMARK_EMBEDDING_BACKEND="sentence-transformers"

tokenmark tm-backfill --lang en
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode vector
```

### OpenAI Embeddings

```powershell
$env:OPENAI_API_KEY="DEIN_OPENAI_KEY"
$env:TOKENMARK_EMBEDDING_BACKEND="openai"

tokenmark tm-backfill --lang en
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode vector
```

---

## 34. TM History / Audit Trail

```powershell
tokenmark tm-history --lang en --id TOKEN_ID
```

Beispiel:

```powershell
tokenmark tm-history --lang en --id 6490160e32fe
```

---

## 35. Alte Kataloge löschen

Vorsicht: Entfernt englische Übersetzungen.

```powershell
Remove-Item locales\en -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item locales\tm.sqlite -Force -ErrorAction SilentlyContinue
```

Danach neu:

```powershell
tokenmark build --force --dashboard
tokenmark extract --lang en
```

---

## 36. PO exportieren

```powershell
tokenmark extract --lang en --format po
```

---

## 37. XLIFF exportieren

```powershell
tokenmark extract --lang en --format xliff
```

---

## 38. PO importieren

```powershell
tokenmark import locales\en.po
```

Je nach Dateiname:

```powershell
tokenmark import locales\en\tokenmark_whitepaper_v0_9_4.po
```

---

## 39. Glossar verwenden

Glossar liegt typischerweise hier:

```text
locales/glossary.json
```

Beispiel:

```json
[
  {
    "source": "TokenMark",
    "target": "TokenMark",
    "note": "Produktname, nicht übersetzen"
  },
  {
    "source": "Arbeitsbereich",
    "target": "workspace",
    "note": "Produktbegriff"
  }
]
```

Mit Glossar übersetzen:

```powershell
tokenmark auto-translate --lang en --provider lmstudio --glossary locales\glossary.json --batch-size 1
```

---

## 40. Begriffe automatisch extrahieren

```powershell
tokenmark extract-terms --min-freq 5 --limit 80
```

Direkt ins Glossar mergen:

```powershell
tokenmark extract-terms --min-freq 5 --limit 80 --merge
```

---

## 41. Compose: aus Brainstorming Dokumentation erzeugen

### Meeting Notes erzeugen

```powershell
cd D:\tm

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

### Compose mit Heuristik

```powershell
tokenmark compose docs\meeting_notes.md `
  --provider heuristic `
  --type technical-guide `
  --audience developers `
  --outdir docs\generated `
  --build
```

### Compose mit LM Studio

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

### Danach bauen

```powershell
tokenmark build --force --dashboard
```

### Ergebnis prüfen

```powershell
dir docs\generated
dir build\generated
dir build\generated\index.html
```

Öffnen:

```text
http://127.0.0.1:8000/generated/index.html
```

---

## 42. Compose-Artefakte

Compose erzeugt zusätzlich:

```text
build/compose.intent.json
build/compose.trace.json
build/compose.open_questions.md
```

Anzeigen:

```powershell
type build\compose.intent.json
type build\compose.trace.json
type build\compose.open_questions.md
```

---

## 43. Pfadfix prüfen

Seit v0.9.1 sollte gelten:

```text
docs/generated/index.md
  → build/generated/index.html
```

Prüfen:

```powershell
dir build\generated\index.html
```

---

## 44. Site Index prüfen

Seit v0.9.2 sollten Seiten aus Unterordnern `/site_index.json` absolut laden.

Prüfen:

```powershell
dir build\site_index.json
Invoke-WebRequest http://127.0.0.1:8000/site_index.json
```

---

## 45. Studio: AI LM Studio Button

Seit v0.9.4 gibt es im Studio:

```text
AI LM Studio
```

Vor dem Start setzen:

```powershell
$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"

tokenmark serve --port 8000 --inspect
```

Im Studio:

```text
1. Segment auswählen
2. AI LM Studio klicken
3. Target prüfen
4. Save klicken
5. Segment wird in Katalog und TM gespeichert
```

---

## 46. Unterschied: TM suggestions vs AI LM Studio

```text
TM suggestions
= sucht ähnliche bereits übersetzte Segmente in tm.sqlite
= kein LLM-Call

AI LM Studio
= schickt aktuelles Segment an lokales Modell
= erzeugt neue Übersetzung
= schreibt Target nach Save in Katalog und TM
```

---

## 47. Git-/CI-Report

```powershell
tokenmark ci-report --lang en
```

CI-Automation:

```powershell
tokenmark ci --lang en --provider lmstudio
```

Mit Commit:

```powershell
tokenmark ci --lang en --provider lmstudio --commit
```

---

## 48. Cross-Branch Sync

Dry run:

```powershell
tokenmark sync-branches --from main --lang en --dry-run
```

Ausführen:

```powershell
tokenmark sync-branches --from main --lang en
```

---

## 49. Server stoppen

Im laufenden Terminal:

```text
CTRL + C
```

---

## 50. Port wechseln

Wenn Port 8000 belegt ist:

```powershell
tokenmark serve --port 8001 --inspect
```

Dann:

```text
http://127.0.0.1:8001/__tokenmark/studio
```

---

## 51. Häufige Fehler: 404 bei `/generated/index.html`

Prüfen:

```powershell
cd D:\tm

dir build\generated\index.html
tokenmark doctor
tokenmark serve --port 8000 --inspect
```

Wenn Datei existiert, aber HTTP 404 kommt:

```text
Der Server läuft wahrscheinlich aus dem falschen Projektordner.
```

Fix:

```powershell
CTRL + C
cd D:\tm
tokenmark serve --port 8000 --inspect
```

---

## 52. Häufige Fehler: `/generated/site_index.json` 404

Seit v0.9.2 sollte das gefixt sein.

Prüfen:

```powershell
tokenmark doctor
```

Erwartet:

```text
version: 0.9.4
```

Dann:

```powershell
tokenmark build --force --dashboard
tokenmark serve --port 8000 --inspect
```

---

## 53. Häufige Fehler: LM Studio JSON kaputt

Lokale Modelle geben manchmal ungültiges JSON aus, zum Beispiel:

```json
["text",]
```

Seit v0.8.3 repariert TokenMark viele solche Fälle. Trotzdem empfohlen:

```powershell
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
```

---

## 54. Häufige Fehler: Gemini 503

Wenn Gemini meldet:

```text
503 UNAVAILABLE
high demand
```

Dann:

```powershell
$env:TOKENMARK_GEMINI_MODEL="gemini-2.5-flash-lite"
tokenmark auto-translate --lang en --provider gemini --batch-size 1
```

Oder später erneut versuchen.

---

## 55. Häufige Fehler: `Both GOOGLE_API_KEY and GEMINI_API_KEY are set`

Nur einen Key setzen:

```powershell
Remove-Item Env:GOOGLE_API_KEY -ErrorAction SilentlyContinue
$env:GEMINI_API_KEY="DEIN_GEMINI_API_KEY"
```

---

## 56. Häufige Fehler: TM suggestions zeigt nichts

TM benötigt vorhandene Übersetzungen.

Fix:

```powershell
tokenmark tm-backfill --lang en
tokenmark tm-suggest "TokenMark soll lokal nutzbar sein" --lang en --mode hybrid
```

Studio neu starten:

```powershell
tokenmark serve --port 8000 --inspect
```

---

## 57. Komplett frischer Projektlauf mit Whitepaper

```powershell
cd D:\tm

python -m pip uninstall -y tokenmark
python -m pip install -e . --force-reinstall

tokenmark doctor

New-Item -ItemType Directory docs -Force | Out-Null

# Beispiel: Whitepaper-Datei in docs ablegen
# Passe den Quellpfad an deinen Download-Ort an.
Copy-Item D:\Downloads\tokenmark_whitepaper_v0_9_4.md docs\tokenmark_whitepaper_v0_9_4.md -Force

tokenmark build --force --dashboard
tokenmark extract --lang en

$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"

tokenmark auto-translate docs\tokenmark_whitepaper_v0_9_4.md --lang en --provider lmstudio --batch-size 1

tokenmark render docs\tokenmark_whitepaper_v0_9_4.md --lang en --format html
tokenmark render docs\tokenmark_whitepaper_v0_9_4.md --lang en --format pdf

tokenmark tm-backfill --lang en
tokenmark lint docs\tokenmark_whitepaper_v0_9_4.md --lang en --fix
tokenmark visual-qa --lang en
tokenmark dashboard --lang en

tokenmark serve --port 8000 --inspect
```

Öffnen:

```text
http://127.0.0.1:8000/tokenmark_whitepaper_v0_9_4.en.html
http://127.0.0.1:8000/__tokenmark/studio
http://127.0.0.1:8000/i18n-dashboard.html
```

---

## 58. Komplett frischer Compose-Lauf

```powershell
cd D:\tm

python -m pip uninstall -y tokenmark
python -m pip install -e . --force-reinstall

tokenmark doctor

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

$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"

tokenmark compose docs\meeting_notes.md `
  --provider lmstudio `
  --type technical-guide `
  --audience developers `
  --outdir docs\generated `
  --build

tokenmark build --force --dashboard
tokenmark extract --lang en

tokenmark render --lang en --format html
tokenmark dashboard --lang en

tokenmark serve --port 8000 --inspect
```

Öffnen:

```text
http://127.0.0.1:8000/generated/index.html
http://127.0.0.1:8000/__tokenmark/studio
http://127.0.0.1:8000/i18n-dashboard.html
```

---

## 59. Nützliche Diagnosebefehle

```powershell
tokenmark --help
tokenmark build --help
tokenmark render --help
tokenmark auto-translate --help
tokenmark compose --help
tokenmark serve --help
```

```powershell
dir docs -Recurse
dir locales -Recurse
dir build -Recurse
```

```powershell
Select-String -Path locales\en\*.catalog.json -Pattern '"status": "missing"'
Select-String -Path locales\en\*.catalog.json -Pattern '"status": "needs_review"'
Select-String -Path locales\en\*.catalog.json -Pattern '"status": "translated"'
```

---

## 60. Minimaler täglicher Workflow

```powershell
cd D:\tm

tokenmark build --force --dashboard
tokenmark extract --lang en
tokenmark status --lang en
tokenmark serve --port 8000 --inspect
```

---

## 61. Minimaler Übersetzungsworkflow mit LM Studio

```powershell
cd D:\tm

$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"

tokenmark extract --lang en
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
tokenmark render --lang en --format html
tokenmark tm-backfill --lang en
tokenmark serve --port 8000 --inspect
```

---

## 62. Minimaler PDF-Workflow

```powershell
cd D:\tm

python -m pip install -e ".[pdf]"

tokenmark build --force
tokenmark render --lang en --format html
tokenmark render --lang en --format pdf

dir build -Recurse *.pdf
```

---

## 63. Minimaler Compose-Workflow

```powershell
cd D:\tm

@"
# Meeting Notes

- Problem
- Zielgruppe
- Architektur
- Risiken
- offene Fragen
"@ | Set-Content docs\meeting_notes.md -Encoding UTF8

tokenmark compose docs\meeting_notes.md --provider heuristic --type technical-guide --audience developers --outdir docs\generated --build
tokenmark build --force --dashboard
tokenmark serve --port 8000 --inspect
```

Öffnen:

```text
http://127.0.0.1:8000/generated/index.html
```

---

## 64. Wichtige URLs

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/__tokenmark/studio
http://127.0.0.1:8000/i18n-dashboard.html
http://127.0.0.1:8000/generated/index.html
http://127.0.0.1:8000/tokenmark_whitepaper_v0_9_4.html
http://127.0.0.1:8000/tokenmark_whitepaper_v0_9_4.en.html
```

---

## 65. Wichtige Dateien

```text
.tokenmark.json
docs/
docs/generated/
locales/en/*.catalog.json
locales/glossary.json
locales/tm.sqlite
build/site_index.json
build/i18n-dashboard.html
build/compose.intent.json
build/compose.trace.json
build/compose.open_questions.md
```

---

## 66. Empfohlener produktiver Ablauf

```powershell
cd D:\tm

# 1. Dokumente schreiben oder aktualisieren
notepad docs\tokenmark_whitepaper_v0_9_4.md

# 2. Build
tokenmark build --force --dashboard

# 3. Katalog aktualisieren
tokenmark extract --lang en

# 4. Automatisch vorübersetzen
$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1

# 5. Rendern
tokenmark render --lang en --format html
tokenmark render --lang en --format pdf

# 6. QA
tokenmark lint --lang en --fix
tokenmark visual-qa --lang en

# 7. TM und Dashboard
tokenmark tm-backfill --lang en
tokenmark dashboard --lang en

# 8. Review
tokenmark serve --port 8000 --inspect
```

---

## 67. Bash-Variante für Linux/macOS

```bash
cd /path/to/tokenmark_project

python -m pip uninstall -y tokenmark
python -m pip install -e . --force-reinstall

tokenmark doctor

mkdir -p docs/generated

cat > docs/meeting_notes.md <<'EOF'
# Meeting Notes

- TokenMark soll chaotische Bullet Points in Dokumentation verwandeln
- Zielgruppe: Entwickler und technische Autoren
- Pipeline: Notizen -> Intent Graph -> Markdown -> QA -> i18n -> PDF
- Risiko: KI darf keine Fakten erfinden
- Wie markieren wir offene Fragen?
- LM Studio soll lokal nutzbar sein
EOF

export TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
export TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"

tokenmark compose docs/meeting_notes.md \
  --provider lmstudio \
  --type technical-guide \
  --audience developers \
  --outdir docs/generated \
  --build

tokenmark build --force --dashboard
tokenmark extract --lang en
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
tokenmark render --lang en --format html
tokenmark tm-backfill --lang en
tokenmark dashboard --lang en
tokenmark serve --port 8000 --inspect
```

Öffnen:

```text
http://127.0.0.1:8000/generated/index.html
http://127.0.0.1:8000/__tokenmark/studio
```

---

# Kurzfassung

Der wichtigste tägliche TokenMark-Befehlssatz:

```powershell
cd D:\tm

tokenmark build --force --dashboard
tokenmark extract --lang en
tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
tokenmark render --lang en --format html
tokenmark tm-backfill --lang en
tokenmark lint --lang en --fix
tokenmark dashboard --lang en
tokenmark serve --port 8000 --inspect
```

Studio:

```text
http://127.0.0.1:8000/__tokenmark/studio
```

Generated Docs:

```text
http://127.0.0.1:8000/generated/index.html
```

Dashboard:

```text
http://127.0.0.1:8000/i18n-dashboard.html
```
