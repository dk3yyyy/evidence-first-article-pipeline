import unittest

from article_pipeline.linting import (
    check_fabrication,
    count_words,
    measure_distinctness,
    scan_em_dashes,
)


class LintingTests(unittest.TestCase):
    def test_dash_scan_ignores_required_status_marker_and_comments(self):
        text = "Intro — claim.\n<!-- private — note -->\n**DRAFT — NOT PUBLISHED**\n"
        report = scan_em_dashes(text, limit=0)
        self.assertFalse(report["pass"])
        self.assertEqual(report["visible_count"], 1)
        self.assertEqual(report["ignored_status_count"], 1)

    def test_dash_scan_passes_without_visible_dashes(self):
        report = scan_em_dashes("A clear sentence.\n**DRAFT — NOT PUBLISHED**\n", limit=0)
        self.assertTrue(report["pass"])

    def test_dash_scan_ignores_fenced_code(self):
        report = scan_em_dashes("```text\nprotocol — literal\n```\n", limit=0)
        self.assertTrue(report["pass"])

    def test_dash_scan_does_not_hide_ordinary_published_sentence(self):
        report = scan_em_dashes("The paper was PUBLISHED — after review.\n", limit=0)
        self.assertFalse(report["pass"])
        self.assertEqual(report["visible_count"], 1)

    def test_wordcount_strips_metadata_urls_images_code_and_status(self):
        text = """---
title: Hidden metadata
---
<!-- private note -->
# Heading
Two visible words.
![Alt words here](visual.png)
https://example.com/path
```python
print('not counted')
```
**DRAFT — NOT PUBLISHED**
"""
        report = count_words(text)
        self.assertEqual(report["regex_count"], 4)
        self.assertEqual(report["whitespace_count"], 4)
        self.assertEqual(report["conservative_count"], 4)

    def test_wordcount_keeps_ordinary_sentence_containing_published(self):
        report = count_words("The paper was PUBLISHED after review.\n")
        self.assertEqual(report["conservative_count"], 6)

    def test_distinctness_reports_long_identical_sentences(self):
        shared = "This sentence contains exactly enough useful words to trigger the long sentence overlap detector today."
        report = measure_distinctness(shared + " Unique ending.", shared + " Different ending.", minimum_words=12)
        self.assertFalse(report["pass"])
        self.assertEqual(report["overlap_count"], 1)

    def test_distinctness_ignores_short_sentences(self):
        report = measure_distinctness("Short shared sentence.", "Short shared sentence.", minimum_words=12)
        self.assertTrue(report["pass"])

    def test_fabrication_gate_flags_configured_phrase(self):
        report = check_fabrication("Our customers rely on this every day.", terms=["our customers"])
        self.assertFalse(report["pass"])
        self.assertEqual(report["hit_count"], 1)

    def test_fabrication_gate_allows_explicit_negation(self):
        report = check_fabrication("This is synthetic. There were no real callers.", terms=["real callers"])
        self.assertTrue(report["pass"])


if __name__ == "__main__":
    unittest.main()
