import tempfile
import unittest
from pathlib import Path

from article_pipeline.checks import run_checks
from article_pipeline.project import initialize_project
from tests.test_integrity import complete_machine_package


class AggregateCheckTests(unittest.TestCase):
    def test_complete_project_passes_without_network(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "article"
            initialize_project(root)
            complete_machine_package(root)
            for path in root.rglob("*.md"):
                path.write_text(path.read_text().replace("{{", "").replace("}}", ""))
            report = run_checks(root, skip_links=True)
            self.assertTrue(report["pass"], report)
            self.assertIn("integrity", report["gates"])

    def test_dash_violation_fails_aggregate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "article"
            initialize_project(root)
            complete_machine_package(root)
            article = root / "article.md"
            article.write_text(article.read_text().replace("may vary", "may — vary"))
            report = run_checks(root, skip_links=True)
            self.assertFalse(report["gates"]["dashes"]["pass"])
            self.assertFalse(report["pass"])


if __name__ == "__main__":
    unittest.main()
