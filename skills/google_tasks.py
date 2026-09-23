from __future__ import annotations

from extensions.google_workspace import google_workspace


def adicionar_google_task(title: str, notes: str = "") -> str:
    return google_workspace.add_google_task(title, notes)


def listar_google_tasks() -> str:
    return google_workspace.list_google_tasks()


def concluir_google_task(identifier: str) -> str:
    return google_workspace.complete_google_task(identifier)


def excluir_google_task(identifier: str) -> str:
    return google_workspace.delete_google_task(identifier)
