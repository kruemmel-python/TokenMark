import re
from dataclasses import dataclass
from markdown_it import MarkdownIt

LINK_RE=re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
IMG_RE=re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
CODE_RE=re.compile(r"`([^`]+)`")
PLACEHOLDER_RE=re.compile(r"(\{\{[^}]+\}\}|\{[A-Za-z_][A-Za-z0-9_]*\}|%[sd]|:[A-Za-z_][A-Za-z0-9_]*|<[^>\s]+>)")

@dataclass
class LintIssue:
    level: str
    segment_id: str
    kind: str
    message: str
    source: str
    target: str

def _links(text):
    return [m.group(2).strip() for m in LINK_RE.finditer(text or "")]

def _images(text):
    return [m.group(2).strip() for m in IMG_RE.finditer(text or "")]

def _codes(text):
    return [m.group(1) for m in CODE_RE.finditer(text or "")]

def _placeholders(text):
    return sorted(set(m.group(1) for m in PLACEHOLDER_RE.finditer(text or "")))

def lint_segment(segment, target=None):
    src=segment.get("source","") if isinstance(segment, dict) else segment.source
    tgt=target if target is not None else (segment.get("target","") if isinstance(segment, dict) else segment.target)
    sid=segment.get("id","") if isinstance(segment, dict) else segment.id
    kind=segment.get("kind","") if isinstance(segment, dict) else segment.kind
    if not tgt:
        return []
    issues=[]
    def add(msg): issues.append(LintIssue("warn", sid, kind, msg, src, tgt))
    src_links,tgt_links=_links(src),_links(tgt)
    if len(src_links)!=len(tgt_links):
        add(f"Markdown link count changed: source={len(src_links)} target={len(tgt_links)}")
    elif src_links!=tgt_links:
        add("Markdown link URLs changed.")
    src_imgs,tgt_imgs=_images(src),_images(tgt)
    if len(src_imgs)!=len(tgt_imgs):
        add(f"Image count changed: source={len(src_imgs)} target={len(tgt_imgs)}")
    elif src_imgs!=tgt_imgs:
        add("Image URLs changed.")
    if len(_codes(src))!=len(_codes(tgt)):
        add(f"Inline code span count changed: source={len(_codes(src))} target={len(_codes(tgt))}")
    if len(src) > 20 and len(tgt) > len(src) * 1.5:
        add(f"Text expansion > 50%: source_len={len(src)} target_len={len(tgt)}. UI layout might break.")
    if len(src) > 20 and len(tgt) < len(src) * 0.45:
        add(f"Text contraction > 55%: source_len={len(src)} target_len={len(tgt)}. Meaning may be missing.")
    sp,tp=_placeholders(src),_placeholders(tgt)
    if sp!=tp:
        add(f"Placeholder mismatch: source={sp} target={tp}")
    sj,tj=_jsx_tags(src),_jsx_tags(tgt)
    if sj!=tj:
        add(f"JSX/MDX tag mismatch: source={sj} target={tj}")
    # Parser smoke test for targets with markdown markers.
    if any(ch in tgt for ch in "[]`()<>"):
        try:
            MarkdownIt("commonmark", {"html": True}).renderInline(tgt)
        except Exception as e:
            add(f"Target Markdown parse failed: {e}")
    return issues

def lint_catalog(catalog):
    issues=[]
    for e in catalog.get("entries",[]):
        if e.get("frozen") or not e.get("target"):
            continue
        issues.extend(lint_segment(e))
    return issues

def format_issue(issue):
    return (f"[{issue.level.upper()}] token={issue.segment_id} kind={issue.kind}\n"
            f"       {issue.message}\n"
            f"       Source: {issue.source}\n"
            f"       Target: {issue.target}")

JSX_TAG_RE=re.compile(r"</?([A-Z][A-Za-z0-9_.]*)\b[^>]*>")

def _jsx_tags(text):
    return [m.group(0) for m in JSX_TAG_RE.finditer(text or "")]

def ai_lint_catalog(catalog, styleguide_path=None, glossary_path=None, provider="openai", model=None):
    """Semantic QA. Uses OpenAI when configured; otherwise applies deterministic style/glossary heuristics.

    Returns LintIssue objects with level='ai-warn'. This is intentionally a linter,
    not an auto-fixer: it flags tone, glossary and semantic risks for human review.
    """
    import os, json, urllib.request
    entries=[e for e in catalog.get("entries",[]) if not e.get("frozen") and e.get("target")]
    style=""
    if styleguide_path:
        try:
            from pathlib import Path
            style=Path(styleguide_path).read_text(encoding="utf-8")
        except Exception:
            style=""
    if provider=="openai" and os.environ.get("OPENAI_API_KEY") and entries:
        model=model or os.environ.get("TOKENMARK_OPENAI_MODEL","gpt-4o-mini")
        payload=[{"id":e.get("id"),"kind":e.get("kind"),"source":e.get("source"),"target":e.get("target")} for e in entries]
        prompt=("Review translations for semantic equivalence, tone of voice, glossary compliance and Markdown safety. "
                "Return JSON array: [{id,level,message,suggestion}]. Do not rewrite every segment; only report problems.\n"
                f"Styleguide:\n{style[:12000]}")
        body=json.dumps({"model":model,"messages":[{"role":"system","content":prompt},{"role":"user","content":json.dumps(payload,ensure_ascii=False)}],"temperature":0}).encode()
        req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,headers={"Authorization":"Bearer "+os.environ["OPENAI_API_KEY"],"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            content=json.loads(r.read().decode())["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content=content.strip("`")
            if content.lower().startswith("json"): content=content[4:].strip()
        raw=json.loads(content)
        byid={e.get("id"):e for e in entries}
        out=[]
        for item in raw:
            e=byid.get(item.get("id"))
            if not e: continue
            out.append(LintIssue(item.get("level","ai-warn"), e.get("id",""), e.get("kind",""), item.get("message") or item.get("rule_violated","AI semantic warning"), e.get("source",""), e.get("target","")))
        return out

    # Offline fallback: useful in CI without API keys.
    issues=[]
    formal_required=("Sie" in style or "formal" in style.lower() or "förmlich" in style.lower())
    informal_forbidden=re.compile(r"\b(du|dir|dein|dich|euch|ihr)\b", re.I)
    for e in entries:
        tgt=e.get("target","")
        if formal_required and informal_forbidden.search(tgt):
            issues.append(LintIssue("ai-warn", e.get("id",""), e.get("kind",""), "Possible informal tone although styleguide appears to require formal address.", e.get("source",""), tgt))
        # Product casing sanity check.
        for product in re.findall(r"\b[A-Z][A-Za-z0-9]+(?:[A-Z][A-Za-z0-9]+)+\b", e.get("source","")):
            if product not in tgt:
                issues.append(LintIssue("ai-warn", e.get("id",""), e.get("kind",""), f"Product/proper-name casing may be lost: {product}", e.get("source",""), tgt))
    return issues


def auto_fix_target(source: str, target: str) -> tuple[str, list[str]]:
    """Deterministic Markdown safety fixer.

    It does not attempt semantic translation. It preserves/injects structural
    markers that translation engines commonly drop: URLs, inline code spans,
    placeholders and JSX tags. Returns (fixed_target, notes).
    """
    fixed = target or ""
    notes = []

    # Preserve markdown links: if target has same number links but changed URLs, put source URLs back.
    src_links = list(LINK_RE.finditer(source or ""))
    tgt_links = list(LINK_RE.finditer(fixed or ""))
    if src_links and len(src_links) == len(tgt_links):
        parts=[]; last=0
        for idx, m in enumerate(tgt_links):
            parts.append(fixed[last:m.start()])
            label=m.group(1)
            url=src_links[idx].group(2).strip()
            parts.append(f"[{label}]({url})")
            last=m.end()
        parts.append(fixed[last:])
        new="".join(parts)
        if new != fixed:
            fixed=new; notes.append("restored markdown link URLs")

    # If all links vanished, append compact source references so HTML will not break.
    if src_links and not list(LINK_RE.finditer(fixed or "")):
        fixed += " " + " ".join(f"[{m.group(1)}]({m.group(2).strip()})" for m in src_links)
        notes.append("reinserted missing markdown links")

    # Preserve image URLs similarly.
    src_imgs = list(IMG_RE.finditer(source or ""))
    tgt_imgs = list(IMG_RE.finditer(fixed or ""))
    if src_imgs and not tgt_imgs:
        fixed += "\n\n" + "\n".join(f"![{m.group(1)}]({m.group(2).strip()})" for m in src_imgs)
        notes.append("reinserted missing images")

    # Add missing inline code spans.
    src_codes = _codes(source)
    tgt_codes = _codes(fixed)
    for c in src_codes:
        if c not in tgt_codes and f"`{c}`" not in fixed:
            fixed += f" `{c}`"
            notes.append(f"reinserted inline code `{c}`")

    # Add missing placeholders.
    sp = _placeholders(source)
    tp = _placeholders(fixed)
    for ph in sp:
        if ph not in tp:
            fixed += f" {ph}"
            notes.append(f"reinserted placeholder {ph}")

    # Add missing JSX/MDX tags as a protected suffix. This is conservative:
    # it ensures the token is not silently lost and marks for human review.
    sj=_jsx_tags(source)
    tj=_jsx_tags(fixed)
    for tag in sj:
        if tag not in tj:
            fixed += f" {tag}"
            notes.append(f"reinserted JSX tag {tag}")

    return fixed.strip(), notes

def fix_catalog(catalog: dict) -> tuple[dict, list[dict]]:
    """Apply deterministic structure fixes to a catalog in-place-ish."""
    fixed=[]
    for e in catalog.get("entries",[]):
        if e.get("frozen") or not e.get("target"):
            continue
        before=e.get("target","")
        after, notes = auto_fix_target(e.get("source",""), before)
        if notes and after != before:
            e["target"]=after
            e["status"]="needs_review"
            meta=e.setdefault("meta",{})
            meta["auto_fixed"]=True
            meta["auto_fix_notes"]=notes
            fixed.append({"id":e.get("id"),"notes":notes})
    return catalog, fixed
