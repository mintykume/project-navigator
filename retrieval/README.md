# Optional retrieval

Opt-in only. Quick mode works offline.

No API keys or scrapers in v0. Use the host agent's web/GitHub tools.

1. Confirm deep (`workflow_plan` / user).
2. `python scripts/build_search_queries.py …`
3. Search via [adapters/host_tools.md](adapters/host_tools.md)
4. `python scripts/normalize_retrieval.py --in hits.json --out facts.json`
5. `python scripts/run_preflight.py … --mode deep --retrieval facts.json`

Packs: [existing-work.md](query_packs/existing-work.md) (primary), [opportunities.md](query_packs/opportunities.md) (optional). Empty results != novelty.
