import argparse, json
from pathlib import Path
from .project import write_default_project, find_project_root, load_config, markdown_files
from .cli_helpers import build_one, build_project, extract_one, render_one, paths_for, export_localized_markdown_tree
from .compiler import compile_markdown
from .catalog import write_catalog, write_tokens_txt, write_manifest, status_summary, load_catalog
from .adapters import import_po_to_catalog
from .qa_linter import lint_catalog, format_issue, ai_lint_catalog, fix_catalog

def _lint_project(root,cfg,lang):
    issues=[]
    for md in markdown_files(root,cfg):
        p=paths_for(root,cfg,md,lang)
        if not p["catalog"].exists():
            continue
        for issue in lint_catalog(load_catalog(p["catalog"])):
            print(f"{md.name}: {format_issue(issue)}")
            issues.append(issue)
    return issues

def main(argv=None):
    parser=argparse.ArgumentParser(prog="tokenmark",description="Markdown-first token compiler and documentation localization engine.")
    sub=parser.add_subparsers(dest="cmd",required=True)

    p=sub.add_parser("init"); p.add_argument("--force",action="store_true")
    sub.add_parser("doctor")

    p=sub.add_parser("build")
    p.add_argument("input",nargs="?"); p.add_argument("--outdir"); p.add_argument("--out"); p.add_argument("--tokens"); p.add_argument("--catalog"); p.add_argument("--ir"); p.add_argument("--manifest"); p.add_argument("--css"); p.add_argument("--fragment",action="store_true"); p.add_argument("--include-frozen",action="store_true")
    p.add_argument("--force",action="store_true",help="Ignore incremental cache for project builds.")
    p.add_argument("--dashboard",action="store_true",help="Also write build/i18n-dashboard.html for the selected/default report language.")
    p.add_argument("--no-cache",action="store_true",help="Disable incremental caching for this run.")

    p=sub.add_parser("extract"); p.add_argument("input",nargs="?"); p.add_argument("--lang"); p.add_argument("--format",choices=["json","po","xliff"],default="json")
    p=sub.add_parser("render"); p.add_argument("input",nargs="?"); p.add_argument("--lang"); p.add_argument("--format",choices=["html","markdown","pdf"],default="html"); p.add_argument("--catalog"); p.add_argument("--out")
    p=sub.add_parser("import"); p.add_argument("input"); p.add_argument("--catalog"); p.add_argument("--lang")
    p=sub.add_parser("status"); p.add_argument("--lang")
    p=sub.add_parser("check"); p.add_argument("--lang"); p.add_argument("--strict",action="store_true"); p.add_argument("--lint",action="store_true",help="Also validate Markdown structure in translated targets.")
    p=sub.add_parser("lint"); p.add_argument("--lang"); p.add_argument("--strict",action="store_true"); p.add_argument("--ai",action="store_true"); p.add_argument("--styleguide"); p.add_argument("--provider",default="heuristic"); p.add_argument("--fix",action="store_true",help="Apply deterministic Markdown/placeholder safety fixes to catalogs.")
    p=sub.add_parser("auto-translate")
    p.add_argument("--lang",required=True); p.add_argument("--provider",default="mock",choices=["mock","identity","deepl","openai","gemini","lmstudio"]); p.add_argument("input",nargs="?")
    p.add_argument("--glossary",help="Glossary path. Defaults to config glossary_path.")
    p.add_argument("--batch-size",type=int,default=20); p.add_argument("--ci",action="store_true",help="Commit updated locales in CI if git is available.")
    p=sub.add_parser("export-ssg"); p.add_argument("--lang",required=True); p.add_argument("--outdir",help="Output localized Markdown tree for MkDocs/Docusaurus/Hugo.")
    p=sub.add_parser("tm-suggest"); p.add_argument("text"); p.add_argument("--lang"); p.add_argument("--threshold",type=float,default=0.55); p.add_argument("--mode",choices=["hybrid","vector","semantic","lexical"],default="hybrid")
    p=sub.add_parser("tm-migrate"); p.add_argument("--from-json",dest="from_json"); p.add_argument("--lang")
    p=sub.add_parser("tm-backfill"); p.add_argument("--lang", help="Optional locale to import before backfilling. Defaults to all locale catalogs.")
    p=sub.add_parser("tm-history"); p.add_argument("--lang"); p.add_argument("--id"); p.add_argument("--limit",type=int,default=8)
    p=sub.add_parser("extract-terms"); p.add_argument("--min-freq",type=int,default=5); p.add_argument("--limit",type=int,default=80); p.add_argument("--merge",action="store_true")
    p=sub.add_parser("dashboard"); p.add_argument("--lang"); p.add_argument("--out")
    p=sub.add_parser("ci-report"); p.add_argument("--lang"); p.add_argument("--base")
    p=sub.add_parser("ci"); p.add_argument("--lang"); p.add_argument("--base"); p.add_argument("--provider",default="mock"); p.add_argument("--commit",action="store_true")
    p=sub.add_parser("visual-qa"); p.add_argument("--lang"); p.add_argument("--strict",action="store_true")
    p=sub.add_parser("sync-branches"); p.add_argument("--from",dest="from_branch",required=True); p.add_argument("--to",dest="to_branch"); p.add_argument("--lang",required=True); p.add_argument("--dry-run",action="store_true")
    p=sub.add_parser("compose")
    p.add_argument("input", help="Unstructured notes file (.md/.txt) to synthesize into controlled Markdown documentation.")
    p.add_argument("--outdir", default="docs/generated", help="Output directory for generated Markdown modules.")
    p.add_argument("--provider", choices=["heuristic","offline","lmstudio","gemini","openai"], default="heuristic", help="Planner provider. heuristic/offline is deterministic and local.")
    p.add_argument("--type", dest="doc_type", default="technical-guide", help="Target documentation type, e.g. technical-guide, whitepaper, runbook, api-guide.")
    p.add_argument("--audience", default="developers", help="Target audience for the documentation plan.")
    p.add_argument("--title", help="Optional title override.")
    p.add_argument("--single", action="store_true", help="Write one generated.md instead of modular files.")
    p.add_argument("--no-trace", action="store_true", help="Do not include traceability sections in generated Markdown.")
    p.add_argument("--build", action="store_true", help="Run tokenmark build after writing generated Markdown.")
    p=sub.add_parser("serve"); p.add_argument("--port",type=int,default=8000); p.add_argument("--inspect",action="store_true"); p.add_argument("--fastapi",action="store_true",help="Use optional FastAPI/WebSocket collaborative server.")

    args=parser.parse_args(argv)
    root=find_project_root("."); cfg=load_config(root); lang=getattr(args,"lang",None) or cfg.get("default_lang","de")

    if args.cmd=="init":
        write_default_project(root,args.force); print("TokenMark project initialized."); return

    if args.cmd=="doctor":
        try:
            from . import __version__ as pkg_version
        except Exception:
            pkg_version = cfg.get("version")
        print(f"root: {root}")
        print(f"version: {pkg_version}")
        if str(cfg.get("version")) != str(pkg_version):
            print(f"config_version: {cfg.get('version')}")
        print(f"docs: {len(markdown_files(root,cfg))}")
        print(f"glossary: {root/cfg.get('glossary_path','locales/glossary.json')}")
        print(f"incremental: {cfg.get('incremental', True)}")
        print(f"tm: {root/cfg.get('tm_path','locales/tm.sqlite')} ({cfg.get('tm_backend','json')})")
        return

    if args.cmd=="build":
        if args.no_cache:
            cfg={**cfg,"incremental":False}
        if args.input:
            md=Path(args.input); md=md if md.is_absolute() else root/md
            if args.out or args.tokens or args.catalog or args.ir or args.manifest:
                segs,ir=compile_markdown(md,args.manifest,cfg.get("id_similarity_threshold",0.88))
                if args.tokens: write_tokens_txt(args.tokens,segs)
                if args.catalog: write_catalog(args.catalog,str(md),segs,args.include_frozen)
                if args.manifest: write_manifest(args.manifest,str(md),segs)
                if args.ir:
                    Path(args.ir).parent.mkdir(parents=True,exist_ok=True); Path(args.ir).write_text(json.dumps(ir.to_dict(),indent=2,ensure_ascii=False),encoding="utf-8")
                if args.out:
                    from .render_html import render_html_from_segments
                    Path(args.out).parent.mkdir(parents=True,exist_ok=True); Path(args.out).write_text(render_html_from_segments(md,segs,css_path=args.css,fragment=args.fragment),encoding="utf-8")
            else:
                print(f"built {build_one(root,cfg,md,args.outdir)['html']}")
        else:
            res=build_project(root,cfg,force=args.force)
            print(f"project built: {len(res['built'])} built, {len(res['skipped'])} skipped")
            if args.dashboard:
                from .analytics import render_dashboard
                out = root/cfg.get("build_dir","build")/"i18n-dashboard.html"
                render_dashboard(root,cfg,lang,out)
                print(f"dashboard written: {out}")
        return

    if args.cmd=="extract":
        inputs=[Path(args.input)] if args.input else markdown_files(root,cfg)
        for md in inputs:
            md=md if md.is_absolute() else root/md
            p=extract_one(root,cfg,md,lang,args.format)
            artifact=p["catalog"] if args.format=="json" else p[args.format]
            print(f"extracted {artifact}")
        return

    if args.cmd=="render":
        inputs=[Path(args.input)] if args.input else markdown_files(root,cfg)
        for md in inputs:
            md=md if md.is_absolute() else root/md; out=render_one(root,cfg,md,lang,args.format,args.catalog)
            if args.out and len(inputs)==1:
                Path(args.out).parent.mkdir(parents=True,exist_ok=True)
                if args.format=="pdf":
                    import shutil; shutil.copy2(out,args.out)
                else:
                    Path(args.out).write_text(Path(out).read_text(encoding="utf-8"),encoding="utf-8")
                print(f"rendered {args.out}")
            else:
                print(f"rendered {out}")
        return

    if args.cmd=="import":
        po=Path(args.input); cat=Path(args.catalog) if args.catalog else root/cfg.get("locales_dir","locales")/lang/f"{po.stem}.catalog.json"; import_po_to_catalog(po,cat); print(f"imported {po} -> {cat}"); return

    if args.cmd in ("status","check"):
        bad=False
        for md in markdown_files(root,cfg):
            p=paths_for(root,cfg,md,lang)
            if not p["catalog"].exists(): print(f"{md.name}: catalog missing"); bad=True; continue
            s=status_summary(p["catalog"]); print(f"{md.name}: {s['translated']} translated, {s['missing']} missing, {s['needs_review']} needs_review, {s['frozen']} frozen, {s['total']} total")
            if s["missing"] or s["needs_review"]: bad=True
        issues=[]
        if args.cmd=="check" and args.lint:
            issues=_lint_project(root,cfg,lang)
            if issues: bad=True
        if args.cmd=="check" and args.strict and bad:
            print("check failed: missing, stale or structurally invalid translations found")
            raise SystemExit(1)
        if args.cmd=="check":
            print("check passed")
        return

    if args.cmd=="lint":
        issues=[]
        fixed_total=0
        for md in markdown_files(root,cfg):
            p=paths_for(root,cfg,md,lang)
            if not p["catalog"].exists():
                continue
            cat=load_catalog(p["catalog"])
            if args.fix:
                cat, fixed = fix_catalog(cat)
                if fixed:
                    p["catalog"].write_text(json.dumps(cat,indent=2,ensure_ascii=False),encoding="utf-8")
                    fixed_total += len(fixed)
                    for item in fixed:
                        print(f"{md.name}: fixed token={item['id']} ({'; '.join(item['notes'])})")
            for issue in lint_catalog(cat):
                print(f"{md.name}: {format_issue(issue)}")
                issues.append(issue)
        if args.ai:
            for md in markdown_files(root,cfg):
                p=paths_for(root,cfg,md,lang)
                if p["catalog"].exists():
                    for issue in ai_lint_catalog(load_catalog(p["catalog"]), styleguide_path=args.styleguide, glossary_path=root/cfg.get("glossary_path","locales/glossary.json"), provider=args.provider):
                        print(f"{md.name}: {format_issue(issue)}")
                        issues.append(issue)
        print(f"lint: {len(issues)} issue(s), fixed: {fixed_total}")
        if args.strict and issues:
            raise SystemExit(1)
        return

    if args.cmd=="auto-translate":
        from .ai_translator import auto_translate_catalog
        inputs=[Path(args.input)] if args.input else markdown_files(root,cfg)
        total=0
        glossary_path=Path(args.glossary) if args.glossary else root/cfg.get("glossary_path","locales/glossary.json")
        if not glossary_path.is_absolute(): glossary_path=root/glossary_path
        for md in inputs:
            md=md if md.is_absolute() else root/md
            p=paths_for(root,cfg,md,args.lang)
            if not p["catalog"].exists():
                extract_one(root,cfg,md,args.lang,"json")
            n=auto_translate_catalog(p["catalog"], args.lang, args.provider, root/cfg.get("tm_path","locales/tm.sqlite"), glossary_path=glossary_path, batch_size=args.batch_size)
            total += n
            print(f"auto-translated {n} segments in {p['catalog']}")
        print(f"auto-translate complete: {total} segments marked needs_review")
        if args.ci:
            from .git_ci import git_commit_locales
            committed=git_commit_locales(root)
            print("ci commit created" if committed else "ci commit skipped: no locale changes")
        return

    if args.cmd=="export-ssg":
        written=export_localized_markdown_tree(root,cfg,args.lang,args.outdir)
        print(f"exported {len(written)} localized Markdown file(s)")
        for p in written:
            print(p)
        return


    if args.cmd=="tm-suggest":
        from .tm import fuzzy_suggestions
        tm_path=root/cfg.get("tm_path","locales/tm.sqlite")
        for s in fuzzy_suggestions(tm_path,args.text,lang,args.threshold,5,args.mode):
            extra=f" semantic={int(s.get('semantic_score',0)*100)}% lexical={int(s.get('lexical_score',0)*100)}%" if "semantic_score" in s else ""
            print(f"{int(s['score']*100)}%{extra} | {s['source']} -> {s['target']}")
        return

    if args.cmd=="tm-migrate":
        from .tm_sqlite import migrate_json
        src=Path(args.from_json) if args.from_json else root/cfg.get("tm_json_path","locales/tm.json")
        dst=root/cfg.get("tm_path","locales/tm.sqlite")
        n=migrate_json(src,dst,lang)
        print(f"migrated {n} TM entries: {src} -> {dst}")
        return

    if args.cmd=="tm-backfill":
        from .tm_sqlite import backfill_embeddings
        from .tm import update_tm
        from .models import Segment
        from .catalog import load_catalog
        dst=root/cfg.get("tm_path","locales/tm.sqlite")
        locales_dir=root/cfg.get("locales_dir","locales")
        imported=0
        wanted_lang=getattr(args, "lang", None)
        catalog_paths=[]
        if locales_dir.exists():
            for cat in sorted(locales_dir.rglob("*.catalog.json")):
                cat_lang=cat.parent.name
                if wanted_lang and cat_lang != wanted_lang:
                    continue
                catalog_paths.append((cat, cat_lang))
        for cat, cat_lang in catalog_paths:
            try:
                data=load_catalog(cat)
                segs=[]
                for e in data.get("entries",[]):
                    if e.get("frozen") or not e.get("source") or not e.get("target"):
                        continue
                    segs.append(Segment(
                        e.get("id",""),
                        e.get("kind",""),
                        e.get("source",""),
                        e.get("target",""),
                        bool(e.get("frozen",False)),
                        e.get("fingerprint",""),
                        e.get("status","needs_review"),
                        e.get("meta") or {},
                    ))
                if segs:
                    update_tm(segs, dst, cat_lang)
                    imported += len(segs)
            except Exception as exc:
                print(f"tm-backfill: skipped {cat}: {exc}")
        n=backfill_embeddings(dst)
        print(f"tm-backfill: imported {imported} translated catalog segment(s) into {dst}")
        print(f"backfilled {n} semantic TM embedding(s) in {dst}")
        return

    if args.cmd=="visual-qa":
        from .visual_qa import visual_qa_html, format_visual_issue
        issues=[]
        build=root/cfg.get("build_dir","build")
        for html in sorted(build.glob("*.html")):
            issues.extend(visual_qa_html(html))
        for issue in issues:
            print(format_visual_issue(issue))
        print(f"visual-qa: {len(issues)} issue(s)")
        if args.strict and issues:
            raise SystemExit(1)
        return

    if args.cmd=="sync-branches":
        from .git_ci import sync_branches
        result=sync_branches(root,cfg,args.from_branch,args.to_branch,args.lang,args.dry_run)
        print(f"sync-branches: {result['updated']} updated, {result['candidates']} candidates, lang={args.lang}")
        for line in result.get("messages",[]):
            print(line)
        return

    if args.cmd=="tm-history":
        from . import tm_sqlite
        dst=root/cfg.get("tm_path","locales/tm.sqlite")
        con=tm_sqlite.connect(dst)
        try:
            rows=tm_sqlite.history(con, segment_id=args.id, lang=lang, limit=args.limit)
        finally:
            con.close()
        for r in rows:
            print(f"{r.get('id')} | {r.get('author')} | {r.get('status')} | {r.get('target')}")
        return

    if args.cmd=="extract-terms":
        from .term_extractor import extract_terms_from_project, merge_terms_into_glossary
        terms=extract_terms_from_project(root,cfg,args.min_freq,args.limit)
        for term,score in terms:
            print(f"{score}\t{term}")
        if args.merge:
            gp=root/cfg.get("glossary_path","locales/glossary.json")
            added=merge_terms_into_glossary(gp, terms)
            print(f"merged {added} candidate term(s) into {gp}")
        return

    if args.cmd=="dashboard":
        from .analytics import render_dashboard
        out=Path(args.out) if args.out else root/cfg.get("build_dir","build")/"i18n-dashboard.html"
        if not out.is_absolute(): out=root/out
        render_dashboard(root,cfg,lang,out)
        print(f"dashboard written: {out}")
        return

    if args.cmd=="ci-report":
        from .git_ci import ci_report
        print(ci_report(root,cfg,lang,args.base or cfg.get("ci_base","origin/main")))
        return

    if args.cmd=="ci":
        from .git_ci import ci_report, git_commit_locales
        # Extract catalogs for changed files, auto-translate gaps, then print a PR-ready Markdown report.
        from .git_ci import changed_markdown_files
        files=changed_markdown_files(root,cfg,args.base or cfg.get("ci_base","origin/main")) or markdown_files(root,cfg)
        from .ai_translator import auto_translate_catalog
        for md in files:
            p=paths_for(root,cfg,md,lang)
            if not p["catalog"].exists(): extract_one(root,cfg,md,lang,"json")
            auto_translate_catalog(p["catalog"], lang, args.provider, root/cfg.get("tm_path","locales/tm.sqlite"), glossary_path=root/cfg.get("glossary_path","locales/glossary.json"))
        print(ci_report(root,cfg,lang,args.base or cfg.get("ci_base","origin/main")))
        if args.commit:
            committed=git_commit_locales(root)
            print("ci commit created" if committed else "ci commit skipped: no locale changes")
        return

    if args.cmd=="compose":
        from .compose import compose_file
        inp=Path(args.input)
        if not inp.is_absolute():
            inp=root/inp
        outdir=Path(args.outdir)
        if not outdir.is_absolute():
            outdir=root/outdir
        result=compose_file(
            inp,
            outdir,
            provider=args.provider,
            doc_type=args.doc_type,
            audience=args.audience,
            title=args.title,
            single=args.single,
            include_trace=not args.no_trace,
            build_dir=root/cfg.get("build_dir","build"),
        )
        print(f"compose: generated {len(result['generated'])} Markdown file(s)")
        for pth in result["generated"]:
            print(pth)
        print(f"intent graph: {result['intent']}")
        print(f"trace: {result['trace']}")
        print(f"open questions: {result['open_questions']}")
        if result.get("graph",{}).get("provider_error"):
            print(f"compose provider fallback: {result['graph']['provider_error']}")
        if args.build:
            # Generated docs are only included in project builds if they are under docs_dir and match the configured patterns.
            res=build_project(root,cfg,force=True)
            print(f"project built: {len(res['built'])} built, {len(res['skipped'])} skipped")
        return

    if args.cmd=="serve":
        if args.fastapi:
            from .server_fastapi import serve_fastapi
            serve_fastapi(args.port,args.inspect)
        else:
            from .server import serve
            serve(args.port,args.inspect)
        return

if __name__=="__main__":
    main()
