"""Article-package initialization and structural validation."""

from __future__ import annotations

import re
from importlib import resources
from importlib.abc import Traversable
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "article-pipeline.toml",
    "brief.md",
    "sources.md",
    "claim-ledger.md",
    "outline.md",
    "unresolved-questions.md",
    "article.md",
    "platform-notes.md",
    "publication-checklist.md",
    "review-summary.md",
    "visuals/visual-plan.md",
    "visuals/provenance.md",
    "evidence/sources.json",
    "evidence/claims.json",
    "evidence/model-provenance.json",
    "visuals/manifest.json",
    "schemas/sources.schema.json",
    "schemas/claims.schema.json",
    "schemas/visuals.schema.json",
    "schemas/model-provenance.schema.json",
)
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_ -]+\}\}")
DRAFT_MARKERS = ("DRAFT — NOT PUBLISHED", "DRAFT - NOT PUBLISHED")


def _template_root() -> Traversable:
    return resources.files("article_pipeline").joinpath("templates/article-package")


def _walk_template_files(
    root: Traversable, prefix: Path = Path()
) -> list[tuple[Traversable, Path]]:
    files: list[tuple[Traversable, Path]] = []
    for item in root.iterdir():
        relative = prefix / item.name
        if item.is_file():
            files.append((item, relative))
        elif item.is_dir():
            files.extend(_walk_template_files(item, relative))
    return files


def initialize_project(target: Path, force: bool = False) -> list[str]:
    target = target.resolve()
    if target.exists() and any(target.iterdir()) and not force:
        raise FileExistsError(
            f"{target} exists and is not empty; pass --force to replace template files"
        )
    target.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    root = _template_root()
    for item, relative in _walk_template_files(root):
        destination = target / str(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and not force:
            continue
        destination.write_bytes(item.read_bytes())
        created.append(str(relative))
    return sorted(created)


def validate_project(root: Path, strict: bool = False) -> dict[str, Any]:
    root = root.resolve()
    missing = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    checks: dict[str, bool] = {"required_files": not missing}
    details: dict[str, Any] = {"missing_files": missing, "root": str(root)}
    article = root / "article.md"
    if article.is_file():
        text = article.read_text(encoding="utf-8")
        checks["draft_status_present"] = any(marker in text for marker in DRAFT_MARKERS)
        # Template placeholders count as structure in normal mode. Strict mode
        # separately rejects unresolved placeholders before release packaging.
        checks["article_not_empty"] = len(text.split()) >= 5
    else:
        checks["draft_status_present"] = False
        checks["article_not_empty"] = False
    if strict:
        placeholder_hits: dict[str, list[str]] = {}
        files = [
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in {".md", ".json", ".toml"}
        ]
        for path in files:
            hits = PLACEHOLDER_RE.findall(path.read_text(encoding="utf-8"))
            if hits:
                placeholder_hits[str(path.relative_to(root))] = sorted(set(hits))
        checks["unresolved_placeholders"] = not placeholder_hits
        details["placeholder_hits"] = placeholder_hits
        from .integrity import validate_integrity

        integrity = validate_integrity(root)
        checks.update(integrity["checks"])
        details["integrity"] = integrity["details"]
    return {"pass": all(checks.values()), "checks": checks, "details": details}
