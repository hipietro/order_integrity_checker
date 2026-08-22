import json
from pathlib import Path

from screenshot_validation import validate_gui_screenshot


REQUIRED_MANIFEST_FIELDS = {
    "asset",
    "format",
    "width",
    "height",
    "sha256",
    "source_commit",
    "generated_at",
}


def verify_screenshot_provenance(screenshot_path, manifest_path):
    """Verify that a reviewed screenshot still matches its provenance manifest."""

    screenshot = validate_gui_screenshot(screenshot_path)
    path = Path(manifest_path)

    if not path.is_file():
        raise ValueError(f"Screenshot manifest does not exist: {path}")

    try:
        manifest = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Screenshot manifest is not valid JSON: {path}") from error

    missing_fields = REQUIRED_MANIFEST_FIELDS.difference(manifest)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Screenshot manifest is missing fields: {missing}")

    expected = {
        "format": screenshot["format"],
        "width": screenshot["width"],
        "height": screenshot["height"],
        "sha256": screenshot["sha256"],
    }

    for field, actual_value in expected.items():
        if manifest[field] != actual_value:
            raise ValueError(
                f"Screenshot manifest {field} does not match the reviewed image."
            )

    return {
        "screenshot": screenshot,
        "manifest": manifest,
        "verified": True,
    }
