from pathlib import Path

DEFAULT_SCREENSHOT_PATH = Path("docs/images/gui-main-window.png")


def get_window_bbox(root):
    """Return the root window bounds as a Pillow-compatible bounding box."""

    root.update_idletasks()
    left = root.winfo_rootx()
    top = root.winfo_rooty()
    width = root.winfo_width()
    height = root.winfo_height()

    if width <= 1 or height <= 1:
        raise RuntimeError("GUI window is not ready for screenshot capture.")

    return (left, top, left + width, top + height)


def capture_window(root, output_path=DEFAULT_SCREENSHOT_PATH):
    """Capture the visible Tkinter root window and save it as a PNG file."""

    from PIL import ImageGrab

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = ImageGrab.grab(bbox=get_window_bbox(root))
    image.save(output_path, format="PNG")
    return output_path
