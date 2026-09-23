from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

from core.config import API_HOST, API_PORT, API_TOKEN, ASSISTANT_NAME


class NexusAPI:
    def __init__(self, command_handler: Callable[[str], str], security, state_provider: Callable[[], dict] | None = None,
                 host: str = API_HOST, port: int = API_PORT, token: str = API_TOKEN) -> None:
        self.command_handler = command_handler
        self.security = security
        self.state_provider = state_provider or (lambda: {
            "assistant": ASSISTANT_NAME,
            "locked": security.locked,
        })
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
        if not self.token:
            return True
        return handler.headers.get("X-NEXUS-TOKEN", "") == self.token


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
        if self.path == "/api/health":
            self._send_json({"ok": True, "assistant": ASSISTANT_NAME})
            return
        if self.path == "/api/status":
            self._send_json(app.state_provider())
            return
        self._send_json({"error": "Rota não encontrada."}, 404)

    def do_POST(self) -> None:
        if not self._guard():
            return
        app = self._app()
        if self.path in {"/api/lock", "/api/unlock"}:
            if self.path.endswith("lock"):
                app.security.lock()
            else:
                app.security.unlock()
            self._send_json(app.state_provider())
            return
        if self.path == "/api/command":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                text = str(payload.get("text", "")).strip()
            except (ValueError, json.JSONDecodeError):
                self._send_json({"error": "JSON inválido."}, 400)
                return
            if not text:
                self._send_json({"error": "Comando vazio."}, 400)
                return
            try:
                response = app.command_handler(text)
                self._send_json({"response": response, "status": app.state_provider()})
            except Exception as exc:
                self._send_json({"error": str(exc)}, 500)
            return
        self._send_json({"error": "Rota não encontrada."}, 404)

    def log_message(self, format: str, *args) -> None:
        return
