import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from screenshot_validation import validate_gui_screenshot


class ScreenshotValidationTests(unittest.TestCase):
    def test_accepts_readable_png_with_expected_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gui.png"
            Image.new("RGB", (1200, 700), "white").save(path, format="PNG")

            result = validate_gui_screenshot(path)

            self.assertEqual(path, result["path"])
            self.assertEqual(1200, result["width"])
            self.assertEqual(700, result["height"])
            self.assertEqual("PNG", result["format"])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                result["sha256"],
            )

    def test_digest_changes_when_screenshot_content_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.png"
            second = Path(directory) / "second.png"
            Image.new("RGB", (1200, 700), "white").save(first, format="PNG")
            Image.new("RGB", (1200, 700), "black").save(second, format="PNG")

            first_result = validate_gui_screenshot(first)
            second_result = validate_gui_screenshot(second)

            self.assertNotEqual(first_result["sha256"], second_result["sha256"])

    def test_rejects_missing_file(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            validate_gui_screenshot("missing-gui.png")

    def test_rejects_non_image_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gui.png"
            path.write_text("not an image")

            with self.assertRaisesRegex(ValueError, "not a valid image"):
                validate_gui_screenshot(path)

    def test_rejects_screenshot_that_is_too_small(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gui.png"
            Image.new("RGB", (400, 300), "white").save(path, format="PNG")

            with self.assertRaisesRegex(ValueError, "too small"):
                validate_gui_screenshot(path)


if __name__ == "__main__":
    unittest.main()
