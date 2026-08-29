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

```bash
python scripts/run_preflight.py --profile tests/fixtures/profile_incomplete.md --question "What next?"
```

## Lint a recommendation

```bash
python scripts/check_recommendation.py --in examples/sample-recommendation.md
```

## Deep path (optional)

```bash
python scripts/build_search_queries.py --profile examples/sample-profile.md --question "Should I build a new ETL framework?" --out queries.json
python scripts/normalize_retrieval.py --in tests/fixtures/retrieval_hits.json --out facts.json
python scripts/run_preflight.py --profile examples/sample-profile.md --question "Should I build a new ETL framework?" --mode deep --retrieval facts.json --out pack.json
```

Then one S8 recommend call from `pack.json` -> `templates/decision-output.md`.
