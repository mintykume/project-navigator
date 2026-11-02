#!/usr/bin/env python3
"""Regression tests for explicit retrieval completion state."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PROFILE = ROOT / "tests" / "fixtures" / "profile_valid.md"
PY = sys.executable
QUESTION = "Should I build a new ETL framework?"
sys.path.insert(0, str(SCRIPTS))

from assemble_context import assemble  # noqa: E402
from lib_pn import (  # noqa: E402
    NOT_SEARCHED,
    SEARCHED_NO_RESULTS,
    SEARCHED_NO_USABLE_EVIDENCE,
    SEARCHED_WITH_RESULTS,
    load_profile,
    plan_workflow,
)


def run_preflight(
    retrieval_path: Path | None = None,
    *,
    with_pack: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [
        PY,
        str(SCRIPTS / "run_preflight.py"),
        "--profile",
        str(PROFILE),
        "--question",
        QUESTION,
        "--mode",
        "deep",
    ]
    if retrieval_path:
        command.extend(["--retrieval", str(retrieval_path)])
    if with_pack:
        command.append("--with-pack")
    return subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class RetrievalStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile(PROFILE)

    def test_no_retrieval_is_not_searched(self):
        plan = plan_workflow(
            question=QUESTION,
            profile=self.profile,
            mode="quick",
        )
        self.assertEqual(plan["retrieval_status"], NOT_SEARCHED)
        self.assertTrue(plan["awaiting_research_decision"])

    def test_quick_or_deferred_search_is_not_zero_results(self):
        deferred = plan_workflow(
            question=QUESTION,
            profile=self.profile,
            mode="quick",
            research_decision="quick",
        )
        completed_empty = plan_workflow(
            question=QUESTION,
            profile=self.profile,
            mode="deep",
            retrieval_status=SEARCHED_NO_RESULTS,
        )

        self.assertEqual(deferred["retrieval_status"], NOT_SEARCHED)
        self.assertEqual(completed_empty["retrieval_status"], SEARCHED_NO_RESULTS)
        self.assertNotEqual(
            deferred["retrieval_status"],
            completed_empty["retrieval_status"],
        )

    def test_preflight_and_context_preserve_not_searched_vs_zero_results(self):
        with tempfile.TemporaryDirectory() as td:
            retrieval = Path(td) / "empty-facts.json"
            retrieval.write_text(
                json.dumps({"facts": [], "retrieval_status": SEARCHED_NO_RESULTS}),
                encoding="utf-8",
            )
            unsearched = run_preflight(with_pack=True)
            zero_results = run_preflight(retrieval, with_pack=True)

        self.assertEqual(unsearched.returncode, 0, unsearched.stderr + unsearched.stdout)
        self.assertEqual(zero_results.returncode, 0, zero_results.stderr + zero_results.stdout)
        unsearched_data = json.loads(unsearched.stdout)
        zero_results_data = json.loads(zero_results.stdout)
        self.assertEqual(
            unsearched_data["workflow_plan"]["retrieval_status"],
            NOT_SEARCHED,
        )
        self.assertEqual(
            unsearched_data["context_pack"]["parts"]["workflow_plan"]["retrieval_status"],
            NOT_SEARCHED,
        )
        self.assertEqual(
            zero_results_data["workflow_plan"]["retrieval_status"],
            SEARCHED_NO_RESULTS,
        )
        self.assertEqual(
            zero_results_data["context_pack"]["parts"]["workflow_plan"]["retrieval_status"],
            SEARCHED_NO_RESULTS,
        )

    def test_all_canonical_states_reach_context_and_s8_unchanged(self):
        states_and_facts = (
            (NOT_SEARCHED, []),
            (SEARCHED_WITH_RESULTS, [
                {
                    "title": "Existing ETL tool",
                    "url": "https://example.test/etl",
                    "snippet": "An ETL pipeline tool for small teams.",
                    "query_id": "q1",
                }
            ]),
            (SEARCHED_NO_RESULTS, []),
            (SEARCHED_NO_USABLE_EVIDENCE, []),
        )
        for state, facts in states_and_facts:
            with self.subTest(state=state):
                pack = assemble(
                    question=QUESTION,
                    mode="deep",
                    profile=self.profile,
                    retrieval_facts=facts,
                    retrieval_status=state,
                )
                self.assertEqual(
                    pack["parts"]["workflow_plan"]["retrieval_status"],
                    state,
                )
                self.assertIn(
                    "parts.workflow_plan.retrieval_status",
                    pack["instruction"],
                )
                self.assertIn(state, pack["parts"]["recommend_rules"])

        recommend_rules = pack["parts"]["recommend_rules"]
        self.assertIn("confidence", recommend_rules.lower())
        self.assertIn("not search state", recommend_rules.lower())

    def test_legacy_nonempty_facts_map_to_searched_with_results(self):
        plan = plan_workflow(
            question=QUESTION,
            profile=self.profile,
            mode="deep",
            has_retrieval_facts=True,
        )
        self.assertEqual(plan["retrieval_status"], SEARCHED_WITH_RESULTS)
        self.assertFalse(plan["run_s4_now"])
        self.assertEqual(plan["next_action"], "continue_from_gaps")

    def test_explicit_empty_search_is_terminal_for_this_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            retrieval = Path(td) / "empty-facts.json"
            retrieval.write_text(
                json.dumps({"facts": [], "retrieval_status": SEARCHED_NO_RESULTS}),
                encoding="utf-8",
            )
            first = run_preflight(retrieval)
            second = run_preflight(retrieval)

        self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
        self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
        data = json.loads(first.stdout)
        plan = data["workflow_plan"]
        self.assertEqual(plan["retrieval_status"], SEARCHED_NO_RESULTS)
        self.assertFalse(plan["run_s4_now"])
        self.assertFalse(plan["awaiting_research_decision"])
        self.assertEqual(plan["next_action"], "continue_from_gaps")

    def test_empty_search_is_not_novelty_in_context_pack(self):
        pack = assemble(
            question=QUESTION,
            mode="deep",
            profile=self.profile,
            retrieval_facts=[],
            retrieval_status=SEARCHED_NO_RESULTS,
        )
        workflow = pack["parts"]["workflow_plan"]
        self.assertEqual(workflow["retrieval_status"], SEARCHED_NO_RESULTS)
        self.assertIn("do not support novelty claims", pack["parts"]["policy"])

    def test_empty_legacy_payload_remains_not_searched(self):
        with tempfile.TemporaryDirectory() as td:
            retrieval = Path(td) / "legacy-empty.json"
            retrieval.write_text(json.dumps({"facts": []}), encoding="utf-8")
            result = run_preflight(retrieval)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        plan = json.loads(result.stdout)["workflow_plan"]
        self.assertEqual(plan["retrieval_status"], NOT_SEARCHED)
        self.assertTrue(plan["run_s4_now"])

    def test_legacy_nonempty_payload_is_still_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            retrieval = Path(td) / "legacy-facts.json"
            retrieval.write_text(
                json.dumps(
                    {
                        "facts": [
                            {
                                "title": "Existing ETL tool",
                                "url": "https://example.test/etl",
                                "snippet": "An ETL pipeline tool for small teams.",
                                "query_id": "q1",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = run_preflight(retrieval)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        plan = json.loads(result.stdout)["workflow_plan"]
        self.assertEqual(plan["retrieval_status"], SEARCHED_WITH_RESULTS)
        self.assertFalse(plan["run_s4_now"])
        self.assertEqual(plan["next_action"], "continue_from_gaps")

    def test_legacy_malformed_nonempty_payload_is_not_usable_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            retrieval = Path(td) / "malformed-facts.json"
            retrieval.write_text(json.dumps({"facts": [{"foo": 1}]}), encoding="utf-8")
            result = run_preflight(retrieval)

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        plan = json.loads(result.stdout)["workflow_plan"]
        self.assertEqual(plan["retrieval_status"], SEARCHED_NO_USABLE_EVIDENCE)
        self.assertFalse(plan["has_retrieval_facts"])
        self.assertFalse(plan["run_s4_now"])

    def test_normalizer_marks_a_completed_zero_result_search(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "hits.json"
            normalized = Path(td) / "facts.json"
            raw.write_text(json.dumps({"hits": []}), encoding="utf-8")
            normalized_result = subprocess.run(
                [
                    PY,
                    str(SCRIPTS / "normalize_retrieval.py"),
                    "--in",
                    str(raw),
                    "--question",
                    QUESTION,
                    "--out",
                    str(normalized),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                normalized_result.returncode,
                0,
                normalized_result.stderr + normalized_result.stdout,
            )
            payload = json.loads(normalized.read_text(encoding="utf-8"))
            preflight = run_preflight(normalized)

        self.assertEqual(payload["retrieval_status"], SEARCHED_NO_RESULTS)
        self.assertEqual(preflight.returncode, 0, preflight.stderr + preflight.stdout)
        plan = json.loads(preflight.stdout)["workflow_plan"]
        self.assertEqual(plan["retrieval_status"], SEARCHED_NO_RESULTS)
        self.assertFalse(plan["run_s4_now"])

    def test_normalizer_marks_irrelevant_returned_hits_as_no_usable_evidence(self):
        raw_hits = {
            "hits": [
                {
                    "title": "A guide to distant galaxies",
                    "url": "https://example.test/astronomy",
                    "snippet": "How to photograph stars and galaxies.",
                    "query_id": "q1",
                }
            ]
        }
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "hits.json"
            normalized = Path(td) / "facts.json"
            raw.write_text(json.dumps(raw_hits), encoding="utf-8")
            result = subprocess.run(
                [
                    PY,
                    str(SCRIPTS / "normalize_retrieval.py"),
                    "--in",
                    str(raw),
                    "--question",
                    QUESTION,
                    "--out",
                    str(normalized),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            preflight = run_preflight(normalized)
            payload = json.loads(normalized.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(payload["facts"], [])
        self.assertEqual(payload["retrieval_status"], SEARCHED_NO_USABLE_EVIDENCE)
        self.assertEqual(preflight.returncode, 0, preflight.stderr + preflight.stdout)
        plan = json.loads(preflight.stdout)["workflow_plan"]
        self.assertEqual(plan["retrieval_status"], SEARCHED_NO_USABLE_EVIDENCE)
        self.assertFalse(plan["has_retrieval_facts"])

    def test_normalizer_rejects_input_that_cannot_prove_search_completion(self):
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "not-a-hit-list.json"
            output = Path(td) / "facts.json"
            raw.write_text(json.dumps({}), encoding="utf-8")
            result = subprocess.run(
                [
                    PY,
                    str(SCRIPTS / "normalize_retrieval.py"),
                    "--in",
                    str(raw),
                    "--question",
                    QUESTION,
                    "--out",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("must be a JSON hit list", result.stderr)
        self.assertFalse(output.exists())

    def test_normalizer_and_preflight_keep_nonempty_results(self):
        raw_hits = json.loads(
            (ROOT / "tests" / "fixtures" / "retrieval_hits.json").read_text(
                encoding="utf-8"
            )
        )
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "hits.json"
            normalized = Path(td) / "facts.json"
            raw.write_text(json.dumps(raw_hits), encoding="utf-8")
            normalize = subprocess.run(
                [
                    PY,
                    str(SCRIPTS / "normalize_retrieval.py"),
                    "--in",
                    str(raw),
                    "--question",
                    QUESTION,
                    "--out",
                    str(normalized),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(normalize.returncode, 0, normalize.stderr)
            preflight = run_preflight(normalized)

        self.assertEqual(preflight.returncode, 0, preflight.stderr + preflight.stdout)
        plan = json.loads(preflight.stdout)["workflow_plan"]
        self.assertEqual(plan["retrieval_status"], SEARCHED_WITH_RESULTS)
        self.assertFalse(plan["run_s4_now"])
        self.assertEqual(plan["next_action"], "continue_from_gaps")


if __name__ == "__main__":
    unittest.main()
