import json
from pathlib import Path
from .idgen import similarity

def load_catalog(path):
    p=Path(path)
    if not p.exists(): return {"source":"","entries":[]}
    data=json.loads(p.read_text(encoding="utf-8"))
    if "entries" not in data: raise SystemExit(f"Catalog {p} has no 'entries' list.")
    return data

def write_catalog(path, source, segments, include_frozen=False):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    entries=[s.to_catalog() for s in segments if include_frozen or not s.frozen]
    p.write_text(json.dumps({"source":source,"entries":entries}, indent=2, ensure_ascii=False), encoding="utf-8")

def catalog_targets(path):
    return {e["id"]:e.get("target","") for e in load_catalog(path).get("entries",[]) if e.get("target","")}

def write_tokens_txt(path, segments):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    lines=[]
    for s in segments:
        flag=(" frozen" if s.frozen else "") + (f" {s.status}" if s.status not in ("new","current","") else "")
        lines.append(f"{s.id}({s.kind}{flag}): {s.source.replace(chr(10),'\\n')}")
    p.write_text("\n".join(lines)+"\n", encoding="utf-8")

def load_manifest(path):
    p=Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"nodes":[]}

def write_manifest(path, source, segments):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    data={"source":source, "nodes":[{"id":s.id,"kind":s.kind,"source":s.source,"fingerprint":s.fingerprint} for s in segments]}
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def reuse_ids_from_manifest(segments, manifest, threshold=0.88):
    old=manifest.get("nodes",[]); used=set()
    for s in segments:
        best=None; best_score=0
        for o in old:
            if o.get("kind")!=s.kind or o.get("id") in used: continue
            score=similarity(s.source, o.get("source",""))
            if score>best_score: best=o; best_score=score
        if best and best_score>=threshold:
            s.id=best["id"]; used.add(s.id)
            s.status="current" if best.get("fingerprint")==s.fingerprint else "needs_review"
    return segments

def merge_existing_targets(segments, catalog_path):
    if not catalog_path or not Path(catalog_path).exists(): return segments
    by={e["id"]:e for e in load_catalog(catalog_path).get("entries",[])}
    for s in segments:
        e=by.get(s.id)
        if e:
            s.target=e.get("target","")
            if s.status=="needs_review" or e.get("status")=="needs_review": s.status="needs_review"
            elif s.target: s.status="translated"
    return segments

def status_summary(catalog_path):
    res={"translated":0,"missing":0,"needs_review":0,"frozen":0,"total":0}
    for e in load_catalog(catalog_path).get("entries",[]):
        res["total"] += 1
        if e.get("frozen"): res["frozen"] += 1
        elif e.get("status")=="needs_review": res["needs_review"] += 1
        elif e.get("target"): res["translated"] += 1
        else: res["missing"] += 1
    return res
