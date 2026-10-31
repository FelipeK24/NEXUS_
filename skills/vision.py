from __future__ import annotations

from skills.files import resolve_safe_path
from core.errors import SkillError
from core.vision import analisar_imagem as _analisar_imagem
from core.vision import analisar_tela as _analisar_tela


def analisar_tela(pergunta: str = "Descreva o que aparece na minha tela.") -> str:
    return _analisar_tela(pergunta)


def analisar_imagem(path: str, pergunta: str = "Descreva o que há nesta imagem.") -> str:
    try:
        safe = resolve_safe_path(path)
    except ValueError as exc:
        raise SkillError(str(exc)) from exc
    return _analisar_imagem(str(safe), pergunta)
