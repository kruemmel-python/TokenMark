
from __future__ import annotations
import html, json
from pathlib import Path
from .project import markdown_files
from .cli_helpers import paths_for
from .catalog import status_summary, load_catalog
from .qa_linter import lint_catalog

def collect_i18n_stats(root: Path, cfg: dict, lang: str):
    pages=[]
    total={"translated":0,"missing":0,"needs_review":0,"frozen":0,"total":0,"lint_issues":0}
    for md in markdown_files(root,cfg):
        p=paths_for(root,cfg,md,lang)
        if not p["catalog"].exists():
            s={"translated":0,"missing":0,"needs_review":0,"frozen":0,"total":0,"lint_issues":0}
        else:
            s=status_summary(p["catalog"])
            s["lint_issues"]=len(lint_catalog(load_catalog(p["catalog"])))
        for k in total:
            total[k]+=s.get(k,0)
        pages.append({"source":str(md.relative_to(root)),"catalog":str(p["catalog"].relative_to(root)),"summary":s})
    pages.sort(key=lambda x:(x["summary"].get("missing",0)+x["summary"].get("needs_review",0)+x["summary"].get("lint_issues",0)), reverse=True)
    return {"lang":lang,"total":total,"pages":pages}

def _pct(a,b):
    return 0 if not b else round((a/b)*100,1)

def render_dashboard(root: Path, cfg: dict, lang: str, out_path: Path):
    data=collect_i18n_stats(root,cfg,lang)
    t=data["total"]; total=max(1,t["total"])
    translated=_pct(t["translated"], total)
    review=_pct(t["needs_review"], total)
    missing=_pct(t["missing"], total)
    rows=[]
    for p in data["pages"]:
        s=p["summary"]; tt=max(1,s.get("total",0))
        rows.append(f"""<tr>
<td><code>{html.escape(p['source'])}</code></td>
<td>{s.get('translated',0)}</td><td>{s.get('needs_review',0)}</td><td>{s.get('missing',0)}</td><td>{s.get('lint_issues',0)}</td>
<td><div class='bar'><i style='width:{_pct(s.get('translated',0),tt)}%'></i></div></td>
</tr>""")
    doc=f"""<!doctype html><html><head><meta charset='utf-8'><title>TokenMark i18n Dashboard</title>
<style>
body{{font-family:system-ui;margin:40px;background:#0f172a;color:#e5e7eb}}
.card{{background:#111827;border:1px solid #334155;border-radius:18px;padding:20px;margin:16px 0;box-shadow:0 10px 30px #0004}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(140px,1fr));gap:16px}}
.big{{font-size:34px;font-weight:800}} .muted{{color:#94a3b8}}
.bar{{height:12px;background:#334155;border-radius:999px;overflow:hidden}} .bar i{{display:block;height:100%;background:#22c55e}}
.stack{{height:24px;border-radius:999px;overflow:hidden;background:#334155;display:flex}} .tr{{background:#22c55e}} .rv{{background:#f59e0b}} .mi{{background:#ef4444}}
table{{width:100%;border-collapse:collapse}} td,th{{padding:10px;border-bottom:1px solid #334155;text-align:left}} code{{color:#93c5fd}}
a{{color:#93c5fd}}
</style></head><body>
<h1>TokenMark Localization Dashboard</h1><p class='muted'>Language: <b>{html.escape(lang)}</b></p>
<div class='card'>
<div class='grid'>
<div><div class='big'>{translated}%</div><div class='muted'>Translated</div></div>
<div><div class='big'>{review}%</div><div class='muted'>Needs review</div></div>
<div><div class='big'>{missing}%</div><div class='muted'>Missing</div></div>
<div><div class='big'>{t['lint_issues']}</div><div class='muted'>QA warnings</div></div>
</div>
<p></p><div class='stack'><span class='tr' style='width:{translated}%'></span><span class='rv' style='width:{review}%'></span><span class='mi' style='width:{missing}%'></span></div>
</div>
<div class='card'><h2>Pages needing attention</h2><table><thead><tr><th>Page</th><th>Translated</th><th>Review</th><th>Missing</th><th>QA</th><th>Progress</th></tr></thead><tbody>
{''.join(rows)}
</tbody></table></div>
<script id='tokenmark-dashboard-data' type='application/json'>{html.escape(json.dumps(data,ensure_ascii=False))}</script>
</body></html>"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(doc,encoding="utf-8")
    return out_path
