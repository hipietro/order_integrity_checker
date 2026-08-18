import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
README_PATH = PROJECT_ROOT / "README.md"
CLI_VISUAL_PATH = PROJECT_ROOT / "docs" / "images" / "cli-validation-example.svg"
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

    def test_gui_capture_workflow_requires_a_real_application_session(self):
        guide = SCREENSHOT_GUIDE_PATH.read_text(encoding="utf-8")

        self.assertIn("python3 gui.py", guide)
        self.assertIn("real Tkinter application session", guide)
        self.assertIn("docs/images/gui-main-window.png", guide)


if __name__ == "__main__":
    unittest.main()
