from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable

from core.command import PlannedCommand
from core.dispatcher import DispatchResult, Dispatcher
from core.errors import PlanningError, SecurityError
from core.events import event_bus
from core.interpreter import llm_name, registrar_nexus, registrar_usuario
from core.planner import Planner
from core import speaker

logger = logging.getLogger("jarvis.pipeline")
_execution_lock = threading.RLock()


@dataclass(frozen=True)
class PipelineResult:
    success: bool
    response: str
    commands_executed: int
    total_commands: int


class CommandPipeline:
    def __init__(self, dispatcher: Dispatcher, planner: Planner, panel=None, events=event_bus) -> None:
        self.dispatcher = dispatcher
        self.planner = planner
        self.panel = panel
        self.events = events
        # Todas as instâncias compartilham o bloqueio para serializar voz, painel e API.
        self.lock = _execution_lock

    @staticmethod
    def _inject_results(command, last_file: str, last_response: str):
        if not command.parameters:
            return command
        parameters = dict(command.parameters)
        for key, value in parameters.items():
            if not isinstance(value, str):
                continue
            if value == "$last_file":
                parameters[key] = last_file
            elif value == "$last_response":
                parameters[key] = last_response
        from core.command import Command
        return Command(command.intent, parameters, command.original_text)

    def execute(
        self,
        text: str,
        *,
        speak: bool = True,
        show_output: bool = True,
        confirmation_callback: Callable[[str], bool] | None = None,
        stop_on_failure: bool = True,
    ) -> PipelineResult:
        with self.lock:
            started_at = time.monotonic()
            self.events.publish("pipeline.started")
            try:
                planned = self.planner.plan(text)
                can_dispatch = getattr(self.dispatcher, "can_dispatch", None)
                if callable(can_dispatch) and any(
                    not can_dispatch(item.command) for item in planned
                ):
                    raise PlanningError("Uma etapa do plano não corresponde a uma Skill executável.")
            except PlanningError:
                message = "Não consegui montar um plano seguro. Divida o pedido em até seis ações claras e tente novamente."
                self.events.publish("pipeline.failed", {"stage": "planning"})
                if show_output:
                    print(f"NEXUS > {message}")
                if self.panel:
                    self.panel.state.update(mode="erro", response=message)
                if speak:
                    speaker.falar(message)
                return PipelineResult(False, message, 0, 0)
            except Exception:
                self.events.publish("pipeline.failed", {"stage": "planning"})
                raise
            responses: list[str] = []
            executed = 0
            total = len(planned)
            overall_success = True
            last_file = ""
            last_response = ""

            for item in planned:
                command = self._inject_results(item.command, last_file, last_response)
                command_started_at = time.monotonic()
                self.events.publish("command.started", {
                    "intent": command.intent,
                    "index": item.index,
                    "total": item.total,
                })
                logger.info(
                    "Comando %d/%d | intent=%s | parameters=%s | provider=%s",
                    item.index, item.total, command.intent, command.parameters, llm_name(),
                )
                if self.panel:
                    self.panel.state.update(
                        mode="processando",
                        user=command.original_text,
                        provider=llm_name(),
                        intent=command.intent,
                    )
                try:
                    registrar_usuario(command.original_text)
                    result: DispatchResult = self.dispatcher.dispatch_result(
                        command,
                        confirmation_callback=confirmation_callback,
                    )
                except SecurityError as exc:
                    result = DispatchResult(False, str(exc), command.intent)

                response = result.response
                responses.append(response)
                last_response = response
                if command.intent == "file_find" and result.success:
                    lines = [line.strip() for line in response.splitlines() if line.strip()]
                    if len(lines) >= 2 and not lines[0].startswith("Não"):
                        last_file = lines[1]
                executed += 1
                overall_success = overall_success and result.success
                self.events.publish("command.completed", {
                    "intent": command.intent,
                    "index": item.index,
                    "total": item.total,
                    "success": result.success,
                    "duration_ms": round((time.monotonic() - command_started_at) * 1000),
                })

                registrar_nexus(response)

                if show_output:
                    print(f"NEXUS > {response}")
                if self.panel:
                    self.panel.state.update(
                        mode="online" if result.success else "erro",
                        response=response,
                        provider=llm_name(),
                        intent=command.intent,
                    )
                if speak:
                    speaker.falar(response)

                if stop_on_failure and not result.success:
                    logger.warning("Pipeline interrompido após falha em %s.", command.intent)
                    break

            pipeline_result = PipelineResult(
                success=overall_success,
                response="\n".join(responses) if responses else "Não consegui executar o comando.",
                commands_executed=executed,
                total_commands=total,
            )
            self.events.publish("pipeline.completed", {
                "success": pipeline_result.success,
                "commands_executed": executed,
                "total_commands": total,
                "duration_ms": round((time.monotonic() - started_at) * 1000),
            })
            return pipeline_result
