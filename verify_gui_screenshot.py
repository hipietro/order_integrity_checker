import argparse

from screenshot_review import verify_screenshot_provenance


def parse_args():
    parser = argparse.ArgumentParser(
        description="Verify a GUI screenshot against its provenance manifest."
    )
    parser.add_argument("screenshot", help="Path to the reviewed PNG screenshot.")
    parser.add_argument("manifest", help="Path to the matching JSON manifest.")
    return parser.parse_args()


def main():
    args = parse_args()
    result = verify_screenshot_provenance(args.screenshot, args.manifest)
    screenshot = result["screenshot"]
    manifest = result["manifest"]
    print(
        "Screenshot provenance verified: "
        f"{screenshot['path']} ({screenshot['width']}x{screenshot['height']}, "
        f"sha256={screenshot['sha256']}, "
        f"source_commit={manifest['source_commit'] or 'unknown'})"
    )


if __name__ == "__main__":
    main()
