from __future__ import annotations

import json
from typing import Any


MAX_JSON_BODY_BYTES = 64 * 1024
MAX_COMMAND_CHARS = 4096


class RequestBodyError(ValueError):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def read_json_object(handler) -> dict[str, Any]:
    if handler.headers.get_content_type() != "application/json":
        raise RequestBodyError("Content-Type precisa ser application/json.", 415)

    try:
        length = int(handler.headers.get("Content-Length", ""))
    except (TypeError, ValueError) as exc:
        raise RequestBodyError("Content-Length inválido.") from exc

    if length <= 0:
        raise RequestBodyError("Corpo JSON vazio.")
    if length > MAX_JSON_BODY_BYTES:
        raise RequestBodyError("Corpo da requisição excede o limite permitido.", 413)

    raw = handler.rfile.read(length)
    if len(raw) != length:
        raise RequestBodyError("Corpo da requisição incompleto.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RequestBodyError("JSON inválido.") from exc
    if not isinstance(payload, dict):
        raise RequestBodyError("O JSON precisa ser um objeto.")
    return payload


def command_text(payload: dict[str, Any]) -> str:
    text = payload.get("text")
    if not isinstance(text, str):
        raise RequestBodyError("O campo 'text' precisa ser uma string.")
    text = text.strip()
    if not text:
        raise RequestBodyError("Comando vazio.")
    if len(text) > MAX_COMMAND_CHARS:
        raise RequestBodyError("Comando excede o limite permitido.", 413)
    return text
