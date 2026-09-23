from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import psutil


class PanelState:
    def __init__(self, assistant_name: str, security) -> None:
        self.assistant_name = assistant_name
        self.security = security
        self._lock = threading.Lock()
        self.confirmation_event = threading.Event()
        self.confirmation_result = False
        self.confirmation_description = ""
        self.mode = "inicializando"
        self.last_user = ""
        self.last_response = ""
        self.last_provider = "none"
        self.last_intent = ""
        self.started = True

    def update(
        self,
        *,
        mode: str | None = None,
        user: str | None = None,
        response: str | None = None,
        provider: str | None = None,
        intent: str | None = None,
    ) -> None:
        with self._lock:
            if mode is not None:
                self.mode = mode
            if user is not None:
                self.last_user = user
            if response is not None:
                self.last_response = response
            if provider is not None:
                self.last_provider = provider
            if intent is not None:
                self.last_intent = intent

    def request_confirmation(self, description: str, timeout: float = 60.0) -> bool:
        with self._lock:
            self.confirmation_description = description
            self.confirmation_result = False
            self.confirmation_event.clear()
            self.mode = "aguardando confirmação"

        approved = self.confirmation_event.wait(timeout)

        with self._lock:
            result = self.confirmation_result if approved else False
            self.confirmation_description = ""
            self.mode = "online" if result else "ação cancelada"

        return result

    def resolve_confirmation(self, approved: bool) -> None:
        with self._lock:
            self.confirmation_result = approved
        self.confirmation_event.set()

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "assistant": self.assistant_name,
                "locked": self.security.locked,
                "mode": self.mode,
                "last_user": self.last_user,
                "last_response": self.last_response,
                "last_provider": self.last_provider,
                "last_intent": self.last_intent,
                "cpu": psutil.cpu_percent(interval=None),
                "ram": psutil.virtual_memory().percent,
                "confirmation_pending": bool(self.confirmation_description),
                "confirmation_description": self.confirmation_description,
            }


class _PanelHandler(BaseHTTPRequestHandler):
    server_version = "NEXUSPanel/1.0"

    def _panel(self):
        return self.server.panel_app  # type: ignore[attr-defined]

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            self._send_json({"error": "Arquivo não encontrado."}, 404)
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        panel = self._panel()

        if parsed.path == "/api/status":
            self._send_json(panel.state.snapshot())
            return

        if parsed.path in {"/", "/index.html"}:
            self._send_file(panel.web_dir / "index.html", "text/html; charset=utf-8")
            return

        if parsed.path == "/style.css":
            self._send_file(panel.web_dir / "style.css", "text/css; charset=utf-8")
            return

        if parsed.path == "/app.js":
            self._send_file(panel.web_dir / "app.js", "text/javascript; charset=utf-8")
            return

        self._send_json({"error": "Rota não encontrada."}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        panel = self._panel()

        if parsed.path == "/api/confirm":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                data = json.loads(raw.decode("utf-8"))
                approved = bool(data.get("approved", False))
            except (ValueError, json.JSONDecodeError):
                self._send_json({"error": "JSON inválido."}, 400)
                return
            panel.resolve_confirmation(approved)
            self._send_json(panel.state.snapshot())
            return

        if parsed.path in {"/api/lock", "/api/unlock", "/api/toggle"}:
            if parsed.path == "/api/lock":
                panel.security.lock()
            elif parsed.path == "/api/unlock":
                panel.security.unlock()
            else:
                panel.security.toggle()
            panel.state.update(mode="painel")
            self._send_json(panel.state.snapshot())
            return

        if parsed.path == "/api/command":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                data = json.loads(raw.decode("utf-8"))
                text = str(data.get("text", "")).strip()
            except (ValueError, json.JSONDecodeError):
                self._send_json({"error": "JSON inválido."}, 400)
                return

            if not text:
                self._send_json({"error": "Comando vazio."}, 400)
                return

            try:
                panel.state.update(mode="processando", user=text)
                response = panel.command_handler(text)
                self._send_json(
                    {
                        "response": response,
                        "status": panel.state.snapshot(),
                    }
                )
            except Exception as exc:
                panel.state.update(mode="erro", response=str(exc))
                self._send_json({"error": str(exc)}, 500)
            return

        self._send_json({"error": "Rota não encontrada."}, 404)

    def log_message(self, format: str, *args) -> None:
        return


class PanelServer:
    def __init__(
        self,
        *,
        assistant_name: str,
        security,
        command_handler: Callable[[str], str],
        web_dir: Path,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self.web_dir = web_dir
        self.command_handler = command_handler
        self.security = security
        self.state = PanelState(assistant_name, security)
        self.server = ThreadingHTTPServer((host, port), _PanelHandler)
        self.server.panel_app = self  # type: ignore[attr-defined]
        self.thread: threading.Thread | None = None
        self.host = host
        self.port = port

    def start(self) -> None:
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            name="nexus-panel",
            daemon=True,
        )
        self.thread.start()

    def request_confirmation(self, description: str, timeout: float = 60.0) -> bool:
        return self.state.request_confirmation(description, timeout)

    def resolve_confirmation(self, approved: bool) -> None:
        self.state.resolve_confirmation(approved)

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()
