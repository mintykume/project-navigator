#!/usr/bin/env python3
"""Orchestrate clarify gate -> workflow plan -> (optional research) -> context pack."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from assemble_context import assemble
from build_search_queries import build_queries
from lib_pn import (
    NOT_SEARCHED,
    critical_missing,
    load_profile,
    plan_workflow,
    profile_questions_for_task,
    read_question_bank,
    resolve_profile,
    validate_profile,
    write_text,
)
from normalize_retrieval import prepare_retrieval


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--question", required=True)
    parser.add_argument("--mode", choices=["quick", "deep"], default="quick")
    parser.add_argument(
        "--research-decision",
        choices=["quick", "deep"],
        help="Resolve an awaiting_research_decision state",
    )
    parser.add_argument("--context", type=Path, help="Optional JSON file with host memory/current context")
    parser.add_argument("--retrieval", type=Path, help="Normalized facts JSON")
    parser.add_argument("--out", type=Path, help="Write JSON result")
    parser.add_argument("--max-chars", type=int, default=8000)
    parser.add_argument(
        "--with-pack",
        action="store_true",
        help="Include context_pack even when waiting on research decision",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Assemble even if critical fields missing",
    )
    args = parser.parse_args()

    try:
        profile = load_profile(args.profile)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    context: dict = {}
    if args.context and args.context.exists():
        try:
            context = json.loads(args.context.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError) as exc:
            print(f"ERROR: failed to load context: {exc}", file=sys.stderr)
            return 2

    resolved = resolve_profile(
        profile=profile,
        context=context,
        current_question=args.question,
    )
    profile = resolved["profile"]
    errors = validate_profile(profile)
    missing = critical_missing(profile)

    facts: list = []
    retrieval_status = NOT_SEARCHED
    if args.retrieval:
        try:
            data = json.loads(args.retrieval.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError) as exc:
            print(f"ERROR: failed to load retrieval data: {exc}", file=sys.stderr)
            return 2
        if isinstance(data, list):
            facts = data
            declared_status = None
        elif isinstance(data, dict):
            if "facts" not in data and "retrieval_status" not in data:
                print(
                    "ERROR: normalized retrieval object must contain facts or retrieval_status",
                    file=sys.stderr,
                )
                return 2
            facts = data.get("facts", [])
            declared_status = data.get("retrieval_status")
        else:
            print(
                "ERROR: retrieval data must be a JSON list or object",
                file=sys.stderr,
            )
            return 2
        if not isinstance(facts, list):
            print("ERROR: retrieval facts must be a JSON list", file=sys.stderr)
            return 2
        try:
            facts, retrieval_status = prepare_retrieval(
                facts,
                question=args.question,
                retrieval_status=declared_status,
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    try:
        plan = plan_workflow(
            question=args.question,
            profile=profile,
            mode=args.mode,
            research_decision=args.research_decision,
            retrieval_status=retrieval_status,
            allow_incomplete=args.allow_incomplete,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if plan["needs_clarification"]:
        bank = read_question_bank()
        targeted = profile_questions_for_task(args.question, profile)
        payload = {
            "status": "needs_clarification",
            "stage": "profile_resolution",
            "workflow_plan": plan,
            "missing": [
                {"field_id": f, "question": bank.get(f, "")} for f in missing[:3]
            ],
            "targeted_questions": targeted[:3],
            "resolved_profile": resolved,
            "validate_errors": errors,
        }
        write_text(None, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        return 1

    result: dict = {
        "status": "ready",
        "mode": plan["mode"],
        "workflow_plan": plan,
    }

    if plan["next_action"] == "offer_quick_vs_deep":
        result["status"] = "awaiting_research_decision"
        result["message"] = (
            "Research is justified but mode is quick. Ask: quick answer now, "
            "or deep prior-art search before recommending?"
        )

    if plan["run_s4_now"]:
        result["retrieval_brief"] = build_queries(args.question, profile)
        result["retrieval_note"] = (
            "S4: host-search retrieval_brief.queries, normalize_retrieval.py "
            "--question \"<original user question>\", "
            "re-run with --retrieval."
        )

    include_pack = result["status"] == "ready" or args.with_pack or bool(args.out)
    if include_pack:
        result["context_pack"] = assemble(
            question=args.question,
            mode=plan["mode"],
            profile=profile,
            retrieval_facts=facts,
            retrieval_status=retrieval_status,
            workflow_plan=plan,
            max_chars=args.max_chars,
        )

    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        write_text(args.out, text)
        print(f"Wrote {args.out} status={result['status']}")
    else:
        write_text(None, text)

    if result["status"] == "awaiting_research_decision":
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
