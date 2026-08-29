#!/usr/bin/env python3
"""Validate a user profile markdown/JSON file against critical schema rules."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib_pn import dump_json, load_profile, validate_profile, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument(
        "--json-out",
        action="store_true",
        help="Print parsed profile JSON on success",
    )
    args = parser.parse_args()

    try:
        profile = load_profile(args.profile)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"ERROR: failed to load profile: {exc}", file=sys.stderr)
        return 2

    errors = validate_profile(profile)
    if errors:
        print("INVALID")
        for e in errors:
            print(e)
        return 1

    print("OK")
    if args.json_out:
        write_text(None, dump_json(profile))
    return 0


if __name__ == "__main__":
    sys.exit(main())
