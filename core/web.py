from __future__ import annotations

import logging
from dataclasses import dataclass
from html import unescape
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

from core.config import WEB_REQUEST_TIMEOUT, WEB_SEARCH_ENGINE, WEB_SEARCH_LIMIT

logger = logging.getLogger("jarvis.web")


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


def _valid_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def _clean_text(value: str) -> str:
    value = unescape(value or "")
    return " ".join(value.split()).strip()


def _search_bing(query: str) -> list[SearchResult]:
    url = f"https://www.bing.com/search?q={quote_plus(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        )
    }
    with httpx.Client(timeout=WEB_REQUEST_TIMEOUT, headers=headers, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []
    for item in soup.select("li.b_algo")[:WEB_SEARCH_LIMIT]:
        link = item.select_one("h2 a")
        if not link:
            continue
        title = _clean_text(link.get_text(" ", strip=True))
        href = str(link.get("href", "")).strip()
        snippet_node = item.select_one(".b_caption p")
        snippet = _clean_text(snippet_node.get_text(" ", strip=True)) if snippet_node else ""
        if title and _valid_http_url(href):
            results.append(SearchResult(title, href, snippet))
    return results


def _search_duckduckgo(query: str) -> list[SearchResult]:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        )
    }
    with httpx.Client(timeout=WEB_REQUEST_TIMEOUT, headers=headers, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []
    for item in soup.select(".result")[:WEB_SEARCH_LIMIT]:
        link = item.select_one(".result__a")
        if not link:
            continue
        title = _clean_text(link.get_text(" ", strip=True))
        href = str(link.get("href", "")).strip()
        snippet_node = item.select_one(".result__snippet")
        snippet = _clean_text(snippet_node.get_text(" ", strip=True)) if snippet_node else ""
        if title and _valid_http_url(href):
            results.append(SearchResult(title, href, snippet))
    return results


def pesquisar_web(query: str) -> str:
    query = query.strip()
    if not query:
        return "Não recebi o que devo pesquisar."

    engines = [WEB_SEARCH_ENGINE.lower().strip(), "bing", "duckduckgo"]
    seen: set[str] = set()
    results: list[SearchResult] = []
    last_error: Exception | None = None

    for engine in engines:
        if engine in seen:
            continue
        seen.add(engine)
        try:
            if engine == "duckduckgo":
                results = _search_duckduckgo(query)
            else:
                results = _search_bing(query)
            if results:
                break
        except Exception as exc:
            last_error = exc
            logger.warning("Pesquisa web falhou em %s: %s", engine, exc)

    if not results:
        if last_error:
            logger.error("Todas as pesquisas web falharam: %s", last_error)
        return "Não consegui fazer a pesquisa na internet agora."

    lines = [f"Resultados para: {query}"]
    for index, result in enumerate(results, start=1):
        lines.append(f"{index}. {result.title}")
        lines.append(f"   {result.url}")
        if result.snippet:
            lines.append(f"   {result.snippet}")
    return "\n".join(lines)
