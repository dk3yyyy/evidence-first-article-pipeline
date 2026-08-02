import unittest

from article_pipeline.links import UnsafeDestinationError, _SafeRedirectHandler, audit_links, extract_links


class LinkTests(unittest.TestCase):
    def test_extracts_citations_and_raw_urls_but_not_images(self):
        text = "See [source](https://example.com/a) and https://example.org/b. ![alt](https://img.example/x.png)"
        self.assertEqual(
            extract_links(text),
            ["https://example.com/a", "https://example.org/b"],
        )

    def test_deduplicates_links(self):
        text = "[one](https://example.com) and [two](https://example.com)"
        self.assertEqual(extract_links(text), ["https://example.com"])

    def test_private_network_urls_are_blocked_without_request(self):
        report = audit_links("See http://127.0.0.1:8000/private", timeout=0.1, workers=1)
        self.assertFalse(report["pass"])
        self.assertEqual(report["results"][0]["result"], "unsafe")

    def test_redirects_to_private_networks_are_blocked(self):
        with self.assertRaises(UnsafeDestinationError):
            _SafeRedirectHandler().redirect_request(
                None, None, 302, "Found", {}, "http://127.0.0.1/private"
            )


if __name__ == "__main__":
    unittest.main()
