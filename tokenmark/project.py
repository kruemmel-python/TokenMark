DEFAULT_CSS = """body{font-family:system-ui;margin:0;line-height:1.65;color:#111827;background:#f8fafc}.tm-sidebar{position:fixed;left:0;top:0;bottom:0;width:220px;background:#0f172a;color:white;padding:24px;overflow:auto}.tm-sidebar a{display:block;color:#dbeafe;text-decoration:none;margin:10px 0}.tm-content{max-width:860px;margin:48px auto;padding:0 280px 0 240px}.tm-toc{position:fixed;right:24px;top:110px;width:220px}.tm-toc a{display:block;color:#334155;text-decoration:none;margin:6px 0}.tm-search{position:fixed;right:24px;top:24px;width:220px}.tm-search input{width:100%;padding:8px}#tm-search-results a{display:block;background:white;padding:6px;border:1px solid #e5e7eb}pre{background:#0f172a;color:white;border-radius:10px;padding:16px;overflow:auto}blockquote{border-left:4px solid #93c5fd;padding-left:16px;color:#334155}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{border:1px solid #cbd5e1;padding:10px}.tokenmark-admonition{border-left:5px solid #3b82f6;background:#eff6ff;padding:12px 16px;margin:16px 0}.tokenmark-admonition-title{font-weight:700}.tokenmark-inspect [data-token]:hover{outline:2px solid #f97316;cursor:pointer}\n"""
import json, importlib
from pathlib import Path

DEFAULT_CONFIG={"version":"0.9.3","source_dir":"docs","build_dir":"build","default_lang":"de","locales_dir":"locales","theme":"themes/default.css","plugins":["tokenmark.plugins.admonitions"],"include_frozen":False,"id_similarity_threshold":0.88,"tm_path":"locales/tm.sqlite","tm_json_path":"locales/tm.json","tm_backend":"sqlite","tm_fuzzy_threshold":0.82,"glossary_path":"locales/glossary.json","site":True,"incremental":True,"mdx":True,"mdx_translatable_props":["title","label","description","alt","aria-label","placeholder"],"semantic_tm":True,"ci_base":"origin/main","compose":{"default_provider":"heuristic","default_outdir":"docs/generated","default_document_type":"technical-guide","default_audience":"developers","include_trace":True}}

def find_project_root(start="."):
    p=Path(start).resolve()
    for c in [p,*p.parents]:
        if (c/".tokenmark.json").exists(): return c
    return p

def load_config(root="."):
    root=find_project_root(root); cfg=dict(DEFAULT_CONFIG); fp=root/".tokenmark.json"
    if fp.exists(): cfg.update(json.loads(fp.read_text(encoding="utf-8")))
    return cfg

def write_default_project(root=".", force=False):
    root=Path(root)
    for d in ["docs","themes","build","locales/de","locales/en"]: (root/d).mkdir(parents=True,exist_ok=True)
    if force or not (root/".tokenmark.json").exists():
        (root/".tokenmark.json").write_text(json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False), encoding="utf-8")
    if force or not (root/"docs/demo.md").exists():
        (root/"docs/demo.md").write_text("# Einführung\n\nHallo **Welt**.\n", encoding="utf-8")
    if force or not (root/"themes/default.css").exists():
        (root/"themes/default.css").write_text(DEFAULT_CSS, encoding="utf-8")
    if force or not (root/"locales/glossary.json").exists():
        (root/"locales/glossary.json").write_text(json.dumps({"version":1,"terms":[{"source":"TokenMark","target":"TokenMark","note":"Product name, do not translate."}]}, indent=2, ensure_ascii=False), encoding="utf-8")

def markdown_files(root, cfg):
    src=root/cfg.get("source_dir","docs")
    return sorted([*src.rglob("*.md"), *src.rglob("*.mdx")]) if src.exists() else []

def load_plugins(cfg):
    mods=[]
    for name in cfg.get("plugins",[]):
        try: mods.append(importlib.import_module(name))
        except Exception as e: print(f"[tokenmark] plugin load failed: {name}: {e}")
    return mods
