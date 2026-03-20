from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI

from app.config.settings import PROVIDERS_CONFIG, settings
from app.daily_digest.constants import KEYWORDS
from app.daily_digest.prompts.relevance_prompt import build_relevance_prompt

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            return json.loads(match.group(0))
        raise


def _keyword_score(text: str) -> float:
    lower = text.lower()
    hits = sum(1 for k in KEYWORDS if k in lower)
    return min(100.0, hits * 12.5)


def _build_fallback(item: dict) -> dict:
    text = " ".join([item.get("title") or "", item.get("summary_raw") or "", item.get("content_raw") or ""])
    score = _keyword_score(text)
    short_summary = (item.get("summary_raw") or item.get("content_raw") or item.get("title") or "").strip()
    if len(short_summary) > 160:
        short_summary = short_summary[:160] + "..."
    reason = "匹配到关键词，初步判断与大模型应用开发相关。" if score > 0 else "未匹配到关键词。"
    return {
        "relevance_score": score,
        "short_summary": short_summary,
        "relevance_reason": reason,
    }


class DigestLLMClient:
    def __init__(self) -> None:
        cfg = (PROVIDERS_CONFIG or {}).get("openai_compatible") or {}
        if cfg.get("api_key") and cfg.get("base_url"):
            base_url = cfg.get("base_url") or ""
            base_url = base_url.rstrip("/")
            if not base_url.endswith("/v1"):
                base_url = f"{base_url}/v1"
            self.client = AsyncOpenAI(api_key=cfg.get("api_key"), base_url=base_url)
            self.model = cfg.get("model") or settings.OPENAI_MODEL
        elif settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)
            self.model = settings.OPENAI_MODEL
        else:
            self.client = None
            self.model = None

    async def score(self, item: dict) -> dict:
        if not self.client or not self.model:
            return _build_fallback(item)
        prompt = build_relevance_prompt(item)
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a careful analyst. Output strict JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = resp.choices[0].message.content or "{}"
            data = _extract_json(content)
            return {
                "relevance_score": float(data.get("relevance_score", 0)),
                "short_summary": data.get("short_summary") or "",
                "relevance_reason": data.get("relevance_reason") or "",
            }
        except Exception as exc:
            logger.warning("daily_digest LLM scoring failed: %s", exc)
            return _build_fallback(item)


async def score_items(items: list[dict], concurrency: int = 5) -> list[dict]:
    client = DigestLLMClient()
    sem = asyncio.Semaphore(concurrency)

    async def _score(item: dict) -> dict:
        async with sem:
            scored = await client.score(item)
            return item | scored

    tasks = [_score(item) for item in items]
    return await asyncio.gather(*tasks) if tasks else []
