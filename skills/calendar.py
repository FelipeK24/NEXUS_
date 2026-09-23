from __future__ import annotations

from extensions.google_workspace import google_workspace
from core.config import GOOGLE_TIMEZONE


def _parse_datetime(value: str) -> str:
    try:
        import dateparser
    except ImportError as exc:
        raise RuntimeError("Instale requirements-integrations.txt para usar o Calendar.") from exc
    parsed = dateparser.parse(
        value,
        settings={
            "TIMEZONE": GOOGLE_TIMEZONE,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
        },
    )
    if parsed is None:
        raise ValueError(f"Não consegui entender a data/hora: {value}")
    return parsed.isoformat()


def listar_agenda(days: int = 7) -> str:
    return google_workspace.list_events(days=int(days))


def criar_evento(summary: str, start: str, end: str, description: str = "") -> str:
    return google_workspace.create_event(summary, _parse_datetime(start), _parse_datetime(end), description)
