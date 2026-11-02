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
S9 lint: python scripts/check_recommendation.py --in <draft> --retrieval-status <status>
```

Use `python scripts/plan_workflow.py` / preflight `workflow_plan` for `active_stages` and whether S4 runs.

**S4 only if** clarification is clear, deep is approved, and `retrieval_status=NOT_SEARCHED`. After any completed retrieval, including zero hits or zero usable evidence, record its explicit status and do not automatically run S4 again. Neither empty state is evidence of novelty.

`workflow_plan.retrieval_status` is the sole internal prior-art state:
`NOT_SEARCHED` (no search run), `SEARCHED_WITH_RESULTS` (usable relevant
evidence), `SEARCHED_NO_RESULTS` (completed search returned zero hits), or
`SEARCHED_NO_USABLE_EVIDENCE` (hits returned, none usable). Human terms such as
"unchecked," "not checked," or "deferred" map to `NOT_SEARCHED` only when no
search was performed; they are not additional states. The recommendation
confidence label `Unknown` describes unresolved facts, not retrieval state.

When preflight returns `awaiting_research_decision`, ask once, then rerun the same `run_preflight.py` request with `--research-decision quick` or `--research-decision deep`. Quick returns `ready` without S4; deep returns `ready` with `run_s4_now: true`. Do not simply abandon the pending preflight call.
