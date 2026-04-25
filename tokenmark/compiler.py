import re
from pathlib import Path
from markdown_it import MarkdownIt
from .models import Segment, DocumentIR
from .idgen import deterministic_id, fingerprint
from .catalog import load_manifest, reuse_ids_from_manifest

FRONTMATTER_RE=re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", re.S)
JSX_PROP_RE=re.compile(r"""\b(title|label|description|alt|aria-label|placeholder)=["\']([^"\']+)["\']""")
JSX_CHILD_RE=re.compile(r"<([A-Z][A-Za-z0-9_.]*)\b[^>]*>(.*?)</\1>", re.S)
ADMONITION_RE=re.compile(r"^:::\s*([a-zA-Z0-9_-]+)(?:\s+(.*))?\n(.*?)\n:::\s*$", re.S|re.M)

def split_frontmatter(text):
    m=FRONTMATTER_RE.match(text)
    return (m.group(0), text[m.end():]) if m else ("", text)

def make_markdown_parser():
    return MarkdownIt("commonmark", {"html": True}).enable("table")

def compile_markdown(path, manifest_path=None, similarity_threshold=0.88):
    p=Path(path); raw=p.read_text(encoding="utf-8"); front, body=split_frontmatter(raw)
    toks=make_markdown_parser().parse(body); segs=[]; nodes=[]; counters={}
    def add(kind, text, frozen=False, meta=None):
        idx=counters.get(kind,0); counters[kind]=idx+1
        s=Segment(deterministic_id(str(p),kind,idx,text), kind, text or "", "", frozen, fingerprint(text or ""), "new", meta or {})
        segs.append(s); nodes.append({"id":s.id,"kind":kind,"frozen":frozen,"meta":meta or {}}); return s
    def add_mdx_props(text, parent_kind):
        for n,m in enumerate(JSX_PROP_RE.finditer(text or "")):
            add("jsx_prop", m.group(2), meta={"prop":m.group(1), "parent":parent_kind, "ordinal":n})
        for n,m in enumerate(JSX_CHILD_RE.finditer(text or "")):
            child=re.sub(r"<[^>]+>","",m.group(2)).strip()
            if child:
                add("jsx_child", child, meta={"component":m.group(1), "parent":parent_kind, "ordinal":n})
    i=0
    while i<len(toks):
        t=toks[i]
        if t.type=="heading_open":
            add("heading", toks[i+1].content if i+1<len(toks) else "", meta={"level":int(t.tag[1]) if t.tag.startswith("h") else 1}); i+=3; continue
        if t.type=="list_item_open":
            j=i+1; parts=[]
            while j<len(toks) and toks[j].type!="list_item_close":
                if toks[j].type=="inline" and toks[j].content: parts.append(toks[j].content)
                j+=1
            if parts: add("list_item", "\n".join(parts))
            i=j+1; continue
        if t.type=="blockquote_open":
            j=i+1; parts=[]
            while j<len(toks) and toks[j].type!="blockquote_close":
                if toks[j].type=="inline" and toks[j].content:
                    parts.append(re.sub(r"^\[![A-Z]+\]\s*", "", toks[j].content))
                j+=1
            if parts: add("blockquote", "\n".join(parts))
            i=j+1; continue
        if t.type=="paragraph_open":
            txt=toks[i+1].content if i+1<len(toks) and toks[i+1].type=="inline" else ""
            if txt:
                # markdown-it-py CommonMark treats ::: admonitions as normal paragraphs.
                # TokenMark upgrades that paragraph into semantic admonition segments.
                m=ADMONITION_RE.match(txt.strip())
                if m:
                    typ,title,content=m.group(1),m.group(2) or m.group(1).title(),m.group(3).strip()
                    add("admonition_title", title, meta={"admonition_type":typ})
                    add("admonition_body", content, meta={"admonition_type":typ})
                else:
                    add("paragraph", txt)
                    for m in re.finditer(r"!\[([^\]]*)\]\([^)]+\)", txt): add("image_alt", m.group(1), meta={"parent":"paragraph"})
                    for m in re.finditer(r"(?<!!)\[([^\]]+)\]\([^)]+\)", txt): add("link_text", m.group(1), meta={"parent":"paragraph"})
                    add_mdx_props(txt, "paragraph")
            i+=3; continue
        if t.type=="fence":
            add("code_block", t.content, True, {"lang":t.info or ""}); i+=1; continue
        if t.type=="html_block":
            txt=t.content.strip(); m=ADMONITION_RE.match(txt)
            if m:
                typ,title,content=m.group(1),m.group(2) or m.group(1).title(),m.group(3).strip()
                add("admonition_title", title, meta={"admonition_type":typ}); add("admonition_body", content, meta={"admonition_type":typ})
            else:
                add("html_block", t.content, True)
                add_mdx_props(t.content, "html_block")
            i+=1; continue
        if t.type in ("th_open","td_open"):
            txt=toks[i+1].content if i+1<len(toks) and toks[i+1].type=="inline" else ""
            if txt: add("table_cell", txt)
            i+=3; continue
        i+=1
    if manifest_path:
        segs=reuse_ids_from_manifest(segs, load_manifest(manifest_path), similarity_threshold)
        for n,s in zip(nodes,segs): n["id"]=s.id
    return segs, DocumentIR(str(p), nodes, front)
