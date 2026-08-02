"""Article-package initialization and structural validation."""
from __future__ import annotations

import re
from importlib import resources
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "brief.md", "sources.md", "claim-ledger.md", "outline.md",
    "unresolved-questions.md", "article.md", "platform-notes.md",
    "publication-checklist.md", "review-summary.md",
    "visuals/visual-plan.md", "visuals/provenance.md",
)
PLACEHOLDER_RE = re.compile(r"\{\{[A-Z0-9_ -]+\}\}")
DRAFT_MARKERS = ("DRAFT — NOT PUBLISHED", "DRAFT - NOT PUBLISHED")


def _template_root():
    return resources.files("article_pipeline").joinpath("templates/article-package")


def initialize_project(target: Path, force: bool = False) -> list[str]:
    target = target.resolve()
    if target.exists() and any(target.iterdir()) and not force:
        raise FileExistsError(f"{target} exists and is not empty; pass --force to replace template files")
    target.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    root = _template_root()
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        relative = item.relative_to(root)
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
        for path in root.rglob("*.md"):
            hits = PLACEHOLDER_RE.findall(path.read_text(encoding="utf-8"))
            if hits:
                placeholder_hits[str(path.relative_to(root))] = sorted(set(hits))
        checks["unresolved_placeholders"] = not placeholder_hits
        details["placeholder_hits"] = placeholder_hits
        visual_dir = root / "visuals"
        exports = [
            p for p in visual_dir.glob("*")
            if p.is_file()
            and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}
            and "source" not in p.stem.lower()
        ] if visual_dir.is_dir() else []
        required_roles = ("illustration", "informative-image", "diagram")
        role_status = {
            role: any(p.stem.lower().startswith(f"{role}-") for p in exports)
            for role in required_roles
        }
        checks["visual_roles_present"] = all(role_status.values())
        details["visual_roles"] = role_status
        details["visual_exports"] = [p.name for p in exports]
    return {"pass": all(checks.values()), "checks": checks, "details": details}
