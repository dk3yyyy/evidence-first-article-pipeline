"""Reproducible article-package archive creation."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from . import __version__
from .project import validate_project


def create_archive(root: Path, output: Path, strict: bool = True) -> dict[str, Any]:
    root, output = root.resolve(), output.resolve()
    validation = validate_project(root, strict=strict)
    if not validation["pass"]:
        raise ValueError(f"project validation failed: {validation}")
    output.parent.mkdir(parents=True, exist_ok=True)
    included: list[tuple[Path, str, bytes]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        relative = path.relative_to(root).as_posix()
        if (
            path == output
            or relative == "MANIFEST.json"
            or any(part.startswith(".") for part in path.relative_to(root).parts)
        ):
            continue
        included.append((path, relative, path.read_bytes()))
    manifest = {
        "schema_version": 1,
        "pipeline_version": __version__,
        "validation_checks": validation["checks"],
        "files": [
            {
                "path": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for _, relative, data in included
        ],
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for _, relative, data in included:
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
        manifest_info = zipfile.ZipInfo("MANIFEST.json", date_time=(1980, 1, 1, 0, 0, 0))
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        manifest_info.external_attr = 0o100644 << 16
        archive.writestr(manifest_info, manifest_bytes)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        file_count = len(archive.namelist())
    return {
        "pass": bad is None,
        "output": str(output),
        "sha256": digest,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "files": file_count,
    }
