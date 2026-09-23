from __future__ import annotations

from core import interpreter
from core.memory import memory


def limpar_contexto() -> str:
    interpreter.limpar_contexto()
    return "Contexto da conversa apagado."


def lembrar(key: str, value: str) -> str:
    key = key.strip()
    value = value.strip()
    if not key or not value:
        return "Não consegui identificar o que devo lembrar."
    existed = memory.has(key)
    if not memory.remember(key, value):
        return "Não consegui salvar essa informação."
    if existed:
        return f"Entendido. Atualizei minha memória: {key} é {value}."
    return f"Entendido. Vou lembrar que {key} é {value}."


def esquecer(key: str) -> str:
    key = key.strip()
    if not key:
        return "Não consegui identificar o que devo esquecer."
    if memory.forget(key):
        return f"Esqueci a informação sobre {key}."
    found = memory.find_relevant(key)
    if found:
        found_key, _ = found
        return f"Não encontrei exatamente '{key}', mas encontrei uma memória sobre '{found_key}'."
    return f"Não encontrei nenhuma memória sobre {key}."


def consultar_memoria(key: str) -> str:
    key = key.strip()
    if not key:
        return "Não consegui identificar o que devo consultar."
    value = memory.recall(key)
    if value is not None:
        return f"Lembro que {key} é {value}."
    found = memory.find_relevant(key)
    if found:
        found_key, found_value = found
        return f"Lembro que {found_key} é {found_value}."
    return f"Não tenho nenhuma memória registrada sobre {key}."


def apagar_toda_memoria() -> str:
    if not memory.clear():
        return "Não consegui apagar toda a memória persistente."
    return "Toda a minha memória persistente foi apagada."
