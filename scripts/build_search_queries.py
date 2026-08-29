#!/usr/bin/env python3
"""Build deterministic search queries from question + profile."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib_pn import compact_profile, load_profile, write_text


def _keywords(question: str, profile: dict) -> list[str]:
    stop = {
        "a",
        "an",
        "the",
        "and",
        "or",
        "to",
        "for",
        "of",
        "in",
        "on",
        "with",
        "what",
        "should",
        "i",
        "my",
        "me",
        "next",
        "project",
        "build",
        "work",
        "on",
    }
    words = re.findall(r"[A-Za-z][A-Za-z0-9+.#-]{1,}", question.lower())
    keys = [w for w in words if w not in stop]
    # Add a few capability tokens
    for field in (
        "demonstrated_capabilities",
        "claimed_capabilities",
        "emerging_capabilities",
    ):
        for item in profile.get(field) or []:
            if isinstance(item, str):
                token = item.strip().split()[0].lower()
                if token and token not in keys and token not in stop:
                    keys.append(token)
            if len(keys) >= 8:
                break
    # stable unique
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out[:8] or ["open source project"]


def build_queries(question: str, profile: dict, max_queries: int = 6) -> dict:
    keys = _keywords(question, compact_profile(profile))
    topic = " ".join(keys[:4])
    loc = ""
    constraints = profile.get("constraints") or {}
    if isinstance(constraints, dict):
        loc = (constraints.get("location") or "").strip()

    intents = [
        ("github_repos", f"{topic} github"),
        ("apps_products", f"{topic} application OR tool OR product"),
        ("papers", f"{topic} research paper"),
        ("datasets", f"{topic} dataset"),
        ("apis_standards", f"{topic} API OR standard OR specification"),
    ]
    if loc:
        intents.append(
            ("opportunities", f"{topic} {loc} hackathon OR lab OR community")
        )

    queries = []
    for i, (intent, query) in enumerate(intents[:max_queries]):
        queries.append({"id": f"q{i+1}", "query": query, "intent": intent})

    return {
        "queries": queries,
        "max_hits": 12,
        "fact_fields": ["title", "url", "snippet", "source_class", "query_id"],
        "sources_allowed": ["web", "github", "host_tools"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--question", required=True)
    parser.add_argument("--max-queries", type=int, default=6)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    brief = build_queries(args.question, profile, max_queries=args.max_queries)
    text = json.dumps(brief, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        write_text(args.out, text)
        print(f"Wrote {args.out}")
    else:
        write_text(None, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
