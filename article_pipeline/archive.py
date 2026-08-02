"""Reproducible article-package archive creation."""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from typing import Any

from .project import validate_project


def create_archive(root: Path, output: Path, strict: bool = True) -> dict[str, Any]:
    root, output = root.resolve(), output.resolve()
    validation = validate_project(root, strict=strict)
    if not validation["pass"]:
        raise ValueError(f"project validation failed: {validation}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            if path == output or any(part.startswith(".") for part in path.relative_to(root).parts):
                continue
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        file_count = len(archive.namelist())
    return {"pass": bad is None, "output": str(output), "sha256": digest, "files": file_count}
