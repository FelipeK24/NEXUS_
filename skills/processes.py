from __future__ import annotations

import json
from pathlib import Path

import psutil

from core.config import PROCESS_ALLOWLIST_PATH, PROCESS_LIST_LIMIT

_PROTECTED = {
    "system",
    "system idle process",
    "registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "services.exe",
    "lsass.exe",
    "winlogon.exe",
}


def _load_allowlist() -> set[str]:
    try:
        data = json.loads(Path(PROCESS_ALLOWLIST_PATH).read_text(encoding="utf-8"))
        return {str(x).lower() for x in data.get("allowed_processes", [])}
    except (OSError, json.JSONDecodeError, AttributeError):
        return set()


def listar_processos() -> str:
    rows: list[tuple[float, int, str]] = []
    for proc in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            name = proc.info.get("name") or "desconhecido"
            mem = proc.info.get("memory_info")
            rss_mb = (mem.rss / 1024 / 1024) if mem else 0.0
            rows.append((rss_mb, int(proc.info.get("pid") or 0), name))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    rows.sort(reverse=True)
    rows = rows[:PROCESS_LIST_LIMIT]
    if not rows:
        return "Não consegui obter os processos."
    return "Processos por uso de memória:\n" + "\n".join(
        f"PID {pid} | {name} | {memory:.1f} MB" for memory, pid, name in rows
    )


def fechar_processo(process_name: str) -> str:
    target = process_name.strip().lower()
    if not target.endswith(".exe"):
        target += ".exe"
    allowlist = _load_allowlist()
    if target not in allowlist:
        return f"O processo '{process_name}' não está na lista de processos autorizados."
    if target in _PROTECTED:
        return "Esse processo é protegido e não pode ser encerrado pelo NEXUS."

    closed = 0
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if name != target:
                continue
            proc.terminate()
            closed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if closed == 0:
        return f"Não encontrei o processo '{process_name}' em execução."
    return f"Solicitei o encerramento de {closed} processo(s) '{process_name}'."
