# S3 -- Existing-work gate (cheap)

**Goal:** Decide if expensive S4 research is justified. No host search yet. Prefer `workflow_plan.research_justified` from preflight when available.

**Justified when:** build/ship/create proposal; asks if something exists/is novel; needs current alternatives/papers/datasets; user requested deep.

**Not justified when:** pure prioritization / learning path among known options; still blocked on S1; immediate "how do I earn this week" with no build claim; retrieval facts already present.

**If justified and mode is not deep:** ask once:

> Quick answer from what you shared, or deeper prior-art search first?

Only then S4 (or `--mode deep`). If declined: `prior_art_status=unchecked`, skip to S5.

**If not justified:** skip S4; continue S5.
