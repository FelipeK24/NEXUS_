from __future__ import annotations

import json
from pathlib import Path

from core.config import CONTACTS_FILE
from extensions.google_workspace import google_workspace


def _contacts() -> dict[str, str]:
    try:
        data = json.loads(Path(CONTACTS_FILE).read_text(encoding="utf-8"))
        return {str(k).lower(): str(v) for k, v in data.items()} if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def resolve_recipient(value: str) -> str:
    value = value.strip()
    if "@" in value:
        return value
    return _contacts().get(value.lower(), value)


def enviar_email(to: str, subject: str, body: str) -> str:
    recipient = resolve_recipient(to)
    if "@" not in recipient:
        return "Não encontrei um endereço de e-mail válido para esse contato. Configure data/contacts.json ou informe o e-mail diretamente."
    return google_workspace.send_email(recipient, subject, body)
