from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import markdown


def _fmt_date(dt: datetime | None) -> str:
    if not dt:
        return ""
    try:
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(dt)


def build_daily_markdown(date_str: str, docs: list[dict]) -> str:
    if not docs:
        return f"# {date_str} 技术日报\n\n暂无高价值内容。"

    top_docs = docs[:5]
    topics = defaultdict(list)
    for d in docs:
        topics[d.get("topic") or "other"].append(d)

    topic_lines = []
    for topic, items in topics.items():
        topic_lines.append(f"### {topic}")
        for d in items[:3]:
            topic_lines.append(f"- [{d['title']}]({d['url']})（score: {d.get('final_score', '-'):.2f}）")

    follow_up = [d for d in docs if d.get("action") in {"track", "read"}][:5]
    reproduce = [d for d in docs if d.get("action") == "reproduce"][:5]

    def fmt_list(items: list[dict]) -> str:
        if not items:
            return "- 暂无"
        return "\n".join(
            [f"- [{d['title']}]({d['url']})（score: {d.get('final_score', '-'):.2f}）" for d in items]
        )

    markdown_content = f"""# {date_str} 技术日报

## 今日总览
- 高价值条目：{len(docs)}
- 主要主题：{", ".join(list(topics.keys())[:5])}

## Top 5 值得关注
{fmt_list(top_docs)}

## 分主题摘要
{chr(10).join(topic_lines)}

## 值得跟进方向
{fmt_list(follow_up)}

## 值得收藏/复现
{fmt_list(reproduce)}

## 附录：全部条目
{fmt_list(docs)}
"""
    return markdown_content.strip()


def render_markdown(md: str) -> str:
    return markdown.markdown(md, extensions=["fenced_code", "tables"])
