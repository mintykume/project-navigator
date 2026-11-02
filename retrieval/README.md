# Optional retrieval

Opt-in only. Quick mode works offline.

No API keys or scrapers in v0. Use the host agent's web/GitHub tools.

1. Confirm deep (`workflow_plan` / user).
2. `python scripts/build_search_queries.py …`
3. Search via [adapters/host_tools.md](adapters/host_tools.md)
4. `python scripts/normalize_retrieval.py --in hits.json --question "Should I build …?" --out facts.json`
5. `python scripts/run_preflight.py … --mode deep --retrieval facts.json`

The normalized file includes `retrieval_status`:

- `NOT_SEARCHED` — no search was attempted.
- `SEARCHED_WITH_RESULTS` — at least one structurally valid fact overlaps a non-generic topic term in the question.
- `SEARCHED_NO_RESULTS` — completed search returned zero hits.
- `SEARCHED_NO_USABLE_EVIDENCE` — hits were returned, but all were malformed or irrelevant to the question.

`workflow_plan.retrieval_status` is the sole internal prior-art state. Human
phrases such as "unchecked", "not checked", or "deferred" map to
`NOT_SEARCHED` only when no search was run; they are not separate states.
`Unknown` in the recommendation confidence section describes unresolved facts,
not retrieval state, and never implies novelty. Zero hits and unusable hits
remain distinct completed-search outcomes.

If no search was attempted, omit the retrieval file; the workflow reports `NOT_SEARCHED`. Older `{"facts": [...]}` files remain supported only when each fact has non-empty `title`, `url`, `snippet`, and `query_id` fields. An older empty `{"facts": []}` file cannot prove a search happened and is treated as `NOT_SEARCHED`; re-run the normalizer or add the explicit state.

To deliberately start a new search after either completed empty state, explicitly invoke the deep path without passing the previous retrieval file. Automatic preflight with a completed-search payload will not retry. Bounded relaxation/recovery is not part of this version.

Packs: [existing-work.md](query_packs/existing-work.md) (primary), [opportunities.md](query_packs/opportunities.md) (optional). Empty results != novelty.

## URL deduplication

Retrieval deduplication ignores URL fragments and normalizes hostname casing,
a final hostname dot, default HTTP/HTTPS ports, and one trailing path slash.
It preserves scheme, `www` versus bare host, non-default ports, path parameters,
and query strings (including parameter order); no tracking parameters are
removed. This intentionally favors retaining potentially distinct evidence
over aggressive URL merging.
