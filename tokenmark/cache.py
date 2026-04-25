import hashlib, json
from pathlib import Path

WATCHED_GLOBALS=(".tokenmark.json",)

def file_hash(path):
    p=Path(path)
    if not p.exists() or not p.is_file():
        return ""
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_cache(root, cfg):
    p=Path(root)/cfg.get("build_dir","build")/".tokenmark_cache.json"
    if not p.exists():
        return {"version":1,"files":{},"globals":{}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"version":1,"files":{},"globals":{}}

def save_cache(root, cfg, cache):
    p=Path(root)/cfg.get("build_dir","build")/".tokenmark_cache.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")

def global_state(root, cfg):
    root=Path(root)
    files=[root/".tokenmark.json", root/cfg.get("theme","themes/default.css")]
    # glossary and TM can influence translations/status, but TM is usually updated by build; don't make it global invalidator.
    gp=cfg.get("glossary_path")
    if gp: files.append(root/gp)
    return {str(p.relative_to(root)): file_hash(p) for p in files if p.exists()}

def inputs_state(root, cfg, md_path, lang=None):
    root=Path(root); md_path=Path(md_path)
    stem=md_path.stem
    loc=root/cfg.get("locales_dir","locales")
    lang=lang or cfg.get("default_lang","de")
    cat=loc/lang/f"{stem}.catalog.json"
    files=[md_path, cat]
    return {str(p.relative_to(root) if p.is_absolute() and root in p.parents else p): file_hash(p) for p in files if p.exists()}

def is_unchanged(root, cfg, md_path, cache, lang=None):
    g=global_state(root,cfg)
    if cache.get("globals") != g:
        return False
    key=str(Path(md_path).relative_to(root) if Path(md_path).is_absolute() else md_path)
    return cache.get("files",{}).get(key)==inputs_state(root,cfg,md_path,lang)

def update_entry(root, cfg, md_path, cache, lang=None):
    cache["globals"]=global_state(root,cfg)
    key=str(Path(md_path).relative_to(root) if Path(md_path).is_absolute() else md_path)
    cache.setdefault("files",{})[key]=inputs_state(root,cfg,md_path,lang)
    return cache
