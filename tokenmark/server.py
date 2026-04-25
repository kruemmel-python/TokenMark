import time, threading, os, json, urllib.parse
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from .project import find_project_root, load_config, markdown_files
from .cli_helpers import build_project, paths_for, extract_one, render_one
from .catalog import status_summary, load_catalog
from .qa_linter import lint_catalog
from .tm import fuzzy_suggestions

_clients=[]
_server_state={}

def _safe_write(handler, payload):
    """Write a response body, ignoring browser-side aborts.

    During Studio saves the page/iframe can reload while a POST response is
    still being written. On Windows this often appears as WinError 10053.
    It is not a failed catalog update; it only means the browser closed the
    socket first.
    """
    try:
        handler.wfile.write(payload)
        return True
    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError):
        return False

def _send_json(handler, data, status=200):
    payload=json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    try:
        handler.send_response(status)
        handler.send_header("Content-Type","application/json; charset=utf-8")
        handler.send_header("Content-Length",str(len(payload)))
        handler.end_headers()
        _safe_write(handler, payload)
    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError):
        return None

def _send_html(handler, html, status=200):
    payload=html.encode("utf-8")
    try:
        handler.send_response(status)
        handler.send_header("Content-Type","text/html; charset=utf-8")
        handler.send_header("Content-Length",str(len(payload)))
        handler.end_headers()
        _safe_write(handler, payload)
    except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError, OSError):
        return None

def _query(path):
    return urllib.parse.parse_qs(urllib.parse.urlparse(path).query)


def _catalog_entry_to_tm(root, cfg, entry, lang):
    if not entry or entry.get("frozen") or not entry.get("source") or not entry.get("target"):
        return False
    try:
        from . import tm_sqlite
        tm_path=root/cfg.get("tm_path","locales/tm.sqlite")
        con=tm_sqlite.connect(tm_path)
        try:
            meta=entry.get("meta") or {}
            meta.setdefault("author", "studio")
            tm_sqlite.upsert(
                con,
                entry.get("source",""),
                entry.get("target",""),
                lang,
                entry.get("kind",""),
                entry.get("id",""),
                entry.get("status","needs_review"),
                meta,
            )
            con.commit()
            return True
        finally:
            con.close()
    except Exception as exc:
        print("[tokenmark] TM update skipped:", exc)
        return False

def _sync_tm_from_catalogs(root, cfg, lang):
    """Keep Studio suggestions in sync with catalog files.

    Older versions only wrote TM entries during auto-translate. That meant
    translations saved in Studio or existing catalog targets were invisible to
    the TM suggestion endpoint until a separate import step existed. This sync
    is intentionally conservative: only entries with non-empty target are added.
    """
    try:
        from . import tm_sqlite
        tm_path=root/cfg.get("tm_path","locales/tm.sqlite")
        con=tm_sqlite.connect(tm_path)
        count=0
        try:
            for md in markdown_files(root,cfg):
                p=paths_for(root,cfg,md,lang)
                if not p["catalog"].exists():
                    continue
                data=load_catalog(p["catalog"])
                for e in data.get("entries",[]):
                    if e.get("frozen") or not e.get("source") or not e.get("target"):
                        continue
                    tm_sqlite.upsert(
                        con,
                        e.get("source",""),
                        e.get("target",""),
                        lang,
                        e.get("kind",""),
                        e.get("id",""),
                        e.get("status","needs_review"),
                        e.get("meta") or {},
                    )
                    count += 1
            con.commit()
        finally:
            con.close()
        return count
    except Exception as exc:
        print("[tokenmark] TM sync skipped:", exc)
        return 0

def _update_catalog_token(root, cfg, token_id, target, lang=None, status="translated"):
    lang=lang or cfg.get("default_lang","de")
    changed=False
    touched=[]
    for md in markdown_files(root,cfg):
        p=paths_for(root,cfg,md,lang)
        if not p["catalog"].exists():
            continue
        data=json.loads(p["catalog"].read_text(encoding="utf-8"))
        for e in data.get("entries",[]):
            if e.get("id")==token_id:
                e["target"]=target
                e["status"]=status
                p["catalog"].write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
                _catalog_entry_to_tm(root, cfg, e, lang)
                changed=True
                touched.append(str(p["catalog"]))
                break
    return changed, touched

def _stats(root,cfg,lang):
    pages=[]
    total={"translated":0,"missing":0,"needs_review":0,"frozen":0,"total":0,"lint_issues":0}
    for md in markdown_files(root,cfg):
        p=paths_for(root,cfg,md,lang)
        if not p["catalog"].exists():
            pages.append({"source":str(md.relative_to(root)),"catalog":str(p["catalog"]),"missing_catalog":True})
            continue
        s=status_summary(p["catalog"])
        issues=lint_catalog(load_catalog(p["catalog"]))
        s["lint_issues"]=len(issues)
        for k in total:
            total[k]+=s.get(k,0)
        pages.append({"source":str(md.relative_to(root)),"catalog":str(p["catalog"].relative_to(root)),"summary":s})
    return {"lang":lang,"total":total,"pages":pages}

def _catalogs(root,cfg,lang):
    cats=[]
    for md in markdown_files(root,cfg):
        p=paths_for(root,cfg,md,lang)
        if not p["catalog"].exists():
            extract_one(root,cfg,md,lang,"json")
        # Ensure the Studio preview exists for the selected language.
        # build_project() only creates the default-language HTML; the Studio can
        # switch languages, so we opportunistically render the localized page here.
        try:
            render_one(root, cfg, md, lang, "html")
        except Exception as exc:
            print("[tokenmark] localized preview render failed:", exc)
        data=load_catalog(p["catalog"])
        cats.append({"source":str(md.relative_to(root)),"catalog":str(p["catalog"].relative_to(root)),"entries":data.get("entries",[])})
    return {"lang":lang,"catalogs":cats}


def _history(root,cfg,token_id,lang,limit=5):
    try:
        from . import tm_sqlite
        con=tm_sqlite.connect(root/cfg.get("tm_path","locales/tm.sqlite"))
        try:
            return {"id":token_id,"history":tm_sqlite.history(con, segment_id=token_id, lang=lang, limit=limit)}
        finally:
            con.close()
    except Exception as exc:
        return {"id":token_id,"history":[],"error":str(exc)}

STUDIO_HTML = r"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TokenMark Studio</title>
<style>
body{font-family:system-ui;margin:0;background:#0f172a;color:#e5e7eb;height:100vh;overflow:hidden}
header{height:64px;background:#111827;padding:10px 16px;border-bottom:1px solid #334155;display:flex;align-items:center;gap:14px}
button,input,select,textarea{font:inherit}
button{border:0;border-radius:10px;padding:8px 12px;background:#2563eb;color:white;cursor:pointer}.secondary{background:#475569}
.layout{display:grid;grid-template-columns:55% 45%;height:calc(100vh - 85px);gap:0}
.preview{border:0;width:100%;height:100%;background:white}
.panel{overflow:auto;padding:16px;border-left:1px solid #334155}
.card{background:#111827;border:1px solid #334155;border-radius:14px;margin:12px 0;padding:14px}
.source{white-space:pre-wrap;background:#020617;border-radius:10px;padding:12px;margin:8px 0}
textarea{width:100%;min-height:130px;border-radius:10px;border:1px solid #475569;background:#020617;color:#e5e7eb;padding:12px}
.badge{display:inline-block;border-radius:999px;padding:3px 8px;background:#334155;margin-left:8px;font-size:12px}
.badge.missing{background:#7f1d1d}.badge.needs_review{background:#78350f}.badge.translated{background:#14532d}
.suggestion{border:1px dashed #64748b;border-radius:10px;padding:8px;margin:6px 0;background:#020617}
small{color:#94a3b8}
</style></head>
<body><header><strong>TokenMark Studio</strong>
<label>Lang <input id="lang" value="en" size="6"></label>
<label>Filter <select id="filter"><option value="">all</option><option value="missing">missing</option><option value="needs_review">needs_review</option><option value="translated">translated</option></select></label>
<select id="page"></select><button onclick="load()">Reload</button><span id="summary"></span>
</header>
<div class="layout"><iframe id="preview" class="preview"></iframe><main class="panel"><div id="app"></div></main></div>
<script>
let CATALOGS=[], CURRENT=null;
async function j(url, opts){const r=await fetch(url,opts); if(!r.ok) throw new Error(await r.text()); return await r.json();}
function statusOf(e){if(e.frozen)return "frozen"; if(e.status==="needs_review")return "needs_review"; if(e.target)return "translated"; return "missing";}
function htmlFile(source,lang){
 let norm=(source||"").replace(/\\\\/g,"/").replace(/\\/g,"/");
 norm=norm.replace(/^docs\//,"");
 let stem=norm.replace(/\.(mdx?|markdown)$/,"");
 return `/${stem}${lang && lang!=="de"? "."+lang:""}.html`;
}
async function load(){
 const lang=document.getElementById("lang").value||"en", filter=document.getElementById("filter").value;
 const stats=await j(`/__tokenmark/api/stats?lang=${encodeURIComponent(lang)}`);
 document.getElementById("summary").textContent=`${stats.total.translated} translated, ${stats.total.missing} missing, ${stats.total.needs_review} review, ${stats.total.lint_issues} lint`;
 const data=await j(`/__tokenmark/api/catalogs?lang=${encodeURIComponent(lang)}`);
 CATALOGS=data.catalogs;
 const page=document.getElementById("page");
 page.innerHTML=CATALOGS.map((c,i)=>`<option value="${i}">${c.source}</option>`).join("");
 page.onchange=()=>render();
 render();
}
function render(){
 const lang=document.getElementById("lang").value||"en", filter=document.getElementById("filter").value;
 const idx=+document.getElementById("page").value||0; const cat=CATALOGS[idx]; if(!cat)return;
 document.getElementById("preview").src=htmlFile(cat.source, lang);
 const app=document.getElementById("app"); app.innerHTML="";
 for(const e of cat.entries){
   const st=statusOf(e); if(filter && st!==filter) continue;
   const card=document.createElement("div"); card.className="card"; card.id="seg-"+e.id;
   card.innerHTML=`<div><strong>${e.kind}</strong> <code>${e.id}</code> <span class="badge ${st}">${st}</span><br><small>${cat.catalog}</small></div>
     <h3>Source</h3><div class="source"></div><h3>Target</h3><textarea></textarea>
     <div class="suggestions"></div>
     <p><button class="save">Save</button> <button class="secondary copy">Copy source</button> <button class="secondary ai">AI mock</button> <button class="secondary ai-lm">AI LM Studio</button> <button class="secondary tm">TM suggestions</button></p>`;
   card.querySelector(".source").textContent=e.source||"";
   const ta=card.querySelector("textarea"); ta.value=e.target||"";
   const save=async(status="translated")=>{await j("/__tokenmark/update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:e.id,target:ta.value,lang,status})}); e.target=ta.value; e.status=status; card.querySelector(".badge").textContent=status; liveUpdate(e.id,ta.value);};
   card.querySelector(".save").onclick=()=>save("translated");
   card.querySelector(".copy").onclick=()=>{ta.value=e.source||""; liveUpdate(e.id,ta.value)};
   card.querySelector(".ai").onclick=async()=>{const r=await j("/__tokenmark/api/translate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:e.id,lang,provider:"mock"})}); ta.value=r.target||ta.value; await save("needs_review");};
   card.querySelector(".ai-lm").onclick=async()=>{
     const btn=card.querySelector(".ai-lm"); const oldText=btn.textContent; btn.textContent="Translating..."; btn.disabled=true;
     try{
       const r=await j("/__tokenmark/api/translate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:e.id,lang,provider:"lmstudio"})});
       ta.value=r.target||ta.value; await save("needs_review");
     }catch(err){ alert("LM Studio translation failed: "+err.message); }
     finally{ btn.textContent=oldText; btn.disabled=false; }
   };
   card.querySelector(".tm").onclick=async()=>{const r=await j(`/__tokenmark/api/tm?id=${e.id}&lang=${encodeURIComponent(lang)}`); showSuggestions(card,e,r.suggestions||[]);};
   ta.oninput=()=>liveUpdate(e.id,ta.value);
   app.appendChild(card);
 }
}
function showSuggestions(card,e,sugs){
 const box=card.querySelector(".suggestions"); box.innerHTML="<h3>TM Suggestions</h3>";
 if(!sugs.length){box.innerHTML+="<small>No fuzzy matches.</small>"; return;}
 for(const s of sugs){
   const div=document.createElement("div"); div.className="suggestion";
   div.innerHTML=`<strong>${Math.round((s.score||0)*100)}%</strong><br><small>${escapeHtml(s.source||"")}</small><br>${escapeHtml(s.target||"")}<br><button class="secondary">Use</button>`;
   div.querySelector("button").onclick=()=>{card.querySelector("textarea").value=s.target||""; liveUpdate(e.id,s.target||"");};
   box.appendChild(div);
 }
}
function escapeHtml(s){return (s||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
function liveUpdate(id,text){
 const frame=document.getElementById("preview").contentWindow; if(!frame)return;
 frame.postMessage({type:"tokenmark-update",id,target:text},"*");
}
window.addEventListener("message",ev=>{
 if(!ev.data || ev.data.type!=="tokenmark-select")return;
 const el=document.getElementById("seg-"+ev.data.id); if(el){el.scrollIntoView({block:"center"}); el.style.outline="2px solid #f97316"; setTimeout(()=>el.style.outline="",1200);}
});
document.getElementById("filter").onchange=render;
load();
</script></body></html>"""

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed=urllib.parse.urlparse(self.path)
        if parsed.path=="/__tokenmark/events":
            self.send_response(200); self.send_header("Content-Type","text/event-stream"); self.send_header("Cache-Control","no-cache"); self.end_headers(); _clients.append(self.wfile)
            try:
                while True:
                    time.sleep(30); self.wfile.write(b": ping\n\n"); self.wfile.flush()
            except Exception:
                pass
            return
        if parsed.path=="/__tokenmark/studio":
            return _send_html(self, STUDIO_HTML)
        if parsed.path=="/__tokenmark/api/stats":
            q=_query(self.path); lang=(q.get("lang") or [_server_state["cfg"].get("default_lang","de")])[0]
            return _send_json(self, _stats(_server_state["root"],_server_state["cfg"],lang))
        if parsed.path=="/__tokenmark/api/catalogs":
            q=_query(self.path); lang=(q.get("lang") or [_server_state["cfg"].get("default_lang","de")])[0]
            return _send_json(self, _catalogs(_server_state["root"],_server_state["cfg"],lang))
        if parsed.path=="/__tokenmark/api/tm":
            q=_query(self.path); lang=(q.get("lang") or [_server_state["cfg"].get("default_lang","de")])[0]; token_id=(q.get("id") or [""])[0]
            source=""
            for cat in _catalogs(_server_state["root"],_server_state["cfg"],lang)["catalogs"]:
                for e in cat["entries"]:
                    if e.get("id")==token_id:
                        source=e.get("source",""); break
                if source: break
            tm_path=_server_state["root"]/_server_state["cfg"].get("tm_path","locales/tm.sqlite")
            _sync_tm_from_catalogs(_server_state["root"], _server_state["cfg"], lang)
            suggestions=fuzzy_suggestions(tm_path, source, lang, threshold=0.35, top_k=5)
            # Avoid suggesting the exact same segment back to itself when the
            # source text matches the selected token exactly.
            suggestions=[s for s in suggestions if s.get("source") != source or s.get("target")]
            return _send_json(self, {"id":token_id,"suggestions":suggestions})
        if parsed.path=="/__tokenmark/api/history":
            q=_query(self.path); lang=(q.get("lang") or [_server_state["cfg"].get("default_lang","de")])[0]; token_id=(q.get("id") or [""])[0]
            return _send_json(self, _history(_server_state["root"],_server_state["cfg"],token_id,lang))
        return super().do_GET()

    def do_POST(self):
        parsed=urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/__tokenmark/update"):
            length=int(self.headers.get("Content-Length","0") or 0)
            body=self.rfile.read(length).decode("utf-8")
            try:
                data=json.loads(body or "{}")
                ok,touched=_update_catalog_token(_server_state["root"], _server_state["cfg"], data.get("id"), data.get("target",""), data.get("lang"), data.get("status","translated"))
                if ok:
                    _server_state["rebuild"]()
                    return _send_json(self, {"ok":True,"touched":touched})
                return _send_json(self, {"ok":False,"error":"token not found"}, 404)
            except Exception as e:
                return _send_json(self, {"ok":False,"error":str(e)}, 500)
        if parsed.path.startswith("/__tokenmark/api/translate"):
            length=int(self.headers.get("Content-Length","0") or 0)
            data=json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            lang=data.get("lang") or _server_state["cfg"].get("default_lang","de")
            provider=data.get("provider","mock")
            token_id=data.get("id")
            try:
                for cat in _catalogs(_server_state["root"],_server_state["cfg"],lang)["catalogs"]:
                    entries=cat.get("entries",[])
                    for idx,e in enumerate(entries):
                        if e.get("id")==token_id:
                            if provider=="mock":
                                target=f"[{lang}] {e.get('source','')}"
                            elif provider=="lmstudio":
                                from .ai_translator import _lmstudio_translate_batch
                                prev=next((entries[j].get("source","") for j in range(idx-1,-1,-1) if not entries[j].get("frozen")), "")
                                nxt=next((entries[j].get("source","") for j in range(idx+1,len(entries)) if not entries[j].get("frozen")), "")
                                glossary_path=_server_state["root"]/_server_state["cfg"].get("glossary_path","locales/glossary.json")
                                if not glossary_path.exists():
                                    glossary_path=None
                                item={"id":e.get("id"),"source":e.get("source",""),"previous":prev,"next":nxt}
                                target=_lmstudio_translate_batch([item], lang, glossary_path=glossary_path)[0]
                            else:
                                return _send_json(self, {"ok":False,"error":f"unsupported studio provider: {provider}"}, 400)
                            return _send_json(self, {"ok":True,"id":token_id,"target":target,"status":"needs_review","provider":provider})
                return _send_json(self, {"ok":False,"error":"token not found"}, 404)
            except SystemExit as e:
                return _send_json(self, {"ok":False,"error":str(e)}, 500)
            except Exception as e:
                return _send_json(self, {"ok":False,"error":str(e)}, 500)
        self.send_response(404); self.end_headers()

def broadcast():
    for w in list(_clients):
        try: w.write(b"data: reload\n\n"); w.flush()
        except Exception:
            try: _clients.remove(w)
            except ValueError: pass

def _watch_poll(dirs, rebuild):
    seen={}
    while True:
        changed=False
        for d in dirs:
            if not d.exists(): continue
            for p in d.rglob("*"):
                if p.is_file() and p.suffix.lower() in (".md",".json",".css",".po",".xliff"):
                    m=p.stat().st_mtime
                    if seen.get(str(p))!=m:
                        if str(p) in seen: changed=True
                        seen[str(p)]=m
        if changed:
            try: rebuild()
            except Exception as e: print("[tokenmark] rebuild failed:",e)
        time.sleep(.8)

def _watch_watchdog(dirs, rebuild):
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except Exception:
        return False
    class H(FileSystemEventHandler):
        def on_any_event(self,event):
            if event.is_directory: return
            if Path(event.src_path).suffix.lower() not in (".md",".json",".css",".po",".xliff"): return
            now=time.time()
            if now - getattr(self, "_last", 0) < .25: return
            self._last=now
            try: rebuild()
            except Exception as e: print("[tokenmark] rebuild failed:",e)
    obs=Observer(); h=H()
    for d in dirs:
        if d.exists(): obs.schedule(h, str(d), recursive=True)
    obs.daemon=True; obs.start()
    return True

def serve(port=8000, inspect=False):
    root=find_project_root("."); cfg=load_config(root); build=root/cfg.get("build_dir","build")
    def rebuild():
        build_project(root,cfg,inspect=inspect,live_reload=True,force=True); broadcast()
    _server_state.update({"root":root,"cfg":cfg,"rebuild":rebuild})
    rebuild()
    dirs=[root/cfg.get("source_dir","docs"), root/cfg.get("locales_dir","locales"), root/"themes"]
    if not _watch_watchdog(dirs,rebuild):
        threading.Thread(target=_watch_poll,args=(dirs,rebuild),daemon=True).start()
    os.chdir(build)
    print(f"TokenMark server: http://127.0.0.1:{port}/")
    print(f"TokenMark Studio: http://127.0.0.1:{port}/__tokenmark/studio")
    ThreadingHTTPServer(("127.0.0.1",port),Handler).serve_forever()
