import json, re
from pathlib import Path

FM_RE=re.compile(r"\A---\s*\n(.*?)\n---", re.S)
TITLE_RE=re.compile(r"^#\s+(.+)$", re.M)

def parse_frontmatter_meta(text):
    meta={}
    m=FM_RE.match(text)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k,v=line.split(":",1)
                meta[k.strip()]=v.strip().strip('"\'')
    return meta

def page_title(md_path):
    text=Path(md_path).read_text(encoding="utf-8")
    meta=parse_frontmatter_meta(text)
    if meta.get("title"):
        return meta["title"]
    m=TITLE_RE.search(text)
    return m.group(1).strip() if m else Path(md_path).stem

def _page_url(root, cfg, md, lang=None):
    src=(root/cfg.get("source_dir","docs")).resolve()
    mdp=Path(md).resolve()
    try:
        rel=mdp.relative_to(src)
    except ValueError:
        rel=Path(mdp.name)
    suffix="" if not lang or lang==cfg.get("default_lang","de") else f".{lang}"
    stem=rel.with_suffix("")
    return str(stem.parent / f"{stem.name}{suffix}.html").replace("\\","/")

def write_site_index(root, cfg, files):
    build=root/cfg.get("build_dir","build")
    src=root/cfg.get("source_dir","docs")
    pages=[]
    for md in files:
        text=Path(md).read_text(encoding="utf-8")
        meta=parse_frontmatter_meta(text)
        pages.append({
            "source": str(Path(md).relative_to(root)) if Path(md).is_absolute() else str(md),
            "title": page_title(md),
            "url": _page_url(root,cfg,md),
            "order": int(meta.get("order","999") or 999),
            "text": re.sub(r"`{3}.*?`{3}", "", text, flags=re.S)[:8000],
        })
    pages.sort(key=lambda p:(p["order"],p["title"]))
    build.mkdir(parents=True,exist_ok=True)
    (build/"site_index.json").write_text(json.dumps({"pages":pages}, indent=2, ensure_ascii=False), encoding="utf-8")
    return pages

def nav_html(root, cfg):
    p=root/cfg.get("build_dir","build")/"site_index.json"
    if not p.exists():
        return ""
    pages=json.loads(p.read_text(encoding="utf-8")).get("pages",[])
    links="\n".join(f'<a class="tm-nav-link" href="/{page["url"].lstrip("/") }">{page["title"]}</a>' for page in pages)
    return f'<nav class="tm-sidebar"><strong>Docs</strong>{links}</nav>'

def search_html():
    return """<div class="tm-search"><input id="tm-search" placeholder="Search docs…" autocomplete="off"><div id="tm-search-results"></div></div>
<script>
(async()=>{try{
const r=await fetch("/site_index.json"); const idx=await r.json();
const q=document.getElementById("tm-search"), out=document.getElementById("tm-search-results");
if(!q||!out)return;
q.addEventListener("input",()=>{const v=q.value.toLowerCase().trim(); out.innerHTML="";
 if(!v)return; idx.pages.filter(p=>(p.title+" "+p.text).toLowerCase().includes(v)).slice(0,8)
 .forEach(p=>{const a=document.createElement("a"); a.href="/"+String(p.url||"").replace(/^[/]+/, ""); a.textContent=p.title; out.appendChild(a);});
});
}catch(e){}})();
</script>"""

def toc_html(segs):
    items=[]
    for s in segs:
        if s.kind=="heading":
            lvl=(s.meta or {}).get("level",1)
            title=s.target or s.source
            items.append(f'<a class="tm-toc-l{lvl}" href="#{s.id}">{title}</a>')
    return '<aside class="tm-toc"><strong>On this page</strong>'+"\n".join(items)+'</aside>' if items else ""
