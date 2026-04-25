import json, html, re
from pathlib import Path
from .catalog import load_catalog

def po_escape(s): return (s or "").replace("\\","\\\\").replace('"','\\"').replace("\n","\\n")
def po_unescape(s): return (s or "").replace("\\n","\n").replace('\\"','"').replace("\\\\","\\")

def export_po(catalog_path, po_path):
    data=load_catalog(catalog_path); lines=['msgid ""','msgstr ""','"Content-Type: text/plain; charset=UTF-8\\n"','']
    for e in data.get("entries",[]):
        if e.get("frozen"): continue
        lines += [f'#: {data.get("source","")}', f'#. kind={e.get("kind","")} status={e.get("status","")}', f'msgctxt "{po_escape(e["id"])}"', f'msgid "{po_escape(e.get("source",""))}"', f'msgstr "{po_escape(e.get("target",""))}"', ""]
    p=Path(po_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text("\n".join(lines), encoding="utf-8")

def import_po_to_catalog(po_path, catalog_path, out_path=None):
    text=Path(po_path).read_text(encoding="utf-8"); entries={}; current=None
    for line in text.splitlines():
        if line.startswith("msgctxt "): current=po_unescape(line.split(" ",1)[1].strip().strip('"'))
        elif line.startswith("msgstr ") and current:
            entries[current]=po_unescape(line.split(" ",1)[1].strip().strip('"')); current=None
    data=load_catalog(catalog_path)
    for e in data.get("entries",[]):
        if e["id"] in entries:
            e["target"]=entries[e["id"]]
            if e["target"]: e["status"]="translated"
    Path(out_path or catalog_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


PH_RE=re.compile(r"(`[^`]+`|\{\{[^}]+\}\}|</?[A-Z][A-Za-z0-9_.]*\b[^>]*>)")
def xliff_text(s):
    parts=[]; last=0; n=1
    for m in PH_RE.finditer(s or ""):
        parts.append(html.escape((s or "")[last:m.start()]))
        parts.append(f'<ph id="{n}" equiv="{html.escape(m.group(0))}"/>')
        last=m.end(); n+=1
    parts.append(html.escape((s or "")[last:]))
    return "".join(parts)

def export_xliff(catalog_path, xliff_path):
    data=load_catalog(catalog_path); units=[]
    for e in data.get("entries",[]):
        if e.get("frozen"): continue
        units.append(f'<unit id="{html.escape(e["id"])}"><segment><source>{xliff_text(e.get("source",""))}</source><target>{xliff_text(e.get("target",""))}</target></segment></unit>')
    xml='<?xml version="1.0" encoding="UTF-8"?>\n<xliff version="2.0" xmlns="urn:oasis:names:tc:xliff:document:2.0"><file id="'+html.escape(data.get("source","document"))+'">\n'+"\n".join(units)+"\n</file></xliff>\n"
    p=Path(xliff_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(xml, encoding="utf-8")
