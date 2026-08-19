import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from screenshot_capture import capture_window, get_window_bbox


class FakeRoot:
    def __init__(self, x=10, y=20, width=640, height=480):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.updated = False

    def update_idletasks(self):
        self.updated = True

    def winfo_rootx(self):
        return self.x

    def winfo_rooty(self):
        return self.y

    def winfo_width(self):
        return self.width

    def winfo_height(self):
        return self.height


class ScreenshotCaptureTests(unittest.TestCase):
    def test_get_window_bbox_uses_visible_window_bounds(self):
        root = FakeRoot()

        bbox = get_window_bbox(root)

        self.assertTrue(root.updated)
        self.assertEqual((10, 20, 650, 500), bbox)

    def test_get_window_bbox_rejects_unrendered_window(self):
        root = FakeRoot(width=1, height=1)

        with self.assertRaisesRegex(RuntimeError, "not ready"):
            get_window_bbox(root)

    @patch("PIL.ImageGrab.grab")
    def test_capture_window_creates_parent_and_saves_png(self, grab):
        image = MagicMock()
        grab.return_value = image

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "gui.png"
            result = capture_window(FakeRoot(), output)

            self.assertEqual(output, result)
            self.assertTrue(output.parent.is_dir())
            grab.assert_called_once_with(bbox=(10, 20, 650, 500))
            image.save.assert_called_once_with(output, format="PNG")


if __name__ == "__main__":
    unittest.main()
