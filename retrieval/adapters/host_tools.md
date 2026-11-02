# Host tools adapter

Use whatever search tools the host LLM already exposes (Cursor web search, GitHub search, browser, etc.).

## Do

- Run each query in `retrieval_brief.queries` (or a subset if budget is tight).
- Prefer official repos, papers, docs, and product pages over SEO blogs.
- Record for each hit: non-empty `title`, `url`, `snippet` (≤220 chars), and `query_id`; `source_class` is optional and inferred when absent.
- Normalize with the original project question so irrelevant hits are removed before the hit cap.
- Relevant hits rank by topic overlap first; inferred source quality breaks relevance ties in this order: papers, GitHub repositories, datasets, then generic web. Input order is stable within equivalent relevance and source class.
- After a completed search, normalize the hits even when the result list is empty. Zero returned hits record `SEARCHED_NO_RESULTS`; returned but unusable/irrelevant hits record `SEARCHED_NO_USABLE_EVIDENCE`.

## Don't

- Require the user to create API keys for v0.
- Paste raw SERP pages into the recommend prompt—normalize first.
- Treat zero hits as proof of novelty.
- Treat malformed or unrelated hits as adequate prior-art evidence.
- Re-run S4 automatically just because the normalized `facts` list is empty.

## Example raw hits JSON

```json
{
  "hits": [
    {
      "query_id": "q1",
      "title": "Example repo",
      "url": "https://github.com/org/example",
      "snippet": "CLI tool that does X for Y users.",
      "source_class": "github_repo"
    }
  ]
}
```
