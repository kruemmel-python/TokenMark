# TokenMark Whitepaper

**Eine Markdown-first Localization, Documentation & Compose Engine für moderne Doc-as-Code-Prozesse**

**Version:** 1.1  
**TokenMark-Stand:** v0.9.4  
**Stand:** April 2026  
**Zielgruppe:** technische Redaktionen, Software-Teams, Entwicklerplattformen, Produktdokumentation, Enterprise Localization, DevRel, Compliance-Dokumentation

---

## Executive Summary

TokenMark ist eine Markdown-first Dokumentations-, Lokalisierungs- und Compose-Engine. Die zentrale Idee ist einfach, aber weitreichend:

> Markdown bleibt die menschlich lesbare Quelle. TokenMark erzeugt daraus stabile semantische Content-Tokens, Übersetzungskataloge, Strukturmodelle, HTML/PDF/Markdown-Ausgaben, QA-Berichte, Translation Memory, KI-Übersetzungen und ein lokales Studio für Review, Kontextbearbeitung und kontrollierte Dokumentationssynthese.

Seit TokenMark v0.8.3 wurde das Projekt deutlich erweitert. TokenMark ist nicht mehr nur eine Engine für Markdown-Lokalisierung, sondern entwickelt sich zu einer kontrollierten **Meaning-to-Documentation Pipeline**:

```text
Unstrukturierte Ideen
    ↓
semantische Ordnung
    ↓
Intent Graph
    ↓
Dokumentationsplan
    ↓
kontrollierte Markdown-Erzeugung
    ↓
Tokenisierung / QA / i18n / HTML / PDF / Studio
```

Klassische Markdown-Workflows behandeln Dokumente als Dateien. TokenMark behandelt Dokumente zusätzlich als **strukturierte, versionierbare, lokalisierbare und synthetisierbare Content-Systeme**. Dadurch wird aus einer einfachen `.md`-Datei ein kontrollierter Dokumentationsprozess mit stabilen IDs, Translation Memory, KI-Übersetzung, Markdown-Strukturprüfung, Glossarunterstützung, Visual QA, Dashboard, lokalem Translation Studio und kontrollierter Dokumentationsgenerierung aus chaotischen Notizen.

TokenMark ist besonders sinnvoll für Teams, die viele technische Dokumente pflegen, mehrere Sprachen unterstützen müssen, KI-gestützte Dokumentation nutzen wollen und dennoch Markdown als einfache, Git-freundliche Quelle behalten möchten.

---

## 1. Ausgangsproblem

Markdown ist hervorragend zum Schreiben technischer Inhalte:

- leichtgewichtig
- Git-freundlich
- lesbar
- kompatibel mit vielen Static Site Generators
- beliebt bei Entwicklerinnen und Entwicklern

Sobald Dokumentation jedoch größer wird, entstehen typische Probleme:

1. **Übersetzungen verlieren Synchronität.**  
   Wenn sich ein Absatz im deutschen Original ändert, ist oft unklar, welche englischen, französischen oder spanischen Übersetzungen betroffen sind.

2. **Dateibasierte Übersetzung skaliert schlecht.**  
   Ganze Markdown-Dateien pro Sprache zu kopieren führt zu Drift, Duplikaten und schwer nachvollziehbaren Änderungen.

3. **KI-Übersetzung zerstört Struktur.**  
   Modelle übersetzen manchmal Links, entfernen Backticks, verändern Platzhalter oder beschädigen MDX/JSX-Syntax.

4. **Review ohne Kontext ist ineffizient.**  
   Übersetzer sehen häufig nur einzelne Strings in JSON, PO oder XLIFF, aber nicht die gerenderte Seite.

5. **Unstrukturierte Ideen bleiben ungenutzt.**  
   Brainstorming-Notizen, Meeting-Mitschriften und lose Bullet Points enthalten oft wertvolles Wissen, sind aber nicht direkt publishable.

6. **Bestehende Tools trennen Publishing, Localization und Wissenssynthese.**  
   Static Site Generators bauen schöne Webseiten, lösen aber meist nicht das Problem stabiler Segment-IDs, Translation Memory, QA, KI-gestützter Lokalisierung und kontrollierter Dokumentationsgenerierung.

TokenMark adressiert genau diese Lücke.

---

## 2. Grundidee von TokenMark

TokenMark ersetzt Markdown nicht. Es erweitert auch nicht primär die Markdown-Syntax. Stattdessen legt TokenMark eine semantische Verarbeitungsschicht um bestehende Markdown-Dateien.

Der Kernprozess:

```text
Markdown-Datei
    ↓
Parser / Segmentierer
    ↓
stabile Content-Tokens
    ↓
Kataloge, IR, Manifest, Translation Memory
    ↓
HTML / PDF / lokalisiertes Markdown / SSG-Export
```

Ab v0.9.x ergänzt TokenMark eine vorgelagerte Compose-Pipeline:

```text
Meeting Notes / Brainstorming / rohe Ideen
    ↓
Intent Extraction
    ↓
Documentation Intent Graph
    ↓
Dokumentationsplan
    ↓
kontrollierte Markdown-Dateien
    ↓
normale TokenMark-Pipeline
```

Die Markdown-Datei bleibt weiterhin die Quelle. Compose erzeugt lediglich neue Markdown-Quellen, die danach wie alle anderen Dokumente behandelt werden.

---

## 3. Was seit v0.8.3 neu ist

TokenMark v0.9.4 erweitert die v0.8.x-Basis um mehrere entscheidende Fähigkeiten:

| Bereich | Erweiterung |
|---|---|
| Compose Engine | unstrukturierte Notizen werden zu Intent Graph, Plan und Markdown |
| Kontrollierte Dokumentationsgenerierung | `tokenmark compose` erzeugt modulare Dokumentation aus Brainstorming |
| Traceability | `compose.intent.json`, `compose.trace.json`, `compose.open_questions.md` |
| Pfadtreues Build-System | `docs/generated/index.md → build/generated/index.html` |
| SiteIndex Fix | Unterseiten verwenden absolute `/site_index.json`-Pfade |
| Translation Memory Fix | vorhandene Katalog-Targets werden zuverlässig in `tm.sqlite` übernommen |
| Studio TM Sync | Studio-Speichern schreibt direkt ins Translation Memory |
| Studio AI LM Studio | einzelnes Segment kann direkt im Studio lokal per LM Studio übersetzt werden |
| LM Studio JSON Robustheit | kaputte JSON-Antworten lokaler Modelle werden toleranter repariert |
| README/Whitepaper-Update | Dokumentation beschreibt v0.9.x-Fähigkeiten konsolidiert |

Der wichtigste architektonische Sprung ist:

> TokenMark verarbeitet nicht mehr nur vorhandene Dokumentation. TokenMark kann aus ungeordneten Ideen kontrollierte Dokumentation erzeugen und diese anschließend lokalisieren, prüfen und veröffentlichen.

---

## 4. Warum TokenMark sinnvoll ist

### 4.1 Markdown bleibt sauber

Viele mächtige Publishing-Systeme machen Markdown selbst komplexer. TokenMark geht bewusst den anderen Weg. Die Autorin schreibt weiterhin normales Markdown. Die Komplexität liegt im Compiler, nicht im Dokument.

Das reduziert kognitive Last und vermeidet Vendor-Lock-in.

### 4.2 Übersetzung wird segmentgenau

Nicht ganze Dateien werden übersetzt, sondern semantische Einheiten:

- Überschrift
- Absatz
- Listenpunkt
- Tabellenzelle
- Bild-Alt-Text
- Link-Text
- Blockquote
- MDX/JSX-Prop
- Callout-Inhalt

Das erlaubt präzise Statusinformationen:

```text
14 translated
2 missing
3 needs_review
1 frozen
```

### 4.3 IDs bleiben stabil

TokenMark nutzt deterministische Token-IDs und Sidecar-Manifeste, um Content-Segmente über Änderungen hinweg wiederzuerkennen.

Das ist entscheidend für:

- Translation Memory
- Review-Status
- CI/CD-Checks
- Cross-Branch-Synchronisation
- Audit Trail
- Studio-Editor
- Visual QA
- In-Context Editing

### 4.4 KI wird kontrollierbar

KI-Übersetzung und KI-Dokumentation sind mächtig, aber riskant. TokenMark setzt KI nicht blind ein, sondern kombiniert sie mit:

- Glossar
- Segmentkontext
- Translation Memory
- Intent Graph
- offenen Fragen
- Markdown-Struktur-Linter
- `needs_review`-Status
- Auto-Fixer
- Visual QA
- lokaler LM-Studio-Unterstützung

Damit entsteht ein kontrollierter Human-in-the-loop-Prozess.

### 4.5 Lokale und private Workflows werden möglich

Durch die LM-Studio-Integration kann TokenMark lokale Sprachmodelle verwenden. Das ist relevant für Teams, die interne Dokumentation, Kundendaten oder regulierte Inhalte nicht an externe APIs senden dürfen.

### 4.6 Chaotische Notizen werden nutzbar

Mit `tokenmark compose` können lose Bullet Points, Meeting Notes oder Brainstorming-Listen in eine erste, modulare technische Dokumentation überführt werden. TokenMark erzeugt dabei nicht nur Markdown, sondern auch:

- Intent Graph
- Trace
- offene Fragen
- modulare Seitenstruktur
- reviewbare Zwischenartefakte

---

## 5. Was TokenMark ist

TokenMark ist eine Kombination aus:

1. **Markdown Compiler**  
   Parse Markdown, segmentiere semantisch, erzeuge IR und HTML/PDF/Markdown.

2. **Localization Engine**  
   Erzeuge Kataloge, übersetze segmentweise, prüfe Status, verwalte Translation Memory.

3. **QA-System**  
   Prüfe Markdown-Struktur, Links, Inline-Code, Platzhalter, JSX-Tags, Text-Expansion und visuelle Risiken.

4. **KI-Orchestrator**  
   Nutze Gemini, OpenAI, DeepL, LM Studio oder Mock/Identity-Provider für Testläufe.

5. **Translation Studio**  
   Lokales Webinterface für Review, Segmentbearbeitung, Kontextvorschau, TM-Vorschläge und Einzel-Segment-Übersetzung per LM Studio.

6. **Compose Engine**  
   Erzeuge aus unstrukturierten Notizen einen Intent Graph, einen Dokumentationsplan und kontrollierte Markdown-Dateien.

7. **Doc-as-Code Tooling**  
   CLI, CI-Reports, Dashboard, Git-Awareness, SSG-Export und Projektkonfiguration.

---

## 6. Was TokenMark nicht ist

TokenMark ist nicht primär:

- ein Ersatz für Markdown
- ein Ersatz für Git
- ein reiner Static Site Generator
- ein reines CAT-Tool
- ein reiner PDF-Renderer
- ein proprietäres Dokumentformat
- ein blinder KI-Autopilot

TokenMark ist stattdessen eine **Integritäts-, Lokalisierungs- und Syntheseschicht** für Markdown-basierte Dokumentationssysteme.

Es kann eigene HTML/PDF-Ausgaben erzeugen, aber auch als Preprocessor für bestehende Systeme wie MkDocs, Docusaurus, Hugo oder andere SSGs dienen.

---

## 7. Architekturübersicht

### 7.1 Komponenten

```text
tokenmark/
  cli.py                 CLI-Einstieg
  compiler.py            Markdown Parsing und Segmentierung
  idgen.py               stabile Token-IDs und Fingerprints
  models.py              Segment-, IR- und Statusmodelle
  catalog.py             JSON-Kataloge und Merge-Logik
  render_html.py         HTML-Rendering mit data-token
  render_markdown.py     lokalisiertes Markdown
  render_pdf.py          PDF via HTML→PDF
  adapters.py            PO/XLIFF Import/Export
  ai_translator.py       Gemini/OpenAI/DeepL/LM Studio Provider
  glossary.py            Glossar-Handling
  qa_linter.py           Strukturprüfung und Auto-Fix
  tm_sqlite.py           SQLite Translation Memory
  analytics.py           Dashboard und Reportdaten
  compose.py             Intent Graph und Markdown-Generierung
  server.py              Dev-Server und Studio
  server_fastapi.py      optionaler WebSocket/FastAPI-Server
  git_ci.py              CI- und Git-Funktionen
  term_extractor.py      Glossar-Kandidaten
  site.py                Navigation, TOC, Suchindex
```

### 7.2 Projektstruktur

Ein typisches TokenMark-Projekt:

```text
project/
  .tokenmark.json
  docs/
    intro.md
    guide.md
    generated/
      index.md
      overview.md
      open_questions.md
  locales/
    de/
      intro.catalog.json
      guide.catalog.json
    en/
      intro.catalog.json
      guide.catalog.json
      generated/
        index.catalog.json
    glossary.json
    tm.sqlite
  themes/
    default.css
  build/
    intro.html
    intro.en.html
    guide.html
    guide.en.html
    generated/
      index.html
      overview.html
    site_index.json
    search_index.en.json
    i18n-dashboard.html
    compose.intent.json
    compose.trace.json
    compose.open_questions.md
```

### 7.3 Konfiguration

Beispiel für `.tokenmark.json`:

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

## 8. Compose Engine

### 8.1 Ziel

Die Compose Engine beantwortet eine neue Frage:

> Wie wird aus chaotischen Meeting-Notizen eine kontrollierte, modulare technische Dokumentation?

Bisherige TokenMark-Pipeline:

```text
Markdown → Tokens → Kataloge → Rendering
```

Neue Compose-Pipeline:

```text
Unstrukturierte Notizen
    ↓
Intent Graph
    ↓
Dokumentationsplan
    ↓
Markdown-Module
    ↓
TokenMark Build / QA / i18n / PDF
```

### 8.2 Beispiel

Input:

```markdown
# Meeting Notes

- TokenMark soll chaotische Bullet Points in Dokumentation verwandeln
- Zielgruppe: Entwickler und technische Autoren
- Pipeline: Notizen -> Intent Graph -> Markdown -> QA -> i18n -> PDF
- Risiko: KI darf keine Fakten erfinden
- Wie markieren wir offene Fragen?
- LM Studio soll lokal nutzbar sein
```

Befehl:

```powershell
tokenmark compose docs\meeting_notes.md `
  --provider heuristic `
  --type technical-guide `
  --audience developers `
  --outdir docs\generated `
  --build
```

Oder mit lokalem LM Studio:

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

Output:

```text
docs/generated/index.md
docs/generated/overview.md
docs/generated/concepts.md
docs/generated/operations.md
docs/generated/risks-and-open-questions.md
docs/generated/open_questions.md

build/compose.intent.json
build/compose.trace.json
build/compose.open_questions.md
```

### 8.3 Intent Graph

Der Intent Graph ist die wichtigste Kontrollschicht. TokenMark generiert nicht direkt blind Markdown, sondern zuerst ein prüfbares semantisches Modell:

```json
{
  "title": "Generated Technical Documentation",
  "document_type": "technical-guide",
  "audience": "developers",
  "confidence": "medium",
  "modules": [
    {
      "title": "Overview",
      "purpose": "Explain the high-level goal",
      "claims": [
        "TokenMark converts unstructured notes into structured documentation"
      ],
      "evidence": [
        "Input notes mention Intent Graph, Markdown, QA, i18n and PDF"
      ]
    }
  ],
  "open_questions": [
    "Wie markieren wir offene Fragen?"
  ]
}
```

Dadurch kann TokenMark:

- offene Fragen sichtbar machen
- Behauptungen und Quellen trennen
- Halluzinationen reduzieren
- Module nachvollziehbar erzeugen
- spätere Reviews erleichtern

### 8.4 Pfadtreues Rendering

Seit v0.9.1 spiegelt TokenMark Unterordner korrekt:

```text
docs/generated/index.md
    ↓
build/generated/index.html
```

Dadurch funktioniert:

```text
http://127.0.0.1:8000/generated/index.html
```

Seit v0.9.2 nutzt die Suche absolute Pfade für `site_index.json`, sodass auch generierte Unterseiten korrekt navigieren.

---

## 9. Tokenisierung und Segmentmodell

TokenMark segmentiert nicht zeichenweise, sondern semantisch. Ein Segment ist eine übersetzbare oder geschützte Content-Einheit.

### 9.1 Segmenttypen

| Segmenttyp | Zweck | Übersetzbar |
|---|---:|---:|
| `heading` | Überschriften | Ja |
| `paragraph` | Absätze | Ja |
| `list_item` | Listenpunkte | Ja |
| `blockquote` | Zitate und Hinweise | Ja |
| `table_cell` | Tabellenzellen | Ja |
| `image_alt` | Alternativtexte | Ja |
| `link_text` | Linkbeschriftungen | Ja |
| `code_block` | Codeblöcke | Nein, frozen |
| `html_block` | Rohes HTML | meist frozen |
| `admonition_title` | Callout-Titel | Ja |
| `admonition_body` | Callout-Inhalt | Ja |
| `jsx_prop` | MDX/JSX-Attribute | Ja |
| `jsx_child` | MDX/JSX-Inhalt | Ja |

### 9.2 Frozen Segments

Nicht alles darf übersetzt werden. Codeblöcke, URLs, HTML-Struktur oder bestimmte JSX-Komponenten können als `frozen` markiert werden.

Beispiel:

```json
{
  "id": "1550e3f9c576",
  "kind": "code_block",
  "source": "print(\"nicht übersetzen\")\n",
  "target": "",
  "frozen": true
}
```

Frozen Segments bleiben im Rendering unverändert.

---

## 10. Stable IDs und Manifest

### 10.1 Warum stabile IDs wichtig sind

Ohne stabile IDs verliert ein System nach jeder kleinen Textänderung die Verbindung zwischen Quelle und Übersetzung.

TokenMark nutzt:

- Segmentart
- Dokumentpfad
- strukturellen Pfad
- normalisierten Text
- Fingerprint
- Sidecar-Manifest

Dadurch kann TokenMark IDs auch dann wiederverwenden, wenn sich ein Absatz leicht verändert.

### 10.2 Beispiel Manifest

```json
{
  "source": "docs/guide.md",
  "nodes": [
    {
      "id": "661bb20a37ee",
      "kind": "paragraph",
      "fingerprint": "sha256:...",
      "text": "Dies ist ein **wichtiger** Absatz."
    }
  ]
}
```

Wenn der Absatz später geändert wird, kann TokenMark erkennen:

```text
gleiche Position + hohe Ähnlichkeit + ähnlicher Fingerprint
→ ID wiederverwenden
→ Status needs_review setzen
```

---

## 11. Kataloge und Übersetzung

### 11.1 JSON-Katalog

Ein Katalog speichert Quelle, Zieltext und Status:

```json
{
  "source": "docs/intro.md",
  "lang": "en",
  "entries": [
    {
      "id": "6490160e32fe",
      "kind": "heading",
      "source": "Einführung",
      "target": "Introduction",
      "status": "translated",
      "frozen": false
    },
    {
      "id": "661bb20a37ee",
      "kind": "paragraph",
      "source": "Dies ist ein **wichtiger** Absatz.",
      "target": "This is an **important** paragraph.",
      "status": "needs_review",
      "frozen": false
    }
  ]
}
```

### 11.2 Statusmodell

| Status | Bedeutung |
|---|---|
| `missing` | noch keine Übersetzung vorhanden |
| `needs_review` | übersetzt, aber noch nicht final freigegeben |
| `translated` | final geprüft |
| `frozen` | nicht übersetzbar |
| `stale` | Quelle hat sich geändert |
| `fixed` | durch Auto-Fixer strukturell korrigiert |

### 11.3 Standardisierte Austauschformate

TokenMark kann Kataloge in etablierte Formate exportieren:

- JSON
- Gettext `.po`
- XLIFF
- lokalisiertes Markdown
- SSG-kompatible Markdown-Dateien

Damit kann TokenMark als Middleware zwischen Markdown-Repositories und professionellen Übersetzungstools dienen.

---

## 12. KI-Übersetzung

TokenMark unterstützt mehrere Provider:

| Provider | Einsatz |
|---|---|
| `mock` | Tests ohne echte Übersetzung |
| `identity` | Zieltext entspricht Quelltext |
| `openai` | Cloud-LLM |
| `gemini` | Google Gemini |
| `deepl` | maschinelle Übersetzung |
| `lmstudio` | lokale OpenAI-kompatible Modelle |

### 12.1 Beispiel: Gemini

```powershell
$env:GEMINI_API_KEY="..."
$env:TOKENMARK_GEMINI_MODEL="gemini-2.5-flash-lite"

tokenmark auto-translate --lang en --provider gemini --batch-size 1
```

### 12.2 Beispiel: LM Studio

```powershell
$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"

tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
```

LM Studio ist besonders nützlich für lokale, private oder experimentelle Übersetzungsworkflows.

### 12.3 Robustheit für lokale Modelle

Lokale Modelle liefern nicht immer perfektes JSON. Seit v0.8.3 repariert TokenMark typische Probleme wie:

```json
["Example translation",]
```

zu:

```json
["Example translation"]
```

Dadurch werden kleinere Formatfehler lokaler Modelle toleriert, ohne dass der ganze Lauf abbricht.

### 12.4 Human-in-the-loop

Automatisch übersetzte Segmente werden nicht blind als final markiert. Typischerweise erhalten sie den Status:

```text
needs_review
```

So bleibt ein menschlicher Review-Prozess Bestandteil der Pipeline.

---

## 13. Glossar und Terminologie

### 13.1 Zweck

Ein Glossar stellt sicher, dass Produktnamen, Fachbegriffe und Unternehmenssprache konsistent bleiben.

Beispiel:

```json
[
  {
    "source": "Arbeitsbereich",
    "target": "workspace",
    "note": "Produktbegriff, immer klein schreiben"
  },
  {
    "source": "Profil",
    "target": "profile",
    "note": "UI-Begriff"
  }
]
```

### 13.2 Verwendung

TokenMark kann relevante Glossar-Einträge in KI-Prompts einfügen. Dadurch wird die Übersetzung konsistenter.

### 13.3 Automatische Glossar-Extraktion

TokenMark kann Kandidaten aus Dokumenten extrahieren:

```powershell
tokenmark extract-terms --min-freq 5 --limit 80
tokenmark extract-terms --min-freq 5 --limit 80 --merge
```

Dabei werden etwa Produktnamen, CamelCase-Begriffe, wiederkehrende Nomen-Phrasen oder technische Begriffe erkannt.

---

## 14. Translation Memory

### 14.1 Ziel

Das Translation Memory verhindert doppelte Arbeit. Wenn ein Satz bereits übersetzt wurde, kann TokenMark ihn wiederverwenden oder als Vorschlag anbieten.

### 14.2 SQLite Backend

TokenMark speichert TM-Einträge in:

```text
locales/tm.sqlite
```

Vorteile:

- schnellere Lookups
- weniger RAM-Verbrauch als große JSON-Dateien
- Revisionierung möglich
- fuzzy Matching
- Audit Trail
- Studio-Vorschläge

### 14.3 Fuzzy Matching

TokenMark unterstützt mehrere Matching-Modi:

```powershell
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode lexical
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode vector
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode hybrid
```

Die lokale Standardvariante nutzt portable Hash-/N-Gram-Vektoren. Optional können neuronale Embeddings verwendet werden.

### 14.4 TM Backfill

Seit v0.9.3 importiert `tm-backfill` vorhandene Katalog-Targets zuverlässig in `tm.sqlite`:

```powershell
tokenmark tm-backfill --lang en
```

Das ist wichtig, wenn Übersetzungen bereits in Katalogen stehen, aber noch nicht im Translation Memory verfügbar sind.

### 14.5 Studio-Sync

Seit v0.9.3 schreibt das Studio beim Speichern eines Targets direkt ins Translation Memory. Außerdem synchronisieren TM-Suggestions vor der Suche automatisch vorhandene Katalogdaten.

### 14.6 Revisionen und Audit Trail

Jede Änderung kann als Revision protokolliert werden:

```text
source_key
lang
target
author
timestamp
```

Damit entstehen Nachvollziehbarkeit und Undo-Möglichkeiten.

---

## 15. Neural Embeddings

### 15.1 Idee

Neural Embeddings sind Zahlenvektoren, die die Bedeutung eines Texts repräsentieren. Statt Zeichenketten zu vergleichen, vergleicht TokenMark semantische Nähe.

Beispiel:

```text
"Speichern Sie das Dokument"
"Sichern Sie die Datei"
```

Ein klassischer Matcher sieht wenig Überschneidung. Ein Embedding-Modell erkennt, dass beide Sätze sinngemäß ähnlich sind.

### 15.2 Nutzung

```powershell
python -m pip install -e ".[vector]"
$env:TOKENMARK_EMBEDDING_BACKEND="sentence-transformers"

tokenmark tm-backfill
tokenmark tm-suggest "Speichern Sie das Dokument" --lang en --mode vector
```

Oder mit OpenAI Embeddings:

```powershell
$env:OPENAI_API_KEY="..."
$env:TOKENMARK_EMBEDDING_BACKEND="openai"

tokenmark tm-backfill
```

### 15.3 Bedeutung für Enterprise

Neural Embeddings erhöhen die Trefferquote von Translation Memory, reduzieren Wiederholungsarbeit und unterstützen semantisch ähnliche Wiederverwendung auch dann, wenn sich Formulierungen unterscheiden.

---

## 16. QA, Linting und Auto-Fix

### 16.1 Strukturprüfung

TokenMark prüft, ob Übersetzungen die technische Struktur erhalten:

- Anzahl der Markdown-Links
- identische URLs
- Inline-Code-Spans
- Platzhalter wie `{{name}}`
- JSX-Tags
- MDX-Props
- Bildreferenzen
- Text-Expansion

Beispielwarnung:

```text
[WARN] docs/demo.md (Token: abc123def456)
       Markdown link count changed.
       Source: "Klicken Sie [hier](https://example.com)."
       Target: "Click here."
```

### 16.2 Auto-Fixer

Mit:

```powershell
tokenmark lint --lang en --fix
```

kann TokenMark bestimmte Strukturfehler konservativ korrigieren:

- fehlende Links wiederherstellen
- URLs aus der Quelle übernehmen
- Platzhalter zurücksetzen
- Inline-Code schützen
- JSX-Tags erhalten

Gefixte Segmente bleiben `needs_review`.

### 16.3 Visual QA

```powershell
tokenmark visual-qa --lang en
```

Visual QA prüft potenzielle Layoutprobleme, insbesondere:

- überlange Texte
- Tabellenrisiken
- mögliche Overflow-Stellen
- Text-Expansion über definierte Schwellenwerte

---

## 17. Rendering und Ausgabeformate

TokenMark kann verschiedene Ausgaben erzeugen.

### 17.1 HTML

```powershell
tokenmark render --lang en --format html
```

HTML enthält `data-token`-Attribute:

```html
<p data-token="661bb20a37ee">
  This is an <strong>important</strong> paragraph.
</p>
```

Diese Attribute ermöglichen:

- Token Inspector
- Studio-Auswahl
- Visual QA
- Debugging
- In-Context Editing

### 17.2 PDF

```powershell
tokenmark render --lang en --format pdf
```

PDF wird über HTML und Print-CSS erzeugt. Dadurch bleiben CSS-Themes, Layouts und später auch Header/Footer kontrollierbar.

### 17.3 Lokalisiertes Markdown

```powershell
tokenmark render --lang en --format markdown
```

Damit kann TokenMark übersetztes Markdown an andere Systeme übergeben.

### 17.4 SSG Export

```powershell
tokenmark export-ssg --lang en --outdir build/ssg/en
```

Dieser Modus ist besonders relevant für Teams, die MkDocs, Docusaurus, Hugo, Nextra oder andere Static Site Generators verwenden.

---

## 18. TokenMark Studio

TokenMark Studio ist eine lokale Weboberfläche für Übersetzung und Review.

Start:

```powershell
tokenmark serve --port 8000 --inspect
```

Aufruf:

```text
http://127.0.0.1:8000/__tokenmark/studio
```

### 18.1 Funktionen

- Side-by-Side-Ansicht
- Quelltext links, Zieltext rechts
- Live-Kontextvorschau
- Klick auf gerenderte Segmente
- Bearbeiten von Targets
- Statusfilter
- Translation-Memory-Vorschläge
- Token-IDs sichtbar
- Dashboard-Verlinkung
- `AI mock` für Testübersetzungen
- `AI LM Studio` für lokale Einzel-Segment-Übersetzung

### 18.2 AI LM Studio im Studio

Seit v0.9.4 gibt es im Studio einen zusätzlichen Button:

```text
AI LM Studio
```

Dieser Button:

1. nimmt das aktuelle Segment,
2. sendet es an den konfigurierten LM-Studio-Server,
3. nutzt optional Nachbar-Kontext,
4. schreibt die Antwort ins Target-Feld,
5. setzt den Status auf `needs_review`,
6. kann beim Speichern direkt ins Translation Memory übernommen werden.

Konfiguration:

```powershell
$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"
```

### 18.3 Unterschied zwischen TM Suggestions und AI LM Studio

```text
TM suggestions
= Suche in bereits vorhandenen Übersetzungen

AI LM Studio
= neue Übersetzung für dieses Segment per lokalem LLM erzeugen
```

Das trennt Wiederverwendung und Neuerzeugung klar.

### 18.4 Warum Studio wichtig ist

Übersetzung ohne Kontext ist fehleranfällig. Studio verbindet Katalogansicht und gerenderte Vorschau. Dadurch sieht eine Übersetzerin, ob ein Segment:

- eine Überschrift ist
- in einer Tabelle steht
- Teil einer Warnbox ist
- ein Button-Label ist
- in einem MDX-Prop steckt
- visuell zu lang wird

---

## 19. Dashboard und Reporting

TokenMark kann ein statisches Lokalisierungsdashboard erzeugen:

```powershell
tokenmark dashboard --lang en
```

Oder direkt beim Build:

```powershell
tokenmark build --force --dashboard
```

Ausgabe:

```text
build/i18n-dashboard.html
```

Das Dashboard zeigt:

- Übersetzungsfortschritt
- Missing Segments
- Needs Review
- QA-Warnungen
- problematische Seiten
- CI-relevante Zusammenfassung

Es eignet sich für GitHub Pages, GitLab Pages oder interne Statusseiten.

---

## 20. CI/CD und Git-Integration

### 20.1 Statusprüfung

```powershell
tokenmark status --lang en
tokenmark check --lang en --strict --lint
```

Ein strenger Check kann Builds fehlschlagen lassen, wenn Segmente fehlen oder QA-Probleme existieren.

### 20.2 CI Report

```powershell
tokenmark ci-report --lang en
```

Erzeugt einen Markdown-Bericht für Pull Requests.

### 20.3 Cross-Branch Sync

```powershell
tokenmark sync-branches --from main --lang en --dry-run
```

Dieser Modus kann Übersetzungen zwischen Branches übernehmen, wenn der Quell-Fingerprint identisch ist. Das ist besonders relevant für versionierte Produktdokumentation.

---

## 21. Plugin-System

TokenMark kann erweitert werden, ohne den Core zu verändern.

Beispielhafte Hooks:

```python
def register(pm):
    pm.register("pre_compile", pre_compile)
    pm.register("post_compile", post_compile)
    pm.register("pre_render", pre_render)
    pm.register("pre_render_segment", pre_render_segment)
    pm.register("post_render", post_render)
```

Mögliche Plugins:

- Mermaid
- PlantUML
- OpenAPI
- interne Makros
- firmenspezifische Callouts
- MDX-Komponenten
- Compliance-Checks
- Custom Exporter

---

## 22. Beispielworkflow: Dokumentation aus Brainstorming erzeugen

### 22.1 Notes erzeugen

```powershell
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

### 22.2 Compose mit Heuristik

```powershell
tokenmark compose docs\meeting_notes.md `
  --provider heuristic `
  --type technical-guide `
  --audience developers `
  --outdir docs\generated `
  --build
```

### 22.3 Compose mit LM Studio

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

### 22.4 Build und Serve

```powershell
tokenmark build --force --dashboard
tokenmark serve --port 8000 --inspect
```

Aufruf:

```text
http://127.0.0.1:8000/generated/index.html
```

---

## 23. Beispielworkflow: Lokalisierung mit LM Studio

### 23.1 Katalog erzeugen

```powershell
tokenmark extract --lang en
```

### 23.2 Auto-Translate mit lokalem Modell

```powershell
$env:TOKENMARK_LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
$env:TOKENMARK_LMSTUDIO_MODEL="google_gemma-4-e4b-it"

tokenmark auto-translate --lang en --provider lmstudio --batch-size 1
```

### 23.3 Rendern

```powershell
tokenmark render --lang en --format html
```

### 23.4 TM befüllen

```powershell
tokenmark tm-backfill --lang en
```

### 23.5 Review im Studio

```powershell
tokenmark serve --port 8000 --inspect
```

Öffnen:

```text
http://127.0.0.1:8000/__tokenmark/studio
```

---

## 24. Enterprise-Nutzen

### 24.1 Skalierbarkeit

TokenMark skaliert von einzelnen Markdown-Dateien bis zu großen Dokumentations-Repositories mit vielen Sprachen.

### 24.2 Governance

Durch Status, Audit Trail, CI Checks, Intent Graphs und Dashboards wird Dokumentation kontrollierbar.

### 24.3 Kostenreduktion

Translation Memory, Fuzzy Matching, Glossar und KI-Vorübersetzung reduzieren manuelle Übersetzungsarbeit.

### 24.4 Qualitätssicherung

Linting, Visual QA und Strukturprüfung verhindern kaputte Ausgaben.

### 24.5 Datenschutz

LM Studio ermöglicht lokale Übersetzung und lokale Dokumentationssynthese ohne Cloud-API.

### 24.6 Kompatibilität

TokenMark kann eigene HTML/PDF-Ausgaben erzeugen oder als Preprocessor für bestehende SSGs arbeiten.

### 24.7 Wissenssynthese

Compose macht aus unstrukturierten Ideen kontrollierte Markdown-Dokumentation. Das reduziert Reibung zwischen Brainstorming, Planung und veröffentlichbarer technischer Dokumentation.

---

## 25. Vergleich zu klassischen Ansätzen

| Ansatz | Vorteil | Problem |
|---|---|---|
| Markdown pro Sprache kopieren | einfach | Drift, hoher Pflegeaufwand |
| SSG i18n | gute Webseiten | oft schwache Segment- und QA-Logik |
| CAT-Tool extern | professionell | wenig Entwickler-Integration |
| KI direkt auf Markdown | schnell | Struktur wird beschädigt |
| KI direkt auf Brainstorming | schnell | oft nicht auditierbar |
| TokenMark | segmentgenau, Markdown-first, QA, KI, TM, Compose | zusätzlicher Build-Schritt |

TokenMark kombiniert Git-nahe Dokumentation mit professionellen Localization-Mechanismen und kontrollierter Wissenssynthese.

---

## 26. Risiken und Grenzen

TokenMark löst viele strukturelle Probleme, ersetzt aber nicht vollständig menschliche Fachprüfung.

Mögliche Grenzen:

- KI-Übersetzungen brauchen Review
- KI-generierte Dokumentation braucht fachliche Prüfung
- komplexes MDX kann Spezialregeln erfordern
- PDF-Layout bleibt ein eigenes Thema
- sehr große Repositories benötigen Caching und klare CI-Konfiguration
- juristische oder sicherheitskritische Inhalte sollten besonders streng geprüft werden
- lokale LLMs können fehlerhafte JSON-Ausgaben erzeugen, auch wenn TokenMark viele Fälle repariert

TokenMark ist daher als kontrollierende Engine gedacht, nicht als blinder Autopilot.

---

## 27. Roadmap-Ideen

Mögliche Weiterentwicklungen:

1. kollaboratives Cloud-Studio
2. Rollen- und Rechteverwaltung
3. Segment-Kommentare
4. Review-Workflows mit Freigabe
5. bessere visuelle Regressionstests
6. native MkDocs- und Docusaurus-Plugins
7. Terminologieprüfung per LLM
8. PDF Book Mode mit Index und Cross References
9. TM-Server für mehrere Repositories
10. Plugin Marketplace
11. Compose Review Mode mit Quellenbindung
12. automatische Diagrammerzeugung aus Intent Graph
13. Multi-Source Compose aus Issues, PRs, Meeting Notes und Code-Kommentaren
14. Team-basierter Studio-Modus mit Rollen
15. branchübergreifender Compose- und Localization-Status

---

## 28. Fazit

TokenMark ist eine Markdown-first Localization, Documentation & Compose Engine. Der wichtigste Unterschied zu klassischen Markdown-Tools liegt darin, dass TokenMark Dokumentation nicht nur rendert, sondern **beherrschbar macht**.

Es beantwortet nicht nur die Frage:

> Wie wird aus Markdown HTML oder PDF?

Sondern auch:

> Welche Segmente wurden geändert?  
> Welche Übersetzungen fehlen?  
> Welche KI-Ergebnisse brauchen Review?  
> Welche Links oder Platzhalter wurden beschädigt?  
> Welche Begriffe müssen konsistent bleiben?  
> Welche Seite ist zu 80 Prozent übersetzt?  
> Welche Absätze können aus dem Translation Memory übernommen werden?  
> Wie kann ich lokal mit einem privaten Modell übersetzen?  
> Wie kann ich aus chaotischen Meeting-Notizen strukturierte Dokumentation erzeugen?  
> Welche offenen Fragen muss ein Mensch vor Veröffentlichung klären?

Damit wird TokenMark zu einer produktionsnahen Grundlage für moderne Doc-as-Code-, Localization-, Compose- und Enterprise-Dokumentationsprozesse.

---

# Glossar

## AI LM Studio

Studio-Funktion ab TokenMark v0.9.4, die ein einzelnes Segment direkt über ein lokales LM-Studio-Modell übersetzt.

## AST

Abstract Syntax Tree. Eine baumartige Struktur, die aus Markdown oder anderem Quelltext geparst wird.

## Auto-Fixer

Eine Komponente, die bestimmte technische Fehler in Übersetzungen automatisch korrigiert, etwa fehlende Platzhalter oder beschädigte Links.

## Catalog

Ein Übersetzungskatalog. Enthält Segment-IDs, Quelltexte, Zieltexte, Status und Metadaten.

## CI/CD

Continuous Integration und Continuous Delivery. Automatisierte Prüfung und Veröffentlichung in Softwareprojekten.

## Compose

TokenMark-Funktion zur Umwandlung unstrukturierter Notizen in Intent Graph, Dokumentationsplan und kontrollierte Markdown-Dateien.

## Doc-as-Code

Arbeitsweise, bei der Dokumentation wie Quellcode behandelt wird: versioniert, reviewed, getestet und automatisch gebaut.

## Fingerprint

Ein Hash oder anderer stabiler Wert, der den Inhalt eines Segments beschreibt und Änderungen erkennbar macht.

## Frozen Segment

Ein Segment, das nicht übersetzt werden darf, zum Beispiel Code oder technische Struktur.

## Glossary

Terminologiedatenbank mit verbindlichen Übersetzungen für Fachbegriffe und Produktnamen.

## Intent Graph

Semantisches Zwischenmodell, das aus unstrukturierten Notizen extrahiert wird und Module, Claims, Risiken, Quellenbezüge und offene Fragen beschreibt.

## IR

Intermediate Representation. Ein internes Strukturmodell des Dokuments zwischen Markdown-Quelle und Ausgabeformat.

## LM Studio

Lokale Anwendung zum Ausführen von Sprachmodellen mit OpenAI-kompatibler API. TokenMark kann darüber lokal übersetzen und Compose-Ergebnisse erzeugen.

## Markdown-first

Prinzip, bei dem Markdown die primäre Quelle bleibt und nicht durch ein proprietäres Format ersetzt wird.

## MDX

Markdown mit JSX-Komponenten. Häufig in modernen Dokumentationsframeworks wie Docusaurus oder Nextra.

## Segment

Eine semantische Content-Einheit, etwa ein Absatz, eine Überschrift oder eine Tabellenzelle.

## Sidecar Manifest

Eine zusätzliche Datei neben der Quelle, die stabile IDs und Fingerprints speichert.

## Stale

Status einer Übersetzung, deren Quelltext sich geändert hat und die deshalb überprüft werden muss.

## Token

Eine stabile, identifizierbare Content-Einheit. In TokenMark ist ein Token die Brücke zwischen Markdown-Quelle, Katalog, Translation Memory und Rendering.

## Translation Memory

Datenbank bereits übersetzter Segmente, die spätere Übersetzungen beschleunigt und vereinheitlicht.

## Visual QA

Visuelle Qualitätssicherung, die potenzielle Layoutprobleme durch Übersetzungen erkennt.

## XLIFF

XML Localization Interchange File Format. Standardformat für professionelle Übersetzungstools.

---

# Kurzpositionierung

**TokenMark ist kein neues Markdown. TokenMark ist die Kontrollschicht, die Markdown enterprise-fähig macht — und seit v0.9.x zusätzlich die Compose-Schicht, die unstrukturierte Ideen in kontrollierte Dokumentation verwandelt.**
