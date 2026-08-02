import tempfile
import unittest
from pathlib import Path

from article_pipeline.config import DEFAULT_CONFIG, load_config


class ConfigTests(unittest.TestCase):
    def test_missing_config_returns_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            config = load_config(Path(td) / "missing.toml")
            self.assertEqual(config["editorial"]["em_dash_limit"], 0)
            self.assertEqual(
                config["visuals"]["required_roles"],
                ["illustration", "informative-image", "diagram"],
            )

    def test_project_config_deep_merges_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "article-pipeline.toml"
            path.write_text("[editorial]\nem_dash_limit = 2\n")
            config = load_config(path)
            self.assertEqual(config["editorial"]["em_dash_limit"], 2)
            self.assertEqual(
                config["links"]["timeout_seconds"], DEFAULT_CONFIG["links"]["timeout_seconds"]
            )

    def test_invalid_config_type_fails(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "article-pipeline.toml"
            path.write_text('[editorial]\nem_dash_limit = "none"\n')
            with self.assertRaises(ValueError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
