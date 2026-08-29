#!/usr/bin/env python3
"""Plan the modular reasoning workflow and research gate (no LLM)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib_pn import load_profile, plan_workflow, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--question", required=True)
    parser.add_argument("--mode", choices=["quick", "deep"], default="quick")
    parser.add_argument(
        "--has-retrieval",
        action="store_true",
        help="Normalized retrieval facts already available",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Plan past clarification even if critical fields missing",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    plan = plan_workflow(
        question=args.question,
        profile=profile,
        mode=args.mode,
        has_retrieval_facts=args.has_retrieval,
        allow_incomplete=args.allow_incomplete,
    )
    text = json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        write_text(args.out, text)
        print(f"Wrote {args.out} next_action={plan['next_action']}")
    else:
        write_text(None, text)
    return 1 if plan["needs_clarification"] else 0


if __name__ == "__main__":
    sys.exit(main())
