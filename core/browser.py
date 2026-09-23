from __future__ import annotations

import logging
import queue
import threading
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from playwright.sync_api import BrowserContext, Page, sync_playwright

from core.config import (
    BROWSER_CHANNEL,
    BROWSER_HEADLESS,
    BROWSER_NAV_TIMEOUT,
    BROWSER_PROFILE_DIR,
    BROWSER_READ_LIMIT,
)

logger = logging.getLogger("jarvis.browser")


class BrowserError(RuntimeError):
    pass


class BrowserManager:
    """Mantém um navegador Playwright em uma thread dedicada para evitar problemas de thread affinity."""

    def __init__(self) -> None:
        self._queue: queue.Queue[tuple[Callable[[], Any] | None, threading.Event, dict[str, Any]]] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._started = threading.Event()
        self._stopped = threading.Event()
        self._lock = threading.Lock()

    def _ensure_worker(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stopped.clear()
            self._started.clear()
            self._thread = threading.Thread(target=self._worker, name="nexus-browser", daemon=True)
            self._thread.start()
        self._started.wait(timeout=10)
        if not self._started.is_set() or not self._thread or not self._thread.is_alive():
            raise BrowserError("Não consegui iniciar o navegador do NEXUS. Verifique se o Chromium do Playwright está instalado.")

    def _call(self, fn: Callable[[], Any], timeout: float | None = None) -> Any:
        self._ensure_worker()
        event = threading.Event()
        holder: dict[str, Any] = {}
        self._queue.put((fn, event, holder))
        if not event.wait(timeout or max(10.0, BROWSER_NAV_TIMEOUT / 1000 + 5)):
            raise BrowserError("A operação do navegador demorou demais.")
        if "error" in holder:
            raise BrowserError(str(holder["error"]))
        return holder.get("result")

    @staticmethod
    def _validate_url(url: str) -> str:
        url = url.strip()
        if not url:
            raise BrowserError("URL vazia.")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise BrowserError("Só aceito URLs HTTP ou HTTPS.")
        return url

    def _worker(self) -> None:
        playwright = None
        context: BrowserContext | None = None
        try:
            playwright = sync_playwright().start()
            profile = Path(BROWSER_PROFILE_DIR)
            profile.mkdir(parents=True, exist_ok=True)
            launch_kwargs: dict[str, Any] = {
                "headless": BROWSER_HEADLESS,
                "user_data_dir": str(profile),
            }
            if BROWSER_CHANNEL:
                launch_kwargs["channel"] = BROWSER_CHANNEL

            context = playwright.chromium.launch_persistent_context(**launch_kwargs)
            threading.current_thread()._nexus_context = context
            context.set_default_timeout(BROWSER_NAV_TIMEOUT)
            if not context.pages:
                context.new_page()
            self._started.set()

            while True:
                fn, event, holder = self._queue.get()
                if fn is None:
                    event.set()
                    break
                try:
                    holder["result"] = fn()
                except Exception as exc:
                    logger.exception("Erro no navegador: %s", exc)
                    holder["error"] = exc
                finally:
                    event.set()
        except Exception as exc:
            logger.exception("Não consegui iniciar o navegador: %s", exc)
            self._started.set()
        finally:
            try:
                if context is not None:
                    context.close()
            except Exception:
                logger.exception("Erro fechando contexto do navegador.")
            try:
                delattr(threading.current_thread(), "_nexus_context")
            except AttributeError:
                pass
            try:
                if playwright is not None:
                    playwright.stop()
            except Exception:
                logger.exception("Erro encerrando Playwright.")
            self._stopped.set()

    def _page(self) -> Page:
        raise RuntimeError("O acesso à página deve ocorrer na thread do navegador.")

    def open(self, url: str) -> str:
        target = self._validate_url(url)

        def operation() -> str:
            nonlocal target
            page = self._get_current_page()
            page.goto(target, wait_until="domcontentloaded", timeout=BROWSER_NAV_TIMEOUT)
            title = page.title().strip()
            return f"Página aberta: {title or target}"

        return self._call(operation)

    def read(self) -> str:
        def operation() -> str:
            page = self._get_current_page()
            title = page.title().strip()
            url = page.url
            try:
                text = page.locator("body").inner_text(timeout=BROWSER_NAV_TIMEOUT)
            except Exception:
                text = page.content()
            text = " ".join(text.split())
            if len(text) > BROWSER_READ_LIMIT:
                text = text[:BROWSER_READ_LIMIT].rstrip() + "..."
            return f"Título: {title or '(sem título)'}\nURL: {url}\n\n{text}"

        return self._call(operation)

    def back(self) -> str:
        return self._call(lambda: self._navigate("back"))

    def forward(self) -> str:
        return self._call(lambda: self._navigate("forward"))

    def refresh(self) -> str:
        def operation() -> str:
            page = self._get_current_page()
            page.reload(wait_until="domcontentloaded", timeout=BROWSER_NAV_TIMEOUT)
            return f"Página atualizada: {page.title().strip() or page.url}"

        return self._call(operation)

    def tabs(self) -> str:
        def operation() -> str:
            pages = self._context_pages()
            if not pages:
                return "Nenhuma aba aberta."
            lines = ["Abas abertas:"]
            for index, page in enumerate(pages, start=1):
                lines.append(f"{index}. {page.title().strip() or '(sem título)'} — {page.url}")
            return "\n".join(lines)

        return self._call(operation)

    def screenshot(self, path: str) -> str:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)

        def operation() -> str:
            page = self._get_current_page()
            page.screenshot(path=str(target), full_page=True)
            return f"Screenshot salvo em: {target}"

        return self._call(operation)

    def click(self, selector: str) -> str:
        selector = selector.strip()
        if not selector:
            raise BrowserError("Informe o seletor do elemento que deve ser clicado.")

        def operation() -> str:
            page = self._get_current_page()
            page.locator(selector).click()
            return f"Cliquei no elemento: {selector}"

        return self._call(operation)

    def type_text(self, selector: str, text: str) -> str:
        selector = selector.strip()
        if not selector or not text:
            raise BrowserError("Informe o seletor e o texto.")

        def operation() -> str:
            page = self._get_current_page()
            page.locator(selector).fill(text)
            return f"Preenchi o campo: {selector}"

        return self._call(operation)

    def submit(self, selector: str) -> str:
        selector = selector.strip()
        if not selector:
            raise BrowserError("Informe o seletor do botão de envio.")

        def operation() -> str:
            page = self._get_current_page()
            page.locator(selector).click()
            return f"Enviei a ação do elemento: {selector}"

        return self._call(operation)

    def close(self) -> str:
        if not self._thread or not self._thread.is_alive():
            return "O navegador já está fechado."
        event = threading.Event()
        holder: dict[str, Any] = {}
        self._queue.put((None, event, holder))
        event.wait(timeout=5)
        return "Navegador encerrado."

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive() and not self._stopped.is_set())

    def _get_current_page(self) -> Page:
        # Este método é chamado somente dentro da thread dedicada.
        thread = threading.current_thread()
        if thread is not self._thread:
            raise BrowserError("Operação de navegador executada fora da thread correta.")
        # Import local para evitar guardar objetos de Playwright fora da thread.
        context = getattr(thread, "_nexus_context", None)
        if context is None:
            raise BrowserError("Contexto do navegador não disponível.")
        pages = context.pages
        if not pages:
            return context.new_page()
        return pages[-1]

    def _context_pages(self) -> list[Page]:
        thread = threading.current_thread()
        context = getattr(thread, "_nexus_context", None)
        if context is None:
            raise BrowserError("Contexto do navegador não disponível.")
        return list(context.pages)

    def _navigate(self, direction: str) -> str:
        page = self._get_current_page()
        if direction == "back":
            page.go_back(wait_until="domcontentloaded", timeout=BROWSER_NAV_TIMEOUT)
            return f"Voltei para: {page.title().strip() or page.url}"
        page.go_forward(wait_until="domcontentloaded", timeout=BROWSER_NAV_TIMEOUT)
        return f"Avancei para: {page.title().strip() or page.url}"


browser = BrowserManager()
