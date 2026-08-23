import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
README_PATH = PROJECT_ROOT / "README.md"
IMAGES_DIR = PROJECT_ROOT / "docs" / "images"
CLI_VISUAL_PATH = IMAGES_DIR / "cli-validation-example.svg"
GUI_VISUAL_PATH = IMAGES_DIR / "gui-main-window.png"
GUI_MANIFEST_PATH = IMAGES_DIR / "gui-main-window.json"
SCREENSHOT_GUIDE_PATH = PROJECT_ROOT / "docs" / "screenshots.md"


class DocumentationAssetTests(unittest.TestCase):
    """Protects recruiter-facing visual documentation from broken references."""

    def test_cli_visual_exists_and_is_accessible_svg(self):
        self.assertTrue(CLI_VISUAL_PATH.is_file())

        svg = CLI_VISUAL_PATH.read_text(encoding="utf-8")
        self.assertIn("<title", svg)
        self.assertIn("<desc", svg)
        self.assertIn("CSV IMPORT PREVIEW", svg)

    def test_readme_embeds_cli_visual_with_descriptive_alt_text(self):
        readme = README_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/images/cli-validation-example.svg", readme)
        self.assertIn("Terminal-style example", readme)

    def test_canonical_gui_visual_and_provenance_are_committed(self):
        self.assertTrue(GUI_VISUAL_PATH.is_file())
        self.assertTrue(GUI_MANIFEST_PATH.is_file())

        manifest = json.loads(GUI_MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["asset"], "docs/images/gui-main-window.png")
        self.assertEqual(manifest["format"], "PNG")
        self.assertEqual(manifest["width"], 1100)
        self.assertEqual(manifest["height"], 760)
        self.assertTrue(manifest["canonical"])
        self.assertEqual(manifest["review_status"], "approved")
        self.assertEqual(len(manifest["sha256"]), 64)

    def test_readme_embeds_gui_visual_with_descriptive_alt_text(self):
        readme = README_PATH.read_text(encoding="utf-8")

        self.assertIn("docs/images/gui-main-window.png", readme)
        self.assertIn("Tkinter main window", readme)

    def test_gui_capture_workflow_requires_a_real_application_session(self):
        guide = SCREENSHOT_GUIDE_PATH.read_text(encoding="utf-8")

        self.assertIn("python3 gui.py", guide)
        self.assertIn("real Tkinter application session", guide)
        self.assertIn("docs/images/gui-main-window.png", guide)
        self.assertIn("publish_gui_screenshot.py", guide)


if __name__ == "__main__":
    unittest.main()
