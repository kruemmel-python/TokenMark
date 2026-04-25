import json, re, shutil
from pathlib import Path
from .compiler import compile_markdown
from .catalog import write_catalog, write_tokens_txt, write_manifest, merge_existing_targets
from .render_html import render_html_from_segments
from .render_markdown import render_markdown_from_segments
from .adapters import export_po, export_xliff
from .project import markdown_files
from .hooks import load_plugin_manager
from .tm import load_tm, apply_tm, update_tm
from .site import write_site_index
from .cache import load_cache, save_cache, is_unchanged, update_entry

def _relative_doc_path(root, cfg, md_path):
    """Return the Markdown path relative to the configured source_dir.

    TokenMark used to flatten all project outputs into build/<stem>.html.
    That broke generated/module docs such as docs/generated/index.md because
    users naturally expect /generated/index.html.  From v0.9.1 onward, project
    artifacts mirror the source tree below source_dir:

        docs/generated/index.md -> build/generated/index.html
        locales/en/generated/index.catalog.json

    Single-file builds outside source_dir still fall back to the file stem.
    """
    root = Path(root).resolve()
    md_path = Path(md_path).resolve()
    src = (root / cfg.get("source_dir", "docs")).resolve()
    try:
        rel = md_path.relative_to(src)
    except ValueError:
        rel = Path(md_path.name)
    return rel

def paths_for(root,cfg,md_path,lang=None):
    build=root/cfg.get("build_dir","build"); loc=root/cfg.get("locales_dir","locales"); default=cfg.get("default_lang","de"); lang=lang or default
    rel=_relative_doc_path(root,cfg,md_path)
    suffix="" if lang==default else f".{lang}"
    stem_path = rel.with_suffix("")
    html_rel = stem_path.parent / f"{stem_path.name}{suffix}.html"
    md_rel = stem_path.parent / f"{stem_path.name}{suffix}.md"
    return {
        "html":build/html_rel,
        "md":build/md_rel,
        "tokens":build/(stem_path.parent / f"{stem_path.name}.tokens.txt"),
        "ir":build/(stem_path.parent / f"{stem_path.name}.ir.json"),
        "manifest":build/(stem_path.parent / f"{stem_path.name}.tokens.manifest.json"),
        "catalog":loc/lang/(stem_path.parent / f"{stem_path.name}.catalog.json"),
        "po":loc/lang/(stem_path.parent / f"{stem_path.name}.po"),
        "xliff":loc/lang/(stem_path.parent / f"{stem_path.name}.xliff"),
    }


def copy_local_assets(md_path, build_dir):
    """Copy local Markdown image assets next to rendered HTML for the dev server."""
    md_path=Path(md_path)
    build_dir=Path(build_dir)
    text=md_path.read_text(encoding="utf-8")
    for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text):
        ref=m.group(1).strip().split()[0].strip("<>")
        if not ref or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", ref) or ref.startswith("#"):
            continue
        src=(md_path.parent/ref).resolve()
        if src.exists() and src.is_file():
            dst=build_dir/ref
            dst.parent.mkdir(parents=True,exist_ok=True)
            try:
                shutil.copy2(src,dst)
            except shutil.SameFileError:
                pass

def build_one(root,cfg,md_path,outdir=None,inspect=False,live_reload=False):
    if outdir: cfg={**cfg,"build_dir":outdir}
    p=paths_for(root,cfg,md_path)
    pm=load_plugin_manager(cfg)
    pm.call("pre_compile", md_path=md_path, config=cfg)
    segs,ir=compile_markdown(md_path,p["manifest"],cfg.get("id_similarity_threshold",0.88))
    segs=pm.mutate_segments("post_compile", segs, md_path=md_path, ir=ir, config=cfg)
    segs=merge_existing_targets(segs,p["catalog"])
    segs=apply_tm(segs, root/cfg.get("tm_path","locales/tm.sqlite"), cfg.get("default_lang","de"), cfg.get("tm_fuzzy_threshold",0.0))
    write_tokens_txt(p["tokens"],segs); write_catalog(p["catalog"],str(md_path),segs,cfg.get("include_frozen",False)); write_manifest(p["manifest"],str(md_path),segs); update_tm(segs, root/cfg.get("tm_path","locales/tm.sqlite"), cfg.get("default_lang","de"))
    p["ir"].parent.mkdir(parents=True,exist_ok=True); p["ir"].write_text(json.dumps(ir.to_dict(),indent=2,ensure_ascii=False),encoding="utf-8")
    css=root/cfg.get("theme","themes/default.css"); p["html"].parent.mkdir(parents=True,exist_ok=True); p["html"].write_text(render_html_from_segments(md_path,segs,css_path=css,inspect=inspect,live_reload=live_reload,config=cfg,root=root),encoding="utf-8")
    copy_local_assets(md_path,p["html"].parent)
    return p

def build_project(root,cfg,inspect=False,live_reload=False,force=False):
    files=markdown_files(root,cfg)
    write_site_index(root,cfg,files)
    cache=load_cache(root,cfg)
    built=[]
    skipped=[]
    use_cache=cfg.get("incremental", True) and not inspect and not live_reload and not force
    for md in files:
        if use_cache and is_unchanged(root,cfg,md,cache,cfg.get("default_lang","de")):
            skipped.append(md)
            continue
        result=build_one(root,cfg,md,inspect=inspect,live_reload=live_reload)
        built.append(result)
        update_entry(root,cfg,md,cache,cfg.get("default_lang","de"))
    write_site_index(root,cfg,files)
    save_cache(root,cfg,cache)
    return {"built":built,"skipped":skipped}

def export_localized_markdown_tree(root,cfg,lang,outdir=None):
    outdir=Path(outdir) if outdir else root/cfg.get("build_dir","build")/"ssg"/lang
    src=root/cfg.get("source_dir","docs")
    written=[]
    for md in markdown_files(root,cfg):
        rel=md.relative_to(src)
        out=outdir/rel
        p=render_one(root,cfg,md,lang,"markdown")
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(Path(p).read_text(encoding="utf-8"),encoding="utf-8")
        written.append(out)
    return written

def extract_one(root,cfg,md_path,lang,fmt):
    p=paths_for(root,cfg,md_path,lang); segs,ir=compile_markdown(md_path,p["manifest"],cfg.get("id_similarity_threshold",0.88)); segs=merge_existing_targets(segs,p["catalog"])
    segs=apply_tm(segs, root/cfg.get("tm_path","locales/tm.sqlite"), cfg.get("default_lang","de"), cfg.get("tm_fuzzy_threshold",0.0))
    write_catalog(p["catalog"],str(md_path),segs,cfg.get("include_frozen",False))
    if fmt=="po": export_po(p["catalog"],p["po"])
    if fmt=="xliff": export_xliff(p["catalog"],p["xliff"])
    return p

def render_one(root,cfg,md_path,lang,fmt,catalog=None):
    p=paths_for(root,cfg,md_path,lang); cat=Path(catalog) if catalog else p["catalog"]; segs,ir=compile_markdown(md_path,p["manifest"],cfg.get("id_similarity_threshold",0.88))
    pm=load_plugin_manager(cfg)
    segs=pm.mutate_segments("pre_render", segs, md_path=md_path, lang=lang, format=fmt, config=cfg)
    if fmt=="markdown":
        p["md"].parent.mkdir(parents=True,exist_ok=True); p["md"].write_text(render_markdown_from_segments(segs,cat,ir.frontmatter),encoding="utf-8"); return p["md"]
    if fmt=="pdf":
        from .render_pdf import render_pdf
        pdf_path=p["html"].with_suffix(".pdf")
        render_pdf(md_path,segs,cat,css_path=root/cfg.get("theme","themes/default.css"),out_path=pdf_path,config=cfg,root=root)
        return pdf_path
    css=root/cfg.get("theme","themes/default.css"); p["html"].parent.mkdir(parents=True,exist_ok=True); p["html"].write_text(render_html_from_segments(md_path,segs,cat,css_path=css,config=cfg,root=root),encoding="utf-8"); return p["html"]
