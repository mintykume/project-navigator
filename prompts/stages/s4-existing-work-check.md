# S4 -- Existing-work check (expensive, optional)

Run only if S3/preflight says so and deep is approved.

1. `python scripts/build_search_queries.py --profile … --question …`
2. Host search: `retrieval/adapters/host_tools.md` + `retrieval/query_packs/existing-work.md`
3. `python scripts/normalize_retrieval.py --in hits.json --question "<original user question>" --out facts.json`
4. Re-preflight with `--retrieval facts.json`. It records `SEARCHED_WITH_RESULTS`, `SEARCHED_NO_RESULTS`, or `SEARCHED_NO_USABLE_EVIDENCE`; every completed state prevents an automatic repeat of S4.

| Class | Stance |
|-------|--------|
| Exists and good | Don't rebuild; study / contribute / extend |
| Clear limitation | Consider the missing piece |
| Abandoned | Confirm value before revival |
| Research only | Small implementation experiment |
| Commercial only | Open alternative / integration / complement |
| `SEARCHED_NO_RESULTS` / `SEARCHED_NO_USABLE_EVIDENCE` | Do **not** claim novelty |

Cap searches. Then continue to S5. `SEARCHED_NO_RESULTS` means the search returned zero hits; `SEARCHED_NO_USABLE_EVIDENCE` means returned hits were malformed or irrelevant. Neither state supports novelty claims.
