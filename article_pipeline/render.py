"""Render human-readable evidence tables from machine-readable authority files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain an object")
    return data


def _cell(value: Any) -> str:
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def render_evidence_markdown(root: Path) -> dict[str, Any]:
    root = root.resolve()
    sources = _load(root / "evidence" / "sources.json").get("sources", [])
    claims = _load(root / "evidence" / "claims.json").get("claims", [])
    if not isinstance(sources, list) or not isinstance(claims, list):
        raise ValueError("sources and claims must be lists")

    source_lines = [
        "# Inspected sources",
        "",
        "<!-- Generated from evidence/sources.json by article-pipeline sync. -->",
        "",
        "| ID | Title | Publisher | URL | Published | Access | Relevance | Limitations |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in sources:
        source_lines.append(
            "| "
            + " | ".join(
                _cell(row.get(key))
                for key in (
                    "id",
                    "title",
                    "publisher",
                    "url",
                    "published_at",
                    "access_level",
                    "relevance",
                    "limitations",
                )
            )
            + " |"
        )

    claim_lines = [
        "# Claim ledger",
        "",
        "<!-- Generated from evidence/claims.json by article-pipeline sync. -->",
        "",
        "| Claim ID | Statement | Type | Sources | Required qualifiers | Scope | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in claims:
        claim_lines.append(
            "| "
            + " | ".join(
                _cell(row.get(key))
                for key in (
                    "id",
                    "statement",
                    "type",
                    "source_ids",
                    "required_qualifiers",
                    "scope",
                    "status",
                )
            )
            + " |"
        )

    source_path = root / "sources.md"
    claim_path = root / "claim-ledger.md"
    source_path.write_text("\n".join(source_lines) + "\n", encoding="utf-8")
    claim_path.write_text("\n".join(claim_lines) + "\n", encoding="utf-8")
    return {
        "pass": True,
        "sources": len(sources),
        "claims": len(claims),
        "files": [str(source_path), str(claim_path)],
    }
