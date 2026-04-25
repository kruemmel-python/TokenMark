
"""Optional FastAPI/WebSocket server for collaborative TokenMark Studio.

Run with:
    tokenmark serve --fastapi --port 8000

The classic stdlib server remains the default so TokenMark has no mandatory web
dependencies. This module is loaded only when requested and requires:
    pip install -e ".[server]"
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Set
from .project import find_project_root, load_config
from .cli_helpers import build_project
from .server import STUDIO_HTML, _stats, _catalogs, _update_catalog_token, _history
from .tm import fuzzy_suggestions

_connections: Set[object] = set()
_editing: Dict[str, str] = {}

async def broadcast(payload: dict):
    dead=[]
    for ws in list(_connections):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections.discard(ws)

def make_app(inspect=False):
    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
        from fastapi.staticfiles import StaticFiles
    except Exception as exc:
        raise RuntimeError("FastAPI server requires: pip install -e '.[server]'") from exc

    root=find_project_root(".")
    cfg=load_config(root)
    build=root/cfg.get("build_dir","build")
    build_project(root,cfg,inspect=inspect,live_reload=True,force=True)

    app=FastAPI(title="TokenMark Studio")
    app.mount("/_assets", StaticFiles(directory=str(build)), name="assets")

    @app.get("/__tokenmark/studio")
    async def studio():
        extra = """
<script>
let TM_WS=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/__tokenmark/ws');
TM_WS.onmessage=(ev)=>{try{const m=JSON.parse(ev.data); if(m.type==='saved'){console.log('remote save',m.id)} if(m.type==='editing'){document.querySelector('#seg-'+m.id)?.classList.add('remote-editing')}}catch(e){}};
document.addEventListener('input', e=>{const card=e.target.closest('.card'); if(card && TM_WS.readyState===1) TM_WS.send(JSON.stringify({type:'editing', id:card.id.replace('seg-','')}));}, true);
</script>"""
        return HTMLResponse(STUDIO_HTML.replace("</body>", extra+"</body>"))

    @app.get("/__tokenmark/api/stats")
    async def stats(lang: str | None = None):
        return _stats(root,cfg,lang or cfg.get("default_lang","de"))

    @app.get("/__tokenmark/api/catalogs")
    async def catalogs(lang: str | None = None):
        return _catalogs(root,cfg,lang or cfg.get("default_lang","de"))

    @app.get("/__tokenmark/api/tm")
    async def tm(id: str, lang: str | None = None):
        lang=lang or cfg.get("default_lang","de")
        source=""
        for cat in _catalogs(root,cfg,lang)["catalogs"]:
            for e in cat["entries"]:
                if e.get("id")==id:
                    source=e.get("source",""); break
            if source: break
        return {"id":id,"suggestions":fuzzy_suggestions(root/cfg.get("tm_path","locales/tm.sqlite"), source, lang, threshold=0.55, top_k=5)}

    @app.get("/__tokenmark/api/history")
    async def history(id: str, lang: str | None = None):
        return _history(root,cfg,id,lang or cfg.get("default_lang","de"))

    @app.post("/__tokenmark/update")
    async def update(data: dict):
        ok,touched=_update_catalog_token(root,cfg,data.get("id"),data.get("target",""),data.get("lang"),data.get("status","translated"))
        if ok:
            build_project(root,cfg,inspect=inspect,live_reload=True,force=True)
            await broadcast({"type":"saved","id":data.get("id"),"target":data.get("target","")})
            return {"ok":True,"touched":touched}
        return JSONResponse({"ok":False,"error":"token not found"}, status_code=404)

    @app.post("/__tokenmark/api/translate")
    async def translate(data: dict):
        lang=data.get("lang") or cfg.get("default_lang","de")
        token_id=data.get("id")
        for cat in _catalogs(root,cfg,lang)["catalogs"]:
            for e in cat["entries"]:
                if e.get("id")==token_id:
                    return {"ok":True,"id":token_id,"target":f"[{lang}] {e.get('source','')}","status":"needs_review"}
        return JSONResponse({"ok":False,"error":"token not found"}, status_code=404)

    @app.websocket("/__tokenmark/ws")
    async def ws(websocket: WebSocket):
        await websocket.accept()
        _connections.add(websocket)
        try:
            while True:
                msg=await websocket.receive_json()
                if msg.get("type")=="editing":
                    _editing[msg.get("id","")]=msg.get("user","anonymous")
                    await broadcast({"type":"editing","id":msg.get("id"),"user":msg.get("user","anonymous")})
        except WebSocketDisconnect:
            _connections.discard(websocket)

    @app.get("/{path:path}")
    async def static(path: str):
        p=(build/path).resolve()
        if p.is_dir():
            p=p/"index.html"
        if p.exists() and build.resolve() in [p, *p.parents]:
            return FileResponse(str(p))
        return JSONResponse({"detail":"Not found"}, status_code=404)

    return app

def serve_fastapi(port=8000, inspect=False):
    import uvicorn
    uvicorn.run(make_app(inspect=inspect), host="127.0.0.1", port=port)
