from __future__ import annotations

import json
import re

from core.command import Command, PlannedCommand
from core.errors import PlanningError
from core.interpreter import ALLOWED_INTENTS, interpretar, validar_command
from core.llm import llm


class Planner:
    """Planeja sequências simples e multi-etapas sem executar nenhuma ação."""

    MAX_COMMANDS = 6
    SEPARATORS = (
        r"\s+e depois\s+",
        r"\s+e entao\s+",
        r"\s+entao\s+",
        r"\s+depois\s+",
        r"\s*;\s*",
    )

    def split_goal(self, text: str) -> list[str]:
        result = [text.strip()]
        for pattern in self.SEPARATORS:
            new_result: list[str] = []
            for item in result:
                new_result.extend(re.split(pattern, item, flags=re.IGNORECASE))
            result = [item.strip() for item in new_result if item.strip()]
        return result

    def _needs_llm_planning(self, text: str) -> bool:
        lowered = text.lower()
        return len(text) > 35 and (
            " e " in lowered
            or "," in lowered
            or "também" in lowered
            or "tambem" in lowered
        )

    def _llm_plan(self, text: str) -> list[Command]:
        schema = {
            "commands": [
                {"intent": "intent permitida", "parameters": {}}
            ]
        }
        prompt = f"""
Você é o planejador do NEXUS. Transforme o objetivo do usuário em uma sequência curta de comandos estruturados.
Não execute nada e não invente ações. Use somente intents permitidas.
Cada comando deve ser executável em ordem. Quando uma etapa depender do resultado de outra, use placeholders como `$last_file` ou `$last_response`.
Use `$last_file` principalmente quando um `file_find` for seguido por `file_open`, `file_move` ou `file_delete`.
Se o usuário pediu apenas uma ação, retorne exatamente um comando.
No máximo 6 comandos.

Intents permitidas:
{", ".join(sorted(ALLOWED_INTENTS))}

Formato obrigatório:
{json.dumps(schema, ensure_ascii=False)}

Objetivo:
{text}
""".strip()
        try:
            data = llm.gerar_json(prompt)
            raw = data.get("commands") if isinstance(data, dict) else None
            if not isinstance(raw, list) or not 1 <= len(raw) <= self.MAX_COMMANDS:
                raise PlanningError("O planejador retornou uma quantidade invÃ¡lida de aÃ§Ãµes.")
            commands: list[Command] = []
            for item in raw:
                if not isinstance(item, dict):
                    raise PlanningError("O planejador retornou uma etapa invÃ¡lida.")
                intent = item.get("intent")
                parameters = item.get("parameters", {})
                if not isinstance(intent, str) or not isinstance(parameters, dict):
                    raise PlanningError("O planejador retornou parÃ¢metros invÃ¡lidos.")
                command = validar_command(Command(intent, parameters, text))
                if command.intent == "unknown":
                    raise PlanningError("Uma etapa do plano nÃ£o passou pela validaÃ§Ã£o.")
                commands.append(command)
            return commands
        except PlanningError:
            raise
        except Exception as exc:
            raise PlanningError("NÃ£o foi possÃ­vel validar o plano gerado.") from exc

    def plan(self, text: str) -> list[PlannedCommand]:
        pieces = self.split_goal(text)
        commands: list[Command]
        if len(pieces) > 1:
            if len(pieces) > self.MAX_COMMANDS:
                raise PlanningError("O pedido excede o limite de seis aÃ§Ãµes por plano.")
            commands = [interpretar(piece) for piece in pieces]
            if any(command.intent == "unknown" for command in commands):
                raise PlanningError("Uma etapa do pedido nÃ£o pÃ´de ser interpretada com seguranÃ§a.")
        elif self._needs_llm_planning(text):
            commands = self._llm_plan(text)
        else:
            commands = [interpretar(text)]

        total = len(commands)
        return [PlannedCommand(command, index + 1, total) for index, command in enumerate(commands)]
