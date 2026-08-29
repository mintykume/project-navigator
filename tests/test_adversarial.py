#!/usr/bin/env python3
"""Adversarial workflow-gate tests for Project Navigator."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ADV = Path(__file__).resolve().parent / "adversarial"
sys.path.insert(0, str(SCRIPTS))

from lib_pn import load_profile, plan_workflow  # noqa: E402

VALID_ACTIONS = {
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


def _load_cases() -> list[dict]:
    data = json.loads((ADV / "cases.json").read_text(encoding="utf-8"))
    return data["cases"]


class AdversarialCaseCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = _load_cases()

    def test_catalog_covers_required_categories(self):
        cats = {c["category"] for c in self.cases}
        required = {
            "generic_project_idea",
            "already_solved",
            "beginner_user",
            "advanced_user",
            "immediate_money",
            "long_term_career",
            "conflicting_preferences",
            "sustainability",
            "research",
            "insufficient_information",
        }
        self.assertTrue(required.issubset(cats), f"missing categories: {required - cats}")

    def test_case_ids_unique_and_profiles_exist(self):
        ids = [c["id"] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case in self.cases:
            path = ADV / case["profile"]
            self.assertTrue(path.is_file(), f"missing profile for {case['id']}: {path}")
            expect = case["expect"]
            for key in ("preferred_actions", "discouraged_actions", "rational_stance"):
                self.assertIn(key, expect)
            for action in expect["preferred_actions"] + expect["discouraged_actions"]:
                self.assertIn(action, VALID_ACTIONS)
            # Rational cases should not treat build as the only preferred action
            preferred = expect["preferred_actions"]
            if preferred and set(preferred) == {"build"}:
                self.fail(f"{case['id']} only prefers build; adversarial suite rejects project-defaulting")


class AdversarialWorkflowGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = _load_cases()

    def test_each_case_workflow_gates(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                profile = load_profile(ADV / case["profile"])
                expect = case["expect"]
                if "income_urgency" in expect:
                    self.assertEqual(
                        str(profile.get("income_urgency", "")).lower(),
                        expect["income_urgency"],
                    )

                plan = plan_workflow(
                    question=case["question"],
                    profile=profile,
                    mode=case.get("mode", "quick"),
                    has_retrieval_facts=bool(case.get("has_retrieval_facts")),
                )

                self.assertEqual(
                    plan["needs_clarification"],
                    expect["needs_clarification"],
                    msg=plan,
                )
                self.assertEqual(
                    plan["research_justified"],
                    expect["research_justified"],
                    msg=plan,
                )
                self.assertEqual(plan["next_action"], expect["next_action"], msg=plan)
                self.assertEqual(plan["run_s4_now"], expect["run_s4_now"], msg=plan)

                if "active_stages" in expect:
                    self.assertEqual(plan["active_stages"], expect["active_stages"])

                if expect["needs_clarification"]:
                    self.assertEqual(plan["active_stages"], ["profile_resolution", "s1_clarify"])
                    self.assertFalse(plan["run_s4_now"])

                # Never jump to S4 when clarification is required
                if plan["needs_clarification"]:
                    self.assertNotIn("s4_existing_work_check", plan["active_stages"])

                # Expensive stage only when explicitly run_s4_now
                if not plan["run_s4_now"]:
                    self.assertNotIn("s4_existing_work_check", plan["active_stages"])


class AdversarialRationalStanceTests(unittest.TestCase):
    """Documented judgment constraints (not LLM-executed)."""

    @classmethod
    def setUpClass(cls):
        cls.cases = {c["id"]: c for c in _load_cases()}

    def test_insufficient_info_forbids_all_actions_until_clarify(self):
        case = self.cases["insufficient-info"]
        self.assertEqual(case["expect"]["preferred_actions"], [])
        self.assertIn("build", case["expect"]["discouraged_actions"])

    def test_generic_and_solved_discourage_build(self):
        for case_id in (
            "generic-todo-app",
            "generic-ai-wrapper",
            "already-solved-weather",
            "beginner-weather-rebuild",
            "sustainability-dashboard",
            "research-paper-impl",
        ):
            expect = self.cases[case_id]["expect"]
            self.assertIn(
                "build",
                expect["discouraged_actions"],
                msg=f"{case_id} should discourage reflexive building",
            )
            self.assertNotIn("build", expect["preferred_actions"])

    def test_immediate_money_prefers_earn_not_platform_build(self):
        for case_id in ("immediate-money-freelance", "immediate-money-no-build-claim"):
            expect = self.cases[case_id]["expect"]
            self.assertIn("earn", expect["preferred_actions"])
            self.assertIn("build", expect["discouraged_actions"])

    def test_conflicting_prefs_surfaces_non_build_preference(self):
        expect = self.cases["conflicting-prefs"]["expect"]
        self.assertIn("dont", expect["preferred_actions"])
        self.assertIn("build", expect["discouraged_actions"])
        self.assertIn("conflict", expect["rational_stance"].lower())

    def test_advanced_may_allow_build_only_after_gap(self):
        expect = self.cases["advanced-gap-hunt"]["expect"]
        self.assertIn("build", expect["preferred_actions"])
        self.assertTrue(expect["run_s4_now"])
        self.assertIn("gap", expect["rational_stance"].lower())


if __name__ == "__main__":
    unittest.main()
