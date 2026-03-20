from __future__ import annotations

from datetime import date
from typing import Iterable

from sqlalchemy.orm import Session

from app.daily_digest.models import DailyDigestItem, DailyDigestReport


def get_report_with_items(db: Session, digest_date: date) -> tuple[DailyDigestReport | None, list[DailyDigestItem]]:
    report = db.query(DailyDigestReport).filter(DailyDigestReport.digest_date == digest_date).first()
    if not report:
        return None, []
    items = db.query(DailyDigestItem).filter(DailyDigestItem.report_id == report.id).order_by(DailyDigestItem.relevance_score.desc().nullslast()).all()
    return report, items


def save_report(
    db: Session,
    digest_date: date,
    title: str,
    summary_overview: str,
    markdown_content: str,
    html_content: str | None,
    items: list[dict],
    force: bool = False,
) -> DailyDigestReport:
    report = db.query(DailyDigestReport).filter(DailyDigestReport.digest_date == digest_date).first()
    if report and not force:
        return report

    if report:
        db.query(DailyDigestItem).filter(DailyDigestItem.report_id == report.id).delete()
        report.title = title
        report.summary_overview = summary_overview
        report.markdown_content = markdown_content
        report.html_content = html_content
        report.item_count = len(items)
    else:
        report = DailyDigestReport(
            digest_date=digest_date,
            title=title,
            summary_overview=summary_overview,
            markdown_content=markdown_content,
            html_content=html_content,
            item_count=len(items),
        )
        db.add(report)
        db.flush()

    for item in items:
        db.add(
            DailyDigestItem(
                report_id=report.id,
                digest_date=digest_date,
                source=item.get("source"),
                source_name=item.get("source_name"),
                external_id=item.get("external_id"),
                url=item.get("url"),
                title=item.get("title"),
                author_text=item.get("author_text"),
                published_at=item.get("published_at"),
                doc_type=item.get("doc_type"),
                summary_raw=item.get("summary_raw"),
                content_raw=item.get("content_raw"),
                relevance_score=item.get("relevance_score"),
                short_summary=item.get("short_summary"),
                relevance_reason=item.get("relevance_reason"),
            )
        )

    db.commit()
    db.refresh(report)
    return report
