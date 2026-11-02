#!/usr/bin/env python3
"""CLI smoke tests mirroring individual script entrypoints."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PY = sys.executable


def run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


class ScriptSmokeTests(unittest.TestCase):
    def test_validate_ok(self):
        r = run([PY, str(SCRIPTS / "validate_profile.py"), "--profile", str(FIXTURES / "profile_valid.md")])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK", r.stdout)

    def test_validate_bad(self):
        r = run([PY, str(SCRIPTS / "validate_profile.py"), "--profile", str(FIXTURES / "profile_incomplete.md")])
        self.assertEqual(r.returncode, 1)
        self.assertIn("INVALID", r.stdout)

    def test_preflight_clarification(self):
        r = run(
            [
                PY,
                str(SCRIPTS / "run_preflight.py"),
                "--profile",
                str(FIXTURES / "profile_incomplete.md"),
                "--question",
                "What next?",
            ]
        )
        self.assertEqual(r.returncode, 1)
        data = json.loads(r.stdout)
        self.assertEqual(data["status"], "needs_clarification")

    def test_preflight_ready(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "pack.json"
            r = run(
                [
                    PY,
                    str(SCRIPTS / "run_preflight.py"),
                    "--profile",
                    str(FIXTURES / "profile_valid.md"),
                    "--question",
                    "What should I work on next?",
                    "--mode",
                    "quick",
                    "--out",
                    str(out),
                ]
            )
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "ready")
            self.assertIn("context_pack", data)

    def test_normalize_and_check(self):
        with tempfile.TemporaryDirectory() as td:
            facts = Path(td) / "facts.json"
            r = run(
                [
                    PY,
                    str(SCRIPTS / "normalize_retrieval.py"),
                    "--in",
                    str(FIXTURES / "retrieval_hits.json"),
                    "--question",
                    "What prior art exists for ETL pipeline lineage data engineering?",
                    "--out",
                    str(facts),
                ]
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            payload = json.loads(facts.read_text(encoding="utf-8"))
            self.assertEqual(payload["count"], 2)

        r2 = run(
            [
                PY,
                str(SCRIPTS / "check_recommendation.py"),
                "--in",
                str(FIXTURES / "recommendation_valid.md"),
            ]
        )
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("OK", r2.stdout)

    def test_sample_profile_preflight(self):
        sample = ROOT / "examples" / "sample-profile.md"
        r = run(
            [
                PY,
                str(SCRIPTS / "run_preflight.py"),
                "--profile",
                str(sample),
                "--question",
                "What should I work on this month?",
                "--mode",
                "quick",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(data["status"], "ready")
        self.assertIn("workflow_plan", data)

    def test_build_question_awaits_research_decision(self):
        r = run(
            [
                PY,
                str(SCRIPTS / "run_preflight.py"),
                "--profile",
                str(FIXTURES / "profile_valid.md"),
                "--question",
                "Should I build a new ETL framework?",
                "--mode",
                "quick",
            ]
        )
        self.assertEqual(r.returncode, 3, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(data["status"], "awaiting_research_decision")
        self.assertTrue(data["workflow_plan"]["research_justified"])
        self.assertFalse(data["workflow_plan"]["run_s4_now"])

    def test_explicit_deep_request_runs_search_from_cli(self):
        r = run(
            [
                PY,
                str(SCRIPTS / "run_preflight.py"),
                "--profile",
                str(FIXTURES / "profile_valid.md"),
                "--question",
                "Do a deep prior-art search for a climbing route planner.",
                "--mode",
                "quick",
            ]
        )
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(data["mode"], "deep")
        self.assertEqual(data["context_pack"]["parts"]["mode"], "deep")
        self.assertTrue(data["workflow_plan"]["run_s4_now"])

    def test_preflight_uses_profile_facts_from_question(self):
        question = (
            "I'm a beginner coder interested in rock climbing. "
            "My objective is learning; I can spend 4 hours a week."
        )
        r = run(
            [
                PY,
                str(SCRIPTS / "run_preflight.py"),
                "--profile",
                str(FIXTURES / "profile_incomplete.md"),
                "--question",
                question,
            ]
        )
        self.assertEqual(r.returncode, 1, r.stderr + r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(
            [item["field_id"] for item in data["missing"]],
            ["demonstrated_capabilities"],
        )
        asked = {item["field"] for item in data["targeted_questions"]}
        self.assertNotIn("coding_level", asked)
        self.assertNotIn("interests", asked)
        self.assertNotIn("primary_objective", asked)
        self.assertEqual(data["resolved_profile"]["profile"]["time_budget"], "4 hours a week")


if __name__ == "__main__":
    unittest.main()
