"""TokenMark Compose: unstructured notes -> intent graph -> controlled Markdown docs.

This module intentionally does not let an LLM write arbitrary final documentation directly.
It first creates an auditable intent graph, then renders Markdown from deterministic templates.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


DEFAULT_MODULES = [
    ("Overview", ["idee", "ziel", "warum", "purpose", "overview", "problem", "mehrwert", "vision"]),
    ("Concepts", ["konzept", "begriff", "definition", "modell", "semantik", "token", "intent", "graph"]),
    ("Architecture", ["architektur", "pipeline", "system", "modul", "komponente", "server", "api", "datenbank", "sqlite"]),
    ("Workflow", ["workflow", "ablauf", "prozess", "schritt", "command", "befehl", "powershell", "bash", "cli"]),
    ("Implementation", ["implementierung", "code", "python", "klasse", "funktion", "parser", "renderer", "provider"]),
    ("Quality Assurance", ["qa", "test", "lint", "prüfung", "validierung", "review", "status", "ci", "dashboard"]),
    ("Operations", ["deployment", "betrieb", "installation", "config", "umgebung", "key", "modell", "lm studio", "gemini"]),
    ("Risks and Open Questions", ["risiko", "frage", "unklar", "todo", "offen", "problem", "limitation", "fehler"]),
]


@dataclass
class ComposeItem:
    index: int
    text: str
    kind: str = "note"
    confidence: float = 0.6


@dataclass
class ComposeModule:
    title: str
    slug: str
    purpose: str
    claims: list[str]
    evidence: list[str]
    steps: list[str]
    risks: list[str]
    open_questions: list[str]
    source_items: list[int]


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "section"


def _strip_json_fences(content: str) -> str:
    content = (content or "").strip()
    if content.startswith("```"):
        content = content.strip("`").strip()
        if content.lower().startswith("json"):
            content = content[4:].strip()
    return content


def _repair_jsonish(content: str) -> str:
    content = _strip_json_fences(content)
    content = re.sub(r",\s*([\]\}])", r"\1", content)
    return content


def parse_jsonish(content: str) -> Any:
    repaired = _repair_jsonish(content)
    try:
        return json.loads(repaired)
    except Exception:
        pass
    starts = [i for i in (repaired.find("{"), repaired.find("[")) if i != -1]
    if not starts:
        raise ValueError("no JSON object or array found")
    start = min(starts)
    end = max(repaired.rfind("}"), repaired.rfind("]"))
    if end <= start:
        raise ValueError("no complete JSON object or array found")
    return json.loads(_repair_jsonish(repaired[start:end + 1]))


def extract_items(raw: str) -> list[ComposeItem]:
    """Extract usable note units from chaotic Markdown/plain text."""
    items: list[ComposeItem] = []
    index = 1
    in_code = False
    para: list[str] = []

    def flush_para() -> None:
        nonlocal index, para
        text = " ".join(x.strip() for x in para if x.strip()).strip()
        para = []
        if text:
            items.append(ComposeItem(index=index, text=text, kind="paragraph", confidence=0.65))
            index += 1

    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_para()
            in_code = not in_code
            continue
        if in_code:
            continue
        if not stripped:
            flush_para()
            continue
        # Headings are strong semantic hints.
        if stripped.startswith("#"):
            flush_para()
            text = stripped.lstrip("#").strip()
            if text:
                items.append(ComposeItem(index=index, text=text, kind="heading", confidence=0.8))
                index += 1
            continue
        # Bullets, checkboxes, numbered points.
        m = re.match(r"^(?:[-*+]\s+|\d+[\.)]\s+|\[[ xX]\]\s+)(.+)$", stripped)
        if m:
            flush_para()
            text = m.group(1).strip()
            if text:
                items.append(ComposeItem(index=index, text=text, kind="bullet", confidence=0.72))
                index += 1
            continue
        # One-line colon statements are often useful as items.
        if len(stripped) < 160 and (":" in stripped or "?" in stripped):
            flush_para()
            items.append(ComposeItem(index=index, text=stripped, kind="statement", confidence=0.7))
            index += 1
            continue
        para.append(stripped)
    flush_para()
    return items


def _score_item_for_module(text: str, keywords: list[str]) -> int:
    t = text.lower()
    return sum(1 for kw in keywords if kw in t)


def _looks_like_question(text: str) -> bool:
    t = text.strip().lower()
    return "?" in t or t.startswith(("wie ", "was ", "warum ", "wann ", "welche ", "wer ", "where ", "how ", "what ", "why "))


def _looks_like_risk(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ["risiko", "problem", "fehler", "kaputt", "limitation", "unsicher", "unklar", "danger", "risk", "broken", "missing"])


def _looks_like_step(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ["dann", "danach", "zuerst", "build", "extract", "render", "serve", "install", "pip", "tokenmark ", "schritt", "workflow"])


def build_heuristic_intent_graph(raw: str, *, doc_type: str, audience: str, title: str | None = None) -> dict[str, Any]:
    items = extract_items(raw)
    buckets: dict[str, list[ComposeItem]] = {name: [] for name, _ in DEFAULT_MODULES}

    for item in items:
        best_name = "Overview"
        best_score = -1
        for name, keywords in DEFAULT_MODULES:
            score = _score_item_for_module(item.text, keywords)
            if score > best_score:
                best_name, best_score = name, score
        if best_score <= 0:
            # Route by shape when no keyword matched.
            if _looks_like_question(item.text) or _looks_like_risk(item.text):
                best_name = "Risks and Open Questions"
            elif _looks_like_step(item.text):
                best_name = "Workflow"
            elif item.kind == "heading":
                best_name = "Concepts"
            else:
                best_name = "Overview" if len(buckets["Overview"]) < 6 else "Implementation"
        buckets[best_name].append(item)

    modules: list[ComposeModule] = []
    for name, _ in DEFAULT_MODULES:
        group = buckets.get(name) or []
        if not group and name not in ("Overview", "Risks and Open Questions"):
            continue

        claims: list[str] = []
        evidence: list[str] = []
        steps: list[str] = []
        risks: list[str] = []
        questions: list[str] = []

        for it in group:
            text = it.text.strip()
            if _looks_like_question(text):
                questions.append(text)
            elif _looks_like_risk(text):
                risks.append(text)
            elif _looks_like_step(text):
                steps.append(text)
            else:
                claims.append(text)
            evidence.append(f"Note #{it.index}: {text}")

        # Keep documentation useful even if notes were sparse.
        if name == "Risks and Open Questions":
            questions.extend([x.text for x in items if _looks_like_question(x.text) and x.text not in questions])
            risks.extend([x.text for x in items if _looks_like_risk(x.text) and x.text not in risks])

        purpose = {
            "Overview": "Explain the purpose, scope, and value of the material.",
            "Concepts": "Define the core concepts and vocabulary before implementation details.",
            "Architecture": "Describe the system structure, data flow, and component boundaries.",
            "Workflow": "Describe the operational flow as reproducible steps.",
            "Implementation": "Turn implementation notes into concrete technical guidance.",
            "Quality Assurance": "Capture validation, review, automation, and CI expectations.",
            "Operations": "Describe setup, configuration, runtime, and operational concerns.",
            "Risks and Open Questions": "Make uncertainty explicit instead of inventing missing facts.",
        }.get(name, "Organize related information.")
        modules.append(ComposeModule(
            title=name,
            slug=slugify(name),
            purpose=purpose,
            claims=claims[:12],
            evidence=evidence[:18],
            steps=steps[:12],
            risks=risks[:12],
            open_questions=questions[:12],
            source_items=[it.index for it in group],
        ))

    graph = {
        "schema": "tokenmark.compose.intent.v1",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "title": title or infer_title(raw, items),
        "document_type": doc_type,
        "audience": audience,
        "confidence": "medium",
        "source_item_count": len(items),
        "items": [asdict(i) for i in items],
        "modules": [asdict(m) for m in modules],
        "global_open_questions": infer_global_questions(items, modules),
    }
    return graph


def infer_title(raw: str, items: list[ComposeItem]) -> str:
    for line in raw.splitlines():
        if line.strip().startswith("#"):
            return line.strip().lstrip("#").strip()
    for item in items:
        if item.kind in ("heading", "statement") and 6 <= len(item.text) <= 90:
            return item.text.rstrip(":")
    return "Generated Technical Documentation"


def infer_global_questions(items: list[ComposeItem], modules: list[ComposeModule]) -> list[str]:
    found = []
    for item in items:
        if _looks_like_question(item.text):
            found.append(item.text)
    if not found:
        found = [
            "Which statements require human confirmation before publication?",
            "Which target audience is authoritative for wording and depth?",
            "Which examples, commands, or screenshots should be treated as canonical?",
        ]
    return found[:20]


def _llm_intent_prompt(raw: str, *, doc_type: str, audience: str, title: str | None) -> str:
    return (
        "You are TokenMark Compose. Convert chaotic meeting notes into an auditable documentation intent graph. "
        "Do not write final prose freely. Extract only what is supported by the notes. "
        "Represent uncertainty as open_questions. Return JSON only with this shape:\n"
        "{"
        '"title": string, "document_type": string, "audience": string, "confidence": "low|medium|high", '
        '"modules": [{"title": string, "slug": string, "purpose": string, "claims": [string], '
        '"evidence": [string], "steps": [string], "risks": [string], "open_questions": [string], "source_items": [number]}], '
        '"global_open_questions": [string]'
        "}\n\n"
        f"Requested document_type: {doc_type}\nAudience: {audience}\nTitle hint: {title or ''}\n\n"
        "Notes:\n" + raw[:45000]
    )


def build_llm_intent_graph(raw: str, *, provider: str, doc_type: str, audience: str, title: str | None = None) -> dict[str, Any]:
    prompt = _llm_intent_prompt(raw, doc_type=doc_type, audience=audience, title=title)
    content = ""

    if provider == "lmstudio":
        base = os.environ.get("TOKENMARK_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
        model = os.environ.get("TOKENMARK_LMSTUDIO_MODEL", "local-model")
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "Return JSON only. No markdown fences."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "stream": False,
        }, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(base + "/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": "Bearer lm-studio"})
        with urllib.request.urlopen(req, timeout=int(os.environ.get("TOKENMARK_LMSTUDIO_TIMEOUT", "300"))) as r:
            payload = json.loads(r.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]

    elif provider == "openai":
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise SystemExit("OPENAI_API_KEY is not set.")
        model = os.environ.get("TOKENMARK_OPENAI_MODEL", "gpt-4o-mini")
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "Return JSON only. No markdown fences."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            payload = json.loads(r.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]

    elif provider == "gemini":
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise SystemExit("GEMINI_API_KEY is not set.")
        try:
            from google import genai
            from google.genai import types
        except Exception as exc:
            raise SystemExit("Gemini compose requires google-genai. Install: python -m pip install google-genai") from exc
        model = os.environ.get("TOKENMARK_GEMINI_MODEL", "gemini-2.5-flash-lite")
        client = genai.Client(api_key=key)
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json"),
            )
        except TypeError:
            response = client.models.generate_content(model=model, contents=prompt)
        content = (getattr(response, "text", None) or "").strip()
    else:
        raise SystemExit(f"Unsupported compose provider: {provider}")

    payload = parse_jsonish(content)
    graph = normalize_intent_graph(payload, raw, doc_type=doc_type, audience=audience, title=title)
    graph["provider"] = provider
    return graph


def normalize_intent_graph(payload: dict[str, Any], raw: str, *, doc_type: str, audience: str, title: str | None) -> dict[str, Any]:
    fallback = build_heuristic_intent_graph(raw, doc_type=doc_type, audience=audience, title=title)
    if not isinstance(payload, dict):
        return fallback
    modules = payload.get("modules") if isinstance(payload.get("modules"), list) else []
    clean_modules = []
    for i, m in enumerate(modules):
        if not isinstance(m, dict):
            continue
        mt = str(m.get("title") or f"Section {i+1}")
        clean_modules.append({
            "title": mt,
            "slug": slugify(str(m.get("slug") or mt)),
            "purpose": str(m.get("purpose") or "Organize related information."),
            "claims": [str(x) for x in (m.get("claims") or []) if str(x).strip()][:16],
            "evidence": [str(x) for x in (m.get("evidence") or []) if str(x).strip()][:20],
            "steps": [str(x) for x in (m.get("steps") or []) if str(x).strip()][:16],
            "risks": [str(x) for x in (m.get("risks") or []) if str(x).strip()][:16],
            "open_questions": [str(x) for x in (m.get("open_questions") or []) if str(x).strip()][:16],
            "source_items": [int(x) for x in (m.get("source_items") or []) if str(x).isdigit()][:50],
        })
    if not clean_modules:
        return fallback
    return {
        "schema": "tokenmark.compose.intent.v1",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "title": str(payload.get("title") or title or fallback["title"]),
        "document_type": str(payload.get("document_type") or doc_type),
        "audience": str(payload.get("audience") or audience),
        "confidence": str(payload.get("confidence") or "medium"),
        "source_item_count": len(extract_items(raw)),
        "items": [asdict(i) for i in extract_items(raw)],
        "modules": clean_modules,
        "global_open_questions": [str(x) for x in (payload.get("global_open_questions") or fallback["global_open_questions"])][:20],
    }


def build_intent_graph(raw: str, *, provider: str = "heuristic", doc_type: str = "technical-guide", audience: str = "developers", title: str | None = None) -> dict[str, Any]:
    if provider in ("heuristic", "offline", "none"):
        return build_heuristic_intent_graph(raw, doc_type=doc_type, audience=audience, title=title)
    try:
        return build_llm_intent_graph(raw, provider=provider, doc_type=doc_type, audience=audience, title=title)
    except Exception as exc:
        graph = build_heuristic_intent_graph(raw, doc_type=doc_type, audience=audience, title=title)
        graph["provider_error"] = str(exc)
        graph["provider"] = provider
        graph["confidence"] = "medium"
        return graph


def render_markdown_module(graph: dict[str, Any], module: dict[str, Any], *, include_trace: bool = True) -> str:
    title = module.get("title", "Section")
    lines = [
        "---",
        f'title: "{title}"',
        f'document_type: "{graph.get("document_type", "technical-guide")}"',
        f'audience: "{graph.get("audience", "developers")}"',
        "generated_by: tokenmark-compose",
        "---",
        "",
        f"# {title}",
        "",
        module.get("purpose") or "This section organizes extracted meeting knowledge.",
        "",
    ]

    if module.get("claims"):
        lines += ["## Key Points", ""]
        for claim in module["claims"]:
            lines.append(f"- {claim}")
        lines.append("")

    if module.get("steps"):
        lines += ["## Procedure", ""]
        for idx, step in enumerate(module["steps"], 1):
            lines.append(f"{idx}. {step}")
        lines.append("")

    if module.get("risks"):
        lines += ["## Risks and Constraints", ""]
        for risk in module["risks"]:
            lines.append(f"- {risk}")
        lines.append("")

    if module.get("open_questions"):
        lines += ["## Open Questions", ""]
        for q in module["open_questions"]:
            lines.append(f"- {q}")
        lines.append("")

    if include_trace and module.get("evidence"):
        lines += ["## Traceability", "", "The following source notes support this section:", ""]
        for ev in module["evidence"]:
            lines.append(f"- {ev}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_index(graph: dict[str, Any]) -> str:
    lines = [
        "---",
        f'title: "{graph.get("title", "Generated Technical Documentation")}"',
        f'document_type: "{graph.get("document_type", "technical-guide")}"',
        f'audience: "{graph.get("audience", "developers")}"',
        "generated_by: tokenmark-compose",
        "---",
        "",
        f"# {graph.get('title', 'Generated Technical Documentation')}",
        "",
        "> This documentation was generated from unstructured notes through TokenMark Compose.",
        "> It should be reviewed before publication.",
        "",
        "## Modules",
        "",
    ]
    for m in graph.get("modules", []):
        lines.append(f"- [{m.get('title')}](./{m.get('slug')}.md)")
    lines.append("")
    if graph.get("global_open_questions"):
        lines += ["## Global Open Questions", ""]
        for q in graph["global_open_questions"]:
            lines.append(f"- {q}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_open_questions(graph: dict[str, Any]) -> str:
    lines = ["# Open Questions", ""]
    seen = set()
    for q in graph.get("global_open_questions", []):
        if q not in seen:
            lines.append(f"- {q}")
            seen.add(q)
    for m in graph.get("modules", []):
        for q in m.get("open_questions", []):
            if q not in seen:
                lines.append(f"- **{m.get('title')}**: {q}")
                seen.add(q)
    if len(lines) == 2:
        lines.append("- No explicit open questions were detected. Human review is still recommended.")
    return "\n".join(lines).rstrip() + "\n"


def write_compose_outputs(graph: dict[str, Any], outdir: Path, *, single: bool = False, include_trace: bool = True) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    generated: list[str] = []

    if single:
        parts = [render_index(graph)]
        for m in graph.get("modules", []):
            parts.append(render_markdown_module(graph, m, include_trace=include_trace))
        p = outdir / "generated.md"
        p.write_text("\n\n".join(parts), encoding="utf-8")
        generated.append(str(p))
    else:
        index = outdir / "index.md"
        index.write_text(render_index(graph), encoding="utf-8")
        generated.append(str(index))
        for m in graph.get("modules", []):
            p = outdir / f"{m.get('slug')}.md"
            p.write_text(render_markdown_module(graph, m, include_trace=include_trace), encoding="utf-8")
            generated.append(str(p))

    oq = outdir / "open_questions.md"
    oq.write_text(render_open_questions(graph), encoding="utf-8")
    generated.append(str(oq))
    return {"generated": generated}


def compose_file(input_path: Path, outdir: Path, *, provider: str = "heuristic", doc_type: str = "technical-guide", audience: str = "developers", title: str | None = None, single: bool = False, include_trace: bool = True, build_dir: Path | None = None) -> dict[str, Any]:
    raw = input_path.read_text(encoding="utf-8")
    graph = build_intent_graph(raw, provider=provider, doc_type=doc_type, audience=audience, title=title)

    result = write_compose_outputs(graph, outdir, single=single, include_trace=include_trace)

    bd = build_dir or (outdir.parent / "build")
    bd.mkdir(parents=True, exist_ok=True)
    intent_path = bd / "compose.intent.json"
    trace_path = bd / "compose.trace.json"
    oq_path = bd / "compose.open_questions.md"

    intent_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    trace = {
        "input": str(input_path),
        "outdir": str(outdir),
        "provider": provider,
        "generated": result["generated"],
        "source_item_count": graph.get("source_item_count"),
        "module_count": len(graph.get("modules", [])),
        "confidence": graph.get("confidence"),
        "provider_error": graph.get("provider_error"),
    }
    trace_path.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
    oq_path.write_text(render_open_questions(graph), encoding="utf-8")
    result.update({"intent": str(intent_path), "trace": str(trace_path), "open_questions": str(oq_path), "graph": graph})
    return result
