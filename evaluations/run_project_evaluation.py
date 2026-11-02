#!/usr/bin/env python3
"""Run the deterministic Project Navigator workflow against a set of evaluated project cases."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "evaluations" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CASES = [
    {
        "id": "habit-tracker",
        "title": "Habit Tracker",
        "profile": "evaluations/cases/habit-tracker.md",
        "question": "I want to build a habit tracker that helps a user sustain routines without guilt or over-engineering.",
    },
    {
        "id": "local-inventory",
        "title": "Local Inventory Tool",
        "profile": "evaluations/cases/local-inventory.md",
        "question": "I want to build a local inventory tool for a small shop or workshop that tracks stock, orders, and restocking lightly.",
    },
    {
        "id": "open-source-contribution",
        "title": "Open-Source Contribution",
        "profile": "evaluations/cases/open-source-contribution.md",
        "question": "I want to find a meaningful open-source contribution and build practical experience without reinventing a product from scratch.",
    },
    {
        "id": "ar-learning-lab",
        "title": "AR Learning Lab",
        "profile": "evaluations/cases/ar-learning-lab.md",
        "question": "I want to build an augmented-reality learning lab for interactive concept exploration in a classroom or maker setting.",
    },
    {
        "id": "sign-language-practice",
        "title": "Sign Language Practice App",
        "profile": "evaluations/cases/sign-language-practice.md",
        "question": "I want to build a sign-language practice app that helps learners improve recognition and feedback using lightweight computer-vision workflows.",
    },
    {
        "id": "study-environment-coach",
        "title": "Study Environment Coach",
        "profile": "evaluations/cases/study-environment-coach.md",
        "question": "I want to build a study-environment coach that uses simple context signals to recommend better focus habits and workspace setup.",
    },
    {
        "id": "weak-duplicate-1",
        "title": "Weak Duplicate 1",
        "profile": "evaluations/cases/weak-duplicate-1.md",
        "question": "I want to build a generic todo app with AI summaries and a dashboard.",
    },
    {
        "id": "weak-duplicate-2",
        "title": "Weak Duplicate 2",
        "profile": "evaluations/cases/weak-duplicate-2.md",
        "question": "I want to build a weather dashboard with charts and a simple chatbot wrapper.",
    },
]


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)


def validate_case_profiles(cases: list[dict]) -> list[str]:
    errors = []
    for case in cases:
        profile_path = ROOT / case["profile"]
        validation = run_cmd([
            sys.executable,
            "scripts/validate_profile.py",
            "--profile",
            str(profile_path),
        ])
        if validation.returncode != 0:
            details = "\n".join(
                item.strip()
                for item in (validation.stdout, validation.stderr)
                if item.strip()
            )
            errors.append(
                f"{case['id']} ({case['profile']}): "
                f"{details or f'validator exited with {validation.returncode}'}"
            )
    return errors


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main() -> int:
    profile_errors = validate_case_profiles(CASES)
    if profile_errors:
        print(
            "ERROR: Evaluation profiles failed validation; no scenarios were run:\n"
            + "\n".join(f"- {error}" for error in profile_errors),
            file=sys.stderr,
        )
        return 1

    results = []
    raw_facts_path = ROOT / "tests" / "fixtures" / "retrieval_hits.json"

    for case in CASES:
        profile_path = ROOT / case["profile"]
        question = case["question"]
        id_ = case["id"]
        quick_out = OUT_DIR / f"{id_}_quick.json"
        deep_out = OUT_DIR / f"{id_}_deep.json"
        queries_out = OUT_DIR / f"{id_}_queries.json"
        context_out = OUT_DIR / f"{id_}_context.json"
        facts_path = OUT_DIR / f"{id_}_normalized-retrieval.json"
        normalization = run_cmd([
            sys.executable,
            "scripts/normalize_retrieval.py",
            "--in",
            str(raw_facts_path),
            "--question",
            question,
            "--out",
            str(facts_path),
        ])
        if normalization.returncode != 0:
            print(normalization.stderr or normalization.stdout, file=sys.stderr)
            return normalization.returncode or 1

        quick = run_cmd([
            sys.executable,
            "scripts/run_preflight.py",
            "--profile",
            str(profile_path),
            "--question",
            question,
            "--mode",
            "quick",
            "--out",
            str(quick_out),
        ])
        query_cmd = run_cmd([
            sys.executable,
            "scripts/build_search_queries.py",
            "--profile",
            str(profile_path),
            "--question",
            question,
            "--out",
            str(queries_out),
        ])
        context_cmd = run_cmd([
            sys.executable,
            "scripts/assemble_context.py",
            "--profile",
            str(profile_path),
            "--question",
            question,
            "--mode",
            "quick",
            "--out",
            str(context_out),
        ])

        deep = run_cmd([
            sys.executable,
            "scripts/run_preflight.py",
            "--profile",
            str(profile_path),
            "--question",
            question,
            "--mode",
            "deep",
            "--retrieval",
            str(facts_path),
            "--out",
            str(deep_out),
        ])

        quick_payload = load_json(quick_out)
        queries_payload = load_json(queries_out)
        context_payload = load_json(context_out)
        deep_payload = load_json(deep_out)

        result = {
            "id": id_,
            "title": case["title"],
            "question": question,
            "quick_cmd": quick.args,
            "quick_returncode": quick.returncode,
            "quick_status": quick_payload.get("status") if quick_payload else None,
            "deep_status": deep_payload.get("status") if deep_payload else None,
            "deep_retrieval_status": (
                deep_payload.get("workflow_plan", {}).get("retrieval_status")
                if deep_payload
                else None
            ),
            "deep_run_s4_now": (
                deep_payload.get("workflow_plan", {}).get("run_s4_now")
                if deep_payload
                else None
            ),
            "query_count": len(queries_payload.get("queries", [])) if queries_payload else 0,
            "generated_queries": queries_payload.get("queries", []) if queries_payload else [],
            "context_pack_chars": context_payload.get("char_count") if context_payload else None,
            "context_pack_status": "generated" if context_payload else "missing",
            "host_tool_note": "No live host search tool executed in this environment; queries are generated and normalized evidence is supplied only from the fixture set.",
            "quick_stdout": quick.stdout.strip() if quick.stdout else "",
            "deep_stdout": deep.stdout.strip() if deep.stdout else "",
            "query_stdout": query_cmd.stdout.strip() if query_cmd.stdout else "",
            "context_stdout": context_cmd.stdout.strip() if context_cmd.stdout else "",
        }
        results.append(result)

    summary_path = OUT_DIR / "project-evaluation-summary.json"
    summary_path.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(results), "summary_path": str(summary_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
