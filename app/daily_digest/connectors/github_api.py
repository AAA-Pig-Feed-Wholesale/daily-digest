from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx


class GitHubAPIClient:
    def __init__(self, base_url: str, token: str | None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _get(self, client: httpx.AsyncClient, path: str) -> Any:
        resp = await client.get(f"{self.base_url}{path}")
        resp.raise_for_status()
        return resp.json()

    async def fetch_repos(self, repos: list[str]) -> list[dict]:
        items: list[dict] = []
        async with httpx.AsyncClient(timeout=20, headers=self._headers()) as client:
            for repo in repos:
                data = await self._get(client, f"/repos/{repo}")
                pushed_at = data.get("pushed_at")
                published = datetime.fromisoformat(pushed_at.replace("Z", "+00:00")) if pushed_at else None
                items.append(
                    {
                        "source": "github",
                        "source_name": "github_watchlist",
                        "external_id": str(data.get("id")) if data.get("id") else None,
                        "url": data.get("html_url") or f"https://github.com/{repo}",
                        "title": data.get("full_name") or repo,
                        "author_text": None,
                        "published_at": published,
                        "doc_type": "repo_update",
                        "summary_raw": data.get("description"),
                        "content_raw": data.get("description"),
                        "metadata": {
                            "stars": data.get("stargazers_count"),
                            "forks": data.get("forks_count"),
                            "topics": data.get("topics", []),
                            "repo": repo,
                        },
                    }
                )
        return items

    async def fetch_releases(self, repos: list[str]) -> list[dict]:
        items: list[dict] = []
        async with httpx.AsyncClient(timeout=20, headers=self._headers()) as client:
            for repo in repos:
                data = await self._get(client, f"/repos/{repo}/releases")
                for rel in data[:10]:
                    published_at = rel.get("published_at")
                    published = datetime.fromisoformat(published_at.replace("Z", "+00:00")) if published_at else None
                    body = rel.get("body") or ""
                    tag = rel.get("tag_name") or ""
                    if not body.strip():
                        body = f"Release {tag} for {repo}".strip()
                    items.append(
                        {
                            "source": "github",
                            "source_name": "github_watchlist",
                            "external_id": str(rel.get("id")) if rel.get("id") else None,
                            "url": rel.get("html_url") or f"https://github.com/{repo}/releases",
                            "title": rel.get("name") or rel.get("tag_name") or repo,
                            "author_text": rel.get("author", {}).get("login") if rel.get("author") else None,
                            "published_at": published,
                            "doc_type": "release",
                            "summary_raw": body,
                            "content_raw": body,
                            "metadata": {"repo": repo, "tag": tag},
                        }
                    )
        return items

    async def fetch_events(self, repos: list[str]) -> list[dict]:
        items: list[dict] = []
        async with httpx.AsyncClient(timeout=20, headers=self._headers()) as client:
            for repo in repos:
                data = await self._get(client, f"/repos/{repo}/events")
                for ev in data[:10]:
                    ev_type = ev.get("type")
                    if ev_type not in {"PullRequestEvent"}:
                        continue
                    created = ev.get("created_at")
                    published = datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None
                    pr = ev.get("payload", {}).get("pull_request", {}) if ev_type == "PullRequestEvent" else {}
                    title = pr.get("title") or f"{repo} PR 更新"
                    url = pr.get("html_url") or f"https://github.com/{repo}"
                    items.append(
                        {
                            "source": "github",
                            "source_name": "github_watchlist",
                            "external_id": str(ev.get("id")) if ev.get("id") else None,
                            "url": url,
                            "title": title,
                            "author_text": pr.get("user", {}).get("login") if pr.get("user") else None,
                            "published_at": published,
                            "doc_type": "repo_event",
                            "summary_raw": pr.get("body") or ev_type,
                            "content_raw": pr.get("body") or ev_type,
                            "metadata": {"repo": repo, "event_type": ev_type},
                        }
                    )
        return items
