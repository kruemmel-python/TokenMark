from .catalog import catalog_targets

def render_markdown_from_segments(segs, catalog_path=None, frontmatter=""):
    targets=catalog_targets(catalog_path) if catalog_path else {}
    out=[]
    table=[]
    list_open=False

    def blank():
        if out and out[-1]!="":
            out.append("")

    def flush_table():
        nonlocal table
        if not table:
            return
        blank()
        cols=2
        out.append("| "+" | ".join(table[:cols])+" |")
        out.append("| "+" | ".join(["---"]*cols)+" |")
        for i in range(cols,len(table),cols):
            out.append("| "+" | ".join(table[i:i+cols])+" |")
        out.append("")
        table=[]

    def close_list():
        nonlocal list_open
        if list_open:
            blank()
            list_open=False

    if frontmatter:
        out += [frontmatter.rstrip(), ""]

    for s in segs:
        txt=targets.get(s.id) or s.target or s.source

        if s.kind=="table_cell":
            close_list()
            table.append(txt)
            continue
        else:
            flush_table()

        if s.kind=="list_item":
            out.append("- "+txt.replace("\n","\n  "))
            list_open=True
            continue
        else:
            close_list()

        if s.kind=="heading":
            out += ["#"*(s.meta or {}).get("level",1)+" "+txt, ""]
        elif s.kind=="paragraph":
            out += [txt, ""]
        elif s.kind=="blockquote":
            out += ["> "+line for line in txt.splitlines()] + [""]
        elif s.kind=="code_block":
            out += ["```"+(s.meta or {}).get("lang",""), txt.rstrip("\n"), "```", ""]
        elif s.kind=="html_block":
            out += [txt, ""]
        elif s.kind in ("image_alt","link_text","jsx_prop","jsx_child"):
            # These are semantic helper segments. The surrounding paragraph keeps the Markdown syntax.
            continue
        elif s.kind=="admonition_title":
            out.append(f"::: {(s.meta or {}).get('admonition_type','note')} {txt}")
        elif s.kind=="admonition_body":
            out += [txt, ":::", ""]

    flush_table()
    close_list()
    return "\n".join(out).rstrip()+"\n"
