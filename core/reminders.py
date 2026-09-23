from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Callable

from core.config import REMINDERS_FILE, REMINDER_POLL_SECONDS, REMINDER_SPEAK, ASSISTANT_NAME, ROOT_DIR

logger = logging.getLogger("jarvis.reminders")


class ReminderManager:
    def __init__(self, notify_callback: Callable[[str, str], None] | None = None):
        self.file_path = REMINDERS_FILE
        self.notify_callback = notify_callback
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._save([])

    def _load(self) -> list[dict]:
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def _save(self, data: list[dict]) -> None:
        self.file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._worker, name="nexus-reminders", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def add(self, message: str, when: str) -> str:
        parsed = self._parse_datetime(when)
        item = {
            "id": uuid.uuid4().hex[:8],
            "message": message.strip(),
            "when": parsed.isoformat(),
            "done": False,
            "created_at": datetime.now().astimezone().isoformat(),
        }
        with self._lock:
            reminders = self._load()
            reminders.append(item)
            self._save(reminders)
        return f"Lembrete criado para {parsed.astimezone().strftime('%d/%m/%Y às %H:%M')}: {message.strip()}"

    def list_pending(self) -> str:
        with self._lock:
            items = [item for item in self._load() if not item.get("done")]
        if not items:
            return "Você não possui lembretes pendentes."
        items.sort(key=lambda item: item.get("when", ""))
        lines = []
        for item in items:
            try:
                when = datetime.fromisoformat(item["when"]).astimezone().strftime("%d/%m/%Y %H:%M")
            except Exception:
                when = item.get("when", "")
            lines.append(f"{item.get('id')} — {when} — {item.get('message', '')}")
        return "Lembretes pendentes:\n" + "\n".join(lines)

    def cancel(self, identifier: str) -> str:
        value = identifier.strip().lower()
        with self._lock:
            reminders = self._load()
            for item in reminders:
                if str(item.get("id", "")).lower() == value:
                    item["done"] = True
                    item["cancelled"] = True
                    self._save(reminders)
                    return f"Lembrete {identifier} cancelado."
                if str(item.get("message", "")).strip().lower() == value:
                    item["done"] = True
                    item["cancelled"] = True
                    self._save(reminders)
                    return f"Lembrete cancelado: {item.get('message', identifier)}."
        return "Não encontrei esse lembrete."

    def _parse_datetime(self, value: str) -> datetime:
        try:
            import dateparser
        except ImportError as exc:
            raise RuntimeError("Instale requirements-integrations.txt para usar lembretes naturais.") from exc
        parsed = dateparser.parse(
            value,
            languages=["pt"],
            settings={
                "RETURN_AS_TIMEZONE_AWARE": True,
                "PREFER_DATES_FROM": "future",
                "TIMEZONE": "America/Sao_Paulo",
            },
        )
        if parsed is None:
            raise ValueError(f"Não consegui entender quando devo lembrar você: {value}")
        if parsed.tzinfo is None:
            parsed = parsed.astimezone()
        return parsed

    def _worker(self) -> None:
        while not self._stop.wait(REMINDER_POLL_SECONDS):
            now = datetime.now().astimezone()
            due: list[dict] = []
            with self._lock:
                reminders = self._load()
                changed = False
                for item in reminders:
                    if item.get("done"):
                        continue
                    try:
                        when = datetime.fromisoformat(str(item["when"])).astimezone()
                    except Exception:
                        continue
                    if when <= now:
                        item["done"] = True
                        item["fired_at"] = now.isoformat()
                        due.append(item)
                        changed = True
                if changed:
                    self._save(reminders)
            for item in due:
                self._fire(item)

    def _fire(self, item: dict) -> None:
        message = str(item.get("message", "Lembrete"))
        logger.info("Lembrete disparado: %s", message)
        if self.notify_callback:
            try:
                self.notify_callback(f"{ASSISTANT_NAME} — Lembrete", message)
            except Exception:
                logger.exception("Falha na notificação do lembrete.")


reminder_manager = ReminderManager()
