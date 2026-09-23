from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from core.config import TASKS_FILE


def _load() -> list[dict]:
    try:
        data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save(data: list[dict]) -> None:
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TASKS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def adicionar_tarefa(title: str) -> str:
    title = title.strip()
    if not title:
        return "Informe o nome da tarefa."
    tasks = _load()
    item = {"id": len(tasks) + 1, "title": title, "done": False, "created_at": datetime.now().isoformat(timespec="seconds")}
    tasks.append(item)
    _save(tasks)
    return f"Tarefa criada: {title}."


def listar_tarefas() -> str:
    tasks = [x for x in _load() if not x.get("done")]
    if not tasks:
        return "Você não possui tarefas pendentes."
    return "Tarefas pendentes:\n" + "\n".join(f"{x['id']}. {x['title']}" for x in tasks)


def concluir_tarefa(identifier: str) -> str:
    value = identifier.strip()
    tasks = _load()
    target = None
    for item in tasks:
        if str(item.get("id")) == value or str(item.get("title", "")).lower() == value.lower():
            target = item
            break
    if target is None:
        return "Não encontrei essa tarefa."
    target["done"] = True
    target["completed_at"] = datetime.now().isoformat(timespec="seconds")
    _save(tasks)
    return f"Tarefa concluída: {target['title']}."


def excluir_tarefa(identifier: str) -> str:
    value = identifier.strip()
    tasks = _load()
    filtered = [x for x in tasks if not (str(x.get("id")) == value or str(x.get("title", "")).lower() == value.lower())]
    if len(filtered) == len(tasks):
        return "Não encontrei essa tarefa."
    _save(filtered)
    return "Tarefa excluída."
