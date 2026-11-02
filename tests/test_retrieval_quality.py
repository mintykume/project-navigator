#!/usr/bin/env python3
"""Tests for usable, relevant retrieval evidence and source-quality ordering."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from check_recommendation import lint_markdown  # noqa: E402
from lib_pn import (  # noqa: E402
    SEARCHED_NO_RESULTS,
    SEARCHED_NO_USABLE_EVIDENCE,
    SEARCHED_WITH_RESULTS,
)
from normalize_retrieval import normalize_hits, prepare_retrieval  # noqa: E402


QUESTION = "Should I build an inventory tool for tracking stock and orders?"


def hit(
    *,
    title: str = "Inventory stock manager",
    url: str = "https://example.test/inventory",
    snippet: str = "Tracks inventory, stock, and orders for small shops.",
    query_id: str = "q1",
    **extra,
) -> dict:
    return {
        "title": title,
        "url": url,
        "snippet": snippet,
        "query_id": query_id,
        **extra,
    }


class RetrievalQualityTests(unittest.TestCase):
    def test_malformed_fact_is_not_counted_as_results(self):
        facts, status = prepare_retrieval([{"foo": 1}], question=QUESTION)
        self.assertEqual(facts, [])
        self.assertEqual(status, SEARCHED_NO_USABLE_EVIDENCE)

    def test_missing_required_fields_are_rejected(self):
        facts, status = prepare_retrieval(
            [{"title": "Inventory manager", "url": "https://example.test"}],
            question=QUESTION,
        )
        self.assertEqual(facts, [])
        self.assertEqual(status, SEARCHED_NO_USABLE_EVIDENCE)

    def test_one_irrelevant_fact_does_not_establish_prior_art(self):
        facts, status = prepare_retrieval(
            [
                hit(
                    title="Astrophotography guide",
                    url="https://example.test/stars",
                    snippet="A guide to photographing distant galaxies.",
                )
            ],
            question=QUESTION,
        )
        self.assertEqual(facts, [])
        self.assertEqual(status, SEARCHED_NO_USABLE_EVIDENCE)

    def test_one_relevant_fact_is_sufficient(self):
        facts, status = prepare_retrieval([hit()], question=QUESTION)
        self.assertEqual(len(facts), 1)
        self.assertEqual(status, SEARCHED_WITH_RESULTS)

    def test_mixed_quality_facts_keep_relevant_evidence_only(self):
        facts, status = prepare_retrieval(
            [
                hit(
                    title="Astronomy catalog",
                    url="https://arxiv.org/abs/1234.5678",
                    snippet="A catalog of stars and galaxies.",
                ),
                hit(
                    title="Inventory tracking service",
                    url="https://example.test/inventory",
                    snippet="Tracks orders and stock levels for workshops.",
                ),
                hit(
                    title="Official inventory dataset",
                    url="https://data.gov/inventory",
                    snippet="Public inventory and stock records.",
                ),
            ],
            question=QUESTION,
        )
        self.assertEqual(status, SEARCHED_WITH_RESULTS)
        self.assertEqual(
            [fact["url"] for fact in facts],
            [
                "https://example.test/inventory",
                "https://data.gov/inventory",
            ],
        )

    def test_strong_source_after_weak_hits_survives_the_hit_cap(self):
        weak_hits = [
            hit(
                title="Inventory tracking stock orders",
                url=f"https://generic{index}.example.test/result",
                snippet="Inventory tracking, stock, and orders.",
            )
            for index in range(12)
        ]
        strong_hit = hit(
            title="Inventory tracking stock orders",
            url="https://data.gov/inventory",
            snippet="Inventory tracking, stock, and orders.",
        )
        facts = normalize_hits(
            weak_hits + [strong_hit],
            max_hits=12,
            question=QUESTION,
        )
        self.assertEqual(len(facts), 12)
        self.assertEqual(facts[0]["source_class"], "dataset")
        self.assertIn("https://data.gov/inventory", {fact["url"] for fact in facts})

    def test_hit_cap_is_preserved_after_quality_ordering(self):
        hits = [
            hit(
                title=f"Inventory record {index}",
                url=f"https://example{index}.test/inventory",
                snippet="Inventory tracking and stock records.",
            )
            for index in range(15)
        ]
        facts = normalize_hits(hits, max_hits=12, question=QUESTION)
        self.assertEqual(len(facts), 12)
        self.assertEqual(
            [fact["url"] for fact in facts],
            [f"https://example{index}.test/inventory" for index in range(12)],
        )

    def test_irrelevant_paper_does_not_displace_relevant_generic_hits(self):
        relevant_hits = [
            hit(
                title=f"Inventory tracking stock orders {index}",
                url=f"https://generic{index}.example.test/inventory",
                snippet="Inventory tracking, stock, and orders.",
            )
            for index in range(12)
        ]
        irrelevant_paper = hit(
            title="Astrophotography guide",
            url="https://arxiv.org/abs/1234.5678",
            snippet="A guide to photographing distant galaxies.",
        )

        facts = normalize_hits(
            relevant_hits + [irrelevant_paper],
            max_hits=12,
            question=QUESTION,
        )
        self.assertEqual(len(facts), 12)
        self.assertTrue(all(fact["source_class"] == "web" for fact in facts))

    def test_relevance_precedes_source_class_when_selecting_under_cap(self):
        highly_relevant_generic = [
            hit(
                title=f"Inventory tracking stock orders {index}",
                url=f"https://generic{index}.example.test/inventory",
                snippet="Inventory tracking, stock, and orders.",
            )
            for index in range(12)
        ]
        weakly_relevant_paper = hit(
            title="Inventory research",
            url="https://arxiv.org/abs/1234.5678",
            snippet="A catalog of inventory topics.",
        )

        facts = normalize_hits(
            highly_relevant_generic + [weakly_relevant_paper],
            max_hits=12,
            question=QUESTION,
        )
        self.assertEqual(len(facts), 12)
        self.assertTrue(all(fact["source_class"] == "web" for fact in facts))

    def test_equal_relevance_and_source_quality_preserve_input_order(self):
        hits = [
            hit(
                title=f"Inventory tracking stock orders {index}",
                url=f"https://generic{index}.example.test/inventory",
                snippet="Inventory tracking, stock, and orders.",
            )
            for index in range(3)
        ]
        facts = normalize_hits(hits, question=QUESTION)
        self.assertEqual(
            [fact["url"] for fact in facts],
            [fact["url"] for fact in hits],
        )

    def test_zero_hits_differs_from_hits_with_no_usable_evidence(self):
        _, empty_status = prepare_retrieval(
            [],
            question=QUESTION,
            retrieval_status=SEARCHED_NO_RESULTS,
        )
        _, invalid_status = prepare_retrieval(
            [{"title": "No required fields"}],
            question=QUESTION,
        )
        self.assertEqual(empty_status, SEARCHED_NO_RESULTS)
        self.assertEqual(invalid_status, SEARCHED_NO_USABLE_EVIDENCE)

    def test_no_usable_evidence_does_not_support_novelty_claims(self):
        recommendation = (
            "## Recommendation\n**Action:** build\n\n"
            "## Why you\nGood fit.\n\n## Why now\nUseful now.\n\n"
            "## Existing alternatives\nNo equivalent tools exist.\n\n"
            "## The gap\nThe project is novel.\n\n"
            "## First experiment\nBuild a small test.\n\n"
            "## Success condition\nA user completes it.\n\n"
            "## Capability unlocked\nProduct validation.\n\n"
            "## Downstream paths\n- Extend it.\n\n"
            "## Trade-off\nTime.\n\n## Alternative\nStudy first.\n\n"
            "## Confidence\nKnown: low.\nInferred: low.\nUnknown: high.\n"
        )
        self.assertIn(
            "unsupported:novelty_claim_without_usable_prior_art",
            lint_markdown(recommendation, SEARCHED_NO_USABLE_EVIDENCE),
        )


if __name__ == "__main__":
    unittest.main()
