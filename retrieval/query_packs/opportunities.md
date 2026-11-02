# Query pack: opportunities (optional)

Light optional pack for later turns—not required for v0 recommendations.

| intent | Look for |
|--------|----------|
| `opportunities` | Jobs, internships, hackathons, labs, civic-tech, fellowships, grants, local meetups |

The retrieval brief and S8 context include `opportunity_context`. Treat
`location` as optional context, not a default recommendation criterion. Use it
for opportunity searches only when `local_opportunity_search_requested` is
true or geography otherwise materially changes the answer. If the location is
absent, do not infer or invent one. Distinguish online options from options
realistically accessible at the stated location.

Prefer skipping this pack unless the user explicitly wants opportunity discovery.
