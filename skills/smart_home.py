from __future__ import annotations

from extensions.smart_home import smart_home


def executar(device: str, action: str, parameters: dict | None = None) -> str:
    return smart_home.execute(device, action, parameters)
