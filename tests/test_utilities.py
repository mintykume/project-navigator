#!/usr/bin/env python3
"""Tests for Project Navigator deterministic utilities."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))

from assemble_context import assemble  # noqa: E402
from build_search_queries import _keywords, build_queries  # noqa: E402
from check_recommendation import lint_markdown  # noqa: E402
from lib_pn import (  # noqa: E402
    critical_missing,
    load_profile,
    missing_field_ids,
    plan_workflow,
    profile_questions_for_task,
    resolve_profile,
    validate_profile,
)
from normalize_retrieval import normalize_hits  # noqa: E402


class ValidateProfileTests(unittest.TestCase):
    def test_valid_profile(self):
        profile = load_profile(FIXTURES / "profile_valid.md")
        self.assertEqual(validate_profile(profile), [])
        self.assertIn("Python ETL scripts in personal repos", profile["demonstrated_capabilities"])

    def test_incomplete_profile(self):
        profile = load_profile(FIXTURES / "profile_incomplete.md")
        errors = validate_profile(profile)
        self.assertTrue(any(e.startswith("missing_or_empty:primary_objective") for e in errors))
        self.assertTrue(any("capabilities" in e for e in errors))


class MissingFieldsTests(unittest.TestCase):
    def test_incomplete_critical(self):
        profile = load_profile(FIXTURES / "profile_incomplete.md")
        missing = critical_missing(profile)
        self.assertIn("primary_objective", missing)
        self.assertIn("time_budget", missing)
        self.assertIn("demonstrated_capabilities", missing)

    def test_valid_has_no_critical_missing(self):
        profile = load_profile(FIXTURES / "profile_valid.md")
        self.assertEqual(critical_missing(profile), [])
        self.assertIsInstance(missing_field_ids(profile), list)


class ProfileResolutionTests(unittest.TestCase):
    def test_complete_profile_requires_no_questions(self):
        profile = {
            "primary_objective": "Build portfolio evidence",
            "time_budget": "Evenings",
            "coding_level": "intermediate",
            "technical_interests": ["AI/ML", "backend"],
            "country": "Germany",
            "demonstrated_capabilities": ["Python", "SQL"],
        }
        resolved = resolve_profile(profile=profile)
        self.assertEqual(profile_questions_for_task("What project should I build next?", resolved["profile"]), [])

    def test_missing_coding_level_asks_coding_level(self):
        profile = {
            "primary_objective": "Build portfolio evidence",
            "time_budget": "Evenings",
            "demonstrated_capabilities": ["Python"],
        }
        questions = profile_questions_for_task("What project should I build next?", profile)
        self.assertTrue(any("coding level" in q["text"].lower() for q in questions))

    def test_missing_interests_asks_interests(self):
        profile = {
            "primary_objective": "Build portfolio evidence",
            "time_budget": "Evenings",
            "coding_level": "intermediate",
            "demonstrated_capabilities": ["Python"],
        }
        questions = profile_questions_for_task("What project should I build next?", profile)
        self.assertTrue(any("which areas are you most interested" in q["text"].lower() for q in questions))

    def test_missing_country_when_local_research_is_needed(self):
        profile = {
            "primary_objective": "Get hired",
            "time_budget": "Evenings",
            "coding_level": "intermediate",
            "technical_interests": ["backend"],
            "demonstrated_capabilities": ["Python"],
        }
        questions = profile_questions_for_task("Which local jobs should I target in my area?", profile)
        self.assertTrue(any(q["field"] == "country" for q in questions))

    def test_country_known_but_city_unnecessary(self):
        profile = {
            "primary_objective": "Get hired",
            "time_budget": "Evenings",
            "coding_level": "intermediate",
            "technical_interests": ["backend"],
            "country": "Germany",
            "demonstrated_capabilities": ["Python"],
        }
        questions = profile_questions_for_task("Which local jobs should I target in Germany?", profile)
        self.assertFalse(any(q["field"] == "city" for q in questions))

    def test_country_known_and_city_materially_affects_the_request(self):
        profile = {
            "primary_objective": "Get hired",
            "time_budget": "Evenings",
            "coding_level": "intermediate",
            "technical_interests": ["backend"],
            "country": "Germany",
            "demonstrated_capabilities": ["Python"],
        }
        questions = profile_questions_for_task("Which local jobs are strongest in my city near Berlin?", profile)
        self.assertTrue(any(q["field"] == "city" for q in questions))

    def test_conversation_context_reused_without_reasking(self):
        profile = {
            "primary_objective": "Build something",
            "time_budget": "Evenings",
            "coding_level": "intermediate",
            "technical_interests": ["AI/ML"],
            "demonstrated_capabilities": ["Python"],
        }
        resolved = resolve_profile(
            profile={"primary_objective": "Build something", "time_budget": "Evenings"},
            context={"current_conversation": {"coding_level": "intermediate", "technical_interests": ["AI/ML"]}},
        )
        questions = profile_questions_for_task("What project should I build next?", resolved["profile"])
        self.assertFalse(any(q["field"] in {"coding_level", "interests"} for q in questions))

    def test_newer_information_overrides_older_information(self):
        resolved = resolve_profile(
            profile={"coding_level": "beginner"},
            context={"host_context": {"coding_level": "intermediate"}},
        )
        self.assertEqual(resolved["profile"]["coding_level"], "intermediate")

    def test_inferred_information_is_lower_confidence(self):
        resolved = resolve_profile(
            profile={},
            context={"inferred_profile": {"coding_level": "intermediate"}},
        )
        self.assertLess(resolved["profile_metadata"]["coding_level"]["confidence"], 1.0)
        self.assertTrue(resolved["profile_metadata"]["coding_level"].get("inference"))

    def test_contradictory_information_is_explicitly_recorded(self):
        resolved = resolve_profile(
            profile={"coding_level": "beginner"},
            context={"current_conversation": {"coding_level": "advanced"}},
        )
        self.assertTrue(any("coding_level" in c for c in resolved["contradictions"]))
        self.assertEqual(resolved["profile"]["coding_level"], "advanced")

    def test_unrelated_missing_fields_do_not_block_workflow(self):
        profile = {
            "primary_objective": "Build portfolio evidence",
            "time_budget": "Evenings",
            "coding_level": "intermediate",
            "technical_interests": ["backend"],
            "demonstrated_capabilities": ["Python"],
        }
        questions = profile_questions_for_task("Which of these three projects should I build?", profile)
        self.assertEqual(questions, [])

    def test_public_fixtures_do_not_write_private_data(self):
        visible = [p.name for p in (ROOT / "tests" / "fixtures").glob("*.md")]
        self.assertNotIn("my-profile.md", visible)
        self.assertNotIn("dinner-table.md", visible)

    def test_private_project_examples_are_excluded_from_public_evaluation_data(self):
        case_names = [p.name for p in (ROOT / "evaluations" / "cases").glob("*.md")]
        self.assertFalse(any(name in case_names for name in ["dinner-table.md", "pixi-tutor.md", "opportunity-bot.md", "ar-circuits.md", "sign-language.md", "adaptive-study-room.md"]))


class WorkflowPlanTests(unittest.TestCase):
    def test_clarify_stops_workflow(self):
        profile = load_profile(FIXTURES / "profile_incomplete.md")
        plan = plan_workflow(
            question="Should I build a dashboard?",
            profile=profile,
            mode="quick",
        )
        self.assertTrue(plan["needs_clarification"])
        self.assertEqual(plan["active_stages"], ["profile_resolution", "s1_clarify"])
        self.assertFalse(plan["run_s4_now"])

    def test_build_intent_gates_research_on_quick(self):
        profile = load_profile(FIXTURES / "profile_valid.md")
        plan = plan_workflow(
            question="Should I build a new ETL framework?",
            profile=profile,
            mode="quick",
        )
        self.assertTrue(plan["research_justified"])
        self.assertTrue(plan["skip_s4"])
        self.assertEqual(plan["next_action"], "offer_quick_vs_deep")
        self.assertNotIn("s4_existing_work_check", plan["active_stages"])
        self.assertIn("s8_recommend", plan["active_stages"])

    def test_deep_mode_runs_s4(self):
        profile = load_profile(FIXTURES / "profile_valid.md")
        plan = plan_workflow(
            question="Should I build a new ETL framework?",
            profile=profile,
            mode="deep",
        )
        self.assertTrue(plan["run_s4_now"])
        self.assertIn("s4_existing_work_check", plan["active_stages"])

    def test_prioritize_only_skips_research(self):
        profile = load_profile(FIXTURES / "profile_valid.md")
        plan = plan_workflow(
            question="Which learning path should I prioritize between SQL and Spark?",
            profile=profile,
            mode="quick",
        )
        self.assertFalse(plan["research_justified"])
        self.assertEqual(plan["next_action"], "continue_without_research")

    def test_existing_facts_skip_s4(self):
        profile = load_profile(FIXTURES / "profile_valid.md")
        plan = plan_workflow(
            question="Should I build a tool?",
            profile=profile,
            mode="deep",
            has_retrieval_facts=True,
        )
        self.assertFalse(plan["run_s4_now"])
        self.assertEqual(plan["next_action"], "continue_from_gaps")


class AssembleContextTests(unittest.TestCase):
    def test_pack_under_budget_and_compact(self):
        profile = load_profile(FIXTURES / "profile_valid.md")
        pack = assemble(
            question="What should I work on next?",
            mode="quick",
            profile=profile,
            max_chars=8000,
        )
        self.assertEqual(pack["parts"]["mode"], "quick")
        self.assertLessEqual(pack["char_count"], 8000)
        self.assertIn("workflow_plan", pack["parts"])
        self.assertNotIn("<!--", pack["parts"]["output_template"])
        self.assertIn("primary_objective", json.dumps(pack["parts"]["profile"]))
        self.assertLess(pack["char_count"], 6000)

class BuildSearchQueriesTests(unittest.TestCase):
    def test_stable_queries(self):
        profile = load_profile(FIXTURES / "profile_valid.md")
        brief = build_queries("Should I build a new ETL framework?", profile)
        self.assertGreaterEqual(len(brief["queries"]), 3)
        ids = [q["id"] for q in brief["queries"]]
        self.assertEqual(ids, sorted(set(ids)))
        intents = {q["intent"] for q in brief["queries"]}
        self.assertIn("github_repos", intents)
        self.assertNotIn("opportunities", intents)

    def test_removes_filler_and_terminal_punctuation(self):
        self.assertEqual(_keywords("I want to study math.", {}), ["study", "math"])

    def test_preserves_technical_tokens(self):
        self.assertEqual(
            _keywords("Build with C++, C#, and Node.js.", {}),
            ["c++", "c#", "node.js"],
        )

    def test_preserves_complete_unicode_words(self):
        self.assertEqual(
            _keywords("I want to study matematică.", {}),
            ["study", "matematică"],
        )


class NormalizeRetrievalTests(unittest.TestCase):
    def test_dedupe_and_fields(self):
        raw = json.loads((FIXTURES / "retrieval_hits.json").read_text(encoding="utf-8"))
        facts = normalize_hits(raw["hits"])
        self.assertEqual(len(facts), 2)
        for fact in facts:
            for key in ("title", "url", "snippet", "source_class", "query_id"):
                self.assertIn(key, fact)
        classes = {f["source_class"] for f in facts}
        self.assertIn("github_repo", classes)
        self.assertIn("paper", classes)


class CheckRecommendationTests(unittest.TestCase):
    def test_valid_fixture(self):
        text = (FIXTURES / "recommendation_valid.md").read_text(encoding="utf-8")
        self.assertEqual(lint_markdown(text), [])

    def test_missing_gap_fails(self):
        text = (FIXTURES / "recommendation_valid.md").read_text(encoding="utf-8")
        text = text.replace("## The gap\n\nYour gap is evidenced collaboration on a real codebase, not another personal toolkit.\n", "## The gap\n\n\n")
        errors = lint_markdown(text)
        self.assertTrue(any("gap" in e for e in errors) or errors)


if __name__ == "__main__":
    unittest.main()
