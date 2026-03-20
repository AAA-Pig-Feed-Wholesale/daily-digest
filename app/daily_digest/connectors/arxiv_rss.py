from __future__ import annotations

from datetime import datetime
import re

import feedparser


def _extract_arxiv_id(value: str) -> str:
    if value.startswith("oai:arXiv.org:"):
        return value.split("oai:arXiv.org:")[-1]
    match = re.search(r"arxiv\.org/(abs|pdf)/([^?#]+)", value)
    if match:
        return match.group(2)
    return value.split("/")[-1]


def fetch_arxiv_rss(feed_url: str, source_name: str) -> list[dict]:
    feed = feedparser.parse(feed_url)
    items: list[dict] = []
    for entry in feed.entries:
        url = getattr(entry, "link", None)
        if not url:
            continue
        title = getattr(entry, "title", "")
        summary = getattr(entry, "summary", None)
        arxiv_id = _extract_arxiv_id(getattr(entry, "id", url))
        published = None
        if getattr(entry, "published_parsed", None):
            published = datetime(*entry.published_parsed[:6])
        authors = [a.name for a in getattr(entry, "authors", [])] if getattr(entry, "authors", None) else []
        categories = [t.term for t in getattr(entry, "tags", [])] if getattr(entry, "tags", None) else []

        items.append(
            {
                "source": "arxiv",
                "source_name": source_name,
                "external_id": arxiv_id,
                "url": url,
                "title": title,
                "author_text": ", ".join(authors) if authors else None,
                "published_at": published,
                "doc_type": "paper",
                "summary_raw": summary,
                "content_raw": summary,
                "metadata": {"categories": categories},
            }
        )
    return items
