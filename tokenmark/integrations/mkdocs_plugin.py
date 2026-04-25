"""
Minimal MkDocs integration.

Usage in mkdocs.yml after installing TokenMark in the same environment:

plugins:
  - search
  - tokenmark:
      lang: en
      project_root: .
"""
from pathlib import Path

try:
    from mkdocs.plugins import BasePlugin
except Exception:  # MkDocs is optional
    BasePlugin = object

class TokenMarkPlugin(BasePlugin):
    def on_page_markdown(self, markdown, page, config, files):
        from tokenmark.project import load_config
        from tokenmark.compiler import compile_markdown
        from tokenmark.cli_helpers import paths_for
        from tokenmark.render_markdown import render_markdown_from_segments
        root=Path(getattr(self, "config", {}).get("project_root", ".")).resolve() if hasattr(self, "config") else Path(".").resolve()
        cfg=load_config(root)
        lang=getattr(self, "config", {}).get("lang", cfg.get("default_lang","de")) if hasattr(self, "config") else cfg.get("default_lang","de")
        src_path=Path(getattr(page.file, "abs_src_path", ""))
        if not src_path.exists():
            return markdown
        p=paths_for(root,cfg,src_path,lang)
        segs,ir=compile_markdown(src_path,p["manifest"],cfg.get("id_similarity_threshold",0.88))
        return render_markdown_from_segments(segs,p["catalog"],ir.frontmatter)
