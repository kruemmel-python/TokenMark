from pathlib import Path
from .render_html import render_html_from_segments

PRINT_CSS = """
@page { size: A4; margin: 22mm 18mm; @bottom-center { content: counter(page); } }
body { max-width: none !important; margin: 0 !important; }
.tm-sidebar,.tm-toc,.tm-search,script { display: none !important; }
pre, blockquote, table { break-inside: avoid; }
h1,h2,h3 { break-after: avoid; }
"""

def render_pdf(md_path, segs, catalog_path=None, css_path=None, out_path=None, config=None, root=None):
    try:
        from weasyprint import HTML, CSS
    except Exception as e:
        raise SystemExit("PDF rendering requires WeasyPrint. Install with: python -m pip install -e .[pdf]") from e
    html_str=render_html_from_segments(md_path,segs,catalog_path,css_path=css_path,config=config,root=root)
    pdf=HTML(string=html_str, base_url=str(Path(md_path).parent)).render(stylesheets=[CSS(string=PRINT_CSS)])
    if not out_path:
        out_path=Path(md_path).with_suffix(".pdf")
    Path(out_path).parent.mkdir(parents=True,exist_ok=True)
    pdf.write_pdf(str(out_path))
    return Path(out_path)
