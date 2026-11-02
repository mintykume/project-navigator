#!/usr/bin/env python3
"""Tests for evaluation profile validity and harness fail-fast behavior."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "evaluations"))

import run_project_evaluation as evaluation  # noqa: E402
from lib_pn import validate_profile  # noqa: E402


class EvaluationProfileTests(unittest.TestCase):
    def test_all_eight_shipped_profiles_pass_validation(self):
        self.assertEqual(len(evaluation.CASES), 8)
        self.assertEqual(evaluation.validate_case_profiles(evaluation.CASES), [])

    def test_income_urgency_uses_only_documented_contract_values(self):
        profile = {
            "primary_objective": "Build a useful prototype",
            "time_budget": "Two weeks",
            "demonstrated_capabilities": ["Python"],
        }
        for urgency in ("none", "soon", "immediate", "unknown"):
            with self.subTest(urgency=urgency):
                self.assertEqual(
                    validate_profile({**profile, "income_urgency": urgency}),
                    [],
                )

        errors = validate_profile({**profile, "income_urgency": "low urgency"})
        self.assertIn("invalid:income_urgency", errors)

    def test_invalid_evaluation_profile_is_reported_and_aborts_runner(self):
        invalid_profile = """\
# User profile

## primary_objective
Build a useful prototype.

## time_budget
Two weeks.

## income_urgency
low urgency

## demonstrated_capabilities
- Python
"""
        with tempfile.TemporaryDirectory() as directory:
            profile_path = Path(directory) / "invalid-profile.md"
            profile_path.write_text(invalid_profile, encoding="utf-8")
            case = {
                "id": "deliberately-invalid",
                "profile": str(profile_path),
                "question": "What should I work on?",
            }
            errors = evaluation.validate_case_profiles([case])
            stderr = io.StringIO()
            with (
                patch.object(evaluation, "CASES", [case]),
                patch.object(
                    evaluation,
                    "run_cmd",
                    wraps=evaluation.run_cmd,
                ) as run_cmd,
                contextlib.redirect_stderr(stderr),
            ):
                result = evaluation.main()

        self.assertEqual(len(errors), 1)
        self.assertIn("invalid:income_urgency", errors[0])
        self.assertEqual(result, 1)
        self.assertIn("deliberately-invalid", stderr.getvalue())
        self.assertIn("no scenarios were run", stderr.getvalue())
        self.assertEqual(run_cmd.call_count, 1)


if __name__ == "__main__":
    unittest.main()
