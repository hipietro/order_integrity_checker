import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from screenshot_manifest import write_screenshot_manifest
from screenshot_review import verify_screenshot_provenance
from screenshot_validation import validate_gui_screenshot


class ScreenshotReviewTests(unittest.TestCase):
    def _create_capture(self, directory):
        screenshot_path = Path(directory) / "gui-main-window.png"
        Image.new("RGB", (900, 600), "white").save(screenshot_path)
        validation = validate_gui_screenshot(screenshot_path)
        manifest_path = Path(directory) / "gui-main-window.json"
        write_screenshot_manifest(
            validation,
            manifest_path,
            source_commit="abc123",
        )
        return screenshot_path, manifest_path

    def test_accepts_matching_screenshot_and_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            screenshot_path, manifest_path = self._create_capture(directory)

            result = verify_screenshot_provenance(screenshot_path, manifest_path)

            self.assertTrue(result["verified"])
            self.assertEqual(result["manifest"]["source_commit"], "abc123")

    def test_rejects_manifest_with_wrong_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            screenshot_path, manifest_path = self._create_capture(directory)
            manifest = json.loads(manifest_path.read_text())
            manifest["sha256"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest))

            with self.assertRaisesRegex(ValueError, "sha256"):
                verify_screenshot_provenance(screenshot_path, manifest_path)

    def test_rejects_manifest_missing_required_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            screenshot_path, manifest_path = self._create_capture(directory)
            manifest = json.loads(manifest_path.read_text())
            del manifest["generated_at"]
            manifest_path.write_text(json.dumps(manifest))

            with self.assertRaisesRegex(ValueError, "generated_at"):
                verify_screenshot_provenance(screenshot_path, manifest_path)


if __name__ == "__main__":
    unittest.main()
