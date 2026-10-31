from __future__ import annotations

import asyncio
import hmac
import ipaddress
import json
import logging
import threading
from dataclasses import asdict
from urllib.parse import urlsplit

from core.events import NexusEvent, event_bus

logger = logging.getLogger("jarvis.websocket")


class EventWebSocketServer:
    """Authenticated, send-only WebSocket stream for NEXUS events."""

    def __init__(self, *, host: str, port: int, token: str) -> None:
        self.host = host.strip()
        self.port = port
        self.token = token.strip()
        if not self.token and not self._is_loopback_host(self.host):
            raise ValueError("PANEL_TOKEN precisa estar configurado para expor o WebSocket fora do loopback.")
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server = None
        self._ready = threading.Event()
        self._stopped = threading.Event()
        self._startup_error: BaseException | None = None

    @staticmethod
    def _is_loopback_host(host: str) -> bool:
        if host.lower() == "localhost":
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._thread_main, name="nexus-websocket", daemon=True)
        self._thread.start()
        if not self._ready.wait(8):
            self.stop()
            raise RuntimeError("Tempo esgotado ao iniciar o WebSocket do NEXUS.")
        if self._startup_error:
            raise RuntimeError("Falha ao iniciar o WebSocket do NEXUS.") from self._startup_error

    def _thread_main(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except BaseException as exc:
            self._startup_error = exc
            self._ready.set()
            if not self._stopped.is_set():
                logger.exception("Servidor WebSocket do NEXUS encerrado com erro.")
        finally:
            pending = asyncio.all_tasks(self._loop)
            for task in pending:
                task.cancel()
            if pending:
                self._loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self._loop.close()

    async def _serve(self) -> None:
        from websockets.asyncio.server import serve

        self._server = await serve(
            self._handle_connection,
            self.host,
            self.port,
            max_size=4096,
            max_queue=16,
            ping_interval=20,
            ping_timeout=20,
            server_header="NEXUS",
        )
        self._ready.set()
        await self._server.wait_closed()

    async def _handle_connection(self, connection) -> None:
        if not self._origin_allowed(connection):
            await connection.close(code=1008, reason="Origem nao permitida")
            return

        try:
            raw_auth = await asyncio.wait_for(connection.recv(), timeout=5)
            auth = json.loads(raw_auth)
        except Exception:
            await connection.close(code=1008, reason="Autenticacao obrigatoria")
            return
        if not isinstance(auth, dict) or auth.get("type") != "auth" or not self._token_valid(auth.get("token")):
            await connection.close(code=1008, reason="Nao autorizado")
            return

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[NexusEvent | None] = asyncio.Queue(maxsize=128)

        def enqueue(event: NexusEvent) -> None:
            def add() -> None:
                if queue.full():
                    asyncio.create_task(connection.close(code=1013, reason="Consumidor atrasado"))
                    return
                queue.put_nowait(event)
            try:
                loop.call_soon_threadsafe(add)
            except RuntimeError:
                pass

        unsubscribe = event_bus.subscribe(enqueue)
        try:
            await connection.send(json.dumps({
                "kind": "ready",
                "stream_id": event_bus.stream_id,
                "latest_id": event_bus.latest_id(),
            }))
            sender = asyncio.create_task(self._send_events(connection, queue))
            receiver = asyncio.create_task(connection.recv())
            done, pending = await asyncio.wait({sender, receiver}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                exception = task.exception()
                if exception:
                    raise exception
            if receiver in done:
                await connection.close(code=1008, reason="Conexao somente para eventos")
        except Exception:
            logger.debug("Cliente WebSocket desconectado.", exc_info=True)
        finally:
            unsubscribe()

    async def _send_events(self, connection, queue: asyncio.Queue[NexusEvent | None]) -> None:
        while True:
            event = await queue.get()
            if event is None:
                return
            await connection.send(json.dumps({"kind": "event", "event": asdict(event)}, ensure_ascii=False))

    def _token_valid(self, supplied: object) -> bool:
        if not self.token:
            return isinstance(supplied, str) and supplied == ""
        return isinstance(supplied, str) and hmac.compare_digest(supplied.encode(), self.token.encode())

    def _origin_allowed(self, connection) -> bool:
        origin = connection.request.headers.get("Origin")
        if not origin:
            remote = connection.remote_address
            return bool(self.token) or (isinstance(remote, tuple) and self._is_loopback_host(str(remote[0])))
        try:
            origin_host = (urlsplit(origin).hostname or "").lower()
            request_host = (urlsplit("//" + connection.request.headers.get("Host", "")).hostname or "").lower()
            return bool(origin_host and request_host and origin_host == request_host)
        except ValueError:
            return False

    def stop(self) -> None:
        self._stopped.set()
        loop = self._loop
        server = self._server
        if loop and loop.is_running() and server:
            loop.call_soon_threadsafe(server.close)
        if self._thread and self._thread.is_alive() and threading.current_thread() is not self._thread:
            self._thread.join(timeout=5)
