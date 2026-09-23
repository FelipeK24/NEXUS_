from __future__ import annotations

import platform

import psutil


def informacoes_sistema() -> str:
    cpu = platform.processor() or "CPU não identificada"
    ram_total = psutil.virtual_memory().total / (1024 ** 3)
    ram_used = psutil.virtual_memory().used / (1024 ** 3)
    return (
        f"Sistema: {platform.system()} {platform.release()}. "
        f"CPU: {cpu}. "
        f"RAM: {ram_used:.1f} de {ram_total:.1f} GB em uso."
    )
