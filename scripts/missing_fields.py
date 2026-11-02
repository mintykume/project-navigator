#!/usr/bin/env python3
"""List missing profile fields and mapped clarifying questions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib_pn import critical_missing, load_profile, missing_field_ids, read_question_bank, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument(
        "--critical-only",
        action="store_true",
        help="Only fields that block recommendation",
    )
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    profile = load_profile(args.profile)
    missing = (
        critical_missing(profile) if args.critical_only else missing_field_ids(profile)
    )
    missing = missing[: max(0, args.limit)] if args.limit else missing
    bank = read_question_bank()
    items = [
        {"field_id": fid, "question": bank.get(fid, f"(no bank entry for {fid})")}
        for fid in missing
    ]

    if args.json:
        write_text(None, json.dumps({"missing": items}, indent=2, ensure_ascii=False) + "\n")
    else:
        if not items:
            print("NONE")
        for item in items:
            print(f"{item['field_id']}: {item['question']}")

    return 1 if (args.critical_only and items) else 0


if __name__ == "__main__":
    sys.exit(main())
