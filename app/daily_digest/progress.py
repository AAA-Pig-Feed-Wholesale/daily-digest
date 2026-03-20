from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Optional


class ProgressStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._data: dict[str, dict] = {}

    def update(
        self,
        date_str: str,
        status: str,
        message: Optional[str] = None,
        progress: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> None:
        with self._lock:
            record = self._data.get(date_str, {})
            current_details = record.get("details") or {}
            if details:
                current_details.update(details)
            record.update(
                {
                    "status": status,
                    "message": message or record.get("message") or "",
                    "progress": progress if progress is not None else record.get("progress", 0),
                    "updated_at": datetime.utcnow().isoformat(),
                    "details": current_details,
                }
            )
            self._data[date_str] = record

    def get(self, date_str: str) -> dict:
        with self._lock:
            return self._data.get(
                date_str,
                {
                    "status": "idle",
                    "message": "就绪",
                    "progress": 0,
                    "updated_at": None,
                    "details": {},
                },
            )


progress_store = ProgressStore()
