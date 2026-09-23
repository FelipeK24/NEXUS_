from __future__ import annotations

import threading
import webbrowser
from pathlib import Path
from typing import Callable

import pystray
from PIL import Image
from pystray import MenuItem


class NexusTray:
    def __init__(
        self,
        *,
        assistant_name: str,
        panel_host: str,
        panel_port: int,
        security,
        stop_event: threading.Event,
        worker: Callable[[], None],
        on_shutdown: Callable[[], None] | None = None,
    ) -> None:
        self.assistant_name = assistant_name
        self.panel_url = f"http://{panel_host}:{panel_port}"
        self.security = security
        self.stop_event = stop_event
        self.worker = worker
        self.on_shutdown = on_shutdown
        self._worker_thread: threading.Thread | None = None
        self._icon: pystray.Icon | None = None
        self._icon_lock = threading.Lock()

    @property
    def icon(self) -> pystray.Icon | None:
        with self._icon_lock:
            return self._icon

    def _set_icon(self, icon: pystray.Icon) -> None:
        with self._icon_lock:
            self._icon = icon

    def _build_image(self) -> Image.Image:
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "nexus.ico"
        if icon_path.exists():
            return Image.open(icon_path)
        return self._fallback_image()

    @staticmethod
    def _fallback_image() -> Image.Image:
        image = Image.new("RGBA", (64, 64), (10, 14, 24, 255))
        pixels = image.load()
        for x in range(8, 56):
            for y in range(8, 56):
                if abs(x - y) < 5 or abs((63 - x) - y) < 5:
                    pixels[x, y] = (80, 180, 255, 255)
        return image

    def _open_panel(self, icon=None, item=None) -> None:
        webbrowser.open(self.panel_url)

    def _toggle_lock(self, icon=None, item=None) -> None:
        locked = self.security.toggle()
        self._update_title()

    def _update_title(self) -> None:
        icon = self.icon
        if icon is None:
            return
        status = "LOCK" if self.security.locked else "UNLOCK"
        icon.title = f"{self.assistant_name} — {status}"

    def _shutdown(self, icon=None, item=None) -> None:
        self.stop_event.set()
        if self.on_shutdown is not None:
            try:
                self.on_shutdown()
            except Exception:
                pass
        try:
            if icon is not None:
                icon.stop()
        except Exception:
            pass

    def run(self) -> None:
        self._worker_thread = threading.Thread(
            target=self.worker,
            name="nexus-core",
            daemon=True,
        )
        self._worker_thread.start()

        menu = pystray.Menu(
            MenuItem("Abrir painel", self._open_panel, default=True),
            MenuItem("Alternar LOCK / UNLOCK", self._toggle_lock),
            MenuItem("Encerrar NEXUS", self._shutdown),
        )

        icon = pystray.Icon(
            "NEXUS",
            self._build_image(),
            f"{self.assistant_name} — LOCK",
            menu,
        )
        self._set_icon(icon)
        icon.run()
        self.stop_event.set()
