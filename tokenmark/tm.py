
import json, hashlib
from pathlib import Path
from .idgen import normalize_text

TRANSLATABLE_KINDS = {
    "heading","paragraph","list_item","blockquote","table_cell",
    "image_alt","link_text","admonition_title","admonition_body","jsx_prop","jsx_child"
}

def source_key(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()

def _is_sqlite(path):
    return str(path).lower().endswith((".sqlite",".db",".sqlite3"))

def load_tm(path):
    p=Path(path)
    if _is_sqlite(p):
        return {"version":2,"backend":"sqlite","path":str(p)}
    if not p.exists():
        return {"version":1,"entries":{}}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"version":1,"entries":{}}

def save_tm(path, tm):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    if _is_sqlite(p): return
    p.write_text(json.dumps(tm, indent=2, ensure_ascii=False), encoding="utf-8")

def apply_tm(segments, tm_path, default_lang="de", fuzzy_threshold=0.0):
    if _is_sqlite(tm_path):
        from . import tm_sqlite
        con=tm_sqlite.connect(tm_path)
        try:
            for s in segments:
                if s.frozen or s.target or s.kind not in TRANSLATABLE_KINDS:
                    continue
                hit=tm_sqlite.exact(con, s.source, default_lang)
                if hit:
                    s.target=hit["target"]; s.status="needs_review" if s.status!="translated" else s.status
                    meta=s.meta or {}; meta["tm_reused"]=True; meta["tm_score"]=1.0; s.meta=meta
                    continue
                if fuzzy_threshold:
                    matches=tm_sqlite.fuzzy(con, s.source, default_lang, threshold=float(fuzzy_threshold), top_k=1)
                    if matches:
                        m=matches[0]
                        s.target=m["target"]; s.status="needs_review"
                        meta=s.meta or {}; meta["tm_fuzzy"]=True; meta["tm_score"]=m["score"]; meta["tm_source"]=m["source"]; s.meta=meta
            return segments
        finally:
            con.close()
    tm=load_tm(tm_path).get("entries",{})
    for s in segments:
        if s.frozen or s.target or s.kind not in TRANSLATABLE_KINDS:
            continue
        hit=tm.get(source_key(s.source))
        if hit and hit.get("target"):
            s.target=hit["target"]
            s.status="needs_review" if s.status!="translated" else s.status
            meta=s.meta or {}
            meta["tm_reused"]=True
            meta["tm_score"]=1.0
            s.meta=meta
    return segments

def update_tm(segments, tm_path, default_lang="de"):
    if _is_sqlite(tm_path):
        from . import tm_sqlite
        con=tm_sqlite.connect(tm_path)
        try:
            for s in segments:
                if s.frozen or not s.target or s.kind not in TRANSLATABLE_KINDS:
                    continue
                tm_sqlite.upsert(con, s.source, s.target, default_lang, s.kind, s.id, s.status, s.meta or {})
            con.commit()
        finally:
            con.close()
        return {"version":2,"backend":"sqlite","path":str(tm_path)}
    data=load_tm(tm_path)
    entries=data.setdefault("entries",{})
    changed=False
    for s in segments:
        if s.frozen or not s.target or s.kind not in TRANSLATABLE_KINDS:
            continue
        k=source_key(s.source)
        val={"source":s.source,"target":s.target,"kind":s.kind,"last_segment_id":s.id}
        if entries.get(k) != val:
            entries[k]=val
            changed=True
    if changed:
        save_tm(tm_path,data)
    return data

def fuzzy_suggestions(tm_path, source, lang, threshold=0.75, top_k=5, mode="hybrid"):
    if _is_sqlite(tm_path):
        from . import tm_sqlite
        con=tm_sqlite.connect(tm_path)
        try:
            return tm_sqlite.fuzzy(con, source, lang, threshold=threshold, top_k=top_k, mode=mode)
        finally:
            con.close()
    data=load_tm(tm_path).get("entries",{})
    from difflib import SequenceMatcher
    out=[]
    for e in data.values():
        score=SequenceMatcher(None, normalize_text(source), normalize_text(e.get("source",""))).ratio()
        if score>=threshold:
            out.append({"score":round(score,4),"source":e.get("source",""),"target":e.get("target",""),"kind":e.get("kind","")})
    return sorted(out, key=lambda x:x["score"], reverse=True)[:top_k]
