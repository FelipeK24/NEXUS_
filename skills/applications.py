from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from core.config import APPLICATIONS_FILE, APPLICATIONS, PROCESS_NAMES


def _load_applications() -> dict[str, dict[str, str]]:
    try:
        data = json.loads(APPLICATIONS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k).lower(): v for k, v in data.items() if isinstance(v, dict)}
    except (OSError, json.JSONDecodeError):
        pass
    return {
        key: {"path": value, "process": PROCESS_NAMES.get(key, "")}
        for key, value in APPLICATIONS.items()
    }


def _entry(application: str) -> dict[str, str] | None:
    return _load_applications().get(application.strip().lower())


def abrir_aplicacao(application: str) -> str:
    key = application.strip().lower()
    entry = _entry(key)
    if entry is None:
        return f"O aplicativo '{key}' não está cadastrado."
    path = os.path.expandvars(os.path.expanduser(entry.get("path", "")))
    if not path or not os.path.exists(path):
        return f"Não encontrei o caminho autorizado para {key}."
    try:
        subprocess.Popen([path], shell=False)
        return f"Abrindo {key}."
    except OSError as exc:
        return f"Não consegui abrir {key}: {exc}"


def fechar_aplicacao(application: str) -> str:
    key = application.strip().lower()
    entry = _entry(key)
    process = (entry or {}).get("process") or PROCESS_NAMES.get(key)
    if not process:
        return f"O processo de {key} não está cadastrado."
    try:
        result = subprocess.run(
            ["taskkill", "/IM", process, "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return f"Fechei {key}."
        return f"Não encontrei {key} em execução."
    except OSError as exc:
        return f"Não consegui fechar {key}: {exc}"
