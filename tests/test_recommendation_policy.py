#!/usr/bin/env python3
"""Policy-aware recommendation linter regression tests."""

from __future__ import annotations

import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_recommendation.py"
PY = sys.executable
sys.path.insert(0, str(ROOT / "scripts"))

from lib_pn import (  # noqa: E402
    NOT_SEARCHED,
    SEARCHED_NO_RESULTS,
    SEARCHED_NO_USABLE_EVIDENCE,
    SEARCHED_WITH_RESULTS,
)
from check_recommendation import lint_json, lint_markdown  # noqa: E402


CONCISE_MARKDOWN = """\
## Recommendation

**Action:** Do not build a generic climbing dashboard.

**Summary:** Study one active tool and reproduce a single data-fetch slice.

## Why you

Your Python practice makes this a realistic short exercise.

## Why now

It fits the time available this week.

## Existing alternatives

Several established climbing apps already serve general route tracking.

## The gap

The learning gap is understanding one existing data pipeline.

## First experiment

Spend 30 minutes running one data fetch and note what fails.

## Success condition

Continue only if the fetch exposes a specific limitation.

## Capability unlocked

You will practice tracing an API-backed data path.

## Downstream paths

- Write a short technical note.

## Trade-offs

You give up a flashy new interface for focused evidence.

## Alternative

If income is the priority, offer a small paid automation.

## Confidence

- **Known:** The user has basic Python experience.
- **Inferred:** Reproduction is more useful than a new dashboard.
- **Unknown:** Which app has the best local route data.
"""


def valid_json() -> dict:
    return {
        "recommendation": {
            "action": "study",
            "summary": "Trace one existing route-data fetch.",
        },
        "why_you": "Python experience makes this accessible.",
        "why_now": "A short test fits this week's schedule.",
        "existing_alternatives": "Several route trackers already exist.",
        "gap": "The useful gap is understanding data freshness.",
        "first_experiment": "Spend 30 minutes tracing one endpoint.",
        "success_condition": "Continue if you find a concrete data issue.",
        "capability_unlocked": "Practice tracing API-backed data.",
        "downstream_paths": ["Write a short technical note."],
        "trade_off": "You defer a polished interface.",
        "alternative": "Choose paid automation if income is urgent.",
        "confidence": {
            "known": "The user has Python experience.",
            "inferred": "Tracing data adds more value than a new UI.",
            "unknown": "The best local route-data source.",
        },
    }


class RecommendationPolicyTests(unittest.TestCase):
    def test_concise_valid_markdown_and_tradeoffs_heading_pass(self):
        self.assertEqual(lint_markdown(CONCISE_MARKDOWN), [])

    def test_concise_valid_json_passes(self):
        self.assertEqual(lint_json(valid_json()), [])

    def test_placeholder_section_body_is_rejected(self):
        text = CONCISE_MARKDOWN.replace(
            "Your Python practice makes this a realistic short exercise.",
            "TODO",
        )
        self.assertIn("hollow_section:why_you", lint_markdown(text))

    def test_empty_json_values_are_rejected(self):
        data = valid_json()
        data["recommendation"]["summary"] = ""
        data["why_you"] = ""
        data["capability_unlocked"] = "TBD"
        data["downstream_paths"] = ["..."]
        data["confidence"]["unknown"] = "N/A"

        errors = lint_json(data)
        self.assertIn("empty:recommendation.summary", errors)
        self.assertIn("empty:why_you", errors)
        self.assertIn("empty:capability_unlocked", errors)
        self.assertIn("empty:downstream_paths.0", errors)
        self.assertIn("empty:confidence.unknown", errors)

    def test_novelty_claim_requires_usable_prior_art(self):
        text = CONCISE_MARKDOWN.replace(
            "The learning gap is understanding one existing data pipeline.",
            "This is the first climbing dashboard of its kind.",
        )
        self.assertIn("**Unknown:**", text)
        self.assertIn(
            "unsupported:novelty_claim_without_usable_prior_art",
            lint_markdown(text, NOT_SEARCHED),
        )
        self.assertIn(
            "unsupported:novelty_claim_without_usable_prior_art",
            lint_markdown(text, SEARCHED_NO_RESULTS),
        )
        self.assertIn(
            "unsupported:novelty_claim_without_usable_prior_art",
            lint_markdown(text, SEARCHED_NO_USABLE_EVIDENCE),
        )
        self.assertNotIn(
            "unsupported:novelty_claim_without_usable_prior_art",
            lint_markdown(text, SEARCHED_WITH_RESULTS),
        )

    def test_json_novelty_claim_requires_usable_prior_art(self):
        data = valid_json()
        data["existing_alternatives"] = "No similar climbing tools exist."
        errors = lint_json(data, SEARCHED_NO_RESULTS)
        self.assertIn(
            "unsupported:novelty_claim_without_usable_prior_art",
            errors,
        )

    def test_multiweek_full_build_is_rejected_as_first_experiment(self):
        text = CONCISE_MARKDOWN.replace(
            "Spend 30 minutes running one data fetch and note what fails.",
            "Spend eight weeks building a complete climbing platform from scratch.",
        )
        self.assertIn(
            "not_cheapest_experiment:multiweek_full_build",
            lint_markdown(text),
        )

    def test_long_but_narrow_experiment_warns_without_failing(self):
        text = CONCISE_MARKDOWN.replace(
            "Spend 30 minutes running one data fetch and note what fails.",
            "Build one narrow API probe over two weeks.",
        )
        findings = lint_markdown(text)
        self.assertIn("warning:experiment_duration_multiweek", findings)
        self.assertNotIn(
            "not_cheapest_experiment:multiweek_full_build",
            findings,
        )

    def test_duration_warning_does_not_fail_cli_validation(self):
        text = CONCISE_MARKDOWN.replace(
            "Spend 30 minutes running one data fetch and note what fails.",
            "Build one narrow API probe over two weeks.",
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "recommendation.md"
            path.write_text(text, encoding="utf-8")
            result = subprocess.run(
                [
                    PY,
                    str(SCRIPT),
                    "--in",
                    str(path),
                    "--retrieval-status",
                    NOT_SEARCHED,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("WARN", result.stdout)
        self.assertIn("warning:experiment_duration_multiweek", result.stdout)

    def test_multiple_actions_in_action_field_are_rejected(self):
        text = CONCISE_MARKDOWN.replace(
            "**Action:** Do not build a generic climbing dashboard.",
            "**Action:** build or study",
        )
        self.assertIn("multiple:recommendation.actions", lint_markdown(text))

    def test_natural_dont_build_action_is_normalized(self):
        for action in ("Don't build a generic dashboard.", "Do not build a generic dashboard."):
            with self.subTest(action=action):
                text = CONCISE_MARKDOWN.replace(
                    "**Action:** Do not build a generic climbing dashboard.",
                    f"**Action:** {action}",
                )
                self.assertFalse(
                    any(error.startswith("invalid:recommendation.action") for error in lint_markdown(text))
                )

    def test_unsupported_natural_action_does_not_expand_action_vocabulary(self):
        text = CONCISE_MARKDOWN.replace(
            "**Action:** Do not build a generic climbing dashboard.",
            "**Action:** Avoid building a generic dashboard.",
        )
        self.assertIn(
            "invalid:recommendation.action:avoid",
            lint_markdown(text),
        )

    def test_json_natural_action_is_normalized(self):
        data = valid_json()
        data["recommendation"]["action"] = "Don't build a generic dashboard."
        errors = lint_json(data)
        self.assertFalse(
            any(error.startswith("invalid:recommendation.action") for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
