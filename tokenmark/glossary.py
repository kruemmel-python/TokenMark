import json, re
from pathlib import Path

def load_glossary(path):
    p=Path(path)
    if not p.exists():
        return {"version":1,"terms":[]}
    data=json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "terms" in data:
        return data
    if isinstance(data, list):
        return {"version":1,"terms":data}
    return {"version":1,"terms":[]}

def relevant_terms(texts, glossary_path):
    data=load_glossary(glossary_path)
    corpus="\n".join(t or "" for t in texts)
    terms=[]
    for term in data.get("terms",[]):
        src=term.get("source") or term.get("term") or ""
        if not src:
            continue
        if re.search(r"(?<!\w)"+re.escape(src)+r"(?!\w)", corpus, flags=re.I):
            terms.append({
                "source": src,
                "target": term.get("target",""),
                "note": term.get("note","")
            })
    return terms

def glossary_prompt(terms):
    if not terms:
        return ""
    lines=["Glossary entries that must be respected:"]
    for t in terms:
        note=f" ({t['note']})" if t.get("note") else ""
        lines.append(f"- {t['source']} -> {t.get('target','')}{note}")
    return "\n".join(lines)
