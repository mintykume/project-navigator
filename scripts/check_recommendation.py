#!/usr/bin/env python3
"""Validate recommendation structure and explicit policy violations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib_pn import (
    NOT_SEARCHED,
    SEARCHED_NO_RESULTS,
    SEARCHED_NO_USABLE_EVIDENCE,
    SEARCHED_WITH_RESULTS,
)

REQUIRED_SECTIONS = (
    "recommendation",
    "why_you",
    "why_now",
    "existing_alternatives",
    "the_gap",
    "first_experiment",
    "success_condition",
    "capability_unlocked",
    "downstream_paths",
    "trade_off",
    "alternative",
    "confidence",
)
TEXT_FIELDS = (
    "why_you",
    "why_now",
    "existing_alternatives",
    "gap",
    "first_experiment",
    "success_condition",
    "capability_unlocked",
    "trade_off",
    "alternative",
)
ACTIONS = {
    "build",
    "study",
    "reproduce",
    "contribute",
    "extend",
    "research",
    "earn",
    "network",
    "wait",
    "dont",
}
_ACTION_PATTERN = "|".join(sorted(ACTIONS, key=len, reverse=True))
_HOLLOW_VALUES = {
    "",
    "-",
    "--",
    "—",
    "...",
    "…",
    "tbd",
    "todo",
    "n/a",
    "na",
    "none",
    "placeholder",
    "to be determined",
    "fill in",
    "insert text",
}
_NOVELTY_CLAIMS = (
    re.compile(
        r"\b(?:first[- ]ever|only|unique|unprecedented|novel|original)\s+"
        r"(?:[\w-]+\s+){0,3}"
        r"(?:app|application|tool|project|product|platform|system|solution|"
        r"framework|service|dashboard|marketplace)s?\b",
        re.I,
    ),
    re.compile(
        r"\b(?:this|the idea|this idea|the project|this project|the product|"
        r"this product)\s+(?:is|will be|would be)\s+(?:the\s+)?"
        r"(?:first|only|unique|unprecedented|novel|original)\b",
        re.I,
    ),
    re.compile(
        r"\bno\s+(?:(?:other|existing|similar)\s+)?"
        r"(?:[\w-]+\s+){0,2}"
        r"(?:apps?|tools?|projects?|products?|platforms?|solutions?|"
        r"frameworks?|services?|alternatives?|competitors?)\b"
        r"(?:\s+(?:exist|exists|are available|have been built))?",
        re.I,
    ),
    re.compile(
        r"\bno one has (?:ever\s+)?(?:built|made|created|done)\b|"
        r"\b(?:nothing|no product|no tool|no app) like this "
        r"(?:exists|has been built|has been done)\b|"
        r"\bnever been (?:built|made|created|done)\b",
        re.I,
    ),
)
_MULTI_ACTIONS = re.compile(
    rf"\b(?:{_ACTION_PATTERN})\b.{{0,50}}"
    rf"(?:/|,|;|\b(?:or|and|then|alternatively)\b).{{0,30}}"
    rf"\b(?:{_ACTION_PATTERN})\b",
    re.I,
)
_LONG_DURATION = re.compile(
    r"\b(?:\d+\s*-\s*\d+|[2-9]\d*|2|3|4|5|6|7|8|9|"
    r"two|three|four|five|six|seven|eight|nine|several|multiple|a few)\s*"
    r"(?:-| )?\s*weeks?\b|"
    r"\b(?:\d+\s*-\s*\d+|[1-9]\d*|one|two|three|four|five|six|"
    r"several|multiple|a few|a)\s*(?:-| )?\s*months?\b|"
    r"\b(?:multi[- ]week|multi[- ]month)\b",
    re.I,
)
_BUILD_ACTION = re.compile(
    r"\b(?:build|create|implement|develop|ship|launch|code|deliver)\w*\b",
    re.I,
)
_FULL_SCOPE = re.compile(
    r"\b(?:full|complete|entire|whole|production[- ]ready|end[- ]to[- ]end|"
    r"from scratch|all features)\b|"
    r"\b(?:app|application|platform|product|system|service|framework|"
    r"marketplace|dashboard)\b",
    re.I,
)


def _canonical_heading(title: str) -> str:
    name = re.sub(r"[^a-z0-9]+", "_", title.strip().lower()).strip("_")
    if name == "trade_offs":
        return "trade_off"
    return name


def _section_bodies(text: str) -> tuple[dict[str, str], list[str]]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.M))
    bodies: dict[str, str] = {}
    duplicates: list[str] = []
    for index, match in enumerate(matches):
        title = _canonical_heading(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        if title in bodies:
            duplicates.append(title)
        bodies[title] = text[start:end].strip()
    return bodies, duplicates


def _is_hollow(value: object) -> bool:
    if not isinstance(value, str):
        return True
    text = re.sub(r"<!--.*?-->", " ", value, flags=re.S)
    lines = []
    for line in text.splitlines():
        line = re.sub(r"^\s*[-*+]\s+", "", line)
        line = re.sub(r"[*_`~]", "", line)
        normalized = re.sub(r"\s+", " ", line).strip(" \t\r\n.,;:!?")
        lines.append(normalized.lower())
    meaningful = [line for line in lines if line]
    return not meaningful or all(line in _HOLLOW_VALUES for line in meaningful)


def _field_value(section: str, name: str) -> str | None:
    labels = {
        "action": rf"(?:\*\*Action:\*\*|Action:)",
        "summary": rf"(?:\*\*Summary:\*\*|Summary:)",
    }
    match = re.search(
        rf"(?im)^\s*{labels[name]}\s*(.*?)\s*$",
        section,
    )
    return match.group(1).strip() if match else None


def _natural_action(value: str) -> tuple[str | None, bool, str]:
    text = value.strip()
    natural = re.match(r"^(?:don['’]t|do not|dont)\s+build\b", text, re.I)
    if natural:
        return "dont", True, text[natural.end():].strip()
    match = re.match(r"([a-z_]+)\b", text, re.I)
    if not match:
        return None, False, text
    return match.group(1).lower(), False, text[match.end():].strip()


def _has_multiple_actions(value: str, *, natural_dont: bool) -> bool:
    if natural_dont:
        _, _, remainder = _natural_action(value)
        if re.search(
            rf"\b(?:and|or|then|alternatively)\b.{{0,40}}\b(?:{_ACTION_PATTERN})\b",
            remainder,
            re.I,
        ):
            return True
        value = re.sub(
            r"^(?:don['’]t|do not|dont)\s+build\b",
            "dont",
            value.strip(),
            flags=re.I,
        )
    return bool(_MULTI_ACTIONS.search(value))


def _novelty_claim_present(text: str) -> bool:
    return any(pattern.search(text) for pattern in _NOVELTY_CLAIMS)


def _experiment_findings(text: str) -> list[str]:
    if not (_LONG_DURATION.search(text) and _BUILD_ACTION.search(text)):
        return []
    if _FULL_SCOPE.search(text):
        return ["not_cheapest_experiment:multiweek_full_build"]
    return ["warning:experiment_duration_multiweek"]


def _policy_findings(text: str, retrieval_status: str) -> list[str]:
    if (
        retrieval_status
        in {
            NOT_SEARCHED,
            SEARCHED_NO_RESULTS,
            SEARCHED_NO_USABLE_EVIDENCE,
        }
        and _novelty_claim_present(text)
    ):
        return ["unsupported:novelty_claim_without_usable_prior_art"]
    return []


def lint_markdown(
    text: str,
    retrieval_status: str = NOT_SEARCHED,
) -> list[str]:
    errors: list[str] = []
    bodies, duplicates = _section_bodies(text)
    for name in REQUIRED_SECTIONS:
        if name not in bodies:
            errors.append(f"missing_section:{name}")
        elif _is_hollow(bodies[name]):
            errors.append(f"hollow_section:{name}")
    for name in duplicates:
        errors.append(f"duplicate_section:{name}")

    recommendation = bodies.get("recommendation", "")
    action_matches = list(
        re.finditer(
            r"(?im)^\s*(?:\*\*Action:\*\*|Action:)\s*(.*?)\s*$",
            recommendation,
        )
    )
    if not action_matches:
        errors.append("missing:recommendation.action")
    elif len(action_matches) > 1:
        errors.append("multiple:recommendation.action")
    else:
        action_value = action_matches[0].group(1).strip()
        action, natural_dont, _ = _natural_action(action_value)
        if _has_multiple_actions(action_value, natural_dont=natural_dont):
            errors.append("multiple:recommendation.actions")
        if action not in ACTIONS:
            errors.append(f"invalid:recommendation.action:{action or action_value.lower()}")

    summary = _field_value(recommendation, "summary")
    if summary is None:
        errors.append("missing:recommendation.summary")
    elif _is_hollow(summary):
        errors.append("empty:recommendation.summary")

    if "confidence" in bodies:
        confidence = bodies["confidence"]
        for label in ("Known", "Inferred", "Unknown"):
            match = re.search(
                rf"(?im)^\s*(?:[-*]\s*)?"
                rf"(?:\*\*{label}:\*\*|{label}:)\s*(.*?)\s*$",
                confidence,
            )
            if not match:
                errors.append(f"missing:confidence.{label.lower()}")
            elif _is_hollow(match.group(1)):
                errors.append(f"empty:confidence.{label.lower()}")

    if "<!--" in text:
        errors.append("contains:html_comments_placeholders")

    scan_text = "\n".join(
        bodies.get(section, "")
        for section in (
            "recommendation",
            "why_you",
            "why_now",
            "existing_alternatives",
            "the_gap",
            "first_experiment",
        )
    )
    errors.extend(_policy_findings(scan_text, retrieval_status))
    errors.extend(_experiment_findings(bodies.get("first_experiment", "")))
    return errors


def lint_json(
    data: dict,
    retrieval_status: str = NOT_SEARCHED,
) -> list[str]:
    errors: list[str] = []
    for key in ("recommendation", *TEXT_FIELDS, "downstream_paths", "confidence"):
        if key not in data:
            errors.append(f"missing_field:{key}")

    recommendation = data.get("recommendation")
    if not isinstance(recommendation, dict):
        errors.append("invalid:recommendation")
    else:
        action_value = recommendation.get("action")
        if not isinstance(action_value, str):
            errors.append(f"invalid:recommendation.action:{action_value}")
        else:
            action, natural_dont, _ = _natural_action(action_value)
            if _has_multiple_actions(action_value, natural_dont=natural_dont):
                errors.append("multiple:recommendation.actions")
            if action not in ACTIONS:
                errors.append(f"invalid:recommendation.action:{action or action_value.lower()}")

        summary = recommendation.get("summary")
        if _is_hollow(summary):
            errors.append("empty:recommendation.summary")

    for key in TEXT_FIELDS:
        value = data.get(key)
        if not isinstance(value, str):
            errors.append(f"invalid:{key}")
        elif _is_hollow(value):
            errors.append(f"empty:{key}")

    paths = data.get("downstream_paths")
    if not isinstance(paths, list) or not paths:
        errors.append("missing:downstream_paths")
    else:
        for index, path in enumerate(paths):
            if _is_hollow(path):
                errors.append(f"empty:downstream_paths.{index}")

    confidence = data.get("confidence")
    if not isinstance(confidence, dict):
        errors.append("invalid:confidence")
    else:
        for label in ("known", "inferred", "unknown"):
            value = confidence.get(label)
            if not isinstance(value, str):
                errors.append(f"invalid:confidence.{label}")
            elif _is_hollow(value):
                errors.append(f"empty:confidence.{label}")

    scan_values = [
        recommendation.get("summary", "") if isinstance(recommendation, dict) else "",
        *(data.get(key, "") for key in TEXT_FIELDS),
    ]
    errors.extend(_policy_findings("\n".join(v for v in scan_values if isinstance(v, str)), retrieval_status))
    errors.extend(_experiment_findings(str(data.get("first_experiment") or "")))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="infile", required=True, type=Path)
    parser.add_argument(
        "--retrieval-status",
        choices=[
            NOT_SEARCHED,
            SEARCHED_WITH_RESULTS,
            SEARCHED_NO_RESULTS,
            SEARCHED_NO_USABLE_EVIDENCE,
        ],
        default=NOT_SEARCHED,
        help="Prior-art state from preflight; defaults conservatively to NOT_SEARCHED",
    )
    args = parser.parse_args()

    try:
        raw = args.infile.read_text(encoding="utf-8")
        if args.infile.suffix.lower() == ".json":
            data = json.loads(raw)
            errors = (
                lint_json(data, args.retrieval_status)
                if isinstance(data, dict)
                else ["invalid:root"]
            )
        else:
            errors = lint_markdown(raw, args.retrieval_status)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    warnings = [message for message in errors if message.startswith("warning:")]
    failures = [message for message in errors if not message.startswith("warning:")]
    if failures:
        print("INVALID")
        for message in failures:
            print(message)
        for warning in warnings:
            print(warning)
        return 1
    if warnings:
        print("WARN")
        for warning in warnings:
            print(warning)
        return 0

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
