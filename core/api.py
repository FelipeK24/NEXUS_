from __future__ import annotations

import hmac
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable
from urllib.parse import urlparse

from core.config import API_HOST, API_PORT, API_TOKEN, ASSISTANT_NAME
from core.events import event_bus, parse_event_query
from core.http_utils import RequestBodyError, command_text, read_json_object

logger = logging.getLogger("jarvis.api")


class NexusAPI:
    def __init__(self, command_handler: Callable[[str], str], security, state_provider: Callable[[], dict] | None = None,
                 host: str = API_HOST, port: int = API_PORT, token: str = API_TOKEN,
                 skills_provider: Callable[[], list[dict]] | None = None,
                 history_provider: Callable[[], list[dict]] | None = None) -> None:
        if not token.strip():
            raise ValueError("API_TOKEN precisa estar configurado para habilitar a API.")
        self.command_handler = command_handler
        self.security = security
        self.state_provider = state_provider or (lambda: {
            "assistant": ASSISTANT_NAME,
            "locked": security.locked,
        })
        self.skills_provider = skills_provider or (lambda: [])
        self.history_provider = history_provider or (lambda: [])
        self.host = host
        self.port = port
        self.token = token
        self.server = ThreadingHTTPServer((host, port), _APIHandler)
        self.server.app = self  # type: ignore[attr-defined]
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        self.thread = threading.Thread(target=self.server.serve_forever, name="nexus-api", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        try:
            self.server.shutdown()
            self.server.server_close()
        except Exception:
            pass

    def authorized(self, handler: BaseHTTPRequestHandler) -> bool:
        supplied = handler.headers.get("X-NEXUS-TOKEN", "")
        return hmac.compare_digest(supplied.encode("utf-8"), self.token.encode("utf-8"))


class _APIHandler(BaseHTTPRequestHandler):
    def _app(self) -> NexusAPI:
        return self.server.app  # type: ignore[attr-defined]

    def _send_json(self, payload: dict, status: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _guard(self) -> bool:
        app = self._app()
        if app.authorized(self):
            return True
        self._send_json({"error": "Não autorizado."}, 401)
        return False

    def do_GET(self) -> None:
        if not self._guard():
            return
        app = self._app()
        parsed = urlparse(self.path)
        if parsed.path == "/api/events":
            try:
                after_id, limit = parse_event_query(parsed.query)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
                return
            events = event_bus.get_events(after_id=after_id, limit=limit)
            self._send_json({
                "events": events,
                "next_id": events[-1]["id"] if events else after_id,
                "latest_id": event_bus.latest_id(),
                "stream_id": event_bus.stream_id,
            })
            return
        if self.path == "/api/health":
            self._send_json({"ok": True, "assistant": ASSISTANT_NAME})
            return
        if self.path == "/api/status":
            self._send_json(app.state_provider())
            return
        if self.path == "/api/skills":
            try:
                self._send_json({"skills": app.skills_provider()})
            except Exception:
                logger.exception("Falha ao consultar skills pela API.")
                self._send_json({"error": "Falha interna ao consultar as skills."}, 500)
            return
        if self.path == "/api/history":
            try:
                self._send_json({"history": app.history_provider()})
            except Exception:
                logger.exception("Falha ao consultar histórico pela API.")
                self._send_json({"error": "Falha interna ao consultar o histórico."}, 500)
            return
        self._send_json({"error": "Rota não encontrada."}, 404)

    def do_POST(self) -> None:
        if not self._guard():
            return
        app = self._app()
        if self.path in {"/api/lock", "/api/unlock"}:
            if self.path == "/api/lock":
                app.security.lock()
            else:
                app.security.unlock()
            event_bus.publish("security.lock_changed", {"locked": app.security.locked})
            self._send_json(app.state_provider())
            return
        if self.path == "/api/command":
            try:
                text = command_text(read_json_object(self))
            except RequestBodyError as exc:
                self._send_json({"error": str(exc)}, exc.status)
                return
            try:
                response = app.command_handler(text)
                self._send_json({"response": response, "status": app.state_provider()})
            except Exception:
                logger.exception("Falha interna ao processar comando pela API.")
                self._send_json({"error": "Falha interna ao processar o comando."}, 500)
            return
        self._send_json({"error": "Rota não encontrada."}, 404)

    def log_message(self, format: str, *args) -> None:
        return
