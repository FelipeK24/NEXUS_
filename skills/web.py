from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from core.browser import browser
from core.config import SITES, SITES_FILE
from core.web import pesquisar_web


def _load_sites() -> dict[str, str]:
    try:
        data = json.loads(Path(SITES_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    merged = dict(SITES)
    for key, value in data.items():
        if isinstance(key, str) and isinstance(value, str) and value.strip():
            merged[key.strip().lower()] = value.strip()
    return merged


def _normalize_url(target: str) -> str:
    target = target.strip().strip('"')
    sites = _load_sites()
    alias = target.lower()
    if alias in sites:
        return sites[alias]
    parsed = urlparse(target)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return target
    if "." in target and " " not in target:
        return f"https://{target}"
    raise ValueError("Informe um site conhecido ou uma URL HTTP/HTTPS válida.")


def pesquisar(query: str) -> str:
    return pesquisar_web(query)


def abrir(target: str) -> str:
    try:
        return browser.open(_normalize_url(target))
    except Exception as exc:
        return f"Não consegui abrir o site: {exc}"


def ler_pagina() -> str:
    try:
        return browser.read()
    except Exception as exc:
        return f"Não consegui ler a página atual: {exc}"


def voltar() -> str:
    try:
        return browser.back()
    except Exception as exc:
        return f"Não consegui voltar no navegador: {exc}"


def avancar() -> str:
    try:
        return browser.forward()
    except Exception as exc:
        return f"Não consegui avançar no navegador: {exc}"


def atualizar() -> str:
    try:
        return browser.refresh()
    except Exception as exc:
        return f"Não consegui atualizar a página: {exc}"


def listar_abas() -> str:
    try:
        return browser.tabs()
    except Exception as exc:
        return f"Não consegui listar as abas: {exc}"


def fechar_navegador() -> str:
    try:
        return browser.close()
    except Exception as exc:
        return f"Não consegui fechar o navegador: {exc}"


def screenshot(path: str = "data/browser_screenshot.png") -> str:
    try:
        return browser.screenshot(path)
    except Exception as exc:
        return f"Não consegui salvar o screenshot: {exc}"


def clicar(selector: str) -> str:
    try:
        return browser.click(selector)
    except Exception as exc:
        return f"Não consegui clicar nesse elemento: {exc}"


def preencher(selector: str, content: str) -> str:
    try:
        return browser.type_text(selector, content)
    except Exception as exc:
        return f"Não consegui preencher esse campo: {exc}"


def enviar(selector: str) -> str:
    try:
        return browser.submit(selector)
    except Exception as exc:
        return f"Não consegui enviar o formulário: {exc}"
