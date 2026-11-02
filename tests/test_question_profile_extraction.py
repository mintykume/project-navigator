#!/usr/bin/env python3
"""Regression tests for profile facts stated in the current user question."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib_pn import (  # noqa: E402
    critical_missing,
    profile_questions_for_task,
    resolve_profile,
)


class QuestionProfileExtractionTests(unittest.TestCase):
    def test_beginner_project_request_does_not_reask_level_or_interest(self):
        question = "I want beginner coding project ideas around rock climbing."
        profile = {
            "primary_objective": "learning",
            "time_budget": "two weeks",
            "demonstrated_capabilities": ["basic Python"],
        }

        questions = profile_questions_for_task(question, profile)
        asked_fields = {item["field"] for item in questions}
        self.assertNotIn("coding_level", asked_fields)
        self.assertNotIn("interests", asked_fields)

    def test_explicit_facts_are_added_to_resolved_profile(self):
        question = (
            "I'm a beginner coder interested in rock climbing. "
            "My goal is portfolio evidence, and I have 6 hours per week."
        )
        resolved = resolve_profile(profile={}, current_question=question)["profile"]

        self.assertEqual(resolved["coding_level"], "beginner")
        self.assertEqual(resolved["technical_interests"], ["rock climbing"])
        self.assertEqual(resolved["primary_objective"], "portfolio evidence")
        self.assertIn("6 hours per week", resolved["time_budget"])

    def test_unstated_fields_still_generate_targeted_questions(self):
        questions = profile_questions_for_task("What project should I build next?", {})
        asked_fields = {item["field"] for item in questions}

        self.assertIn("coding_level", asked_fields)
        self.assertIn("interests", asked_fields)
        self.assertIn("primary_objective", asked_fields)

    def test_mixed_question_facts_leave_only_capabilities_critical_missing(self):
        question = (
            "I'm a beginner coder interested in rock climbing. "
            "My objective is learning; I can spend 4 hours a week."
        )
        resolved = resolve_profile(profile={}, current_question=question)["profile"]

        self.assertEqual(
            critical_missing(resolved),
            ["demonstrated_capabilities"],
        )
        asked_fields = {
            item["field"]
            for item in profile_questions_for_task(question, resolved)
        }
        self.assertNotIn("coding_level", asked_fields)
        self.assertNotIn("interests", asked_fields)
        self.assertNotIn("primary_objective", asked_fields)


if __name__ == "__main__":
    unittest.main()
