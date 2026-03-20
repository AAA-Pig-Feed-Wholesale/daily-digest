from __future__ import annotations

from datetime import date
import logging

from sqlalchemy.orm import Session

from app.daily_digest.constants import DEFAULT_SUMMARY_LIMIT
from app.daily_digest.services.fetch_service import fetch_candidates
from app.config.settings import settings
from app.daily_digest.progress import progress_store
from app.daily_digest.services.rank_service import score_items
from app.daily_digest.services.storage_service import get_report_with_items, save_report
from app.reports.formatter import render_markdown

logger = logging.getLogger(__name__)


def _build_summary_overview(items: list[dict]) -> str:
    if not items:
        return "暂无符合条件的条目。"
    top_titles = [item.get("title") for item in items[:3] if item.get("title")]
    focus = "；".join(top_titles)
    return f"共 {len(items)} 条，重点关注：{focus}" if focus else f"共 {len(items)} 条。"


def _build_markdown(digest_date: date, summary: str, items: list[dict]) -> str:
    lines = [f"# {digest_date.strftime('%Y-%m-%d')} 前沿文章日报", "", "## 概览", summary, "", "## 详情"]
    if not items:
        lines.append("暂无条目。")
        return "\n".join(lines)
    for idx, item in enumerate(items, start=1):
        title = item.get("title") or "(无标题)"
        url = item.get("url") or ""
        source = item.get("source_name") or item.get("source") or ""
        published = item.get("published_at")
        published_str = published.strftime("%Y-%m-%d") if published else "未知"
        score = item.get("relevance_score")
        score_str = f"{score:.1f}" if score is not None else "-"
        short_summary = (item.get("short_summary") or "").strip()
        if len(short_summary) > DEFAULT_SUMMARY_LIMIT:
            short_summary = short_summary[:DEFAULT_SUMMARY_LIMIT] + "..."
        reason = (item.get("relevance_reason") or "").strip()
        lines.append(f"{idx}. [{title}]({url})")
        lines.append(f"   - 来源：{source}")
        lines.append(f"   - 发布时间：{published_str}")
        lines.append(f"   - 相关性评分：{score_str}")
        if short_summary:
            lines.append(f"   - 一句话总结：{short_summary}")
        if reason:
            lines.append(f"   - 为什么相关：{reason}")
    return "\n".join(lines)


async def generate_daily_digest(db: Session, digest_date: date, force: bool = False) -> tuple[dict, list[dict]]:
    date_str = digest_date.strftime("%Y-%m-%d")
    existing_report, existing_items = get_report_with_items(db, digest_date)
    if existing_report and not force:
        progress_store.update(date_str, "done", "已生成", 100)
        report_dict = {
            "id": existing_report.id,
            "digest_date": existing_report.digest_date,
            "title": existing_report.title,
            "summary_overview": existing_report.summary_overview,
            "markdown_content": existing_report.markdown_content,
            "html_content": existing_report.html_content,
            "item_count": existing_report.item_count,
            "created_at": existing_report.created_at,
        }
        items_dict = [
            {
                "id": item.id,
                "source": item.source,
                "source_name": item.source_name,
                "external_id": item.external_id,
                "url": item.url,
                "title": item.title,
                "author_text": item.author_text,
                "published_at": item.published_at,
                "doc_type": item.doc_type,
                "summary_raw": item.summary_raw,
                "content_raw": item.content_raw,
                "relevance_score": item.relevance_score,
                "short_summary": item.short_summary,
                "relevance_reason": item.relevance_reason,
                "created_at": item.created_at,
                "digest_date": item.digest_date,
            }
            for item in existing_items
        ]
        return report_dict, items_dict

    try:
        progress_store.update(date_str, "fetching", "抓取前一天内容", 15, {"fetched_total": 0})
        candidates, stats = await fetch_candidates(digest_date)
        progress_store.update(
            date_str,
            "fetching",
            (
                f"抓取完成：{stats.get('total', 0)} 条（arXiv {stats.get('arxiv', 0)} / "
                f"HF {stats.get('huggingface', 0)} / GH {stats.get('github', 0)} / "
                f"Info {stats.get('info', 0)}，去重 {stats.get('deduped', 0)}）"
            ),
            35,
            {
                "fetched_total": stats.get("total", 0),
                "arxiv": stats.get("arxiv", 0),
                "huggingface": stats.get("huggingface", 0),
                "github": stats.get("github", 0),
                "info": stats.get("info", 0),
                "deduped": stats.get("deduped", 0),
            },
        )

        progress_store.update(date_str, "scoring", "相关性评分与摘要", 60)
        scored = await score_items(candidates)
        scored = [item for item in scored if (item.get("relevance_score") or 0) >= settings.MIN_RELEVANCE_SCORE]
        scored = sorted(scored, key=lambda x: x.get("relevance_score", 0), reverse=True)
        progress_store.update(date_str, "scoring", f"评分完成：{len(scored)} 条", 70, {"scored": len(scored)})

        progress_store.update(date_str, "reporting", "生成日报与保存", 85)
    except Exception:
        progress_store.update(date_str, "failed", "生成失败，请重试", 0)
        raise

    summary = _build_summary_overview(scored)
    markdown_content = _build_markdown(digest_date, summary, scored)
    html_content = render_markdown(markdown_content)
    title = f"{digest_date.strftime('%Y-%m-%d')} 前沿文章日报"

    report = save_report(
        db,
        digest_date=digest_date,
        title=title,
        summary_overview=summary,
        markdown_content=markdown_content,
        html_content=html_content,
        items=scored,
        force=True,
    )

    refreshed_report, refreshed_items = get_report_with_items(db, digest_date)
    if not refreshed_report:
        progress_store.update(date_str, "failed", "生成失败，请重试", 0)
        report_dict = {
            "id": report.id,
            "digest_date": report.digest_date,
            "title": report.title,
            "summary_overview": report.summary_overview,
            "markdown_content": report.markdown_content,
            "html_content": report.html_content,
            "item_count": report.item_count,
            "created_at": report.created_at,
        }
        return report_dict, []

    progress_store.update(date_str, "done", "生成完成", 100, {"stored": len(refreshed_items)})
    report_dict = {
        "id": refreshed_report.id,
        "digest_date": refreshed_report.digest_date,
        "title": refreshed_report.title,
        "summary_overview": refreshed_report.summary_overview,
        "markdown_content": refreshed_report.markdown_content,
        "html_content": refreshed_report.html_content,
        "item_count": refreshed_report.item_count,
        "created_at": refreshed_report.created_at,
    }
    items_dict = [
        {
            "id": item.id,
            "source": item.source,
            "source_name": item.source_name,
            "external_id": item.external_id,
            "url": item.url,
            "title": item.title,
            "author_text": item.author_text,
            "published_at": item.published_at,
            "doc_type": item.doc_type,
            "summary_raw": item.summary_raw,
            "content_raw": item.content_raw,
            "relevance_score": item.relevance_score,
            "short_summary": item.short_summary,
            "relevance_reason": item.relevance_reason,
            "created_at": item.created_at,
            "digest_date": item.digest_date,
        }
        for item in refreshed_items
    ]
    return report_dict, items_dict
