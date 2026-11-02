# Example usage (scripts)

Agent-oriented chats: [interactions.md](interactions.md). Install: [../QUICKSTART.md](../QUICKSTART.md).

All commands run from the **skill root**. Use `python` or `python3`. Outputs write to the current directory (Windows-safe).

## Profile

```bash
cp examples/sample-profile.md my-profile.md
```

## Preflight

```bash
python scripts/run_preflight.py --profile examples/sample-profile.md --question "What should I work on this month?" --mode quick --out pack.json

python scripts/plan_workflow.py --profile examples/sample-profile.md --question "Should I build a new ETL framework?" --mode quick
```

| Exit / status | Meaning |
|---------------|---------|
| `1` / `needs_clarification` | Ask bank questions only (S1) |
| `3` / `awaiting_research_decision` | Ask quick vs deep (S3) |
| `0` / `ready` | Continue stages; use `context_pack` for S8 |

After exit `3`, rerun the same request with `--research-decision quick` or `--research-decision deep`. Quick continues without S4; deep returns a retrieval brief and sets `run_s4_now`.

```bash
python scripts/run_preflight.py --profile tests/fixtures/profile_incomplete.md --question "What next?"
```

## Lint a recommendation

```bash
python scripts/check_recommendation.py --in examples/sample-recommendation.md --retrieval-status NOT_SEARCHED
```

## Deep path (optional)

```bash
python scripts/build_search_queries.py --profile examples/sample-profile.md --question "Should I build a new ETL framework?" --out queries.json
python scripts/normalize_retrieval.py --in tests/fixtures/retrieval_hits.json --question "Should I build a new ETL framework?" --out facts.json
python scripts/run_preflight.py --profile examples/sample-profile.md --question "Should I build a new ETL framework?" --mode deep --retrieval facts.json --out pack.json
```

Then one S8 recommend call from `pack.json` -> `templates/decision-output.md`.
The canonical prior-art state is `workflow_plan.retrieval_status`: no search is
`NOT_SEARCHED`; usable evidence is `SEARCHED_WITH_RESULTS`; a completed search
with zero hits is `SEARCHED_NO_RESULTS`; returned but malformed or irrelevant
hits are `SEARCHED_NO_USABLE_EVIDENCE`. Re-preflight continues without
repeating S4 for either completed-empty state; neither implies novelty.
Human-readable "unchecked"/"deferred" maps to `NOT_SEARCHED` only when no search
was run, while confidence `Unknown` describes unresolved facts, not search state.
