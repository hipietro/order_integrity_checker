import argparse
import os
import tkinter as tk
from pathlib import Path

from database import create_database, insert_sample_orders
from gui import OrderIntegrityCheckerGUI
from screenshot_capture import DEFAULT_SCREENSHOT_PATH, capture_window
from screenshot_manifest import write_screenshot_manifest
from screenshot_validation import validate_gui_screenshot


def parse_args():
    parser = argparse.ArgumentParser(
        description="Capture and validate a real screenshot of the Tkinter main window."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_SCREENSHOT_PATH),
        help="PNG output path (default: docs/images/gui-main-window.png)",
    )
    parser.add_argument(
        "--manifest",
        default="",
        help=(
            "Optional JSON provenance manifest path. When omitted, a .json file "
            "is written next to the screenshot."
        ),
    )
    parser.add_argument(
        "--delay-ms",
        type=int,
        default=800,
        help="Delay before capture so the window can finish rendering.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    create_database()
    insert_sample_orders()

    root = tk.Tk()
    OrderIntegrityCheckerGUI(root)

    def capture_and_close():
        try:
            path = capture_window(root, args.output)
            result = validate_gui_screenshot(path)
            manifest_path = (
                Path(args.manifest)
                if args.manifest
                else Path(path).with_suffix(".json")
            )
            write_screenshot_manifest(
                result,
                manifest_path,
                source_commit=os.getenv("GITHUB_SHA", ""),
            )
            print(
                "GUI screenshot saved and validated: "
                f"{result['path']} ({result['width']}x{result['height']}, "
                f"sha256={result['sha256']})"
            )
            print(f"Screenshot manifest saved: {manifest_path}")
        finally:
            root.destroy()

    root.after(max(args.delay_ms, 0), capture_and_close)
    root.mainloop()


if __name__ == "__main__":
    main()
