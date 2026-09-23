from __future__ import annotations

import json
import webbrowser
from pathlib import Path
from urllib.parse import quote

from core.config import DATA_DIR, SPOTIFY_PLAYLISTS


def _carregar_playlists() -> dict[str, str]:
    playlists = dict(SPOTIFY_PLAYLISTS)
    arquivo = DATA_DIR / "spotify_playlists.json"

    try:
        if arquivo.exists():
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            if isinstance(dados, dict):
                for chave, url in dados.items():
                    if isinstance(chave, str) and isinstance(url, str):
                        playlists[chave.strip().lower()] = url.strip()
    except (OSError, json.JSONDecodeError):
        pass

    return playlists


def abrir_playlist(nome: str) -> str:
    nome = nome.strip()
    if not nome:
        return "Não consegui identificar a playlist."

    chave = nome.lower()
    playlists = _carregar_playlists()
    url = playlists.get(chave, "").strip()

    if url:
        webbrowser.open(url)
        return f"Abrindo a playlist {nome} no Spotify."

    pesquisa = f"https://open.spotify.com/search/{quote(nome)}"
    webbrowser.open(pesquisa)
    return f"Não tenho o link exato salvo para {nome}, então abri a busca do Spotify."
