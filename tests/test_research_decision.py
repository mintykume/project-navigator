#!/usr/bin/env python3
"""End-to-end tests for the quick/deep research decision transition."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_preflight.py"
PLANNER_SCRIPT = ROOT / "scripts" / "plan_workflow.py"
PROFILE = ROOT / "tests" / "fixtures" / "profile_valid.md"
PY = sys.executable
QUESTION = "Should I build a new ETL framework?"


def run_preflight(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            PY,
            str(SCRIPT),
            "--profile",
            str(PROFILE),
            "--question",
            QUESTION,
            "--mode",
            "quick",
            *extra,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ResearchDecisionTransitionTests(unittest.TestCase):
    def test_build_request_enters_awaiting_state(self):
        result = run_preflight()

        self.assertEqual(result.returncode, 3, result.stderr + result.stdout)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "awaiting_research_decision")
        self.assertTrue(data["workflow_plan"]["awaiting_research_decision"])
        self.assertIsNone(data["workflow_plan"]["research_decision"])

    def test_quick_decision_resumes_without_s4(self):
        result = run_preflight("--research-decision", "quick")

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        data = json.loads(result.stdout)
        plan = data["workflow_plan"]
        self.assertEqual(data["status"], "ready")
        self.assertEqual(plan["research_decision"], "quick")
        self.assertFalse(plan["awaiting_research_decision"])
        self.assertEqual(plan["next_action"], "continue_without_research")
        self.assertFalse(plan["run_s4_now"])

    def test_deep_decision_enters_research_path(self):
        result = run_preflight("--research-decision", "deep")

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        data = json.loads(result.stdout)
        plan = data["workflow_plan"]
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["mode"], "deep")
        self.assertEqual(plan["research_decision"], "deep")
        self.assertFalse(plan["awaiting_research_decision"])
        self.assertEqual(plan["next_action"], "run_existing_work_search")
        self.assertTrue(plan["run_s4_now"])
        self.assertIn("retrieval_brief", data)

    def test_same_decision_is_deterministic_across_invocations(self):
        for decision in ("quick", "deep"):
            with self.subTest(decision=decision):
                first = run_preflight("--research-decision", decision)
                second = run_preflight("--research-decision", decision)
                self.assertEqual(first.returncode, second.returncode)
                self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))

    def test_invalid_decision_is_rejected(self):
        result = run_preflight("--research-decision", "maybe")

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr.lower())
        self.assertIn("quick", result.stderr)
        self.assertIn("deep", result.stderr)

    def test_decision_cannot_override_a_non_awaiting_workflow(self):
        result = subprocess.run(
            [
                PY,
                str(SCRIPT),
                "--profile",
                str(PROFILE),
                "--question",
                "What should I work on this month?",
                "--research-decision",
                "deep",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("only valid when the workflow is awaiting", result.stderr)

    def test_planner_cli_accepts_choice_and_rejects_mode_conflict(self):
        command = [
            PY,
            str(PLANNER_SCRIPT),
            "--profile",
            str(PROFILE),
            "--question",
            QUESTION,
            "--research-decision",
            "quick",
        ]
        accepted = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(accepted.returncode, 0, accepted.stderr + accepted.stdout)
        self.assertEqual(
            json.loads(accepted.stdout)["research_decision"],
            "quick",
        )

        conflict = subprocess.run(
            [*command, "--mode", "deep"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(conflict.returncode, 2)
        self.assertIn("only valid when the workflow is awaiting", conflict.stderr)


if __name__ == "__main__":
    unittest.main()
