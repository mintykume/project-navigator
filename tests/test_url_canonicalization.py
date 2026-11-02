#!/usr/bin/env python3
"""Tests for conservative retrieval URL deduplication."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from normalize_retrieval import normalize_hits  # noqa: E402


def hit(url: str) -> dict[str, str]:
    return {
        "title": "Inventory stock manager",
        "url": url,
        "snippet": "Tracks inventory, stock, and orders for small shops.",
        "query_id": "q1",
    }


class URLCanonicalizationTests(unittest.TestCase):
    def normalized_urls(self, *urls: str) -> list[str]:
        facts = normalize_hits([hit(url) for url in urls])
        return [fact["url"] for fact in facts]

    def test_query_string_variants_remain_distinct(self):
        self.assertEqual(
            self.normalized_urls(
                "https://example.test/search?q=inventory",
                "https://example.test/search?q=orders",
            ),
            [
                "https://example.test/search?q=inventory",
                "https://example.test/search?q=orders",
            ],
        )

    def test_query_parameter_order_remains_distinct(self):
        self.assertEqual(
            len(
                self.normalized_urls(
                    "https://example.test/search?a=1&b=2",
                    "https://example.test/search?b=2&a=1",
                )
            ),
            2,
        )

    def test_single_trailing_slash_is_ignored(self):
        self.assertEqual(
            self.normalized_urls(
                "https://example.test/inventory",
                "https://example.test/inventory/",
            ),
            ["https://example.test/inventory"],
        )

    def test_only_one_trailing_slash_is_normalized(self):
        self.assertEqual(
            len(
                self.normalized_urls(
                    "https://example.test/inventory",
                    "https://example.test/inventory//",
                )
            ),
            2,
        )

    def test_host_case_and_trailing_dot_are_normalized(self):
        self.assertEqual(
            self.normalized_urls(
                "https://EXAMPLE.TEST./inventory",
                "https://example.test/inventory",
            ),
            ["https://EXAMPLE.TEST./inventory"],
        )

    def test_default_ports_are_normalized_for_both_schemes(self):
        self.assertEqual(
            self.normalized_urls(
                "http://example.test:80/inventory",
                "http://example.test/inventory",
                "https://example.test:443/inventory",
                "https://example.test/inventory",
            ),
            [
                "http://example.test:80/inventory",
                "https://example.test:443/inventory",
            ],
        )

    def test_http_and_https_remain_distinct(self):
        self.assertEqual(
            len(
                self.normalized_urls(
                    "http://example.test/inventory",
                    "https://example.test/inventory",
                )
            ),
            2,
        )

    def test_www_and_bare_host_remain_distinct(self):
        self.assertEqual(
            len(
                self.normalized_urls(
                    "https://www.example.test/inventory",
                    "https://example.test/inventory",
                )
            ),
            2,
        )

    def test_fragment_variants_are_deduplicated(self):
        self.assertEqual(
            self.normalized_urls(
                "https://example.test/inventory#overview",
                "https://example.test/inventory#pricing",
            ),
            ["https://example.test/inventory#overview"],
        )

    def test_non_default_ports_remain_distinct(self):
        self.assertEqual(
            len(
                self.normalized_urls(
                    "https://example.test:8443/inventory",
                    "https://example.test/inventory",
                )
            ),
            2,
        )


if __name__ == "__main__":
    unittest.main()
