from __future__ import annotations

import hmac
import ipaddress
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import psutil
from core.events import event_bus, parse_event_query
from core.http_utils import RequestBodyError, command_text, read_json_object

logger = logging.getLogger("jarvis.panel")


class PanelState:
    def __init__(self, assistant_name: str, security, *, websocket_enabled: bool = False, websocket_port: int = 8767, websocket_public_url: str = "") -> None:
        self.assistant_name = assistant_name
        self.security = security
        self.websocket_enabled = websocket_enabled
        self.websocket_port = websocket_port
        self.websocket_public_url = websocket_public_url
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
        self.events = event_bus
        self._network_counters = psutil.net_io_counters()
        self._network_sample_at = time.monotonic()

    def update(
        self,
        *,
        mode: str | None = None,
        user: str | None = None,
        response: str | None = None,
        provider: str | None = None,
        intent: str | None = None,
    ) -> None:
        changed: dict[str, str] = {}
        with self._lock:
            if mode is not None:
                if mode != self.mode:
                    changed["mode"] = mode
                self.mode = mode
            if user is not None:
                self.last_user = user
            if response is not None:
                self.last_response = response
            if provider is not None:
                if provider != self.last_provider:
                    changed["provider"] = provider
                self.last_provider = provider
            if intent is not None:
                if intent != self.last_intent:
                    changed["intent"] = intent
                self.last_intent = intent
        if changed:
            self.events.publish("assistant.state_changed", changed)

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
            now = time.monotonic()
            counters = psutil.net_io_counters()
            elapsed = max(now - self._network_sample_at, 0.001)
            sent_kbps = recv_kbps = 0.0
            if counters is not None and self._network_counters is not None:
                sent_kbps = max(0, counters.bytes_sent - self._network_counters.bytes_sent) / elapsed / 1024
                recv_kbps = max(0, counters.bytes_recv - self._network_counters.bytes_recv) / elapsed / 1024
            self._network_counters = counters
            self._network_sample_at = now
            try:
                disk_percent = psutil.disk_usage(Path.home().anchor or "/").percent
            except (OSError, ValueError):
                disk_percent = None
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
                "disk": disk_percent,
                "network_sent_kbps": round(sent_kbps, 1),
                "network_recv_kbps": round(recv_kbps, 1),
                "confirmation_pending": bool(self.confirmation_description),
                "confirmation_description": self.confirmation_description,
                "websocket_enabled": self.websocket_enabled,
                "websocket_port": self.websocket_port,
                "websocket_public_url": self.websocket_public_url,
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

    def _send_file(self, path: Path, content_type: str, *, cache_control: str = "no-store", service_worker: bool = False) -> None:
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            self._send_json({"error": "Arquivo não encontrado."}, 404)
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache_control)
        if service_worker:
            self.send_header("Service-Worker-Allowed", "/")
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        panel = self._panel()
        if not panel.token:
            return True
        supplied = self.headers.get("X-NEXUS-TOKEN", "")
        if hmac.compare_digest(supplied.encode("utf-8"), panel.token.encode("utf-8")):
            return True
        self._send_json({"error": "Não autorizado."}, 401)
        return False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        panel = self._panel()

        if parsed.path == "/api/events":
            if not self._authorized():
                return
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

        if parsed.path == "/api/status":
            if not self._authorized():
                return
            self._send_json(panel.state.snapshot())
            return

        if parsed.path in {"/api/history", "/api/skills"}:
            if not self._authorized():
                return
            try:
                if parsed.path == "/api/history":
                    self._send_json({"history": panel.history_provider()})
                else:
                    self._send_json({"skills": panel.skills_provider()})
            except Exception:
                logger.exception("Falha ao carregar dados auxiliares do painel.")
                label = "histórico" if parsed.path == "/api/history" else "skills"
                self._send_json({"error": f"Falha interna ao carregar {label}."}, 500)
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

        if parsed.path == "/manifest.webmanifest":
            self._send_file(
                panel.web_dir / "manifest.webmanifest",
                "application/manifest+json; charset=utf-8",
                cache_control="no-cache",
            )
            return

        if parsed.path == "/sw.js":
            self._send_file(
                panel.web_dir / "sw.js",
                "text/javascript; charset=utf-8",
                cache_control="no-cache",
                service_worker=True,
            )
            return

        if parsed.path == "/icons/nexus.svg":
            self._send_file(panel.web_dir / "icons" / "nexus.svg", "image/svg+xml")
            return

        self._send_json({"error": "Rota não encontrada."}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        panel = self._panel()

        if parsed.path.startswith("/api/") and not self._authorized():
            return

        if parsed.path == "/api/confirm":
            try:
                data = read_json_object(self)
                approved = data.get("approved")
                if not isinstance(approved, bool):
                    raise RequestBodyError("O campo 'approved' precisa ser booleano.")
            except RequestBodyError as exc:
                self._send_json({"error": str(exc)}, exc.status)
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
            event_bus.publish("security.lock_changed", {"locked": panel.security.locked})
            panel.state.update(mode="painel")
            self._send_json(panel.state.snapshot())
            return

        if parsed.path == "/api/command":
            try:
                text = command_text(read_json_object(self))
            except RequestBodyError as exc:
                self._send_json({"error": str(exc)}, exc.status)
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
            except Exception:
                logger.exception("Falha interna ao processar comando pelo painel.")
                message = "Falha interna ao processar o comando."
                panel.state.update(mode="erro", response=message)
                self._send_json({"error": message}, 500)
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
        token: str = "",
        skills_provider: Callable[[], list[dict]] | None = None,
        history_provider: Callable[[], list[dict]] | None = None,
        websocket_enabled: bool = False,
        websocket_port: int = 8767,
        websocket_public_url: str = "",
    ) -> None:
        if not token and not self._is_loopback_host(host):
            raise ValueError("PANEL_TOKEN precisa estar configurado para expor o painel fora do loopback.")
        self.web_dir = web_dir
        self.command_handler = command_handler
        self.security = security
        self.token = token.strip()
        self.skills_provider = skills_provider or (lambda: [])
        self.history_provider = history_provider or (lambda: [])
        self.state = PanelState(
            assistant_name,
            security,
            websocket_enabled=websocket_enabled,
            websocket_port=websocket_port,
            websocket_public_url=websocket_public_url,
        )
        self.server = ThreadingHTTPServer((host, port), _PanelHandler)
        self.server.panel_app = self  # type: ignore[attr-defined]
        self.thread: threading.Thread | None = None
        self.host = host
        self.port = port

    @staticmethod
    def _is_loopback_host(host: str) -> bool:
        if host.lower() == "localhost":
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

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
