from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from core.config import GOOGLE_CREDENTIALS_FILE, GOOGLE_ENABLED, GOOGLE_TIMEZONE, GOOGLE_TOKEN_FILE

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleWorkspace:
    def __init__(self) -> None:
        self.enabled = GOOGLE_ENABLED
        self._gmail = None
        self._calendar = None

    def _credentials(self, scopes: list[str]):
        if not self.enabled:
            raise RuntimeError("Integração Google desativada. Defina GOOGLE_ENABLED=true.")
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise RuntimeError("Instale requirements-integrations.txt para usar Gmail/Calendar.") from exc

        creds = None
        if GOOGLE_TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), scopes)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            if not GOOGLE_CREDENTIALS_FILE.exists():
                raise RuntimeError(f"Credenciais Google não encontradas em {GOOGLE_CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(str(GOOGLE_CREDENTIALS_FILE), scopes)
            creds = flow.run_local_server(port=0)
            GOOGLE_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            GOOGLE_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        return creds

    def _gmail_service(self):
        if self._gmail is None:
            from googleapiclient.discovery import build
            self._gmail = build("gmail", "v1", credentials=self._credentials(GMAIL_SCOPES), cache_discovery=False)
        return self._gmail

    def _calendar_service(self):
        if self._calendar is None:
            from googleapiclient.discovery import build
            self._calendar = build("calendar", "v3", credentials=self._credentials(CALENDAR_SCOPES), cache_discovery=False)
        return self._calendar

    def send_email(self, to: str, subject: str, body: str) -> str:
        message = MIMEText(body, "plain", "utf-8")
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        sent = self._gmail_service().users().messages().send(userId="me", body={"raw": raw}).execute()
        return f"E-mail enviado para {to}. ID: {sent.get('id', 'desconhecido')}"

    def list_events(self, days: int = 7) -> str:
        now = datetime.now().astimezone()
        end = now + timedelta(days=max(1, days))
        events = self._calendar_service().events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=20,
        ).execute().get("items", [])
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


google_workspace = GoogleWorkspace()
