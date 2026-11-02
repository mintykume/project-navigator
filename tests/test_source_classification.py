#!/usr/bin/env python3
"""Tests for strict retrieval source-domain classification."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from normalize_retrieval import normalize_hits  # noqa: E402


class SourceClassificationTests(unittest.TestCase):
    def classify(self, url: str) -> str:
        facts = normalize_hits(
            [
                {
                    "title": "Source",
                    "url": url,
                    "snippet": "Evidence",
                    "query_id": "q1",
                }
            ]
        )
        self.assertEqual(len(facts), 1)
        return facts[0]["source_class"]

    def test_existing_trusted_domains_keep_their_classes(self):
        expected = {
            "https://github.com/project/repo": "github_repo",
            "https://arxiv.org/abs/1234.5678": "paper",
            "https://dl.acm.org/paper": "paper",
            "https://ieeexplore.ieee.org/paper": "paper",
            "https://openreview.net/forum": "paper",
            "https://kaggle.com/datasets/example": "dataset",
            "https://data.gov/dataset": "dataset",
        }
        for url, source_class in expected.items():
            with self.subTest(url=url):
                self.assertEqual(self.classify(url), source_class)

    def test_legitimate_subdomains_keep_trusted_classes(self):
        self.assertEqual(
            self.classify("https://api.github.com/repos"),
            "github_repo",
        )
        self.assertEqual(
            self.classify("https://subdomain.arxiv.org/abs/1234"),
            "paper",
        )

    def test_suffix_and_prefix_lookalikes_are_ordinary_web(self):
        for url in (
            "https://github.com.evil.example/project",
            "https://notgithub.com/project",
            "https://evilgithub.com/project",
            "https://kaggle.com.attacker.test/dataset",
        ):
            with self.subTest(url=url):
                self.assertEqual(self.classify(url), "web")

    def test_mixed_case_trusted_hostname_is_matched(self):
        self.assertEqual(
            self.classify("https://GitHub.COM/project/repo"),
            "github_repo",
        )

    def test_port_does_not_change_hostname_classification(self):
        self.assertEqual(
            self.classify("https://github.com:443/project/repo"),
            "github_repo",
        )

    def test_trailing_dot_fqdn_is_matched(self):
        self.assertEqual(
            self.classify("https://github.com./project/repo"),
            "github_repo",
        )

    def test_unrelated_domain_is_ordinary_web(self):
        self.assertEqual(
            self.classify("https://example.org/project"),
            "web",
        )


if __name__ == "__main__":
    unittest.main()
