"""Cross-file evidence, claim and visual integrity validation."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .config import load_config
from .markdown import extract_destinations

CLAIM_MARKER_RE = re.compile(r"<!--\s*claims?\s*:\s*([^>]+?)\s*-->", re.I)
ID_RE = re.compile(r"^[A-Z]+-[A-Z0-9_-]+$")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON at {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _unique_ids(rows: Any, label: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if not isinstance(rows, list):
        return {}, [f"{label} must be a list"]
    index: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for number, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"{label}[{number}] must be an object")
            continue
        identifier = row.get("id")
        if not isinstance(identifier, str) or not ID_RE.fullmatch(identifier):
            errors.append(f"{label}[{number}] has invalid id {identifier!r}")
            continue
        if identifier in index:
            errors.append(f"duplicate {label} id {identifier}")
        index[identifier] = row
    return index, errors


def _claim_blocks(article: str) -> tuple[dict[str, list[str]], list[str]]:
    blocks: dict[str, list[str]] = {}
    errors: list[str] = []
    matches = list(CLAIM_MARKER_RE.finditer(article))
    for match in matches:
        raw_ids = [item.strip() for item in match.group(1).split(",") if item.strip()]
        end = article.find("\n\n", match.end())
        block = article[match.end() : end if end >= 0 else len(article)].strip()
        if not block:
            errors.append(f"claim marker at character {match.start()} has no following paragraph")
        for identifier in raw_ids:
            blocks.setdefault(identifier, []).append(block)
    return blocks, errors


def _safe_project_path(root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def _valid_visual_file(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    suffix = path.suffix.lower()
    try:
        if suffix == ".svg":
            root = ET.parse(path).getroot()
            return root.tag.rsplit("}", 1)[-1].lower() == "svg"
        header = path.read_bytes()[:16]
        if suffix == ".png":
            return header.startswith(b"\x89PNG\r\n\x1a\n")
        if suffix in {".jpg", ".jpeg"}:
            return header.startswith(b"\xff\xd8\xff")
        if suffix == ".webp":
            return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    except (OSError, ET.ParseError):
        return False
    return False


def validate_integrity(root: Path) -> dict[str, Any]:
    root = root.resolve()
    errors: dict[str, list[str]] = {
        "sources": [],
        "claims": [],
        "qualifiers": [],
        "visuals": [],
        "article": [],
    }
    try:
        config = load_config(root / "article-pipeline.toml")
        source_data = _load_json(root / "evidence" / "sources.json")
        claim_data = _load_json(root / "evidence" / "claims.json")
        model_data = _load_json(root / "evidence" / "model-provenance.json")
        visual_data = _load_json(root / "visuals" / "manifest.json")
        article = (root / "article.md").read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        return {
            "pass": False,
            "checks": {"machine_files_load": False},
            "details": {"load_error": str(exc)},
        }

    sources, source_id_errors = _unique_ids(source_data.get("sources"), "sources")
    claims, claim_id_errors = _unique_ids(claim_data.get("claims"), "claims")
    assets, asset_id_errors = _unique_ids(visual_data.get("assets"), "assets")
    errors["sources"].extend(source_id_errors)
    errors["claims"].extend(claim_id_errors)
    errors["visuals"].extend(asset_id_errors)

    for identifier, source in sources.items():
        for field in ("title", "url", "publisher", "published_at", "access_level"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                errors["sources"].append(f"{identifier} missing {field}")
        if isinstance(source.get("url"), str) and not source["url"].startswith(
            ("http://", "https://")
        ):
            errors["sources"].append(f"{identifier} URL must be HTTP(S)")

    model_provenance_valid = model_data.get("schema_version") == 1
    for role in ("research", "writing"):
        record = model_data.get(role)
        if not isinstance(record, dict) or any(
            not isinstance(record.get(field), str) or not record[field].strip()
            for field in ("provider", "model", "verified_at")
        ):
            errors["article"].append(f"model provenance missing {role} provider/model/verified_at")
            model_provenance_valid = False

    claim_sources_resolve = True
    for identifier, claim in claims.items():
        for field in ("statement", "type", "status"):
            if not isinstance(claim.get(field), str) or not claim[field].strip():
                errors["claims"].append(f"{identifier} missing {field}")
        source_ids = claim.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            errors["claims"].append(f"{identifier} must cite at least one source")
            claim_sources_resolve = False
        else:
            unknown = [value for value in source_ids if value not in sources]
            if unknown:
                errors["claims"].append(f"{identifier} has unknown sources: {unknown}")
                claim_sources_resolve = False

    blocks, marker_errors = _claim_blocks(article)
    errors["article"].extend(marker_errors)
    unknown_markers = sorted(set(blocks) - set(claims))
    if unknown_markers:
        errors["article"].append(f"article has unknown claim markers: {unknown_markers}")
    verified = {
        identifier for identifier, claim in claims.items() if claim.get("status") == "verified"
    }
    missing_markers = sorted(verified - set(blocks))
    if missing_markers:
        errors["article"].append(f"verified claims missing article markers: {missing_markers}")

    qualifier_ok = True
    for identifier, claim in claims.items():
        qualifiers = claim.get("required_qualifiers", [])
        if not isinstance(qualifiers, list) or not all(
            isinstance(q, str) and q.strip() for q in qualifiers
        ):
            errors["qualifiers"].append(f"{identifier} required_qualifiers must be a string list")
            qualifier_ok = False
            continue
        combined = "\n".join(blocks.get(identifier, [])).casefold()
        missing = [q for q in qualifiers if q.casefold() not in combined]
        if missing:
            errors["qualifiers"].append(f"{identifier} missing claim-local qualifiers: {missing}")
            qualifier_ok = False

    role_status = {role: False for role in config["visuals"]["required_roles"]}
    manifest_exports: set[str] = set()
    visual_files_valid = True
    visual_metadata_valid = True
    for identifier, asset in assets.items():
        asset_role = asset.get("role")
        asset_files_valid = True
        for field in ("source", "export"):
            path = _safe_project_path(root, asset.get(field))
            if path is None or not _valid_visual_file(path):
                errors["visuals"].append(f"{identifier} has invalid {field} file")
                visual_files_valid = False
                asset_files_valid = False
        if isinstance(asset_role, str) and asset_role in role_status and asset_files_valid:
            role_status[asset_role] = True
        export_value = asset.get("export")
        if isinstance(export_value, str):
            manifest_exports.add(export_value)
        if config["visuals"]["require_alt_text"] and not str(asset.get("alt_text", "")).strip():
            errors["visuals"].append(f"{identifier} missing alt_text")
            visual_metadata_valid = False
        if not str(asset.get("caption", "")).strip():
            errors["visuals"].append(f"{identifier} missing caption")
            visual_metadata_valid = False
        if config["visuals"]["require_provenance"] and not str(asset.get("provenance", "")).strip():
            errors["visuals"].append(f"{identifier} missing provenance")
            visual_metadata_valid = False

    parsed = extract_destinations(article)
    local_images = [
        destination
        for _, destination in parsed["images"]
        if not destination.startswith(("http://", "https://"))
    ]
    unresolved_images = sorted(set(local_images) - manifest_exports)
    if unresolved_images:
        errors["visuals"].append(f"article images absent from visual manifest: {unresolved_images}")

    checks = {
        "machine_files_load": True,
        "source_schema_valid": not errors["sources"],
        "model_provenance_valid": model_provenance_valid,
        "claim_schema_valid": not [e for e in errors["claims"] if "unknown sources" not in e],
        "claim_sources_resolve": claim_sources_resolve,
        "article_claim_markers_resolve": not unknown_markers and not marker_errors,
        "verified_claims_marked": not missing_markers,
        "claim_qualifiers_present": qualifier_ok,
        "visual_roles_present": all(role_status.values()),
        "visual_files_valid": visual_files_valid,
        "visual_metadata_valid": visual_metadata_valid,
        "article_images_in_manifest": not unresolved_images,
    }
    details = {"errors": errors, "visual_roles": role_status, "marked_claims": sorted(blocks)}
    return {"pass": all(checks.values()), "checks": checks, "details": details}
