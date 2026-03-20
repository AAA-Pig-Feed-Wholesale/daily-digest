from __future__ import annotations

from datetime import datetime
import html
import re

import feedparser


def _extract_published(entry) -> datetime | None:
    if getattr(entry, "published_parsed", None):
        return datetime(*entry.published_parsed[:6])
    if getattr(entry, "updated_parsed", None):
        return datetime(*entry.updated_parsed[:6])
    return None


def _clean_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_info_rss(name: str, url: str) -> list[dict]:
    feed = feedparser.parse(url)
    items: list[dict] = []
    for entry in feed.entries:
        link = getattr(entry, "link", None)
        if not link:
            continue
        title = getattr(entry, "title", "")
        summary_html = getattr(entry, "summary", None)
        content_html = None
        if getattr(entry, "content", None):
            try:
                content_html = entry.content[0].value
            except Exception:
                content_html = None
        summary_text = _clean_html(summary_html)
        content_text = _clean_html(content_html)
        if not summary_text and content_text:
            summary_text = content_text[:200]
        text = content_text or summary_text or title
        published = _extract_published(entry)
        ext_id = getattr(entry, "id", None) or link
        items.append(
            {
                "source": "info",
                "source_name": name,
                "external_id": re.sub(r"\s+", " ", str(ext_id))[:255],
                "url": link,
                "title": title or link,
                "author_text": getattr(entry, "author", None),
                "published_at": published,
                "doc_type": "info",
                "summary_raw": summary_text or None,
                "content_raw": text,
                "metadata": {"feed": url},
            }
        )
    return items
