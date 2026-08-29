# S4 -- Existing-work check (expensive, optional)

Run only if S3/preflight says so and deep is approved.

1. `python scripts/build_search_queries.py --profile … --question …`
2. Host search: `retrieval/adapters/host_tools.md` + `retrieval/query_packs/existing-work.md`
3. `python scripts/normalize_retrieval.py --in hits.json --out facts.json`
4. Re-preflight with `--retrieval facts.json`

| Class | Stance |
|-------|--------|
| Exists and good | Don't rebuild; study / contribute / extend |
| Clear limitation | Consider the missing piece |
| Abandoned | Confirm value before revival |
| Research only | Small implementation experiment |
| Commercial only | Open alternative / integration / complement |
| Not found | Do **not** claim novelty |

Cap searches. Then S5 with `prior_art_status=checked`.
