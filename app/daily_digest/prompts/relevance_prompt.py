from __future__ import annotations

from typing import Any


def build_relevance_prompt(item: dict[str, Any]) -> str:
    title = item.get("title") or ""
    summary = item.get("summary_raw") or ""
    content = item.get("content_raw") or ""
    source = item.get("source") or ""
    doc_type = item.get("doc_type") or ""

    return f"""
你是一名资深 AI 应用工程师，请对下面内容做相关性评分（0-100），并输出严格 JSON。
评分维度：
- 主题相关性（是否与大模型应用开发有关）
- 工程价值（是否对落地/实现有价值）
- 信息密度（是否有明确的技术信息）

要求输出 JSON：
{{
  "relevance_score": 0-100,
  "short_summary": "一句话总结",
  "relevance_reason": "为什么相关"
}}

内容信息：
来源：{source}
类型：{doc_type}
标题：{title}
摘要：{summary}
正文片段：{content[:1200]}
""".strip()
