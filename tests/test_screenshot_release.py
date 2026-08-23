import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from screenshot_manifest import write_screenshot_manifest
from screenshot_release import promote_verified_screenshot
from screenshot_validation import validate_gui_screenshot


class ScreenshotReleaseTests(unittest.TestCase):
    def _create_capture(self, directory):
        root = Path(directory)
        screenshot_path = root / "reviewed.png"
        manifest_path = root / "reviewed.json"
        Image.new("RGB", (900, 600), "white").save(screenshot_path)
        validation = validate_gui_screenshot(screenshot_path)
        write_screenshot_manifest(
            validation,
            manifest_path,
            source_commit="abc123",
        )
        return screenshot_path, manifest_path, validation

    def test_promotes_verified_pair_and_marks_manifest_approved(self):
        with tempfile.TemporaryDirectory() as directory:
            source_image, source_manifest, validation = self._create_capture(directory)
            destination_image = Path(directory) / "docs" / "images" / "gui.png"
            destination_manifest = Path(directory) / "docs" / "images" / "gui.json"

            result = promote_verified_screenshot(
                source_image,
                source_manifest,
                destination_image,
                destination_manifest,
            )

            self.assertTrue(destination_image.is_file())
            self.assertEqual(destination_image.read_bytes(), source_image.read_bytes())
            released = json.loads(destination_manifest.read_text(encoding="utf-8"))
            self.assertTrue(released["canonical"])
            self.assertEqual(released["review_status"], "approved")
            self.assertEqual(released["sha256"], validation["sha256"])
            self.assertEqual(result["sha256"], validation["sha256"])

    def test_rejects_unverified_pair_before_copying(self):
        with tempfile.TemporaryDirectory() as directory:
            source_image, source_manifest, _ = self._create_capture(directory)
            manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
            manifest["sha256"] = "0" * 64
            source_manifest.write_text(json.dumps(manifest), encoding="utf-8")
            destination_image = Path(directory) / "docs" / "images" / "gui.png"

            with self.assertRaisesRegex(ValueError, "sha256"):
                promote_verified_screenshot(
                    source_image,
                    source_manifest,
                    destination_image,
                    Path(directory) / "docs" / "images" / "gui.json",
                )

            self.assertFalse(destination_image.exists())


if __name__ == "__main__":
    unittest.main()
