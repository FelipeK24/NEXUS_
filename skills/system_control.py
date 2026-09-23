from __future__ import annotations

import os
import webbrowser
from urllib.parse import quote_plus

from core.config import SITES


def _volume_key(code: int) -> None:
    if os.name != "nt":
        return
    import ctypes
    ctypes.windll.user32.keybd_event(code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(code, 0, 2, 0)


def controlar_sistema(action: str, target: str = "", query: str = "") -> str:
    if action == "volume_up":
        _volume_key(0xAF)
        return "Aumentando o volume."

    if action == "volume_down":
        _volume_key(0xAE)
        return "Diminuindo o volume."

    if action == "volume_mute":
        _volume_key(0xAD)
        return "Alternando o mudo."

    if action == "open_site":
        url = SITES.get(target)
        if not url:
            return "Esse site não está na lista autorizada."
        webbrowser.open(url)
        return f"Abrindo {target}."

    if action == "google_search":
        if not query.strip():
            return "Não recebi o que devo pesquisar."
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
        return f"Pesquisando por {query}."

    if action == "youtube_search":
        if not query.strip():
            return "Não recebi o que devo pesquisar no YouTube."
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
        return f"Pesquisando no YouTube por {query}."

    return "Não reconheci esse controle do sistema."
