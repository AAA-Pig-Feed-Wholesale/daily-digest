from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DigestItemIn(BaseModel):
    source: str
    source_name: str
    external_id: Optional[str] = None
    url: str
    title: str
    author_text: Optional[str] = None
    published_at: Optional[datetime] = None
    doc_type: Optional[str] = None
    summary_raw: Optional[str] = None
    content_raw: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class DigestItemOut(BaseModel):
    id: int
    source: str
    source_name: str
    external_id: Optional[str] = None
    url: str
    title: str
    author_text: Optional[str] = None
    published_at: Optional[datetime] = None
    doc_type: Optional[str] = None
    summary_raw: Optional[str] = None
    content_raw: Optional[str] = None
    relevance_score: Optional[float] = None
    short_summary: Optional[str] = None
    relevance_reason: Optional[str] = None
    created_at: datetime
    digest_date: date


class DailyDigestReportOut(BaseModel):
    id: int
    digest_date: date
    title: str
    summary_overview: str
    markdown_content: str
    html_content: Optional[str] = None
    item_count: int
    created_at: datetime


class DailyDigestResponse(BaseModel):
    report: Optional[DailyDigestReportOut] = None
    items: list[DigestItemOut] = Field(default_factory=list)


class RunDigestRequest(BaseModel):
    date: Optional[date] = None
    force: bool = False
