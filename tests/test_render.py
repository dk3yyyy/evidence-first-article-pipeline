import tempfile
import unittest
from pathlib import Path

from article_pipeline.project import initialize_project
from article_pipeline.render import render_evidence_markdown
from tests.test_integrity import complete_machine_package


class RenderTests(unittest.TestCase):
    def test_json_evidence_renders_human_markdown(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "article"
            initialize_project(root)
            complete_machine_package(root)
            report = render_evidence_markdown(root)
            self.assertTrue(report["pass"])
            self.assertIn("SRC-001", (root / "sources.md").read_text())
            self.assertIn("CLM-001", (root / "claim-ledger.md").read_text())
            self.assertIn("Generated from", (root / "sources.md").read_text())


if __name__ == "__main__":
    unittest.main()
