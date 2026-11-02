#!/usr/bin/env python3
"""Regression tests for tolerant, exact-name profile heading parsing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib_pn import (  # noqa: E402
    critical_missing,
    load_profile,
    parse_profile_markdown,
    profile_questions_for_task,
    resolve_profile,
)


class ProfileParserTests(unittest.TestCase):
    def test_h1_profile_field_heading_is_parsed(self):
        profile = parse_profile_markdown(
            "# primary_objective\nBuild portfolio evidence.\n"
        )
        self.assertEqual(profile["primary_objective"], "Build portfolio evidence.")

    def test_h2_profile_field_heading_is_parsed(self):
        profile = parse_profile_markdown(
            "## time_budget\nEvenings, six hours a week.\n"
        )
        self.assertEqual(profile["time_budget"], "Evenings, six hours a week.")

    def test_trailing_colon_on_field_heading_is_accepted(self):
        profile = parse_profile_markdown(
            "## primary_objective:\nBuild portfolio evidence.\n"
        )
        self.assertEqual(profile["primary_objective"], "Build portfolio evidence.")

    def test_existing_canonical_profile_format_remains_supported(self):
        profile = load_profile(
            Path(__file__).resolve().parent / "fixtures" / "profile_valid.md"
        )
        self.assertEqual(
            profile["primary_objective"],
            "Build portfolio evidence toward a data engineering role.",
        )
        self.assertEqual(profile["preferences"]["working_style"], "deep focus blocks")
        self.assertIn("Python ETL scripts in personal repos", profile["demonstrated_capabilities"])

    def test_unrecognized_heading_is_ignored(self):
        profile = parse_profile_markdown(
            "## objective\nA vaguely similar but unsupported heading.\n"
            "## side_project\nThis is not a profile field.\n"
        )
        self.assertNotIn("objective", profile)
        self.assertNotIn("side_project", profile)
        self.assertNotIn("primary_objective", profile)

    def test_unknown_nested_heading_content_is_not_absorbed_into_field(self):
        profile = parse_profile_markdown(
            "## primary_objective\nLearn data engineering.\n"
            "### unrelated_notes\nThis is not profile data.\n"
            "## time_budget\nEvenings.\n"
        )
        self.assertEqual(profile["primary_objective"], "Learn data engineering.")
        self.assertEqual(profile["time_budget"], "Evenings.")

    def test_genuinely_missing_field_remains_critical_missing(self):
        profile = parse_profile_markdown(
            "# primary_objective\nLearn data engineering.\n"
            "## demonstrated_capabilities\n- Python\n"
        )
        self.assertIn("time_budget", critical_missing(profile))

    def test_raw_question_resolution_still_fills_profile_and_avoids_reasking(self):
        question = (
            "I'm a beginner coder interested in rock climbing. "
            "My goal is portfolio evidence, and I have 6 hours per week."
        )
        profile = parse_profile_markdown(
            "# primary_objective:\nLearning.\n"
            "## demonstrated_capabilities\n- Python\n"
        )
        resolved = resolve_profile(
            profile=profile,
            current_question=question,
        )["profile"]

        self.assertEqual(resolved["primary_objective"], "portfolio evidence")
        self.assertIn("6 hours per week", resolved["time_budget"])
        asked_fields = {
            item["field"]
            for item in profile_questions_for_task(question, resolved)
        }
        self.assertNotIn("primary_objective", asked_fields)
        self.assertNotIn("coding_level", asked_fields)
        self.assertNotIn("interests", asked_fields)


if __name__ == "__main__":
    unittest.main()
