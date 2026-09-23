from __future__ import annotations

import logging
from typing import Callable

from core.command import Command
from core.errors import SecurityError

logger = logging.getLogger("jarvis.security")


class SecurityManager:
    def __init__(self, confirmation_callback: Callable[[str], bool] | None = None) -> None:
        self.locked = True
        self.confirmation_callback = confirmation_callback

    def set_confirmation_callback(self, callback: Callable[[str], bool]) -> None:
        self.confirmation_callback = callback

    def lock(self) -> None:
        self.locked = True
        logger.info("Modo LOCK ativado.")

    def unlock(self) -> None:
        self.locked = False
        logger.info("Modo UNLOCK ativado.")

    def toggle(self) -> bool:
        self.locked = not self.locked
        logger.info("Modo LOCK=%s", self.locked)
        return self.locked

    def risk_level(self, command: Command) -> str:
        if command.intent in {
            "file_delete",
            "email_send",
            "email_reply",
            "smart_home_action",
            "clear_memory",
            "calendar_delete",
            "web_action",
            "google_task_delete",
        }:
            return "high"
        if command.intent in {
            "file_move",
            "process_close",
            "close_application",
            "calendar_create",
            "task_delete",
            "reminder_cancel",
            "google_task_complete",
            "browser_click",
            "browser_type",
        }:
            return "medium"
        return "low"

    def authorize(
        self,
        command: Command,
        confirmation_callback: Callable[[str], bool] | None = None,
    ) -> None:
        risk = self.risk_level(command)
        callback = confirmation_callback or self.confirmation_callback

        if risk == "low":
            return

        if self.locked:
            raise SecurityError(
                f"Ação bloqueada pelo modo LOCK: {command.intent}."
            )

        if risk == "medium":
            if not callback:
                raise SecurityError("Ação de risco médio exige confirmação.")
            description = self.describe(command)
            if not callback(description):
                raise SecurityError("Ação cancelada pelo usuário.")
            return

        if not callback:
            raise SecurityError("Ação de alto risco exige confirmação.")
        description = self.describe(command)
        if not callback(f"CONFIRMAÇÃO DE ALTO RISCO: {description}"):
            raise SecurityError("Ação de alto risco cancelada.")

    @staticmethod
    def describe(command: Command) -> str:
        p = command.parameters
        if command.intent == "close_application":
            return f"Fechar o aplicativo {p.get('application', 'informado')}?"
        if command.intent == "process_close":
            return f"Encerrar o processo {p.get('process_name', 'informado')}?"
        if command.intent == "file_move":
            return f"Mover '{p.get('source', 'origem')}' para '{p.get('destination', 'destino')}'?"
        if command.intent == "file_delete":
            return f"Excluir o arquivo {p.get('path', 'informado')}?"
        if command.intent == "email_send":
            return (
                f"Enviar um e-mail para {p.get('to', 'o destinatário')} "
                f"com assunto '{p.get('subject', 'sem assunto')}'?"
            )
        if command.intent == "email_reply":
            return "Enviar a resposta para o e-mail selecionado?"
        if command.intent == "smart_home_action":
            return "Executar a ação de automação residencial?"
        if command.intent == "calendar_create":
            return f"Criar o evento '{p.get('summary', 'informado')}' na agenda?"
        if command.intent == "calendar_delete":
            return "Excluir o evento da agenda?"
        if command.intent == "task_delete":
            return f"Excluir a tarefa '{p.get('identifier', 'informada')}'?"
        if command.intent == "google_task_delete":
            return f"Excluir a tarefa do Google '{p.get('identifier', 'informada')}'?"
        if command.intent == "reminder_cancel":
            return f"Cancelar o lembrete '{p.get('identifier', 'informado')}'?"
        if command.intent == "google_task_complete":
            return f"Concluir a tarefa do Google '{p.get('identifier', 'informada')}'?"
        if command.intent == "web_action":
            return f"Executar a ação web '{p.get('action', 'informada')}' no elemento {p.get('selector', 'informado')}?"
        if command.intent == "browser_click":
            return f"Clicar no elemento {p.get('selector', 'informado')}?"
        if command.intent == "browser_type":
            return f"Preencher o elemento {p.get('selector', 'informado')} com texto?"
        return f"Executar a ação {command.intent}?"
