from pathlib import Path

MIN_SCREENSHOT_WIDTH = 800
MIN_SCREENSHOT_HEIGHT = 500


def validate_gui_screenshot(
    screenshot_path,
    min_width=MIN_SCREENSHOT_WIDTH,
    min_height=MIN_SCREENSHOT_HEIGHT,
):
    """Validate that a GUI screenshot is a readable PNG of useful size."""

    from PIL import Image

    path = Path(screenshot_path)

    if not path.is_file():
        raise ValueError(f"Screenshot does not exist: {path}")

    try:
        with Image.open(path) as image:
            image.verify()

        with Image.open(path) as image:
            width, height = image.size
            image_format = image.format
    except Exception as error:
        raise ValueError(f"Screenshot is not a valid image: {path}") from error

    if image_format != "PNG":
        raise ValueError("GUI screenshot must use PNG format.")

    if width < min_width or height < min_height:
        raise ValueError(
            "GUI screenshot is too small for README use: "
            f"{width}x{height}; expected at least {min_width}x{min_height}."
        )

    return {
        "path": path,
        "width": width,
        "height": height,
        "format": image_format,
    }
