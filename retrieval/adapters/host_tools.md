# Host tools adapter

Use whatever search tools the host LLM already exposes (Cursor web search, GitHub search, browser, etc.).

## Do

- Run each query in `retrieval_brief.queries` (or a subset if budget is tight).
- Prefer official repos, papers, docs, and product pages over SEO blogs.
- Record for each hit: `title`, `url`, `snippet` (≤220 chars), `query_id`, optional `source_class`.

## Don't

- Require the user to create API keys for v0.
- Paste raw SERP pages into the recommend prompt—normalize first.
- Treat zero hits as proof of novelty.

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
