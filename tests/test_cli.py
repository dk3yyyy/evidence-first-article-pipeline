import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from article_pipeline.project import initialize_project
from tests.test_integrity import complete_machine_package


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "article_pipeline.cli", *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_init_and_validate(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "article"
            created = self.run_cli("init", str(target))
            self.assertEqual(created.returncode, 0, created.stderr)
            validated = self.run_cli("validate", str(target))
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            self.assertTrue(json.loads(validated.stdout)["pass"])

    def test_compare_returns_nonzero_on_drift(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a.md", Path(td) / "b.md"
            a.write_text("Value: 10 ms\n")
            b.write_text("Value: 11 ms\n")
            result = self.run_cli("compare", str(a), str(b))
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["pass"])

    def test_lint_dashes_fails_on_visible_dash(self):
        with tempfile.TemporaryDirectory() as td:
            article = Path(td) / "article.md"
            article.write_text("Visible — dash.\n**DRAFT — NOT PUBLISHED**\n")
            result = self.run_cli("lint-dashes", str(article))
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["visible_count"], 1)

    def test_wordcount_returns_normalized_counts(self):
        with tempfile.TemporaryDirectory() as td:
            article = Path(td) / "article.md"
            article.write_text("# Heading\n\nTwo visible words.\n")
            result = self.run_cli("wordcount", str(article))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["conservative_count"], 4)

    def test_distinctness_fails_on_long_overlap(self):
        with tempfile.TemporaryDirectory() as td:
            master, candidate = Path(td) / "master.md", Path(td) / "candidate.md"
            sentence = (
                "This sentence has enough words to be treated as a meaningful "
                "verbatim overlap in both drafts."
            )
            master.write_text(sentence)
            candidate.write_text(sentence)
            result = self.run_cli(
                "distinctness", str(master), str(candidate), "--minimum-words", "12"
            )
            self.assertEqual(result.returncode, 1)

    def test_fabrication_gate_accepts_custom_terms(self):
        with tempfile.TemporaryDirectory() as td:
            article = Path(td) / "article.md"
            article.write_text("Our customers use this every day.")
            result = self.run_cli("check-fabrication", str(article), "--term", "our customers")
            self.assertEqual(result.returncode, 1)

    def test_missing_input_returns_documented_error_exit(self):
        result = self.run_cli("wordcount", "/definitely/missing/article.md")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(json.loads(result.stderr)["pass"])

    def test_aggregate_check_command(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "article"
            initialize_project(root)
            complete_machine_package(root)
            result = self.run_cli("check", str(root), "--skip-links")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)["pass"])


if __name__ == "__main__":
    unittest.main()
