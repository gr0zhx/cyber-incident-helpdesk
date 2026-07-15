"""Helpers untuk format datetime yang konsisten di seluruh UI."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

WIB = timezone(timedelta(hours=7))


def parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime/string ISO8601 ke datetime, atau return None."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def format_system_wib(value: Any, fmt: str = "%d %b %Y %H:%M WIB") -> str:
    """Format timestamp sistem yang disimpan sebagai UTC ke WIB."""
    dt = parse_datetime(value)
    if dt is None:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(WIB).strftime(fmt)


def format_input_time(value: Any, fmt: str = "%d %b %Y %H:%M WIB") -> str:
    """Format waktu input pelapor.

    Jika nilai sudah timezone-aware, waktu akan ditampilkan dalam WIB.
    Jika nilai naive, waktu dianggap sebagai waktu lokal yang dimasukkan user.
    """
    dt = parse_datetime(value)
    if dt is None:
        return "—"
    if dt.tzinfo is not None:
        dt = dt.astimezone(WIB)
    return dt.strftime(fmt)
