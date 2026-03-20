from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.daily_digest.routes import router as daily_digest_router
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title="Daily Digest")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(daily_digest_router)


@app.on_event("startup")
def _init_db() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def _root():
    return RedirectResponse(url="/daily-digest")
