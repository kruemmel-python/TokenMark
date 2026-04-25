import html

def pre_render_segment(segment, **kwargs):
    if segment.kind == "code_block" and (segment.meta or {}).get("lang", "").strip() == "mermaid":
        segment.kind = "html_block"
        segment.frozen = True
        source = segment.target or segment.source
        segment.target = f'<div class="mermaid" data-token="{html.escape(segment.id)}">{html.escape(source)}</div>'
    return segment

def register(pm):
    pm.register("pre_render_segment", pre_render_segment)
