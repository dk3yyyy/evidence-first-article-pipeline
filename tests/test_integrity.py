import json
import tempfile
import unittest
from pathlib import Path

from article_pipeline.integrity import validate_integrity
from article_pipeline.project import initialize_project


def complete_machine_package(root: Path) -> None:
    (root / "article.md").write_text(
        "# Tested article\n\n<!-- claims: CLM-001 -->\n"
        "The measured result may vary by environment.\n\n"
        "![Concept](visuals/illustration-web.svg)\n"
        "![Evidence](visuals/informative-image-web.svg)\n"
        "![Process](visuals/diagram-web.svg)\n\n**DRAFT — NOT PUBLISHED**\n"
    )
    (root / "evidence" / "sources.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sources": [
                    {
                        "id": "SRC-001",
                        "title": "Primary source",
                        "url": "https://example.org/source",
                        "publisher": "Example",
                        "published_at": "2026-01-01",
                        "access_level": "full-text",
                    }
                ],
            }
        )
    )
    (root / "evidence" / "claims.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "claims": [
                    {
                        "id": "CLM-001",
                        "statement": "The measured result may vary by environment.",
                        "type": "fact",
                        "source_ids": ["SRC-001"],
                        "required_qualifiers": ["may"],
                        "status": "verified",
                    }
                ],
            }
        )
    )
    visuals = root / "visuals"
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        '<rect width="100" height="100"/></svg>'
    )
    assets = []
    for role in ("illustration", "informative-image", "diagram"):
        export = f"{role}-web.svg"
        source = f"{role}-source.svg"
        (visuals / export).write_text(svg)
        (visuals / source).write_text(svg)
        assets.append(
            {
                "id": f"VIS-{len(assets) + 1:03d}",
                "role": role,
                "source": f"visuals/{source}",
                "export": f"visuals/{export}",
                "caption": f"{role} caption",
                "alt_text": f"Accessible {role} description",
                "provenance": "Original project asset",
            }
        )
    (visuals / "manifest.json").write_text(json.dumps({"schema_version": 1, "assets": assets}))
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".json"}:
            path.write_text(
                __import__("re").sub(r"\{\{[A-Z0-9_ -]+\}\}", "Completed content", path.read_text())
            )


class IntegrityTests(unittest.TestCase):
    def test_complete_machine_package_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "article"
            initialize_project(root)
            complete_machine_package(root)
            report = validate_integrity(root)
            self.assertTrue(report["pass"], report)

    def test_unknown_source_id_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "article"
            initialize_project(root)
            complete_machine_package(root)
            path = root / "evidence" / "claims.json"
            data = json.loads(path.read_text())
            data["claims"][0]["source_ids"] = ["SRC-404"]
            path.write_text(json.dumps(data))
            report = validate_integrity(root)
            self.assertFalse(report["checks"]["claim_sources_resolve"])

    def test_claim_local_qualifier_removal_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "article"
            initialize_project(root)
            complete_machine_package(root)
            article = root / "article.md"
            article.write_text(article.read_text().replace("may vary", "varies"))
            report = validate_integrity(root)
            self.assertFalse(report["checks"]["claim_qualifiers_present"])

    def test_empty_visual_export_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "article"
            initialize_project(root)
            complete_machine_package(root)
            (root / "visuals" / "diagram-web.svg").write_bytes(b"")
            report = validate_integrity(root)
            self.assertFalse(report["checks"]["visual_files_valid"])

    def test_unmarked_verified_claim_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "article"
            initialize_project(root)
            complete_machine_package(root)
            article = root / "article.md"
            article.write_text(article.read_text().replace("<!-- claims: CLM-001 -->\n", ""))
            report = validate_integrity(root)
            self.assertFalse(report["checks"]["verified_claims_marked"])


if __name__ == "__main__":
    unittest.main()
