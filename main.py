from __future__ import annotations

import argparse
import logging
import sys
import threading

from core.config import ASSISTANT_NAME, LOG_FILE, PANEL_ENABLED, PANEL_HOST, PANEL_PORT, TEXT_ONLY, API_ENABLED, API_HOST, API_PORT, API_TOKEN
from core.dispatcher import Dispatcher
from core.errors import SecurityError
from core.interpreter import llm_name, registrar_nexus, registrar_usuario
from core.planner import Planner
from core.security import SecurityManager
from core import listener, speaker
from core.reminders import reminder_manager
from core.config import REMINDER_SPEAK
from core.panel import PanelServer
from pathlib import Path


def setup_logging() -> None:
    handlers = [logging.FileHandler(LOG_FILE, encoding="utf-8")]
    if sys.stdout is not None:
        handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=handlers,
    )


def confirm_action(description: str) -> bool:
    print(f"CONFIRMAR: {description} [s/N]")
    try:
        answer = input("> ").strip().lower()
    except (EOFError, OSError):
        return False
    return answer in {"s", "sim", "y", "yes", "confirmar"}


def voice_confirm_action(description: str) -> bool:
    speaker.falar(description + " Diga confirmar para continuar ou cancelar para interromper.")
    answer = listener.transcribe_command().lower().strip()
    return "confirmar" in answer or answer in {"sim", "sim, pode", "pode"}


def notify_reminder(title: str, message: str) -> None:
    try:
        from winotify import Notification, audio

        icon = str(Path(__file__).resolve().parent / "assets" / "nexus.ico")
        toast = Notification(app_id=ASSISTANT_NAME, title=title, msg=message, icon=icon)
        try:
            toast.set_audio(audio.Default, loop=False)
        except Exception:
            pass
        toast.build().show()
    except Exception:
        logging.getLogger("jarvis.main").exception("Falha ao mostrar notificação do Windows.")

    if panel := _RUNTIME.get("panel"):
        try:
            panel.state.update(mode="lembrete", response=message)
        except Exception:
            pass

    if REMINDER_SPEAK:
        try:
            speaker.falar(message)
        except Exception:
            logging.getLogger("jarvis.main").exception("Falha ao falar lembrete.")


def run_text_mode(dispatcher: Dispatcher, planner: Planner, panel: PanelServer | None = None) -> None:
    print(f"{ASSISTANT_NAME} em modo texto. Digite 'sair' para encerrar.")
    while True:
        try:
            text = input("Você > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not text:
            continue
        if text.lower() in {"sair", "exit", "quit"}:
            return
        if text.lower() == "unlock":
            dispatcher.security.unlock()
            print("NEXUS desbloqueado.")
            continue
        if text.lower() == "lock":
            dispatcher.security.lock()
            print("NEXUS bloqueado.")
            continue

        execute_text(
            text,
            dispatcher,
            planner,
            speak=False,
            panel=panel,
            confirmation_callback=confirm_action,
        )


execution_lock = threading.RLock()


def execute_text(
    text: str,
    dispatcher: Dispatcher,
    planner: Planner,
    speak: bool = True,
    show_output: bool = True,
    panel: PanelServer | None = None,
    confirmation_callback=None,
) -> str:
    from core.pipeline import CommandPipeline

    pipeline = CommandPipeline(dispatcher, planner, panel)
    result = pipeline.execute(
        text,
        speak=speak,
        show_output=show_output,
        confirmation_callback=confirmation_callback,
        stop_on_failure=True,
    )
    return result.response


def run_voice_mode(dispatcher: Dispatcher, planner: Planner, panel: PanelServer | None = None, stop_event: threading.Event | None = None) -> None:
    while True:
        if stop_event is not None and stop_event.is_set():
            return
        try:
            if panel:
                panel.state.update(mode="aguardando wake word")
            listener.listen_for_wake_word(stop_event=stop_event)
            if panel:
                panel.state.update(mode="ouvindo")
            command = listener.transcribe_command()
            if not command:
                continue
            if command.lower().strip() in {"sair", "encerrar", "desligar nexus"}:
                speaker.falar("Encerrando.")
                return
            execute_text(
                command,
                dispatcher,
                planner,
                speak=True,
                panel=panel,
                confirmation_callback=voice_confirm_action,
            )
        except KeyboardInterrupt:
            speaker.falar("Encerrando.")
            return
        except Exception as exc:
            logging.getLogger("jarvis.main").exception("Erro no modo de voz: %s", exc)
            message = "Ocorreu um erro. Verifique o log do sistema."
            logging.getLogger("jarvis.main").error("%s > %s", ASSISTANT_NAME, message)
            speaker.falar(message)


_RUNTIME: dict[str, object] = {}


def _build_runtime():
    security = SecurityManager()
    api = None
    security.set_confirmation_callback(confirm_action)
    dispatcher = Dispatcher(security)
    planner = Planner()
    panel = None

    web_dir = Path(__file__).resolve().parent / "panel"
    if PANEL_ENABLED:
        holder: dict[str, PanelServer | None] = {"panel": None}

        def panel_command(text: str) -> str:
            active_panel = holder["panel"]
            return execute_text(
                text,
                dispatcher,
                planner,
                speak=False,
                show_output=False,
                panel=active_panel,
                confirmation_callback=(active_panel.request_confirmation if active_panel else None),
            )

        panel = PanelServer(
            assistant_name=ASSISTANT_NAME,
            security=security,
            command_handler=panel_command,
            web_dir=web_dir,
            host=PANEL_HOST,
            port=PANEL_PORT,
        )
        holder["panel"] = panel
        panel.start()

    _RUNTIME["panel"] = panel
    reminder_manager.notify_callback = notify_reminder
    reminder_manager.start()

    if API_ENABLED:
        from core.api import NexusAPI
        api = NexusAPI(
            command_handler=lambda text: execute_text(
                text, dispatcher, planner, speak=False, show_output=False, panel=panel, confirmation_callback=(panel.request_confirmation if panel else None)
            ),
            security=security,
            state_provider=(panel.state.snapshot if panel else lambda: {"assistant": ASSISTANT_NAME, "locked": security.locked}),
            host=API_HOST,
            port=API_PORT,
            token=API_TOKEN,
        )
        api.start()

    return security, dispatcher, planner, panel, api


def run_tray_mode() -> None:
    from core.tray import NexusTray

    stop_event = threading.Event()
    security, dispatcher, planner, panel, api = _build_runtime()

    def worker() -> None:
        run_voice_mode(
            dispatcher,
            planner,
            panel,
            stop_event=stop_event,
        )

    def shutdown() -> None:
        stop_event.set()
        reminder_manager.stop()
        if panel is not None:
            panel.stop()
        if api is not None:
            api.stop()

    tray = NexusTray(
        assistant_name=ASSISTANT_NAME,
        panel_host=PANEL_HOST,
        panel_port=PANEL_PORT,
        security=security,
        stop_event=stop_event,
        worker=worker,
        on_shutdown=shutdown,
    )
    tray.run()


def main() -> None:
    parser = argparse.ArgumentParser(description="NEXUS/JARVIS")
    parser.add_argument("--text", action="store_true", help="Executa em modo texto.")
    parser.add_argument("--tray", action="store_true", help="Executa em segundo plano na bandeja do Windows.")
    args = parser.parse_args()

    setup_logging()

    if args.tray:
        run_tray_mode()
        return

    security, dispatcher, planner, panel, api = _build_runtime()

    print(f"{ASSISTANT_NAME} iniciado.")
    print(f"IA atual: {llm_name()}")
    print("Modo de segurança: LOCK")

    if args.text or TEXT_ONLY:
        run_text_mode(dispatcher, planner, panel)
    else:
        run_voice_mode(dispatcher, planner, panel)


if __name__ == "__main__":
    main()
