# Documentation image assets

This directory contains visual assets used by the project documentation.

## Naming conventions

Use descriptive, lowercase, hyphen-separated names:

- `gui-main-window.png` for a real capture of the main Tkinter window
- `cli-validation-example.svg` for the deterministic CLI example used in the README

## Capture rules

Documentation images should represent the current application rather than a redesigned mockup.

For GUI captures:

1. Install development dependencies with `python3 -m pip install -r requirements-dev.txt`.
2. Run `python3 capture_gui_screenshot.py` from a clean checkout in a desktop session.
3. Keep the default window size unless a feature specifically requires a larger view.
4. Use sample data only; do not include personal or production data.
5. Verify the complete application window is visible with readable controls and output.
6. Confirm the generated file is `docs/images/gui-main-window.png`.
7. Update the README only after verifying the stored image matches the current UI.

The capture command instantiates the real `OrderIntegrityCheckerGUI` and captures its rendered window bounds. A hand-drawn replacement is not acceptable as the canonical GUI screenshot.

For CLI visuals, prefer output copied from real application behavior and keep it synchronized with the corresponding Python presentation code.

## Accessibility

Every image embedded in Markdown must have meaningful alternative text that explains what a reader should understand from the visual.
