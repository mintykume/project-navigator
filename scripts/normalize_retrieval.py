#!/usr/bin/env python3
"""Normalize and dedupe raw retrieval hits into compact facts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib_pn import write_text

REQUIRED = ("title", "url", "snippet", "source_class", "query_id")


def _canon_url(url: str) -> str:
    try:
        p = urlparse(url.strip())
        netloc = p.netloc.lower()
        path = p.path.rstrip("/") or ""
        return urlunparse((p.scheme.lower(), netloc, path, "", "", ""))
    except Exception:
        return url.strip().lower()


def _guess_source_class(url: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    host = urlparse(url).netloc.lower()
    if "github.com" in host:
        return "github_repo"
    if any(x in host for x in ("arxiv.org", "acm.org", "ieee.org", "openreview.net")):
        return "paper"
    if "kaggle.com" in host or "data.gov" in host:
        return "dataset"
    return "web"


def normalize_hits(hits: list, max_hits: int = 12, snippet_len: int = 220) -> list[dict]:
    seen: set[str] = set()
    facts: list[dict] = []
    for raw in hits:
        if not isinstance(raw, dict):
            continue
        url = str(raw.get("url") or "").strip()
        title = str(raw.get("title") or "").strip()
        if not url or not title:
            continue
        key = _canon_url(url)
        if key in seen:
            continue
        seen.add(key)
        snippet = re.sub(r"\s+", " ", str(raw.get("snippet") or "").strip())
        fact = {
            "title": title[:200],
            "url": url,
            "snippet": snippet[:snippet_len],
            "source_class": _guess_source_class(url, raw.get("source_class")),
            "query_id": str(raw.get("query_id") or "unknown"),
        }
        facts.append(fact)
        if len(facts) >= max_hits:
            break
    return facts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--in",
        dest="infile",
        required=True,
        type=Path,
        help="JSON list of hits or {hits:[...]}",
    )
    parser.add_argument("--max-hits", type=int, default=12)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    data = json.loads(args.infile.read_text(encoding="utf-8"))
    hits = data if isinstance(data, list) else data.get("hits", [])
    facts = normalize_hits(hits, max_hits=args.max_hits)
    payload = {"facts": facts, "count": len(facts)}
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        write_text(args.out, text)
        print(f"Wrote {args.out} ({len(facts)} facts)")
    else:
        write_text(None, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
