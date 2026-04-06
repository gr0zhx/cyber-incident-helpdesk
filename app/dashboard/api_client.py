"""HTTP client untuk memanggil FastAPI helpdesk API dari dashboard Streamlit."""
import os
from typing import Any

import requests

_BASE_URL = os.getenv("HELPDESK_API_URL", "http://localhost:8000/api/v1")
_TIMEOUT = 10


def _url(path: str) -> str:
    return f"{_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


def get_all_tickets(
    reporter_id: str | None = None,
    limit: int = 200,
) -> list[dict]:
    params: dict[str, Any] = {}
    if reporter_id:
        params["reporter_id"] = reporter_id
    resp = requests.get(_url("/tickets"), params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_ticket(ticket_id: str) -> dict | None:
    resp = requests.get(_url(f"/tickets/{ticket_id}"), timeout=_TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def update_ticket(
    ticket_id: str,
    status: str | None = None,
    assigned_to: str | None = None,
    escalation_level: str | None = None,
    notify_reporter: bool = True,
) -> dict:
    payload: dict[str, Any] = {"notify_reporter": notify_reporter}
    if status is not None:
        payload["status"] = status
    if assigned_to is not None:
        payload["assigned_to"] = assigned_to
    if escalation_level is not None:
        payload["escalation_level"] = escalation_level
    resp = requests.patch(_url(f"/tickets/{ticket_id}"), json=payload, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_stats() -> dict:
    resp = requests.get(_url("/tickets/stats"), timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def health_check() -> bool:
    try:
        resp = requests.get(_url("/health"), timeout=5)
        return resp.status_code == 200
    except Exception:
        return False
