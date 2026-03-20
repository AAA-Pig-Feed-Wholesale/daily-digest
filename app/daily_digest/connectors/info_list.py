from __future__ import annotations

import asyncio
from datetime import datetime
import html
import re
from typing import Iterable
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

EXCLUDE_FRAGMENTS = [
    "/tag",
    "/tags",
    "/category",
    "/categories",
    "/topic",
    "/topics",
    "/column",
    "/columns",
    "/feed",
    "/rss",
    "/search",
    "/login",
    "/signup",
    "/about",
    "/contact",
]

ASSET_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js", ".webp", ".ico", ".pdf")


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    text = text.replace("Z", "+00:00")
    # Try ISO first
    try:
        return datetime.fromisoformat(text)
    except Exception:
        pass
    # Common date patterns
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text[:10], fmt)
        except Exception:
            continue
    # Date-time patterns
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(text[:16], fmt)
        except Exception:
            continue
    return None


def _extract_published_from_html(html_text: str) -> datetime | None:
    soup = BeautifulSoup(html_text, "html.parser")
    meta_keys = {
        "article:published_time",
        "og:published_time",
        "pubdate",
        "publishdate",
        "publish_date",
        "date",
        "timestamp",
        "article:modified_time",
        "lastmod",
    }
    for meta in soup.find_all("meta"):
        key = (meta.get("property") or meta.get("name") or "").strip().lower()
        if key in meta_keys:
            dt = _parse_datetime(meta.get("content"))
            if dt:
                return dt
    for time_tag in soup.find_all("time"):
        dt = _parse_datetime(time_tag.get("datetime"))
        if not dt:
            dt = _parse_datetime(time_tag.get_text())
        if dt:
            return dt
    # Fallback: search in text
    text = soup.get_text(" ")
    match = re.search(r"(20\d{2}[./-]\d{1,2}[./-]\d{1,2})", text)
    if match:
        return _parse_datetime(match.group(1))
    return None


def _is_article_url(url: str, base_host: str, list_url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc and base_host not in parsed.netloc:
        return False
    if not parsed.path or parsed.path in {"/", ""}:
        return False
    lower = parsed.path.lower()
    if lower.endswith(ASSET_EXTS):
        return False
    if any(fragment in lower for fragment in EXCLUDE_FRAGMENTS):
        return False
    if url.rstrip("/") == list_url.rstrip("/"):
        return False
    # Require some structure or digits
    if lower.count("/") < 2 and not re.search(r"\d{4}|\d{2,}", lower):
        return False
    return True


async def fetch_list_candidates(name: str, list_url: str, max_items: int = 20) -> list[dict]:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}
    async with httpx.AsyncClient(timeout=12, follow_redirects=True, headers=headers) as client:
        resp = await client.get(list_url)
        resp.raise_for_status()
        html_text = resp.text

    soup = BeautifulSoup(html_text, "html.parser")
    base_host = urlparse(list_url).netloc
    seen: set[str] = set()
    items: list[dict] = []

    for a in soup.find_all("a", href=True):
        href = a.get("href")
        if not href:
            continue
        url = urljoin(list_url, href)
        if url in seen:
            continue
        if not _is_article_url(url, base_host, list_url):
            continue
        title = _clean_text(a.get_text())
        if len(title) < 4:
            continue
        seen.add(url)
        items.append(
            {
                "source": "info",
                "source_name": name,
                "external_id": url[:255],
                "url": url,
                "title": title,
                "author_text": None,
                "published_at": None,
                "doc_type": "info",
                "summary_raw": None,
                "content_raw": None,
                "metadata": {"list_url": list_url},
            }
        )
        if len(items) >= max_items:
            break
    return items


def _extract_content(html_text: str) -> str | None:
    text = trafilatura.extract(html_text, include_comments=False, include_tables=False)
    if text:
        return _clean_text(text)
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(" ")
    text = _clean_text(text)
    return text or None


async def enrich_items_with_content(items: list[dict], max_items: int = 12) -> list[dict]:
    if not items:
        return items
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=headers) as client:
        for idx, item in enumerate(items[:max_items]):
            url = item.get("url")
            if not url:
                continue
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                html_text = resp.text
            except Exception:
                continue
            content = _extract_content(html_text)
            if content:
                item["content_raw"] = content
                if not item.get("summary_raw"):
                    item["summary_raw"] = content[:200]
            if not item.get("published_at"):
                item["published_at"] = _extract_published_from_html(html_text)
            if idx < max_items - 1:
                await asyncio.sleep(0.2)
    return items
