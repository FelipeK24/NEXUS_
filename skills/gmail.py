from __future__ import annotations

from extensions.google_workspace import google_workspace


def listar_emails(query: str = "in:inbox") -> str:
    return google_workspace.list_emails(query=query)


def pesquisar_emails(query: str) -> str:
    return google_workspace.search_emails(query)


def ler_email(identifier: str) -> str:
    return google_workspace.read_email(identifier)


def enviar_email(to: str, subject: str, body: str) -> str:
    return google_workspace.send_email(to, subject, body)


def responder_email(message_id: str, body: str) -> str:
    return google_workspace.reply_email(message_id, body)
