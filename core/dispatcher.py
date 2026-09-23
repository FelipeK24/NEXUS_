from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from core.command import Command
from core.security import SecurityManager
from core.skill import Skill
from core.skill_registry import SkillRegistry
from core.errors import SecurityError
from skills import applications, calculator, files, memory as memory_skill, processes, spotify, system, system_control, time, web, email, calendar, tasks, vision, smart_home, gmail, google_tasks
from core.reminders import reminder_manager

logger = logging.getLogger("jarvis.dispatcher")


@dataclass(frozen=True)
class DispatchResult:
    success: bool
    response: str
    intent: str


class Dispatcher:
    def __init__(self, security: SecurityManager) -> None:
        self.registry = SkillRegistry()
        self.security = security
        self._register_skills()

    def _register_skills(self) -> None:
        skills = (
            Skill("time", time.dizer_hora, "Diz o horário atual."),
            Skill("calculator", calculator.calcular, "Calcula expressões matemáticas."),
            Skill("open_application", applications.abrir_aplicacao, "Abre aplicativos autorizados."),
            Skill("open_spotify_playlist", spotify.abrir_playlist, "Abre uma playlist do Spotify."),
            Skill("close_application", applications.fechar_aplicacao, "Fecha aplicativos autorizados."),
            Skill("system_info", system.informacoes_sistema, "Mostra informações do sistema."),
            Skill("system_control", system_control.controlar_sistema, "Controla funções básicas do sistema."),
            Skill("clear_context", memory_skill.limpar_contexto, "Limpa o contexto da conversa."),
            Skill("remember", memory_skill.lembrar, "Salva uma memória."),
            Skill("forget", memory_skill.esquecer, "Remove uma memória."),
            Skill("recall_memory", memory_skill.consultar_memoria, "Consulta a memória."),
            Skill("clear_memory", memory_skill.apagar_toda_memoria, "Apaga a memória persistente."),
            Skill("file_list", files.listar_arquivos, "Lista arquivos de uma pasta autorizada."),
            Skill("file_find", files.encontrar_arquivo, "Procura arquivos em pastas autorizadas."),
            Skill("file_open", files.abrir_arquivo, "Abre um arquivo autorizado."),
            Skill("file_create_folder", files.criar_pasta, "Cria uma pasta autorizada."),
            Skill("file_move", files.mover_arquivo, "Move um arquivo entre pastas autorizadas."),
            Skill("file_delete", files.excluir_arquivo, "Exclui um arquivo autorizado."),
            Skill("process_list", processes.listar_processos, "Lista processos em execução."),
            Skill("process_close", processes.fechar_processo, "Encerra processos explicitamente autorizados."),
            Skill("web_search", web.pesquisar, "Pesquisa informações na internet."),
            Skill("web_open", web.abrir, "Abre uma URL ou site no navegador do NEXUS."),
            Skill("browser_read", web.ler_pagina, "Lê o conteúdo da página atual."),
            Skill("browser_back", web.voltar, "Volta uma página no navegador."),
            Skill("browser_forward", web.avancar, "Avança uma página no navegador."),
            Skill("browser_refresh", web.atualizar, "Atualiza a página atual."),
            Skill("browser_tabs", web.listar_abas, "Lista as abas abertas."),
            Skill("browser_close", web.fechar_navegador, "Fecha o navegador controlado pelo NEXUS."),
            Skill("browser_screenshot", web.screenshot, "Salva um screenshot da página atual."),
            Skill("browser_click", web.clicar, "Clica em um elemento do navegador."),
            Skill("browser_type", web.preencher, "Preenche um campo do navegador."),
            Skill("web_action", web.enviar, "Executa uma ação web sensível."),
            Skill("email_list", gmail.listar_emails, "Lista e-mails da caixa de entrada."),
            Skill("email_search", gmail.pesquisar_emails, "Pesquisa e-mails no Gmail."),
            Skill("email_read", gmail.ler_email, "Lê um e-mail específico."),
            Skill("email_send", email.enviar_email, "Envia um e-mail via Google Workspace."),
            Skill("email_reply", gmail.responder_email, "Responde a um e-mail existente."),
            Skill("calendar_list", calendar.listar_agenda, "Consulta a agenda do Google Calendar."),
            Skill("calendar_create", calendar.criar_evento, "Cria um evento no Google Calendar."),
            Skill("task_add", tasks.adicionar_tarefa, "Cria uma tarefa local."),
            Skill("task_list", tasks.listar_tarefas, "Lista tarefas locais pendentes."),
            Skill("task_complete", tasks.concluir_tarefa, "Conclui uma tarefa local."),
            Skill("task_delete", tasks.excluir_tarefa, "Exclui uma tarefa local."),
            Skill("google_task_add", google_tasks.adicionar_google_task, "Cria uma tarefa no Google Tasks."),
            Skill("google_task_list", google_tasks.listar_google_tasks, "Lista tarefas do Google Tasks."),
            Skill("google_task_complete", google_tasks.concluir_google_task, "Conclui uma tarefa do Google Tasks."),
            Skill("google_task_delete", google_tasks.excluir_google_task, "Exclui uma tarefa do Google Tasks."),
            Skill("reminder_add", reminder_manager.add, "Cria um lembrete local."),
            Skill("reminder_list", reminder_manager.list_pending, "Lista lembretes pendentes."),
            Skill("reminder_cancel", reminder_manager.cancel, "Cancela um lembrete."),
            Skill("vision_screen", vision.analisar_tela, "Analisa a tela do computador com visão da IA."),
            Skill("vision_image", vision.analisar_imagem, "Analisa uma imagem autorizada."),
            Skill("smart_home_action", smart_home.executar, "Executa uma ação de Smart Home quando habilitada."),
        )
        for skill in skills:
            self.registry.register(skill)

    def register_skill(self, skill: Skill) -> None:
        self.registry.register(skill)

    def dispatch_result(self, command: Command, confirmation_callback=None) -> DispatchResult:
        if command.intent == "general_question":
            from core.interpreter import responder_pergunta
            return DispatchResult(True, responder_pergunta(command.original_text), command.intent)

        try:
            self.security.authorize(command, confirmation_callback=confirmation_callback)
        except SecurityError:
            raise

        skill = self.registry.get(command.intent)
        if skill is None:
            return DispatchResult(False, "Ainda não possuo uma Skill para essa ação.", command.intent)

        try:
            result = skill.handler(**command.parameters)
        except TypeError:
            try:
                result = skill.handler()
            except Exception as exc:
                logger.exception("Erro executando intent=%s", command.intent)
                return DispatchResult(False, f"Não consegui executar essa ação: {exc}", command.intent)
        except Exception as exc:
            logger.exception("Erro executando intent=%s", command.intent)
            return DispatchResult(False, f"Não consegui executar essa ação: {exc}", command.intent)

        response = str(result)
        failed = response.startswith(("Não consegui", "Não encontrei", "Não recebi", "Não tenho", "Ainda não", "O caminho", "O arquivo", "O processo"))
        return DispatchResult(not failed, response, command.intent)

    def dispatch_command(self, command: Command, confirmation_callback=None) -> str:
        return self.dispatch_result(command, confirmation_callback=confirmation_callback).response

    def dispatch(self, text: str) -> str:
        from core.interpreter import interpretar
        return self.dispatch_command(interpretar(text))
