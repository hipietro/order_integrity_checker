import json
from datetime import datetime, timezone
from pathlib import Path


def build_screenshot_manifest(validation_result, source_commit=""):
    """Build metadata that makes a generated GUI screenshot traceable."""

    path = Path(validation_result["path"])
    return {
        "asset": path.as_posix(),
        "format": validation_result["format"],
        "width": validation_result["width"],
        "height": validation_result["height"],
        "sha256": validation_result["sha256"],
        "source_commit": source_commit,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_screenshot_manifest(validation_result, output_path, source_commit=""):
    """Write screenshot provenance metadata as deterministic, readable JSON."""

    manifest = build_screenshot_manifest(validation_result, source_commit)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return path
