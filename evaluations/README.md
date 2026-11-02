# Project Navigator evaluation harness

This directory contains a reproducible workflow-integration harness for Project Navigator using eight project scenarios.

## Purpose

The harness runs the deterministic scripts used by the skill and checks that each case can produce query, context, quick-preflight, and deep-preflight outputs.

The harness intentionally avoids a UI and keeps the workflow grounded in the same scripts that the repo already ships:

- `scripts/run_preflight.py`
- `scripts/build_search_queries.py`
- `scripts/normalize_retrieval.py`
- `scripts/assemble_context.py`
- `scripts/check_recommendation.py`

## How to rerun

From the Skill 2.0 root:

```bash
python evaluations/run_project_evaluation.py
```

This reads the project cases under `evaluations/cases/`, runs the available deterministic workflow, and writes a compact summary under `evaluations/output/`.

## Scope and limitations

The harness does not grade recommendation quality or measure whether Project Navigator improves real project decisions. It uses the shared retrieval fixture at `tests/fixtures/retrieval_hits.json` for every case; that evidence is unrelated to most case-specific questions. It therefore validates workflow integration and evidence-state handling, not realistic case-specific search quality. No live host search tool is executed. External research remains the host agent's responsibility.

## What is recorded

For each case, the summary records:

- the case ID, title, and question;
- generated query IDs, intents, and query text;
- quick- and deep-preflight statuses, including retrieval status;
- context-pack generation status and size;
- command output and the note that no live host search ran.

It does not record a scored profile-fit or opportunity-cost assessment, and it does not produce or score a final AI recommendation.
