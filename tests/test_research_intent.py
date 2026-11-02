#!/usr/bin/env python3
"""Regression tests for deterministic research-intent classification."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib_pn import load_profile, plan_workflow, research_signals  # noqa: E402


class ResearchIntentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile(ROOT / "tests" / "fixtures" / "profile_valid.md")

    def test_natural_project_phrases_are_build_intent(self):
        questions = (
            "I'm thinking of building a climbing route planner.",
            "Should I work on a project about rock climbing?",
            "I have an idea for an app that tracks climbing routes.",
            "Should I write a parser?",
            "Should I code a climbing route planner?",
            "Give me beginner coding project ideas around rock climbing.",
        )
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(research_signals(question)["build_intent"])
                plan = plan_workflow(question=question, profile=self.profile)
                self.assertTrue(plan["research_justified"])

    def test_existence_questions_trigger_research(self):
        questions = (
            "Has this been done before?",
            "Is this idea original?",
            "Does a local inventory tool already exist?",
        )
        for question in questions:
            with self.subTest(question=question):
                self.assertTrue(research_signals(question)["existence_intent"])
                plan = plan_workflow(question=question, profile=self.profile)
                self.assertTrue(plan["research_justified"])

    def test_learning_questions_do_not_become_build_intent(self):
        questions = (
            "What tool should I learn?",
            "Which API should I learn?",
            "How should I develop my skills?",
            "How can I make money with my Python skills?",
        )
        for question in questions:
            with self.subTest(question=question):
                signals = research_signals(question)
                self.assertFalse(signals["build_intent"])
                self.assertFalse(signals["existence_intent"])
                plan = plan_workflow(question=question, profile=self.profile)
                self.assertFalse(plan["research_justified"])

    def test_temporal_between_phrase_is_not_project_comparison(self):
        signals = research_signals(
            "What should I focus on between my exams and my internship?"
        )
        self.assertFalse(signals["option_comparison"])
        self.assertFalse(signals["build_intent"])

    def test_build_choice_is_distinct_from_learning_prioritization(self):
        signals = research_signals(
            "Which should I build first: a CLI, dashboard, or bot?"
        )
        self.assertTrue(signals["build_intent"])
        self.assertTrue(signals["option_comparison"])
        self.assertFalse(signals["learning_only"])
        self.assertTrue(
            plan_workflow(
                question="Which should I build first: a CLI, dashboard, or bot?",
                profile=self.profile,
            )["research_justified"]
        )

        learning = research_signals(
            "Which learning path should I prioritize between SQL and Spark?"
        )
        self.assertTrue(learning["learning_only"])
        self.assertFalse(learning["option_comparison"])
        self.assertFalse(
            plan_workflow(
                question="Which learning path should I prioritize between SQL and Spark?",
                profile=self.profile,
            )["research_justified"]
        )

    def test_negated_build_does_not_trigger_affirmative_build_intent(self):
        signals = research_signals(
            "I don't want to build a parser; I just want to use one."
        )
        self.assertTrue(signals["negated_build_intent"])
        self.assertFalse(signals["build_intent"])
        self.assertFalse(
            plan_workflow(
                question="I don't want to build a parser; I just want to use one.",
                profile=self.profile,
            )["research_justified"]
        )

    def test_affirmative_build_after_negation_is_preserved(self):
        signals = research_signals(
            "I don't want to build a parser, but I may create a route planner."
        )
        self.assertTrue(signals["negated_build_intent"])
        self.assertTrue(signals["build_intent"])

    def test_explicit_deep_request_is_classified_and_honored(self):
        profile = load_profile(ROOT / "tests" / "fixtures" / "profile_valid.md")
        question = "Do a deep prior-art search for a climbing route planner."
        signals = research_signals(question)
        self.assertTrue(signals["explicit_deep_request"])

        plan = plan_workflow(question=question, profile=profile, mode="quick")
        self.assertEqual(plan["mode"], "deep")
        self.assertTrue(plan["research_justified"])
        self.assertTrue(plan["run_s4_now"])


if __name__ == "__main__":
    unittest.main()
