import tempfile
import unittest
from pathlib import Path

from article_pipeline.project import initialize_project, validate_project


class ProjectTests(unittest.TestCase):
    def test_init_creates_complete_package(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "story"
            initialize_project(target)
            report = validate_project(target, strict=False)
            self.assertTrue(report["pass"], report)
            self.assertTrue((target / "visuals" / "visual-plan.md").exists())

    def test_strict_validation_rejects_placeholders(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "story"
            initialize_project(target)
            report = validate_project(target, strict=True)
            self.assertFalse(report["pass"])
            self.assertIn("unresolved_placeholders", report["checks"])

    def test_missing_required_file_fails(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "story"
            initialize_project(target)
            (target / "claim-ledger.md").unlink()
            report = validate_project(target, strict=False)
            self.assertFalse(report["pass"])

    def test_strict_validation_requires_all_three_visual_roles(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "story"
            initialize_project(target)
            for path in target.rglob("*.md"):
                path.write_text(__import__("re").sub(
                    r"\{\{[A-Z0-9_ -]+\}\}", "Completed content", path.read_text()
                ))
            (target / "visuals" / "diagram-web.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'
            )
            report = validate_project(target, strict=True)
            self.assertFalse(report["pass"])
            self.assertFalse(report["checks"]["visual_roles_present"])


if __name__ == "__main__":
    unittest.main()
