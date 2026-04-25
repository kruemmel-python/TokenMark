import html
from pathlib import Path
from markdown_it import MarkdownIt
from .catalog import catalog_targets
from .hooks import load_plugin_manager

def md_inline(text):
    return MarkdownIt("commonmark", {"html": True}).renderInline(text or "")

INSPECT_SCRIPT = """<script>
document.addEventListener("click", async e=>{
  const el=e.target.closest("[data-token]");
  if(!el || !document.body.classList.contains("tokenmark-inspect")) return;
  e.preventDefault();
  const tokenId=el.dataset.token;
  const current=el.innerText || el.textContent || "";
  const next=prompt("TokenMark Übersetzung für "+tokenId+":", current);
  if(next===null) return;
  try{
    await fetch("/__tokenmark/update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:tokenId,target:next})});
    location.reload();
  }catch(err){
    navigator.clipboard?.writeText(tokenId);
    console.log("TokenMark token:",tokenId,err);
  }
});
</script>"""

STUDIO_PREVIEW_SCRIPT = """<script>
window.addEventListener("message", ev=>{
  if(!ev.data || ev.data.type!=="tokenmark-update") return;
  const el=document.querySelector(`[data-token="${ev.data.id}"]`);
  if(el) el.innerHTML=ev.data.target;
});
document.addEventListener("click", e=>{
  const el=e.target.closest("[data-token]");
  if(el && window.parent && window.parent!==window){
    window.parent.postMessage({type:"tokenmark-select", id:el.dataset.token}, "*");
  }
});
</script>"""
LIVE_RELOAD_SCRIPT='<script>try{const es=new EventSource("/__tokenmark/events");es.onmessage=e=>{if(e.data==="reload")location.reload()}}catch(e){console.warn(e)}</script>'

def render_html_from_segments(source_path, segs, catalog_path=None, css_path=None, fragment=False, inspect=False, live_reload=False, config=None, root=None):
    config=config or {}
    root=Path(root) if root else Path(source_path).parent
    pm=load_plugin_manager(config)
    targets=catalog_targets(catalog_path) if catalog_path else {}
    parts=[]
    in_list=False
    table=[]

    def close_list():
        nonlocal in_list
        if in_list:
            parts.append("</ul>")
            in_list=False

    def flush_table():
        nonlocal table
        if not table:
            return
        close_list()
        parts.append("<table><tbody>")
        for i in range(0,len(table),2):
            parts.append("<tr>"+"".join(f'<td data-token="{html.escape(tid)}">{md_inline(val)}</td>' for tid,val in table[i:i+2])+"</tr>")
        parts.append("</tbody></table>")
        table=[]

    for original in segs:
        s=pm.mutate_segment(original, source_path=source_path, config=config)
        txt=targets.get(s.id) or s.target or s.source
        data=f' data-token="{html.escape(s.id)}"'

        if s.kind=="table_cell":
            table.append((s.id,txt))
            continue
        else:
            flush_table()

        if s.kind=="list_item":
            if not in_list:
                parts.append("<ul>")
                in_list=True
            parts.append(f"<li{data}>{md_inline(txt)}</li>")
            continue

        close_list()

        if s.kind=="heading":
            lvl=(s.meta or {}).get("level",1)
            parts.append(f'<h{lvl} id="{html.escape(s.id)}"{data}>{md_inline(txt)}</h{lvl}>')
        elif s.kind=="paragraph":
            parts.append(f"<p{data}>{md_inline(txt)}</p>")
        elif s.kind=="blockquote":
            parts.append(f"<blockquote{data}>{md_inline(txt)}</blockquote>")
        elif s.kind=="code_block":
            lang=(s.meta or {}).get("lang","")
            parts.append(f'<pre{data}><code class="language-{html.escape(lang)}">{html.escape(txt)}</code></pre>')
        elif s.kind in ("image_alt","link_text","jsx_prop","jsx_child"):
            parts.append(f"<span hidden{data}>{html.escape(txt)}</span>")
        elif s.kind=="admonition_title":
            typ=html.escape((s.meta or {}).get("admonition_type","note"))
            parts.append(f'<div class="tokenmark-admonition tokenmark-admonition-{typ}"><div class="tokenmark-admonition-title"{data}>{md_inline(txt)}</div>')
        elif s.kind=="admonition_body":
            parts.append(f'<div class="tokenmark-admonition-body"{data}>{md_inline(txt)}</div></div>')
        elif s.kind=="html_block":
            parts.append(txt)

    flush_table()
    close_list()
    content="\n".join(parts)
    if fragment:
        return content
    css=Path(css_path).read_text(encoding="utf-8") if css_path and Path(css_path).exists() else ""
    site_bits=""
    if config.get("site", True):
        try:
            from .site import nav_html, toc_html, search_html
            site_bits = nav_html(root, config) + search_html()
            toc = toc_html(segs)
            content = f'<main class="tm-content">{content}</main>{toc}'
        except Exception:
            content = f'<main class="tm-content">{content}</main>'
    body_class="tokenmark-inspect" if inspect else ""
    html_doc = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>{css}</style></head><body class="{body_class}">
{site_bits}
{content}
{STUDIO_PREVIEW_SCRIPT}{INSPECT_SCRIPT if inspect else ""}{LIVE_RELOAD_SCRIPT if live_reload else ""}</body></html>
"""
    out=pm.call("post_render", html_doc, source_path=source_path, config=config)
    return out if out is not None else html_doc
