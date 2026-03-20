from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailyDigestReport(Base):
    __tablename__ = "daily_digest_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    digest_date: Mapped[date] = mapped_column(Date, index=True, unique=True)
    title: Mapped[str] = mapped_column(String(255))
    summary_overview: Mapped[str] = mapped_column(Text)
    markdown_content: Mapped[str] = mapped_column(Text)
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    items = relationship("DailyDigestItem", back_populates="report", cascade="all, delete-orphan")


class DailyDigestItem(Base):
    __tablename__ = "daily_digest_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("daily_digest_reports.id"))
    digest_date: Mapped[date] = mapped_column(Date, index=True)

    source: Mapped[str] = mapped_column(String(50))
    source_name: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(1024))
    title: Mapped[str] = mapped_column(String(1024))
    author_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    doc_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    summary_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_raw: Mapped[str | None] = mapped_column(Text, nullable=True)

    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    short_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    report = relationship("DailyDigestReport", back_populates="items")
