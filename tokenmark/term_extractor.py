
from __future__ import annotations
import json, re
from collections import Counter
from pathlib import Path
from .compiler import compile_markdown

STOP = {
    "und","oder","der","die","das","ein","eine","einer","eines","mit","für","von","auf","im","in","zu","den","dem","des",
    "the","and","or","for","with","from","into","this","that","you","your","are","is","to","of"
}
WORD_RE = re.compile(r"\b[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß0-9_-]{2,}\b")
PHRASE_RE = re.compile(r"\b([A-ZÄÖÜ][\wÄÖÜäöüß-]+(?:\s+[A-ZÄÖÜ][\wÄÖÜäöüß-]+){1,4})\b")

def extract_terms_from_text(text: str, min_freq: int = 2, limit: int = 50):
    candidates=Counter()
    for m in PHRASE_RE.finditer(text or ""):
        phrase=m.group(1).strip()
        if len(phrase) > 4:
            candidates[phrase]+=3
    for w in WORD_RE.findall(text or ""):
        wl=w.lower()
        if wl in STOP or wl.isdigit():
            continue
        # Boost CamelCase, all-caps, product-ish and long nouns.
        score=1
        if any(c.isupper() for c in w[1:]): score+=2
        if w.isupper() and len(w)>2: score+=2
        if "-" in w or "_" in w: score+=1
        if len(w)>10: score+=1
        candidates[w]+=score
    return [(term,score) for term,score in candidates.most_common(limit) if score >= min_freq]

def extract_terms_from_project(root: Path, cfg: dict, min_freq: int = 2, limit: int = 80):
    from .project import markdown_files
    corpus=[]
    for md in markdown_files(root,cfg):
        try:
            segs,_=compile_markdown(md)
            corpus.extend(s.source for s in segs if not s.frozen and s.source)
        except Exception:
            corpus.append(md.read_text(encoding="utf-8", errors="ignore"))
    return extract_terms_from_text("\n".join(corpus), min_freq=min_freq, limit=limit)

def merge_terms_into_glossary(glossary_path: Path, terms):
    glossary_path.parent.mkdir(parents=True, exist_ok=True)
    if glossary_path.exists():
        try:
            data=json.loads(glossary_path.read_text(encoding="utf-8"))
        except Exception:
            data={"terms":[]}
    else:
        data={"terms":[]}
    existing={str(t.get("source","")).lower() for t in data.get("terms",[]) if isinstance(t,dict)}
    added=0
    for term,score in terms:
        if term.lower() in existing:
            continue
        data.setdefault("terms",[]).append({"source":term,"target":"","note":f"candidate score {score}"})
        added+=1
    glossary_path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
    return added
