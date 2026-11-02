# S3 -- Existing-work gate (cheap)

**Goal:** Decide if expensive S4 research is justified. No host search yet. Prefer `workflow_plan.research_justified` from preflight when available.

**Justified when:** build/ship/create proposal; asks if something exists/is novel; needs current alternatives/papers/datasets; user requested deep.

**Not justified when:** pure prioritization / learning path among known options; still blocked on S1; immediate "how do I earn this week" with no build claim; retrieval facts already present.

The deterministic preflight distinguishes build intent, existence intent, project-option comparison, learning-only requests, negated build intent, and explicit deep requests. Do not treat generic tool/API learning or temporal "between X and Y" phrasing as a project comparison. The deterministic classifier is English-only in this version; do not assume its result applies to other languages.

**If justified and mode is not deep:** ask once:

> Quick answer from what you shared, or deeper prior-art search first?

Only then S4 (or `--mode deep`). If the user chooses quick/deferred research,
keep `retrieval_status=NOT_SEARCHED` and continue to S5. "Deferred" is not a
completed search: it must not be mapped to `SEARCHED_NO_RESULTS`.

**If not justified:** skip S4; continue S5.
