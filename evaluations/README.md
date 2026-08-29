# Project Navigator evaluation harness

This directory contains a small, reproducible evaluation setup for Project Navigator using real project ideas.

## Purpose

The goal is to evaluate whether the current implementation actually improves project decisions, rather than just generating plausible ideas.

The harness intentionally avoids a UI and keeps the workflow grounded in the same scripts that the repo already ships:

- `scripts/run_preflight.py`
- `scripts/build_search_queries.py`
- `scripts/normalize_retrieval.py`
- `scripts/assemble_context.py`
- `scripts/check_recommendation.py`

## How to rerun

From the repo root:

```bash
python evaluations/run_project_evaluation.py
```

This reads the project cases under `evaluations/cases/`, runs the available deterministic workflow, and writes a compact summary under `evaluations/output/`.

## What is evaluated

Each case captures:

- the original idea
- the clarified objective
- profile fit
- constraints and opportunity cost
- whether prior-art search is justified
- generated queries
- any evidence available from the current environment
- the workflow status and next action

It does not automatically lock in one “correct answer”; instead it checks whether the workflow used evidence, recognized uncertainty, and produced a defensible next action.
