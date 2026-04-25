
import json, subprocess
from pathlib import Path
from .project import markdown_files
from .cli_helpers import paths_for
from .catalog import status_summary, load_catalog

def _run(args, cwd):
    try:
        return subprocess.check_output(args, cwd=str(cwd), text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def changed_markdown_files(root, cfg, base="origin/main"):
    out=_run(["git","diff","--name-only",f"{base}...HEAD"], root)
    if not out:
        return []
    files=[]
    src=(Path(root)/cfg.get("source_dir","docs")).resolve()
    for line in out.splitlines():
        p=(Path(root)/line).resolve()
        if p.suffix.lower() in (".md",".mdx") and src in [p,*p.parents] and p.exists():
            files.append(p)
    return files

def ci_report(root, cfg, lang, base="origin/main"):
    changed=changed_markdown_files(root,cfg,base) or markdown_files(root,cfg)
    lines=[f"# TokenMark localization report ({lang})",""]
    total={"translated":0,"missing":0,"needs_review":0,"frozen":0,"total":0}
    for md in changed:
        p=paths_for(Path(root),cfg,md,lang)
        if not p["catalog"].exists():
            lines.append(f"- `{md.relative_to(root)}`: catalog missing")
            total["missing"]+=1; continue
        s=status_summary(p["catalog"])
        for k in total: total[k]+=s.get(k,0)
        lines.append(f"- `{md.relative_to(root)}`: {s['translated']} translated, {s['missing']} missing, {s['needs_review']} needs_review, {s['total']} total")
    lines += ["", f"**Summary:** {total['translated']} translated, {total['missing']} missing, {total['needs_review']} needs_review, {total['total']} total."]
    return "\n".join(lines)

def git_commit_locales(root, message="chore(i18n): auto-translate [skip ci]"):
    _run(["git","add","locales"], root)
    status=_run(["git","status","--porcelain","locales"], root)
    if not status:
        return False
    subprocess.check_call(["git","commit","-m",message], cwd=str(root))
    return True


def _git_json(root, branch, relpath):
    data=_run(["git","show",f"{branch}:{relpath}"], root)
    if not data:
        return None
    try:
        return json.loads(data)
    except Exception:
        return None

def _catalog_relpaths(root, cfg, lang):
    loc=Path(cfg.get("locales_dir","locales"))/lang
    base=Path(root)/loc
    if not base.exists():
        return []
    return [str((loc/p.name).as_posix()) for p in sorted(base.glob("*.catalog.json"))]

def sync_branches(root, cfg, from_branch, to_branch, lang, dry_run=False):
    """Copy exact fingerprint translation matches across git branches.

    Current working tree is treated as the target branch unless --to is provided.
    The function never fuzzy-matches: only identical source fingerprints are reused.
    """
    root=Path(root)
    messages=[]
    updated=0
    candidates=0
    rels=_catalog_relpaths(root,cfg,lang)
    if not rels:
        # Fall back to known markdown files: current branch may not have catalogs yet.
        rels=[str((Path(cfg.get("locales_dir","locales"))/lang/f"{md.stem}.catalog.json").as_posix()) for md in markdown_files(root,cfg)]
    for rel in rels:
        src_data=_git_json(root, from_branch, rel)
        if not src_data:
            continue
        src_by_fp={}
        for e in src_data.get("entries",[]):
            if e.get("fingerprint") and e.get("target") and e.get("status") in ("translated","needs_review"):
                src_by_fp[e["fingerprint"]]=e
        target_path=root/rel
        if not target_path.exists():
            continue
        try:
            tgt_data=json.loads(target_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        changed=False
        for e in tgt_data.get("entries",[]):
            if e.get("frozen") or e.get("target"):
                continue
            hit=src_by_fp.get(e.get("fingerprint"))
            if hit:
                candidates+=1
                if not dry_run:
                    e["target"]=hit.get("target","")
                    e["status"]="translated"
                    meta=e.setdefault("meta",{})
                    meta["synced_from_branch"]=from_branch
                    meta["synced_from_id"]=hit.get("id")
                    changed=True
                    updated+=1
                messages.append(f"{rel}: {e.get('id')} <= {from_branch}:{hit.get('id')}")
        if changed:
            target_path.write_text(json.dumps(tgt_data, indent=2, ensure_ascii=False), encoding="utf-8")
    if to_branch and not dry_run:
        messages.append("note: --to is recorded for CI logs; TokenMark updates the current working tree. Checkout the target branch before running for safest results.")
    return {"updated":updated,"candidates":candidates,"messages":messages}
