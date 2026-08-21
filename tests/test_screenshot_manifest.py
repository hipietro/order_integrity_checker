import json
import tempfile
import unittest
from pathlib import Path

from screenshot_manifest import build_screenshot_manifest, write_screenshot_manifest


class ScreenshotManifestTests(unittest.TestCase):
    def setUp(self):
        self.validation_result = {
            "path": Path("docs/images/gui-main-window.png"),
            "format": "PNG",
            "width": 1100,
            "height": 760,
            "sha256": "a" * 64,
        }

    def test_manifest_keeps_capture_metadata_and_source_commit(self):
        manifest = build_screenshot_manifest(
            self.validation_result,
            source_commit="abc123",
        )

        self.assertEqual("docs/images/gui-main-window.png", manifest["asset"])
        self.assertEqual("PNG", manifest["format"])
        self.assertEqual(1100, manifest["width"])
        self.assertEqual(760, manifest["height"])
        self.assertEqual("a" * 64, manifest["sha256"])
        self.assertEqual("abc123", manifest["source_commit"])
        self.assertTrue(manifest["generated_at"].endswith("+00:00"))

    def test_writer_creates_readable_json_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "manifest.json"

            written = write_screenshot_manifest(
                self.validation_result,
                output,
                source_commit="def456",
            )

            data = json.loads(written.read_text())
            self.assertEqual("def456", data["source_commit"])
            self.assertEqual("a" * 64, data["sha256"])


if __name__ == "__main__":
    unittest.main()
