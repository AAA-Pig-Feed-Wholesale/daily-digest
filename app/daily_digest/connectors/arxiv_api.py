from __future__ import annotations

from datetime import datetime
import asyncio
import logging

import feedparser
import httpx

logger = logging.getLogger(__name__)


class ArxivAPIClient:
    def __init__(
        self,
        base_url: str = "https://export.arxiv.org/api/query",
        batch_size: int = 10,
        min_delay_seconds: float = 3.0,
        retries: int = 3,
    ) -> None:
        self.base_url = base_url
        self.batch_size = batch_size
        self.min_delay_seconds = min_delay_seconds
        self.retries = retries

    async def _fetch_batch(self, client: httpx.AsyncClient, batch: list[str]) -> str | None:
        url = f"{self.base_url}?id_list={','.join(batch)}"
        for attempt in range(1, self.retries + 1):
            resp = await client.get(url)
            if resp.status_code == 429:
                wait = self.min_delay_seconds * (2 ** (attempt - 1))
                logger.warning("arxiv api rate limited, retrying in %.1fs", wait)
                await asyncio.sleep(wait)
                continue
            try:
                resp.raise_for_status()
                return resp.text
            except httpx.HTTPStatusError as exc:
                if attempt >= self.retries:
                    logger.error("arxiv api failed: %s", exc)
                    return None
                wait = self.min_delay_seconds * (2 ** (attempt - 1))
                logger.warning("arxiv api error, retrying in %.1fs", wait)
                await asyncio.sleep(wait)
        return None

    async def enrich(self, candidates: list[dict]) -> list[dict]:
        ids: list[str] = []
        for c in candidates:
            ext = c.get("external_id")
            if ext:
                if isinstance(ext, str) and ext.startswith("oai:arXiv.org:"):
                    ext = ext.split("oai:arXiv.org:")[-1]
                ids.append(str(ext))
        if not ids:
            return candidates

        batches = [ids[i : i + self.batch_size] for i in range(0, len(ids), self.batch_size)]
        enriched: dict[str, dict] = {}

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for batch in batches:
                xml_text = await self._fetch_batch(client, batch)
                if not xml_text:
                    continue
                feed = feedparser.parse(xml_text)
                for entry in feed.entries:
                    url = getattr(entry, "link", None) or ""
                    arxiv_id = url.split("/")[-1]
                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", None)
                    published = None
                    if getattr(entry, "published_parsed", None):
                        published = datetime(*entry.published_parsed[:6])
                    authors = [a.name for a in getattr(entry, "authors", [])] if getattr(entry, "authors", None) else []
                    categories = [t.term for t in getattr(entry, "tags", [])] if getattr(entry, "tags", None) else []

                    payload: dict = {"metadata": {"categories": categories}}
                    if authors:
                        payload["author_text"] = ", ".join(authors)
                    if summary:
                        payload["summary_raw"] = summary
                        payload["content_raw"] = summary
                    if published:
                        payload["published_at"] = published
                    if title:
                        payload["title"] = title
                    if url:
                        payload["url"] = url
                    enriched[arxiv_id] = payload
                await asyncio.sleep(self.min_delay_seconds)

        result: list[dict] = []
        for c in candidates:
            ext = c.get("external_id")
            if ext and ext in enriched:
                merged = c | enriched[ext]
                result.append(merged)
            else:
                result.append(c)
        return result
