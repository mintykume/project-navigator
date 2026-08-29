---
name: project-navigator
description: >-
  Decision-support skill for deciding what to work on next, whether an idea is worth pursuing,
  whether it already exists, and what the smallest useful next experiment should be. Use when
  the user asks what to build, research, learn, contribute to, or pursue next, and when the
  goal is to avoid AI-generated project slop.
metadata:
  version: "0.1.0"
  requires: "python3>=3.9 (optional scripts, stdlib only)"
---

# Project Navigator

Project Navigator is a decision-support skill for a host AI agent. It helps the agent determine:

- what the user should work on next;
- whether an idea is worth pursuing;
- whether a project already exists;
- what the real gap is;
- whether to build, research, learn, contribute, reframe, defer, or drop;
- what the smallest useful next experiment is.

## What Project Navigator is not

Project Navigator is not:

- an idea generator;
- a generic brainstorming assistant;
- a standalone search engine;
- a project-management app;
- a replacement for the host agent's tools;
- an automatic "yes" machine.

It should be willing to say "do not build this", "research first", "study existing work", or "the user is not a good fit for this idea right now".

## Host-agent responsibilities

The host agent provides the tools and runtime:

- user conversation and context;
- LLM reasoning;
- web search / GitHub / academic / other search tools when available;
- filesystem access when available;
- retrieval results returned in the expected formats.

The host agent is responsible for actual external evidence gathering.

## Project Navigator responsibilities

The skill provides the decision methodology and workflow:

- profile parsing and clarification;
- objective and constraint extraction;
- existing-work gate logic;
- prior-art research planning;
- evidence normalization;
- opportunity-cost and personal-fit reasoning;
- recommendation structure;
- validation of the final recommendation.

## Runtime contract

Use the repo's deterministic scripts before or alongside the conversational reasoning.

```bash
python scripts/run_preflight.py --profile <file> --question "..." --mode quick|deep
```

Workflow status meanings:

- `needs_clarification`: ask only the returned missing questions and stop.
- `awaiting_research_decision`: ask whether the user wants a quick answer or deeper prior-art research first.
- `ready` + `run_s4_now`: the host agent should do research, normalize results, and re-run preflight with `--retrieval`.
- `ready`: continue in the stage flow S2-S7 and then S8 recommendation.
- after S8: run `python scripts/check_recommendation.py --in <draft>`.

The flow is:

```text
USER REQUEST
  -> S1 clarify
  -> S2 objective + constraints
  -> S3 existing-work gate
  -> research if required
  -> S4 existing-work check
  -> S5 gap
  -> S6 trajectory + leverage
  -> S7 horizon + trade-off
  -> S8 recommend
  -> S9 validate
```

Do not blindly run every stage for every request. The gates decide whether clarification or prior-art research is warranted.

## Research protocol

When existing-work research is justified, the host agent should do two things:

1. Generate a retrieval brief (`build_search_queries.py` / `run_preflight.py` output).
2. Use whatever host search tools it has to collect evidence.

The skill is intentionally tool-agnostic. It requires a host search backend, not its own proprietary search API.

The host agent should return normalized evidence in the format expected by `scripts/normalize_retrieval.py`.

## Context handling

Keep input compact and structured.

- Prefer a profile file or a compact user summary.
- Prefer one project question at a time.
- Load `prompts/core-policy.md` once per session.
- Load only the current stage file when working that stage.
- Do not dump `README.md` into the context unnecessarily.

## Validation

The recommendation output must satisfy the contract used by `scripts/check_recommendation.py`.

Local checks:

```bash
python -m unittest discover -s tests -v
python scripts/validate_profile.py --profile examples/sample-profile.md
python scripts/check_recommendation.py --in examples/sample-recommendation.md
```

## Entry files

Relevant files for a host agent:

- `prompts/core-policy.md`
- `prompts/workflow.md`
- `prompts/stages/`
- `templates/decision-output.md`
- `scripts/run_preflight.py`
- `scripts/build_search_queries.py`
- `scripts/normalize_retrieval.py`
- `scripts/check_recommendation.py`

## Examples

- `QUICKSTART.md`
- `examples/sample-profile.md`
- `examples/sample-recommendation.md`
- `evaluations/host-agent-test.md`
