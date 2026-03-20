from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.daily_digest.constants import get_default_digest_date
from app.daily_digest.deps import get_db
from app.daily_digest.schemas import DailyDigestResponse
from app.daily_digest.services.report_service import generate_daily_digest
from app.daily_digest.services.storage_service import get_report_with_items
from app.daily_digest.progress import progress_store

router = APIRouter()

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)


def _parse_date(value: str | None) -> date:
    if not value:
        return get_default_digest_date()
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return get_default_digest_date()


@router.get("/daily-digest")
async def daily_digest_page(request: Request, date: Optional[str] = None):
    target_date = _parse_date(date)
    return templates.TemplateResponse(
        "daily_digest_page.html",
        {
            "request": request,
            "date": target_date.strftime("%Y-%m-%d"),
        },
    )


@router.post("/daily-digest/run")
async def run_daily_digest(
    request: Request,
    date: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    target_date = _parse_date(date)
    await generate_daily_digest(db, target_date, force=True)
    return RedirectResponse(url=f"/daily-digest?date={target_date.strftime('%Y-%m-%d')}", status_code=303)


@router.get("/api/daily-digest", response_model=DailyDigestResponse)
async def get_daily_digest(date: Optional[str] = None, db: Session = Depends(get_db)):
    target_date = _parse_date(date)
    report, items = get_report_with_items(db, target_date)
    if not report:
        return {"report": None, "items": []}
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
        for item in items
    ]
    return {"report": report_dict, "items": items_dict}


@router.get("/api/daily-digest/status")
async def get_daily_digest_status(date: Optional[str] = None):
    target_date = _parse_date(date)
    date_str = target_date.strftime("%Y-%m-%d")
    return progress_store.get(date_str)


@router.post("/api/daily-digest/run", response_model=DailyDigestResponse)
async def run_daily_digest_api(request: Request, db: Session = Depends(get_db)):
    payload: dict = {}
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    date_str = payload.get("date")
    force = bool(payload.get("force", False))
    target_date = _parse_date(date_str)
    report, items = await generate_daily_digest(db, target_date, force=force)
    return {"report": report, "items": items}
