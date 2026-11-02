#!/usr/bin/env python3
"""Tests for location as conditional opportunity context."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from assemble_context import assemble  # noqa: E402
from build_search_queries import (  # noqa: E402
    build_opportunity_context,
    build_queries,
)


PROFILE_WITH_LOCATION = {
    "primary_objective": "Build portfolio evidence",
    "time_budget": "Two weeks",
    "demonstrated_capabilities": ["Python"],
    "constraints": {"location": "Berlin"},
}
PROFILE_WITHOUT_LOCATION = {
    "primary_objective": "Build portfolio evidence",
    "time_budget": "Two weeks",
    "demonstrated_capabilities": ["Python"],
}


class OpportunityLocationTests(unittest.TestCase):
    def test_present_location_flows_to_query_and_recommendation_context(self):
        question = "Should I build a habit tracker?"
        brief = build_queries(question, PROFILE_WITH_LOCATION)
        pack = assemble(
            question=question,
            mode="quick",
            profile=PROFILE_WITH_LOCATION,
        )

        self.assertEqual(brief["opportunity_context"]["location"], "Berlin")
        self.assertEqual(
            brief["opportunity_context"]["local_opportunity_search_requested"],
            False,
        )
        self.assertEqual(
            pack["parts"]["opportunity_context"],
            brief["opportunity_context"],
        )

    def test_missing_location_is_not_fabricated_for_local_opportunity_request(self):
        question = "Find local AI meetups and hackathons."
        brief = build_queries(question, PROFILE_WITHOUT_LOCATION)

        self.assertEqual(
            brief["opportunity_context"],
            {"local_opportunity_search_requested": True},
        )
        self.assertFalse(
            any("Berlin" in query["query"] for query in brief["queries"])
        )
        self.assertNotIn("opportunities", {q["intent"] for q in brief["queries"]})

    def test_local_opportunity_query_uses_profile_location(self):
        question = "Find local AI meetups and hackathons in my city."
        brief = build_queries(question, PROFILE_WITH_LOCATION)
        opportunity_queries = [
            item["query"]
            for item in brief["queries"]
            if item["intent"] == "opportunities"
        ]

        self.assertTrue(
            brief["opportunity_context"]["local_opportunity_search_requested"]
        )
        self.assertEqual(len(opportunity_queries), 1)
        self.assertIn("Berlin", opportunity_queries[0])

    def test_location_independent_project_is_not_localized(self):
        question = "Should I build a habit tracker?"
        brief = build_queries(question, PROFILE_WITH_LOCATION)
        pack = assemble(
            question=question,
            mode="quick",
            profile=PROFILE_WITH_LOCATION,
        )

        self.assertFalse(
            brief["opportunity_context"]["local_opportunity_search_requested"]
        )
        self.assertNotIn("opportunities", {q["intent"] for q in brief["queries"]})
        self.assertFalse(
            any("Berlin" in query["query"] for query in brief["queries"])
        )
        self.assertEqual(
            pack["parts"]["opportunity_context"]["location"],
            "Berlin",
        )
        self.assertFalse(
            pack["parts"]["opportunity_context"]["local_opportunity_search_requested"]
        )

    def test_context_explicitly_signals_no_location_when_absent(self):
        context = build_opportunity_context(
            "Should I build a habit tracker?",
            PROFILE_WITHOUT_LOCATION,
        )
        self.assertEqual(
            context,
            {"local_opportunity_search_requested": False},
        )


if __name__ == "__main__":
    unittest.main()
