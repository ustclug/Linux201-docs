import tempfile
import unittest

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from hooks.image_aspect_ratio import on_page_content


class ImageAspectRatioTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.docs_dir = Path(self.temporary_directory.name)
        (self.docs_dir / "images").mkdir()
        Image.new("RGB", (640, 360)).save(self.docs_dir / "images/example.png")
        self.config = SimpleNamespace(docs_dir=str(self.docs_dir))

    def tearDown(self):
        self.temporary_directory.cleanup()

    def render(self, html, page_url="guide/example/"):
        page = SimpleNamespace(file=SimpleNamespace(url=page_url))
        return on_page_content(html, page, self.config)

    def test_adds_aspect_ratio_without_dimensions(self):
        html = self.render(
            '<p><img alt="Example" '
            'src="../../images/example.png#only-light" /></p>'
        )

        self.assertNotIn('width=', html)
        self.assertNotIn('height=', html)
        self.assertIn('style="aspect-ratio: 16 / 9"', html)
        self.assertIn('src="../../images/example.png#only-light"', html)

    def test_preserves_existing_style_and_single_dimension(self):
        html = self.render(
            '<img src="../../images/example.png" width="320" '
            'style="border: 0">'
        )

        self.assertIn('width="320"', html)
        self.assertNotIn('height=', html)
        self.assertIn('style="border: 0; aspect-ratio: 16 / 9"', html)

    def test_skips_image_with_width_and_height(self):
        original = (
            '<img src="../../images/example.png" '
            'width="320" height="180">'
        )

        self.assertEqual(self.render(original), original)

    def test_does_not_override_an_explicit_aspect_ratio(self):
        original = (
            '<img src="../../images/example.png" '
            'style="aspect-ratio: 1 / 1">'
        )

        self.assertEqual(self.render(original), original)

    def test_logs_remote_image_and_skips_missing_image(self):
        remote = '<img src="https://example.com/image.png">'
        missing = '<img src="../../images/missing.png">'

        with patch.dict("os.environ", {"DEBUG": "1"}):
            with self.assertLogs(
                "mkdocs.hooks.image_aspect_ratio", level="INFO"
            ) as logs:
                self.assertEqual(self.render(remote), remote)
        self.assertIn("https://example.com/image.png", logs.output[0])

        with patch.dict("os.environ", {}, clear=True):
            with self.assertNoLogs(
                "mkdocs.hooks.image_aspect_ratio", level="INFO"
            ):
                self.assertEqual(self.render(remote), remote)
        self.assertEqual(self.render(missing), missing)

    def test_reads_svg_view_box(self):
        (self.docs_dir / "images/example.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'viewBox="0 0 300 200"></svg>',
            encoding="utf-8",
        )

        html = self.render('<img src="../../images/example.svg">')

        self.assertNotIn('width=', html)
        self.assertNotIn('height=', html)
        self.assertIn('style="aspect-ratio: 3 / 2"', html)


if __name__ == "__main__":
    unittest.main()
