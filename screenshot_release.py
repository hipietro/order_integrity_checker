import json
import shutil
from pathlib import Path

from screenshot_review import verify_screenshot_provenance


CANONICAL_SCREENSHOT_PATH = Path("docs/images/gui-main-window.png")
CANONICAL_MANIFEST_PATH = Path("docs/images/gui-main-window.json")


def promote_verified_screenshot(
    screenshot_path,
    manifest_path,
    destination_image=CANONICAL_SCREENSHOT_PATH,
    destination_manifest=CANONICAL_MANIFEST_PATH,
):
    """Promote a verified GUI capture pair to the canonical documentation assets."""

    verification = verify_screenshot_provenance(screenshot_path, manifest_path)
    source_image = Path(screenshot_path)
    target_image = Path(destination_image)
    target_manifest = Path(destination_manifest)

    target_image.parent.mkdir(parents=True, exist_ok=True)
    target_manifest.parent.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(source_image, target_image)

    released_manifest = dict(verification["manifest"])
    released_manifest["asset"] = target_image.as_posix()
    released_manifest["canonical"] = True
    released_manifest["review_status"] = "approved"

    target_manifest.write_text(
        json.dumps(released_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "screenshot": target_image,
        "manifest": target_manifest,
        "sha256": verification["screenshot"]["sha256"],
    }
