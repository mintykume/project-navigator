# Reasoning workflow

Run stages in order. Load **only** the current `prompts/stages/sN-*.md`. Stop when a stage says STOP.

```text
S1 clarify
S2 constraints + objective
S3 existing-work gate (cheap) -> maybe ask quick vs deep
S4 existing-work check (expensive; only if gated + deep)
S5 gaps
S6 trajectory + leverage
S7 immediate vs long-term
S8 recommend (one LLM call)
S9 lint: python scripts/check_recommendation.py --in <draft>
```

Use `python scripts/plan_workflow.py` / preflight `workflow_plan` for `active_stages` and whether S4 runs.

**S4 only if** clarification clear, research justified, deep approved, and facts not already in the pack. If justified but user stays on quick: mark prior art Unknown and continue S5-S8.
