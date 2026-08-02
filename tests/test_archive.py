import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from article_pipeline.archive import create_archive
from article_pipeline.project import initialize_project


class ArchiveTests(unittest.TestCase):
    def test_strict_archive_rejects_incomplete_template(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "article"
            initialize_project(project)
            with self.assertRaises(ValueError):
                create_archive(project, Path(td) / "article.zip", strict=True)

    def test_completed_project_creates_valid_reproducible_archive(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "article"
            initialize_project(project)
            for path in project.rglob("*.md"):
                text = re.sub(r"\{\{[A-Z0-9_ -]+\}\}", "Completed content", path.read_text())
                path.write_text(text)
            for name in ("illustration-web.svg", "informative-image-web.svg", "diagram-web.svg"):
                (project / "visuals" / name).write_text(
                    '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'
                )
            output = Path(td) / "article.zip"
            first = create_archive(project, output, strict=True)
            first_bytes = output.read_bytes()
            second = create_archive(project, output, strict=True)
            self.assertTrue(first["pass"] and second["pass"])
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(first_bytes, output.read_bytes())
            with zipfile.ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                self.assertIn("article.md", archive.namelist())


if __name__ == "__main__":
    unittest.main()
