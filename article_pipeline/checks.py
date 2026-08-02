"""Aggregate release-check orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .config import load_config
from .fingerprint import compare_text
from .integrity import validate_integrity
from .links import audit_links
from .linting import check_fabrication, count_words, scan_em_dashes
from .project import validate_project


def run_checks(
    root: Path,
    master: Path | None = None,
    skip_links: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    config = load_config(root / "article-pipeline.toml")
    article_path = root / "article.md"
    article = article_path.read_text(encoding="utf-8")

    project = validate_project(root, strict=True)
    integrity = validate_integrity(root)
    dashes = scan_em_dashes(article, config["editorial"]["em_dash_limit"])
    words = count_words(article)
    minimum = config["editorial"]["minimum_words"]
    maximum = config["editorial"]["maximum_words"]
    word_policy_pass = words["conservative_count"] >= minimum and (
        maximum == 0 or words["conservative_count"] <= maximum
    )
    words = {
        "pass": word_policy_pass,
        "minimum": minimum,
        "maximum": maximum,
        **words,
    }
    fabrication = check_fabrication(article, terms=config["editorial"]["fabrication_terms"])

    if skip_links or not config["links"]["enabled"]:
        links: dict[str, Any] = {
            "pass": True,
            "skipped": True,
            "reason": "disabled by invocation or configuration",
        }
    else:
        links = audit_links(
            article,
            timeout=float(config["links"]["timeout_seconds"]),
            workers=int(config["links"]["workers"]),
        )
        if not config["links"]["allow_blocked"] and links["summary"]["blocked"]:
            links["pass"] = False
            links["policy_error"] = "blocked HTTP responses are failures in project configuration"

    gates: dict[str, Any] = {
        "project": project,
        "integrity": integrity,
        "dashes": dashes,
        "wordcount": words,
        "fabrication": fabrication,
        "links": links,
    }
    if master is not None:
        gates["evidence_comparison"] = compare_text(master.read_text(encoding="utf-8"), article)

    return {
        "schema_version": 1,
        "pipeline_version": __version__,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "root": root.name,
        "article": "article.md",
        "pass": all(gate.get("pass", False) for gate in gates.values()),
        "gates": gates,
    }
