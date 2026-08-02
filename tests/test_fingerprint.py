import unittest

from article_pipeline.fingerprint import compare_text, fingerprint_text


MASTER = """# A measured claim

A synthetic run may improve latency from 120 ms to 95 ms for `predict()`.
See [the source](https://example.com/paper).

![Flow](visuals/diagram-web.svg)

```python
predict()
```

**DRAFT — NOT PUBLISHED**
"""


class FingerprintTests(unittest.TestCase):
    def test_unchanged_evidence_surface_passes(self):
        candidate = MASTER.replace("A synthetic run may improve", "In this synthetic run, the result may improve")
        report = compare_text(MASTER, candidate)
        self.assertTrue(report["pass"], report)

    def test_changed_number_fails(self):
        report = compare_text(MASTER, MASTER.replace("95 ms", "80 ms"))
        self.assertFalse(report["pass"])
        self.assertFalse(report["checks"]["numeric_tokens"])

    def test_changed_link_fails(self):
        report = compare_text(MASTER, MASTER.replace("example.com/paper", "example.com/other"))
        self.assertFalse(report["checks"]["markdown_link_destinations"])

    def test_removed_uncertainty_fails(self):
        report = compare_text(MASTER, MASTER.replace("may improve", "improves"))
        self.assertFalse(report["checks"]["uncertainty_counts_not_reduced"])

    def test_changed_code_fence_fails(self):
        report = compare_text(MASTER, MASTER.replace("predict()\n```", "predict_fast()\n```"))
        self.assertFalse(report["checks"]["code_fences"])

    def test_fingerprint_is_deterministic(self):
        self.assertEqual(fingerprint_text(MASTER), fingerprint_text(MASTER))


if __name__ == "__main__":
    unittest.main()
