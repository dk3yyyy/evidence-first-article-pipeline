import unittest

from article_pipeline.markdown import extract_destinations, reader_text


class MarkdownTests(unittest.TestCase):
    def test_balanced_parentheses_in_inline_link(self):
        parsed = extract_destinations("[paper](https://example.org/a_(b))")
        self.assertEqual(parsed["links"], ["https://example.org/a_(b)"])

    def test_reference_style_link_and_image(self):
        text = (
            "See [paper][p].\n\n[p]: https://example.org/source\n"
            "![Flow][fig]\n[fig]: visuals/diagram-web.svg\n"
        )
        parsed = extract_destinations(text)
        self.assertIn("https://example.org/source", parsed["links"])
        self.assertEqual(parsed["images"], [("Flow", "visuals/diagram-web.svg")])

    def test_links_inside_code_are_ignored(self):
        text = "```md\n[fake](https://bad.example)\n```\n[real](https://example.org)\n"
        self.assertEqual(extract_destinations(text)["links"], ["https://example.org"])

    def test_reader_text_preserves_alt_text_optionally(self):
        text = "# Heading\n![Useful alt words](visual.png)\nBody words.\n"
        self.assertNotIn("Useful alt", reader_text(text, include_alt=False))
        self.assertIn("Useful alt words", reader_text(text, include_alt=True))


if __name__ == "__main__":
    unittest.main()
