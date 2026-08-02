import tempfile
import unittest
import zipfile
from pathlib import Path

from article_pipeline.archive import create_archive
from article_pipeline.project import initialize_project
from tests.test_integrity import complete_machine_package


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
            complete_machine_package(project)
            (project / ".private-note").write_text("must not ship")
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
                self.assertIn("MANIFEST.json", archive.namelist())
                manifest = __import__("json").loads(archive.read("MANIFEST.json"))
                self.assertEqual(manifest["schema_version"], 1)
                self.assertTrue(all("sha256" in row for row in manifest["files"]))
                self.assertNotIn(".private-note", archive.namelist())


if __name__ == "__main__":
    unittest.main()
