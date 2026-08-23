import argparse

from screenshot_release import promote_verified_screenshot


def build_parser():
    parser = argparse.ArgumentParser(
        description="Promote a verified GUI screenshot pair to canonical documentation assets."
    )
    parser.add_argument("screenshot", help="Path to the reviewed PNG capture.")
    parser.add_argument("manifest", help="Path to the matching provenance JSON.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    result = promote_verified_screenshot(args.screenshot, args.manifest)
    print(f"Published GUI screenshot: {result['screenshot']}")
    print(f"Published provenance: {result['manifest']}")
    print(f"SHA-256: {result['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
