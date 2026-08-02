"""Command-line interface for the evidence-first article pipeline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .archive import create_archive
from .fingerprint import compare_text, fingerprint_text
from .links import audit_links
from .linting import check_fabrication, count_words, measure_distinctness, scan_em_dashes
from .project import initialize_project, validate_project


def _emit(payload, output: str | None = None) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    if output:
        Path(output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="article-pipeline", description="Evidence-first technical article production tools")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a complete article-package template")
    init.add_argument("path")
    init.add_argument("--force", action="store_true")

    validate = sub.add_parser("validate", help="validate package structure and release readiness")
    validate.add_argument("path")
    validate.add_argument("--strict", action="store_true")
    validate.add_argument("--json-out")

    fingerprint = sub.add_parser("fingerprint", help="record protected evidence surfaces")
    fingerprint.add_argument("article")
    fingerprint.add_argument("--json-out")

    compare = sub.add_parser("compare", help="compare a revised draft with its evidence-locked master")
    compare.add_argument("master")
    compare.add_argument("candidate")
    compare.add_argument("--json-out")

    links = sub.add_parser("audit-links", help="check citation and source URLs")
    links.add_argument("article")
    links.add_argument("--timeout", type=float, default=20.0)
    links.add_argument("--workers", type=int, default=8)
    links.add_argument("--json-out")

    dashes = sub.add_parser("lint-dashes", help="enforce a visible em-dash limit")
    dashes.add_argument("article")
    dashes.add_argument("--limit", type=int, default=0)
    dashes.add_argument("--json-out")

    words = sub.add_parser("wordcount", help="count normalized reader-facing words two ways")
    words.add_argument("article")
    words.add_argument("--json-out")

    distinct = sub.add_parser("distinctness", help="find long verbatim sentence overlap")
    distinct.add_argument("master")
    distinct.add_argument("candidate")
    distinct.add_argument("--minimum-words", type=int, default=12)
    distinct.add_argument("--json-out")

    fabrication = sub.add_parser("check-fabrication", help="scan for unsupported-experience phrases")
    fabrication.add_argument("article")
    fabrication.add_argument("--term", action="append", dest="terms")
    fabrication.add_argument("--json-out")

    package = sub.add_parser("package", help="validate and create a reproducible ZIP archive")
    package.add_argument("path")
    package.add_argument("--out", required=True)
    package.add_argument("--no-strict", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            _emit({"pass": True, "path": str(Path(args.path).resolve()), "created": initialize_project(Path(args.path), args.force)})
            return 0
        if args.command == "validate":
            report = validate_project(Path(args.path), strict=args.strict)
            _emit(report, args.json_out)
            return 0 if report["pass"] else 1
        if args.command == "fingerprint":
            report = fingerprint_text(Path(args.article).read_text(encoding="utf-8"))
            _emit(report, args.json_out)
            return 0
        if args.command == "compare":
            report = compare_text(Path(args.master).read_text(encoding="utf-8"), Path(args.candidate).read_text(encoding="utf-8"))
            _emit(report, args.json_out)
            return 0 if report["pass"] else 1
        if args.command == "audit-links":
            report = audit_links(Path(args.article).read_text(encoding="utf-8"), args.timeout, args.workers)
            _emit(report, args.json_out)
            return 0 if report["pass"] else 1
        if args.command == "lint-dashes":
            report = scan_em_dashes(Path(args.article).read_text(encoding="utf-8"), args.limit)
            _emit(report, args.json_out)
            return 0 if report["pass"] else 1
        if args.command == "wordcount":
            report = count_words(Path(args.article).read_text(encoding="utf-8"))
            _emit(report, args.json_out)
            return 0
        if args.command == "distinctness":
            report = measure_distinctness(
                Path(args.master).read_text(encoding="utf-8"),
                Path(args.candidate).read_text(encoding="utf-8"),
                args.minimum_words,
            )
            _emit(report, args.json_out)
            return 0 if report["pass"] else 1
        if args.command == "check-fabrication":
            report = check_fabrication(
                Path(args.article).read_text(encoding="utf-8"), args.terms
            )
            _emit(report, args.json_out)
            return 0 if report["pass"] else 1
        if args.command == "package":
            report = create_archive(Path(args.path), Path(args.out), strict=not args.no_strict)
            _emit(report)
            return 0 if report["pass"] else 1
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(json.dumps({"pass": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
