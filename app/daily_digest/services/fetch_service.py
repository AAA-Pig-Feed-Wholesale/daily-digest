from __future__ import annotations

from datetime import date, datetime
import logging
import re
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode

from app.config.settings import SOURCES_CONFIG, settings
from app.daily_digest.constants import (
    ARXIV_RSS_SOURCES,
    DEFAULT_REPO_WATCHLIST,
    HF_PAPERS_DATE_URL_TEMPLATE,
    HF_PAPERS_URLS,
    INFO_RSS_SOURCES,
    KEYWORDS,
)
from app.daily_digest.connectors.arxiv_api import ArxivAPIClient
from app.daily_digest.connectors.arxiv_rss import fetch_arxiv_rss
from app.daily_digest.connectors.github_api import GitHubAPIClient
from app.daily_digest.connectors.hf_papers import fetch_hf_papers
from app.daily_digest.connectors.rss_info import fetch_info_rss
from app.daily_digest.connectors.info_list import fetch_list_candidates, enrich_items_with_content

logger = logging.getLogger(__name__)


def _is_on_date(dt: datetime | None, target_date: date) -> bool:
    if not dt:
        return False
    if dt.tzinfo:
        return dt.astimezone().date() == target_date
    return dt.date() == target_date


def _contains_keywords(text: str | None) -> bool:
    if not text:
        return False
    lower = text.lower()
    return any(k in lower for k in KEYWORDS)


def _prefilter(item: dict) -> bool:
    text = " ".join(
        [
            item.get("title") or "",
            item.get("summary_raw") or "",
            item.get("content_raw") or "",
        ]
    )
    # minimum content length heuristic (no blacklist, only quality gate)
    source = (item.get("source") or "").lower()
    doc_type = (item.get("doc_type") or "").lower()
    content = (item.get("content_raw") or item.get("summary_raw") or "").strip()
    if _contains_keywords(text):
        return True
    if source == "huggingface" and doc_type == "paper":
        return len(content) >= 80
    if source == "arxiv" and doc_type == "paper":
        return len(content) >= 80
    if source == "github" and doc_type == "release":
        return len(content) >= 40
    if source == "info":
        return len(content) >= 60
    return len(content) >= 60


def _normalize_title(title: str) -> str:
    lowered = title.lower()
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def _normalize_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        query = [(k, v) for k, v in parse_qsl(parsed.query) if not k.lower().startswith("utm_")]
        query = [(k, v) for k, v in query if k.lower() not in {"ref", "source", "spm"}]
        cleaned = parsed._replace(query=urlencode(query, doseq=True), fragment="")
        return urlunparse(cleaned)
    except Exception:
        return url


def _append_jiqizhixin_token(url: str | None) -> str | None:
    if not url:
        return url
    if not settings.JIQIZHIXIN_TOKEN:
        return url
    try:
        parsed = urlparse(url)
        if parsed.netloc != "mcp.applications.jiqizhixin.com":
            return url
        query_items = parse_qsl(parsed.query, keep_blank_values=True)
        if any(k == "token" and v for k, v in query_items):
            return url
        query_items.append(("token", settings.JIQIZHIXIN_TOKEN))
        return urlunparse(parsed._replace(query=urlencode(query_items, doseq=True)))
    except Exception:
        return url


def _dedup(items: list[dict]) -> tuple[list[dict], int]:
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    result: list[dict] = []
    dropped = 0
    for item in items:
        url = item.get("url") or ""
        norm_url = _normalize_url(url) if url else ""
        title = item.get("title") or ""
        norm_title = _normalize_title(title) if title else ""
        if norm_url and norm_url in seen_urls:
            dropped += 1
            continue
        if norm_title and norm_title in seen_titles:
            dropped += 1
            continue
        if norm_url:
            seen_urls.add(norm_url)
        if norm_title:
            seen_titles.add(norm_title)
        result.append(item)
    return result, dropped


def _get_watchlist() -> list[str]:
    repos = (SOURCES_CONFIG or {}).get("github_watchlists", {}).get("repos")
    if repos:
        return list(repos)
    return DEFAULT_REPO_WATCHLIST


def _get_info_sources() -> list[dict]:
    sources = (SOURCES_CONFIG or {}).get("daily_digest_info_sources")
    if sources and isinstance(sources, list):
        result: list[dict] = []
        for s in sources:
            name = s.get("name")
            rss_url = s.get("rss_url") or s.get("url")
            list_url = s.get("list_url")
            if name and (rss_url or list_url):
                rss_url = _append_jiqizhixin_token(rss_url)
                list_url = _append_jiqizhixin_token(list_url)
                result.append({"name": name, "rss_url": rss_url, "list_url": list_url})
        if result:
            return result
    return [{"name": n, "rss_url": u, "list_url": None} for n, u in INFO_RSS_SOURCES]


async def fetch_candidates(target_date: date) -> tuple[list[dict], dict]:
    candidates: list[dict] = []
    stats = {"total": 0, "arxiv": 0, "github": 0, "huggingface": 0, "info": 0, "deduped": 0}

    # arXiv RSS -> API
    arxiv_items: list[dict] = []
    for cat, url in ARXIV_RSS_SOURCES:
        source_name = f"arxiv_{cat.lower().replace('.', '_')}"
        arxiv_items.extend(fetch_arxiv_rss(url, source_name))
    arxiv_items = [i for i in arxiv_items if _is_on_date(i.get("published_at"), target_date)]
    if arxiv_items:
        try:
            api = ArxivAPIClient()
            arxiv_items = await api.enrich(arxiv_items)
        except Exception as exc:
            logger.warning("arxiv api enrich failed: %s", exc)
    arxiv_items = [i for i in arxiv_items if _is_on_date(i.get("published_at"), target_date)]
    arxiv_items = [i for i in arxiv_items if _prefilter(i)]
    stats["arxiv"] += len(arxiv_items)
    candidates.extend(arxiv_items)

    # GitHub
    try:
        gh = GitHubAPIClient("https://api.github.com", settings.GITHUB_TOKEN)
        watchlist = _get_watchlist()
        rel_items = await gh.fetch_releases(watchlist)
        gh_items = rel_items
        gh_items = [i for i in gh_items if _is_on_date(i.get("published_at"), target_date)]
        gh_items = [i for i in gh_items if _prefilter(i)]
        stats["github"] += len(gh_items)
        candidates.extend(gh_items)
    except Exception as exc:
        logger.warning("github fetch failed: %s", exc)

    # Hugging Face papers
    try:
        date_url = HF_PAPERS_DATE_URL_TEMPLATE.format(date_str=target_date.strftime("%Y-%m-%d"))
        hf_items = await fetch_hf_papers(HF_PAPERS_URLS, date_url)
        hf_items = [i for i in hf_items if _is_on_date(i.get("published_at"), target_date)]
        hf_items = [i for i in hf_items if _prefilter(i)]
        stats["huggingface"] += len(hf_items)
        candidates.extend(hf_items)
    except Exception as exc:
        logger.warning("hf papers fetch failed: %s", exc)

    # Info RSS sources
    for source in _get_info_sources():
        name = source.get("name")
        rss_url = source.get("rss_url")
        list_url = source.get("list_url")
        try:
            info_items: list[dict] = []
            if rss_url:
                info_items = fetch_info_rss(name, rss_url)
                if info_items:
                    info_items = await enrich_items_with_content(info_items, max_items=12)
                    info_items = [i for i in info_items if _is_on_date(i.get("published_at"), target_date)]
            if (not info_items) and list_url:
                info_items = await fetch_list_candidates(name, list_url, max_items=20)
                info_items = await enrich_items_with_content(info_items, max_items=12)
                info_items = [i for i in info_items if _is_on_date(i.get("published_at"), target_date)]
            info_items = [i for i in info_items if _prefilter(i)]
            stats["info"] += len(info_items)
            candidates.extend(info_items)
        except Exception as exc:
            logger.warning("info rss fetch failed for %s: %s", name, exc)

    before = len(candidates)
    candidates, dropped = _dedup(candidates)
    stats["deduped"] = dropped
    stats["total"] = len(candidates)
    logger.info("daily_digest fetched %d candidates for %s", len(candidates), target_date)
    return candidates, stats
