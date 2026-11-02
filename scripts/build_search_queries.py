#!/usr/bin/env python3
"""Build deterministic search queries from question + profile."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib_pn import compact_profile, has_local_search_need, load_profile, write_text

_OPPORTUNITY_SEARCH_TERMS = re.compile(
    r"\b(?:opportunit(?:y|ies)|jobs?|internships?|scholarships?|fellowships?|"
    r"grants?|hackathons?|meetups?|events?|accelerators?|labs?|civic[- ]tech|"
    r"volunteer(?:ing)?|communities|community|resources?|makerspaces?|"
    r"coworking|contribut(?:e|ion|ions)|organizations?)\b",
    re.I,
)
_KEYWORD_PATTERN = re.compile(r"[^\W\d_][\w+#.-]*", re.UNICODE)
_TRAILING_KEYWORD_PUNCTUATION = ".,;:!?-"


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
        "want",
        "wants",
        "wanted",
    }
    normalized_question = unicodedata.normalize("NFC", question).casefold()
    words = [
        word.rstrip(_TRAILING_KEYWORD_PUNCTUATION)
        for word in _KEYWORD_PATTERN.findall(normalized_question)
    ]
    keys = [word for word in words if len(word) > 1 and word not in stop]
    # Add a few capability tokens
    for field in (
        "demonstrated_capabilities",
        "claimed_capabilities",
        "emerging_capabilities",
    ):
        for item in profile.get(field) or []:
            if isinstance(item, str):
                parts = item.strip().split()
                token = (
                    parts[0].casefold().rstrip(_TRAILING_KEYWORD_PUNCTUATION)
                    if parts
                    else ""
                )
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


def build_opportunity_context(question: str, profile: dict) -> dict:
    """Expose location and whether geography is relevant to opportunity discovery."""
    compacted = compact_profile(profile)
    constraints = compacted.get("constraints")
    location = constraints.get("location") if isinstance(constraints, dict) else None
    if not isinstance(location, str) or not location:
        location_parts = [
            compacted.get(field)
            for field in ("city", "country")
            if isinstance(compacted.get(field), str) and compacted[field]
        ]
        location = ", ".join(location_parts) if location_parts else None

    context = {
        "local_opportunity_search_requested": (
            has_local_search_need(question)
            and bool(_OPPORTUNITY_SEARCH_TERMS.search(question))
        )
    }
    if location:
        context["location"] = location
    return context


def build_queries(question: str, profile: dict, max_queries: int = 6) -> dict:
    keys = _keywords(question, compact_profile(profile))
    topic = " ".join(keys[:4])
    opportunity_context = build_opportunity_context(question, profile)

    intents = [
        ("github_repos", f"{topic} github"),
        ("apps_products", f"{topic} application OR tool OR product"),
        ("papers", f"{topic} research paper"),
        ("datasets", f"{topic} dataset"),
        ("apis_standards", f"{topic} API OR standard OR specification"),
    ]
    location = opportunity_context.get("location")
    if opportunity_context["local_opportunity_search_requested"] and location:
        intents.append(
            ("opportunities", f"{topic} {location} hackathon OR lab OR community")
        )

    queries = []
    for i, (intent, query) in enumerate(intents[:max_queries]):
        queries.append({"id": f"q{i+1}", "query": query, "intent": intent})

    return {
        "queries": queries,
        "max_hits": 12,
        "fact_fields": ["title", "url", "snippet", "source_class", "query_id"],
        "sources_allowed": ["web", "github", "host_tools"],
        "opportunity_context": opportunity_context,
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
