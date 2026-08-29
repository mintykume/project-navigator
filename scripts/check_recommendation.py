#!/usr/bin/env python3
"""Lint a recommendation markdown or JSON against the required contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

REQUIRED_SECTIONS = [
    ("recommendation", re.compile(r"^##\s+Recommendation\s*$", re.I | re.M)),
    ("why_you", re.compile(r"^##\s+Why you\s*$", re.I | re.M)),
    ("why_now", re.compile(r"^##\s+Why now\s*$", re.I | re.M)),
    ("existing_alternatives", re.compile(r"^##\s+Existing alternatives\s*$", re.I | re.M)),
    ("gap", re.compile(r"^##\s+The gap\s*$", re.I | re.M)),
    ("first_experiment", re.compile(r"^##\s+First experiment\s*$", re.I | re.M)),
    ("success_condition", re.compile(r"^##\s+Success condition\s*$", re.I | re.M)),
    ("capability_unlocked", re.compile(r"^##\s+Capability unlocked\s*$", re.I | re.M)),
    ("downstream_paths", re.compile(r"^##\s+Downstream paths\s*$", re.I | re.M)),
    ("trade_off", re.compile(r"^##\s+Trade-off\s*$", re.I | re.M)),
    ("alternative", re.compile(r"^##\s+Alternative\s*$", re.I | re.M)),
    ("confidence", re.compile(r"^##\s+Confidence\s*$", re.I | re.M)),
]

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


def _section_bodies(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.M))
    bodies: dict[str, str] = {}
    for i, m in enumerate(matches):
        title = m.group(1).strip().lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        bodies[title] = text[start:end].strip()
    return bodies


def lint_markdown(text: str) -> list[str]:
    errors: list[str] = []
    for name, pattern in REQUIRED_SECTIONS:
        if not pattern.search(text):
            errors.append(f"missing_section:{name}")

    bodies = _section_bodies(text)
    rec = bodies.get("recommendation", "")
    action_m = re.search(r"\*\*Action:\*\*\s*([a-z_]+)", rec, re.I)
    if not action_m:
        # also allow plain Action:
        action_m = re.search(r"Action:\s*([a-z_]+)", rec, re.I)
    if not action_m:
        errors.append("missing:recommendation.action")
    else:
        action = action_m.group(1).lower()
        if action not in ACTIONS:
            errors.append(f"invalid:recommendation.action:{action}")

    summary_m = re.search(r"\*\*Summary:\*\*\s*(.+)", rec, re.I)
    if not summary_m:
        summary_m = re.search(r"Summary:\s*(.+)", rec, re.I)
    if not summary_m or not summary_m.group(1).strip():
        errors.append("missing:recommendation.summary")

    gap = bodies.get("the gap", "")
    if "missing_section:gap" not in errors and len(gap.strip()) < 8:
        errors.append("empty:gap")

    conf = bodies.get("confidence", "")
    for label in ("Known", "Inferred", "Unknown"):
        if not re.search(rf"{label}\s*:", conf, re.I):
            errors.append(f"missing:confidence.{label.lower()}")

    # Placeholder leftovers
    if "<!--" in text:
        errors.append("contains:html_comments_placeholders")

    return errors


def lint_json(data: dict) -> list[str]:
    errors: list[str] = []
    required = [
        "recommendation",
        "why_you",
        "why_now",
        "existing_alternatives",
        "gap",
        "first_experiment",
        "success_condition",
        "capability_unlocked",
        "downstream_paths",
        "trade_off",
        "alternative",
        "confidence",
    ]
    for key in required:
        if key not in data:
            errors.append(f"missing_field:{key}")

    rec = data.get("recommendation")
    if not isinstance(rec, dict):
        errors.append("invalid:recommendation")
    else:
        action = rec.get("action")
        if action not in ACTIONS:
            errors.append(f"invalid:recommendation.action:{action}")
        if not str(rec.get("summary") or "").strip():
            errors.append("missing:recommendation.summary")

    conf = data.get("confidence")
    if not isinstance(conf, dict):
        errors.append("invalid:confidence")
    else:
        for k in ("known", "inferred", "unknown"):
            if not str(conf.get(k) or "").strip():
                errors.append(f"missing:confidence.{k}")

    paths = data.get("downstream_paths")
    if not isinstance(paths, list) or not paths:
        errors.append("missing:downstream_paths")

    if not str(data.get("gap") or "").strip():
        errors.append("empty:gap")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="infile", required=True, type=Path)
    args = parser.parse_args()

    raw = args.infile.read_text(encoding="utf-8")
    if args.infile.suffix.lower() == ".json":
        errors = lint_json(json.loads(raw))
    else:
        errors = lint_markdown(raw)

    if errors:
        print("INVALID")
        for e in errors:
            print(e)
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
