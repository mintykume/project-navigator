#!/usr/bin/env python3
"""Tests for exact profile placeholder handling across input formats."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib_pn import (  # noqa: E402
    compact_profile,
    critical_missing,
    load_profile,
    missing_field_ids,
    parse_profile_markdown,
    plan_workflow,
    profile_questions_for_task,
    resolve_profile,
    validate_profile,
)


PLACEHOLDERS = ("TBD", "tbd", "n/a", "N/A", "?", "unknown", " \tN/a  ")


def complete_profile(**overrides) -> dict:
    profile = {
        "primary_objective": "Build portfolio evidence",
        "time_budget": "Two weeks",
        "demonstrated_capabilities": ["Python"],
        "coding_level": "intermediate",
        "technical_interests": ["data engineering"],
    }
    profile.update(overrides)
    return profile


class ProfilePlaceholderTests(unittest.TestCase):
    def test_explicit_placeholder_forms_make_critical_field_missing(self):
        for value in PLACEHOLDERS:
            with self.subTest(value=value):
                profile = complete_profile(primary_objective=value)
                self.assertIn("primary_objective", critical_missing(profile))
                self.assertIn(
                    "missing_or_empty:primary_objective",
                    validate_profile(profile),
                )

    def test_placeholders_in_both_critical_fields_are_reported_missing(self):
        profile = complete_profile(
            primary_objective=" UNKNOWN ",
            time_budget="N/A",
        )
        self.assertEqual(
            critical_missing(profile),
            ["primary_objective", "time_budget"],
        )
        errors = validate_profile(profile)
        self.assertIn("missing_or_empty:primary_objective", errors)
        self.assertIn("missing_or_empty:time_budget", errors)

    def test_markdown_placeholder_is_missing_and_triggers_clarification(self):
        profile = parse_profile_markdown(
            "## primary_objective\n  tBd \n"
            "## time_budget\nTwo weeks\n"
            "## demonstrated_capabilities\n- Python\n"
            "## coding_level\nunknown\n"
            "## technical_interests\nN/A\n"
        )
        question = "What project should I build next?"

        self.assertIn("primary_objective", critical_missing(profile))
        self.assertTrue(plan_workflow(question=question, profile=profile)["needs_clarification"])
        asked_fields = {
            item["field"]
            for item in profile_questions_for_task(question, profile)
        }
        self.assertIn("primary_objective", asked_fields)
        self.assertIn("coding_level", asked_fields)
        self.assertIn("interests", asked_fields)

    def test_json_profile_uses_the_same_placeholder_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "profile.json"
            path.write_text(
                json.dumps(
                    complete_profile(
                        primary_objective="  N/A ",
                        time_budget=" TBD ",
                    )
                ),
                encoding="utf-8",
            )
            profile = load_profile(path)

        self.assertEqual(
            critical_missing(profile),
            ["primary_objective", "time_budget"],
        )
        self.assertIn("missing_or_empty:primary_objective", validate_profile(profile))

    def test_placeholder_only_capability_lists_count_as_missing(self):
        profile = complete_profile(
            demonstrated_capabilities=["TBD", "  n/A ", "?"],
            claimed_capabilities=["unknown"],
            emerging_capabilities=[],
        )
        self.assertIn("demonstrated_capabilities", critical_missing(profile))
        self.assertIn("missing_or_empty:capabilities", validate_profile(profile))

    def test_placeholder_only_optional_lists_and_fields_count_as_missing(self):
        profile = complete_profile(
            trajectory=" TBD ",
            artifacts=["N/A"],
            preferences={"research_vs_build": "unknown"},
            constraints={"location": " ? "},
        )
        missing = missing_field_ids(profile)
        self.assertIn("trajectory", missing)
        self.assertIn("artifacts", missing)
        self.assertIn("preferences.research_vs_build", missing)
        self.assertIn("constraints.location", missing)

    def test_legitimate_short_and_embedded_unknown_values_remain_valid(self):
        profile = complete_profile(
            primary_objective="Learn",
            time_budget="1 week",
            demonstrated_capabilities=["C"],
            trajectory="Study unknown failure modes",
        )
        self.assertEqual(validate_profile(profile), [])
        self.assertEqual(critical_missing(profile), [])

    def test_compact_profile_omits_placeholders_but_keeps_income_enum(self):
        compact = compact_profile(
            complete_profile(
                primary_objective=" TBD ",
                income_urgency="unknown",
                demonstrated_capabilities=["Python", "N/A"],
            )
        )
        self.assertNotIn("primary_objective", compact)
        self.assertEqual(compact["income_urgency"], "unknown")
        self.assertEqual(compact["demonstrated_capabilities"], ["Python"])

    def test_p0_question_facts_replace_placeholders(self):
        question = (
            "I'm a beginner coder interested in rock climbing. "
            "My goal is portfolio evidence, and I have 6 hours per week."
        )
        resolved = resolve_profile(
            profile=complete_profile(
                primary_objective="TBD",
                time_budget="unknown",
            ),
            current_question=question,
        )["profile"]

        self.assertEqual(resolved["primary_objective"], "portfolio evidence")
        self.assertEqual(resolved["time_budget"], "6 hours per week")
        self.assertEqual(critical_missing(resolved), [])


if __name__ == "__main__":
    unittest.main()
