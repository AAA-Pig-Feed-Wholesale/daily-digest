from __future__ import annotations

import sys
from typing import Any

import feedparser
import httpx

from app.config.settings import settings


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def _get_sources() -> dict[str, Any]:
    return settings.SOURCES_CONFIG or {}


def _http_client() -> httpx.Client:
    return httpx.Client(
        timeout=10,
        follow_redirects=True,
        headers={"User-Agent": UA},
        trust_env=True,
    )


def fetch_rss(url: str) -> tuple[int, str | None]:
    try:
        with _http_client() as client:
            resp = client.get(url)
        if resp.status_code != 200:
            return 0, f"status={resp.status_code}"
        parsed = feedparser.parse(resp.text)
        return len(parsed.entries or []), None
    except Exception as exc:  # noqa: BLE001
        return 0, f"error: {exc}"


def check_list(url: str) -> str:
    try:
        with _http_client() as client:
            resp = client.get(url)
        return f"status={resp.status_code}"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def check_github(repos: list[str]) -> str:
    headers = {"User-Agent": UA}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
    total = 0
    try:
        with _http_client() as client:
            for repo in repos:
                resp = client.get(
                    f"https://api.github.com/repos/{repo}/releases?per_page=1",
                    headers=headers,
                )
                if resp.status_code != 200:
                    return f"error: status={resp.status_code}"
                data = resp.json()
                if isinstance(data, list):
                    total += len(data)
        return f"releases={total}"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def check_structured_page(name: str, url: str) -> str:
    try:
        headers = {"User-Agent": UA}
        if "huggingface.co" in url and settings.HF_TOKEN:
            headers["Authorization"] = f"Bearer {settings.HF_TOKEN}"
        with _http_client() as client:
            resp = client.get(url, headers=headers)
        return f"status={resp.status_code}"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def main() -> int:
    sources = _get_sources()

    print("== core sources ==")
    for src in sources.get("sources", []):
        name = src.get("name")
        src_type = src.get("type")
        if not name or not src_type:
            continue
        if src_type == "rss":
            count, err = fetch_rss(src.get("base_url", ""))
            if err:
                print(f"{name}: rss={err}")
            else:
                print(f"{name}: rss_items={count}")
        elif src_type == "api" and name == "github_watchlist":
            repos = sources.get("github_watchlists", {}).get("repos", [])
            print(f"{name}: {check_github(repos)}")
        elif src_type == "structured_page":
            url = src.get("base_url", "")
            print(f"{name}: {check_structured_page(name, url)}")
        else:
            print(f"{name}: type={src_type} (skipped)")

    print("\n== daily_digest_info_sources ==")
    for info in sources.get("daily_digest_info_sources", []):
        name = info.get("name")
        rss_url = info.get("rss_url")
        list_url = info.get("list_url")
        if not name:
            continue
        rss_part = "rss=-"
        list_part = "list=-"
        if rss_url:
            count, err = fetch_rss(rss_url)
            rss_part = f"rss_items={count}" if not err else f"rss_{err}"
        if list_url:
            list_part = check_list(list_url)
        print(f"{name}: {rss_part} {list_part}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
