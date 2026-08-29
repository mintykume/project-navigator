#!/usr/bin/env python3
"""Assemble a budgeted context pack for the recommend stage (S8)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib_pn import (
    PROMPTS,
    TEMPLATES,
    compact_profile,
    load_profile,
    plan_workflow,
    strip_html_comments,
    write_text,
)


DEFAULT_MAX_CHARS = 8000


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def assemble(
    *,
    question: str,
    mode: str,
    profile: dict,
    retrieval_facts: list | None = None,
    include_recommend_prompt: bool = True,
    workflow_plan: dict | None = None,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> dict:
    facts = retrieval_facts or []
    plan = workflow_plan or plan_workflow(
        question=question,
        profile=profile,
        mode=mode,
        has_retrieval_facts=bool(facts),
    )

    parts = {
        "policy": _read(PROMPTS / "core-policy.md"),
        "question": question.strip(),
        "mode": mode,
        "profile": compact_profile(profile),
        "retrieval_facts": facts,
        "workflow_plan": {
            "active_stages": plan.get("active_stages"),
            "research_justified": plan.get("research_justified"),
            "run_s4_now": plan.get("run_s4_now"),
            "skip_s4": plan.get("skip_s4"),
            "next_action": plan.get("next_action"),
            "research_reasons": plan.get("research_reasons"),
            "prior_art": (
                "checked"
                if facts
                else (
                    "deferred"
                    if plan.get("research_justified")
                    else "not_required_or_unchecked"
                )
            ),
        },
        "output_template": strip_html_comments(
            _read(TEMPLATES / "decision-output.md")
        ),
    }
    if include_recommend_prompt:
        parts["recommend_rules"] = _read(PROMPTS / "stages" / "s8-recommend.md")

    pack = {
        "version": 2,
        "instruction": (
            "S8 only: fill output_template using this pack. "
            "Do not load README. One recommendation."
        ),
        "parts": parts,
    }

    encoded = json.dumps(pack, ensure_ascii=False)
    if len(encoded) > max_chars and pack["parts"]["retrieval_facts"]:
        trimmed = []
        for fact in pack["parts"]["retrieval_facts"]:
            f = dict(fact)
            f["snippet"] = str(f.get("snippet", ""))[:160]
            trimmed.append(f)
        pack["parts"]["retrieval_facts"] = trimmed
        encoded = json.dumps(pack, ensure_ascii=False)

    if len(encoded) > max_chars:
        pack["parts"].pop("recommend_rules", None)
        pack["parts_omitted"] = ["recommend_rules"]
        encoded = json.dumps(pack, ensure_ascii=False)

    if len(encoded) > max_chars:
        pack["parts"]["policy"] = pack["parts"]["policy"][:1200] + "\n...(truncated)"
        pack.setdefault("parts_omitted", []).append("policy_truncated")

    pack["char_count"] = len(json.dumps(pack, ensure_ascii=False))
    return pack


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--question", required=True)
    parser.add_argument("--mode", choices=["quick", "deep"], default="quick")
    parser.add_argument("--retrieval", type=Path, help="Normalized facts JSON")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    facts = []
    if args.retrieval:
        data = json.loads(args.retrieval.read_text(encoding="utf-8"))
        facts = data if isinstance(data, list) else data.get("facts", [])

    pack = assemble(
        question=args.question,
        mode=args.mode,
        profile=profile,
        retrieval_facts=facts,
        max_chars=args.max_chars,
    )
    text = json.dumps(pack, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        write_text(args.out, text)
        print(f"Wrote {args.out} ({pack['char_count']} chars)")
    else:
        write_text(None, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
