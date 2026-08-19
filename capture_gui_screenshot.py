import argparse
import tkinter as tk

from database import create_database, insert_sample_orders
from gui import OrderIntegrityCheckerGUI
from screenshot_capture import DEFAULT_SCREENSHOT_PATH, capture_window


def parse_args():
    parser = argparse.ArgumentParser(
        description="Capture a real screenshot of the Tkinter main window."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_SCREENSHOT_PATH),
        help="PNG output path (default: docs/images/gui-main-window.png)",
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
        path = capture_window(root, args.output)
        print(f"GUI screenshot saved to {path}")
        root.destroy()

    root.after(max(args.delay_ms, 0), capture_and_close)
    root.mainloop()


if __name__ == "__main__":
    main()
