from __future__ import annotations

import base64
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.parser import BytesParser
from email import policy
from pathlib import Path
from typing import Any

from core.config import (
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_ENABLED,
    GOOGLE_GMAIL_TOKEN_FILE,
    GOOGLE_TASKS_TOKEN_FILE,
    GMAIL_MAX_RESULTS,
    GOOGLE_TIMEZONE,
    GOOGLE_TOKEN_FILE,
)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
TASKS_SCOPES = ["https://www.googleapis.com/auth/tasks"]


class GoogleWorkspace:
    def __init__(self) -> None:
        self.enabled = GOOGLE_ENABLED
        self._gmail = None
        self._calendar = None
        self._tasks = None

    def _credentials(self, scopes: list[str], token_file: Path):
        if not self.enabled:
            raise RuntimeError("Integração Google desativada. Defina GOOGLE_ENABLED=true.")
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise RuntimeError(
                "Instale requirements-integrations.txt para usar Gmail, Calendar e Tasks."
            ) from exc

        creds = None
        if token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_file), scopes)
            except Exception:
                creds = None

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        if not creds or not creds.valid:
            if not GOOGLE_CREDENTIALS_FILE.exists():
                raise RuntimeError(
                    f"Credenciais Google não encontradas em {GOOGLE_CREDENTIALS_FILE}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GOOGLE_CREDENTIALS_FILE), scopes
            )
            creds = flow.run_local_server(port=0)
            token_file.parent.mkdir(parents=True, exist_ok=True)
            token_file.write_text(creds.to_json(), encoding="utf-8")

        return creds

    def _gmail_service(self):
        if self._gmail is None:
            from googleapiclient.discovery import build

            self._gmail = build(
                "gmail",
                "v1",
                credentials=self._credentials(GMAIL_SCOPES, GOOGLE_GMAIL_TOKEN_FILE),
                cache_discovery=False,
            )
        return self._gmail

    def _calendar_service(self):
        if self._calendar is None:
            from googleapiclient.discovery import build

            self._calendar = build(
                "calendar",
                "v3",
                credentials=self._credentials(CALENDAR_SCOPES, GOOGLE_TOKEN_FILE),
                cache_discovery=False,
            )
        return self._calendar

    def _tasks_service(self):
        if self._tasks is None:
            from googleapiclient.discovery import build

            self._tasks = build(
                "tasks",
                "v1",
                credentials=self._credentials(TASKS_SCOPES, GOOGLE_TASKS_TOKEN_FILE),
                cache_discovery=False,
            )
        return self._tasks

    @staticmethod
    def _headers(message: dict[str, Any]) -> dict[str, str]:
        return {
            str(item.get("name", "")).lower(): str(item.get("value", ""))
            for item in message.get("payload", {}).get("headers", [])
        }

    @staticmethod
    def _decode_part(data: str) -> str:
        raw = base64.urlsafe_b64decode(data.encode("ascii"))
        return raw.decode("utf-8", errors="replace")

    @classmethod
    def _extract_body(cls, payload: dict[str, Any]) -> str:
        mime_type = payload.get("mimeType", "")
        body_data = payload.get("body", {}).get("data")
        if body_data and mime_type.startswith("text/"):
            return cls._decode_part(body_data)

        parts = payload.get("parts", []) or []
        plain_parts: list[str] = []
        html_parts: list[str] = []
        for part in parts:
            content = cls._extract_body(part)
            if not content:
                continue
            if part.get("mimeType") == "text/html":
                html_parts.append(content)
            else:
                plain_parts.append(content)

        if plain_parts:
            return "\n".join(plain_parts)
        if html_parts:
            return "\n".join(html_parts)
        return ""

    def send_email(self, to: str, subject: str, body: str) -> str:
        message = MIMEText(body, "plain", "utf-8")
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        sent = (
            self._gmail_service()
            .users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )
        return f"E-mail enviado para {to}. ID: {sent.get('id', 'desconhecido')}"

    def list_emails(self, query: str = "in:inbox", max_results: int = GMAIL_MAX_RESULTS) -> str:
        result = (
            self._gmail_service()
            .users()
            .messages()
            .list(userId="me", q=query, maxResults=max(1, min(max_results, 20)))
            .execute()
        )
        items = result.get("messages", [])
        if not items:
            return "Não encontrei e-mails para essa consulta."

        lines: list[str] = []
        for item in items:
            message = (
                self._gmail_service()
                .users()
                .messages()
                .get(userId="me", id=item["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"])
                .execute()
            )
            headers = self._headers(message)
            sender = headers.get("from", "remetente desconhecido")
            subject = headers.get("subject", "sem assunto")
            date = headers.get("date", "")
            lines.append(f"{sender} | {subject} | {date} | id={message.get('id', '')}")
        return "E-mails encontrados:\n" + "\n".join(lines)

    def search_emails(self, query: str, max_results: int = GMAIL_MAX_RESULTS) -> str:
        query = query.strip()
        if not query:
            return "Informe o que devo pesquisar nos e-mails."
        return self.list_emails(query=query, max_results=max_results)

    def read_email(self, identifier: str) -> str:
        identifier = identifier.strip()
        if not identifier:
            return "Informe o ID ou assunto do e-mail."

        service = self._gmail_service()
        message_id = identifier

        if "@" not in identifier and " " in identifier:
            found = (
                service.users()
                .messages()
                .list(userId="me", q=f'subject:"{identifier}"', maxResults=5)
                .execute()
                .get("messages", [])
            )
            if not found:
                return "Não encontrei um e-mail com esse assunto."
            message_id = found[0]["id"]

        message = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        headers = self._headers(message)
        body = self._extract_body(message.get("payload", {})).strip()
        body = body[:12000]
        return (
            f"De: {headers.get('from', 'desconhecido')}\n"
            f"Assunto: {headers.get('subject', 'sem assunto')}\n"
            f"Data: {headers.get('date', '')}\n"
            f"ID: {message.get('id', '')}\n\n"
            f"{body or '[E-mail sem texto legível.]'}"
        )

    def reply_email(self, message_id: str, body: str) -> str:
        service = self._gmail_service()
        original = service.users().messages().get(
            userId="me", id=message_id.strip(), format="metadata", metadataHeaders=["From", "To", "Reply-To", "Subject", "Message-ID", "References"]
        ).execute()
        headers = self._headers(original)
        recipient = headers.get("reply-to") or headers.get("from", "")
        subject = headers.get("subject", "")
        if not recipient:
            return "Não consegui identificar o destinatário do e-mail original."
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        message = MIMEText(body, "plain", "utf-8")
        message["to"] = recipient
        message["subject"] = subject
        if headers.get("message-id"):
            message["In-Reply-To"] = headers["message-id"]
            refs = headers.get("references", "")
            message["References"] = (refs + " " + headers["message-id"]).strip()

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        service.users().messages().send(
            userId="me",
            body={"raw": raw, "threadId": original.get("threadId")},
        ).execute()
        return f"Resposta enviada para {recipient}."

    def list_events(self, days: int = 7) -> str:
        now = datetime.now().astimezone()
        end = now + timedelta(days=max(1, days))
        events = (
            self._calendar_service()
            .events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=20,
            )
            .execute()
            .get("items", [])
        )
        if not events:
            return f"Não há eventos nos próximos {days} dias."
        lines = []
        for item in events:
            start = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
            lines.append(f"{start} — {item.get('summary', 'Sem título')}")
        return "Agenda:\n" + "\n".join(lines)

    def create_event(self, summary: str, start: str, end: str, description: str = "") -> str:
        body: dict[str, Any] = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start, "timeZone": GOOGLE_TIMEZONE},
            "end": {"dateTime": end, "timeZone": GOOGLE_TIMEZONE},
        }
        event = self._calendar_service().events().insert(calendarId="primary", body=body).execute()
        return f"Evento criado: {event.get('htmlLink', summary)}"

    def _default_task_list_id(self) -> str:
        service = self._tasks_service()
        lists = service.tasklists().list(maxResults=20).execute().get("items", [])
        if not lists:
            raise RuntimeError("Nenhuma lista do Google Tasks foi encontrada.")
        return lists[0]["id"]

    def list_google_tasks(self, show_completed: bool = False) -> str:
        service = self._tasks_service()
        task_list_id = self._default_task_list_id()
        items = (
            service.tasks()
            .list(
                tasklist=task_list_id,
                maxResults=20,
                showCompleted=show_completed,
                showHidden=False,
            )
            .execute()
            .get("items", [])
        )
        if not items:
            return "Não há tarefas no Google Tasks."
        visible = [x for x in items if show_completed or x.get("status") != "completed"]
        if not visible:
            return "Não há tarefas pendentes no Google Tasks."
        return "Google Tasks:\n" + "\n".join(
            f"{index}. {item.get('title', 'Sem título')} (id={item.get('id', '')})"
            for index, item in enumerate(visible, start=1)
        )

    def add_google_task(self, title: str, notes: str = "") -> str:
        service = self._tasks_service()
        task_list_id = self._default_task_list_id()
        item = service.tasks().insert(
            tasklist=task_list_id,
            body={"title": title.strip(), "notes": notes.strip()},
        ).execute()
        return f"Tarefa adicionada ao Google Tasks: {item.get('title', title)}."

    def complete_google_task(self, identifier: str) -> str:
        service = self._tasks_service()
        task_list_id = self._default_task_list_id()
        tasks = service.tasks().list(tasklist=task_list_id, maxResults=50, showCompleted=False).execute().get("items", [])
        target = None
        for item in tasks:
            if item.get("id") == identifier.strip() or item.get("title", "").strip().lower() == identifier.strip().lower():
                target = item
                break
        if target is None:
            return "Não encontrei essa tarefa no Google Tasks."
        service.tasks().patch(tasklist=task_list_id, task=target["id"], body={"status": "completed"}).execute()
        return f"Tarefa concluída no Google Tasks: {target.get('title', identifier)}."

    def delete_google_task(self, identifier: str) -> str:
        service = self._tasks_service()
        task_list_id = self._default_task_list_id()
        tasks = service.tasks().list(tasklist=task_list_id, maxResults=50, showCompleted=True).execute().get("items", [])
        target = None
        for item in tasks:
            if item.get("id") == identifier.strip() or item.get("title", "").strip().lower() == identifier.strip().lower():
                target = item
                break
        if target is None:
            return "Não encontrei essa tarefa no Google Tasks."
        service.tasks().delete(tasklist=task_list_id, task=target["id"]).execute()
        return f"Tarefa excluída do Google Tasks: {target.get('title', identifier)}."


google_workspace = GoogleWorkspace()
