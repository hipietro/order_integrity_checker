# Documentation image assets

This directory contains visual assets used by the project documentation.

## Naming conventions

Use descriptive, lowercase, hyphen-separated names:

- `gui-main-window.png` for a real capture of the main Tkinter window
- `cli-validation-example.svg` for the deterministic CLI example used in the README

## Capture rules

Documentation images should represent the current application rather than a redesigned mockup.

For GUI captures:

1. Run `python3 gui.py` from a clean checkout.
2. Keep the default window size unless a feature specifically requires a larger view.
3. Use sample data only; do not include personal or production data.
4. Capture the complete application window with readable controls and output.
5. Save the image as `docs/images/gui-main-window.png`.
6. Update the README only after verifying the stored image matches the current UI.

For CLI visuals, prefer output copied from real application behavior and keep it synchronized with the corresponding Python presentation code.

## Accessibility

Every image embedded in Markdown must have meaningful alternative text that explains what a reader should understand from the visual.
