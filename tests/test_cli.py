import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "article_pipeline.cli", *args],
            text=True, capture_output=True, check=False,
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


if __name__ == "__main__":
    unittest.main()
