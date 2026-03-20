from __future__ import annotations

from datetime import datetime
import logging
import re

import httpx
from bs4 import BeautifulSoup

from app.config.settings import settings

logger = logging.getLogger(__name__)


def _extract_paper_ids(html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    ids: set[str] = set()
    for a in soup.select("a[href^='/papers/']"):
        href = a.get("href") or ""
        if href.startswith("/papers/trending") or href.startswith("/papers/date/"):
            continue
        paper_id = href.strip("/").split("/")[-1]
        if paper_id:
            ids.add(paper_id)
    return ids


def _parse_iso_date_from_html(html: str) -> datetime | None:
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", html)
    if not match:
        return None
    try:
        return datetime.fromisoformat(match.group(1))
    except ValueError:
        return None


def _parse_title(soup: BeautifulSoup) -> str | None:
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
        return title or None
    return None


def _parse_author(soup: BeautifulSoup) -> str | None:
    # Try to locate "Submitted by" text; fallback to None
    text = soup.get_text(" ", strip=True)
    match = re.search(r"Submitted by\s+([A-Za-z0-9_\- ]{2,50})\s+on", text)
    if match:
        return match.group(1).strip()
    return None


def _parse_summary(soup: BeautifulSoup) -> str | None:
    meta = soup.find("meta", {"name": "description"})
    if meta:
        return meta.get("content")
    og = soup.find("meta", {"property": "og:description"})
    if og:
        return og.get("content")
    return None


def _parse_abstract(soup: BeautifulSoup) -> str | None:
    # Try explicit abstract blocks
    abstract = soup.find(id=re.compile("abstract", re.I))
    if abstract:
        text = abstract.get_text(" ", strip=True)
        if text:
            return text
    # Try heading "Abstract" and next sibling
    for header in soup.find_all(["h2", "h3", "strong"]):
        if header.get_text(strip=True).lower() == "abstract":
            nxt = header.find_next_sibling()
            if nxt:
                text = nxt.get_text(" ", strip=True)
                if text:
                    return text
    return None


async def fetch_hf_papers(papers_urls: list[str], date_url: str) -> list[dict]:
    items: list[dict] = []
    ids: set[str] = set()

    headers = {}
    if settings.HF_TOKEN:
        headers["Authorization"] = f"Bearer {settings.HF_TOKEN}"

    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=headers) as client:
        # date-specific page
        try:
            resp = await client.get(date_url)
            resp.raise_for_status()
            ids |= _extract_paper_ids(resp.text)
        except Exception as exc:
            logger.warning("hf papers date fetch failed: %s", exc)

        # standard pages
        for url in papers_urls:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                ids |= _extract_paper_ids(resp.text)
            except Exception as exc:
                logger.warning("hf papers fetch failed: %s", exc)

        # detail pages
        for paper_id in ids:
            url = f"https://huggingface.co/papers/{paper_id}"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
            except Exception:
                continue
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")
            title = _parse_title(soup) or paper_id
            summary = _parse_summary(soup)
            abstract = _parse_abstract(soup)
            author = _parse_author(soup)
            published_dt = _parse_iso_date_from_html(html)
            content = abstract or summary

            items.append(
                {
                    "source": "huggingface",
                    "source_name": "hf_papers",
                    "external_id": paper_id,
                    "url": url,
                    "title": title,
                    "author_text": author,
                    "published_at": published_dt,
                    "doc_type": "paper",
                    "summary_raw": summary or abstract,
                    "content_raw": content,
                    "metadata": {"paper_id": paper_id},
                }
            )

    return items
