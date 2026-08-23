# Documentation image assets

This directory contains the visual assets used by the recruiter-facing project documentation.

## Canonical assets

- `gui-main-window.png` is the approved real capture of the main Tkinter window.
- `gui-main-window.json` stores the capture provenance, dimensions, SHA-256 digest, source commit, and approval state for the canonical GUI image.
- `cli-validation-example.svg` is the deterministic CLI validation example embedded in the README.

## Naming conventions

Use descriptive, lowercase, hyphen-separated names. Keep the canonical GUI screenshot and its provenance manifest together so a reviewer can verify that the documented image is the exact capture that passed the release workflow.

## Capture rules

Documentation images should represent the current application rather than a redesigned mockup.

For GUI captures:

1. Install development dependencies with `python3 -m pip install -r requirements-dev.txt`.
2. Run `python3 capture_gui_screenshot.py` from a clean checkout in a desktop session or use the equivalent Xvfb-backed CI capture.
3. Keep the default window size unless a feature specifically requires a larger view.
4. Use sample data only; do not include personal or production data.
5. Verify the complete application window is visible with readable controls and output.
6. Verify the generated PNG and JSON provenance pair.
7. Promote the reviewed pair with `publish_gui_screenshot.py`.
8. Confirm the canonical output is `docs/images/gui-main-window.png` with the matching `docs/images/gui-main-window.json`.
9. Update the README only after verifying the stored image matches the current UI.

The capture command instantiates the real `OrderIntegrityCheckerGUI` and captures its rendered window bounds. A hand-drawn replacement is not acceptable as the canonical GUI screenshot.

For CLI visuals, prefer output copied from real application behavior and keep it synchronized with the corresponding Python presentation code.

## Accessibility

Every image embedded in Markdown must have meaningful alternative text that explains what a reader should understand from the visual.
