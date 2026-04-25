
from pathlib import Path
import re, json

def _token_blocks(html):
    # Lightweight static visual QA fallback. Playwright can be plugged in later,
    # but this catches the most common overflows in tables/code/inline badges.
    for m in re.finditer(r'<(?P<tag>[a-z0-9]+)[^>]*data-token="(?P<id>[^"]+)"[^>]*>(?P<body>.*?)</(?P=tag)>', html, re.I|re.S):
        text=re.sub(r"<[^>]+>", "", m.group("body"))
        text=re.sub(r"\s+", " ", text).strip()
        yield m.group("id"), m.group("tag").lower(), text

def visual_qa_html(html_path, max_table_chars=80, max_heading_chars=120):
    p=Path(html_path)
    html=p.read_text(encoding="utf-8")
    issues=[]
    for token_id, tag, text in _token_blocks(html):
        limit = max_heading_chars if tag.startswith("h") else max_table_chars if tag in ("td","th") else 240
        if len(text) > limit:
            issues.append({
                "level":"visual-warn",
                "token":token_id,
                "file":str(p),
                "message":f"Potential overflow: <{tag}> has {len(text)} visible chars (limit {limit}).",
                "text":text[:240]
            })
    return issues

def format_visual_issue(issue):
    return f"[{issue['level'].upper()}] {issue['file']} token={issue['token']}\n       {issue['message']}\n       Text: {issue['text']}"
