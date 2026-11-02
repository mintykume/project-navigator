#!/usr/bin/env python3
"""Normalize and dedupe raw retrieval hits into compact facts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib_pn import (
    NOT_SEARCHED,
    SEARCHED_NO_RESULTS,
    SEARCHED_NO_USABLE_EVIDENCE,
    SEARCHED_WITH_RESULTS,
    normalize_retrieval_status,
    write_text,
)

REQUIRED = ("title", "url", "snippet", "query_id")
_VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
_HIDDEN_ELEMENTS = {"script", "style", "template", "noscript"}
_RELEVANCE_STOP_WORDS = {
    "a", "about", "after", "all", "also", "an", "and", "any", "app",
    "are", "as", "at", "be", "because", "been", "before", "being", "between",
    "both", "but", "by", "can", "could", "create", "do", "does", "for",
    "from", "get", "give", "has", "have", "help", "how", "i", "if", "in",
    "into", "is", "it", "its", "just", "make", "me", "might", "more", "most",
    "my", "new", "not", "of", "on", "one", "or", "our", "out", "over",
    "project", "should", "small", "so", "some", "source", "such", "system", "that",
    "the", "their", "them", "then", "there", "these", "they", "this", "those",
    "through", "to", "tool", "under", "up", "use", "using", "very", "want",
    "was", "way", "we", "what", "when", "where", "which", "while", "who",
    "will", "with", "work", "would", "you", "your", "open", "engineering",
    "build", "building",
}
_SOURCE_QUALITY = {
    "paper": 0,
    "github_repo": 1,
    "dataset": 2,
    "web": 3,
}


class _EvidenceHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self._suppressed: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._suppressed:
            if tag not in _VOID_ELEMENTS:
                self._suppressed.append(tag)
            return

        attributes = {name.lower(): value or "" for name, value in attrs}
        style = attributes.get("style", "")
        hidden_style = re.search(
            r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden)"
            r"\s*(?:!\s*important\s*)?(?:;|$)",
            style,
            re.I,
        )
        if (
            tag in _HIDDEN_ELEMENTS
            or "hidden" in attributes
            or attributes.get("aria-hidden", "").lower() == "true"
            or hidden_style
        ):
            if tag not in _VOID_ELEMENTS:
                self._suppressed.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self._suppressed:
            return
        for index in range(len(self._suppressed) - 1, -1, -1):
            if self._suppressed[index] == tag:
                del self._suppressed[index:]
                break

    def handle_data(self, data: str) -> None:
        if not self._suppressed:
            self.text_parts.append(data)


def sanitize_untrusted_text(value: str) -> str:
    """Keep visible evidence while removing markup and neutralizing delimiters."""
    without_comments = re.sub(r"<!--.*?(?:-->|$)", " ", value, flags=re.S)
    parser = _EvidenceHTMLParser()
    parser.feed(without_comments)
    parser.close()
    text = re.sub(r"\s+", " ", " ".join(parser.text_parts)).strip()
    return text.replace("<", "‹").replace(">", "›")


def sanitize_untrusted_value(value: Any) -> Any:
    """Sanitize every string nested in data passed through the retrieval boundary."""
    if isinstance(value, str):
        return sanitize_untrusted_text(value)
    if isinstance(value, dict):
        return {
            sanitize_untrusted_text(key) if isinstance(key, str) else key:
            sanitize_untrusted_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_untrusted_value(item) for item in value]
    return value


def _canon_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower()
    hostname = parsed.hostname or ""
    if hostname.endswith("."):
        hostname = hostname[:-1]

    if ":" in hostname:
        hostname = f"[{hostname}]"

    userinfo, separator, _ = parsed.netloc.rpartition("@")
    netloc = f"{userinfo}@" if separator else ""
    netloc += hostname.lower()

    port = parsed.port
    if port is not None and not (
        (scheme == "http" and port == 80)
        or (scheme == "https" and port == 443)
    ):
        netloc += f":{port}"

    path = parsed.path
    if path == "/":
        path = ""
    elif path.endswith("/"):
        path = path[:-1]

    return urlunparse(
        (scheme, netloc, path, parsed.params, parsed.query, "")
    )


def _guess_source_class(url: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    host = (urlparse(url).hostname or "").lower()
    if host.endswith("."):
        host = host[:-1]

    def matches_domain(domain: str) -> bool:
        return host == domain or host.endswith(f".{domain}")

    if matches_domain("github.com"):
        return "github_repo"
    if any(
        matches_domain(domain)
        for domain in ("arxiv.org", "acm.org", "ieee.org", "openreview.net")
    ):
        return "paper"
    if any(matches_domain(domain) for domain in ("kaggle.com", "data.gov")):
        return "dataset"
    return "web"


def _topic_terms(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[a-z0-9]+", text, flags=re.I)
        if token.lower() not in _RELEVANCE_STOP_WORDS
        and not token.isdigit()
        and (len(token) >= 3 or token.lower() in {"ai", "ml", "ui", "ux"})
    }


def relevance_score(question: str, fact: dict) -> int:
    """Count shared topic terms; generic task language is excluded."""
    question_terms = _topic_terms(question)
    evidence_terms = _topic_terms(
        f"{fact.get('title', '')} {fact.get('snippet', '')}"
    )
    return len(question_terms & evidence_terms)


def _source_quality(url: str) -> int:
    inferred_class = _guess_source_class(url, None)
    return _SOURCE_QUALITY.get(inferred_class, _SOURCE_QUALITY["web"])


def normalize_hits(
    hits: list,
    max_hits: int = 12,
    snippet_len: int = 220,
    question: str | None = None,
) -> list[dict]:
    if max_hits < 1:
        raise ValueError("max_hits must be greater than zero")

    seen: set[str] = set()
    candidates: list[tuple[int, int, int, dict]] = []
    for index, raw in enumerate(hits):
        if not isinstance(raw, dict):
            continue
        if any(not isinstance(raw.get(field), str) for field in REQUIRED):
            continue
        url = sanitize_untrusted_text(raw["url"].strip())
        title = sanitize_untrusted_text(raw["title"].strip())
        snippet = sanitize_untrusted_text(raw["snippet"])
        query_id = sanitize_untrusted_text(raw["query_id"].strip())
        parsed_url = urlparse(url)
        try:
            hostname = parsed_url.hostname
            _ = parsed_url.port
        except ValueError:
            continue
        if (
            not title
            or not snippet
            or not query_id
            or any(character.isspace() for character in url)
            or parsed_url.scheme.lower() not in {"http", "https"}
            or not hostname
        ):
            continue
        key = _canon_url(url)
        if key in seen:
            continue
        seen.add(key)
        explicit_source = sanitize_untrusted_text(
            str(raw.get("source_class") or "")
        )
        fact = {
            "title": title[:200],
            "url": url,
            "snippet": snippet[:snippet_len],
            "source_class": _guess_source_class(url, explicit_source or None),
            "query_id": query_id,
        }
        score = relevance_score(question, fact) if question is not None else 0
        if question is not None and score == 0:
            continue
        candidates.append((score, _source_quality(url), index, fact))

    if question is None:
        candidates.sort(key=lambda item: (item[1], item[2]))
    else:
        candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [item[3] for item in candidates[:max_hits]]


def prepare_retrieval(
    hits: list,
    *,
    question: str,
    retrieval_status: str | None = None,
    max_hits: int = 12,
) -> tuple[list[dict], str]:
    """Validate, relevance-filter, rank and derive the truthful retrieval state."""
    facts = normalize_hits(hits, max_hits=max_hits, question=question)
    if facts:
        status = normalize_retrieval_status(retrieval_status, True)
        return facts, status
    if hits:
        if retrieval_status == NOT_SEARCHED:
            raise ValueError("NOT_SEARCHED conflicts with returned retrieval hits")
        if retrieval_status is not None:
            normalize_retrieval_status(retrieval_status)
        return [], SEARCHED_NO_USABLE_EVIDENCE
    if retrieval_status == SEARCHED_WITH_RESULTS:
        normalize_retrieval_status(retrieval_status, False)
    return [], normalize_retrieval_status(retrieval_status, False)


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
    parser.add_argument(
        "--question",
        required=True,
        help="Filter and rank hits for the user's project question before applying the cap",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    data = json.loads(args.infile.read_text(encoding="utf-8"))
    if isinstance(data, list):
        hits = data
    elif isinstance(data, dict) and isinstance(data.get("hits"), list):
        hits = data["hits"]
    else:
        print(
            "ERROR: retrieval input must be a JSON hit list or an object with a hits list",
            file=sys.stderr,
        )
        return 2
    if args.max_hits < 1:
        parser.error("--max-hits must be greater than zero")
    if hits:
        facts, retrieval_status = prepare_retrieval(
            hits,
            question=args.question,
            max_hits=args.max_hits,
        )
    else:
        facts, retrieval_status = [], SEARCHED_NO_RESULTS
    payload = {
        "facts": facts,
        "count": len(facts),
        "retrieval_status": retrieval_status,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        write_text(args.out, text)
        print(f"Wrote {args.out} ({len(facts)} facts)")
    else:
        write_text(None, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
