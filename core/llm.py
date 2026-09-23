from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import ollama
from groq import Groq

from core.config import (
    GROQ_API_KEY,
    GROQ_COOLDOWN,
    GROQ_MODEL,
    GROQ_TIMEOUT,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
)
from core.errors import LLMError

logger = logging.getLogger("jarvis.llm")


class LLM(ABC):
    @abstractmethod
    def gerar(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def gerar_json(self, prompt: str) -> dict[str, Any]:
        raise NotImplementedError


class GroqProvider:
    def __init__(self) -> None:
        self.enabled = bool(GROQ_API_KEY)
        self.model = GROQ_MODEL
        self._client = Groq(api_key=GROQ_API_KEY, timeout=GROQ_TIMEOUT) if self.enabled else None

    def gerar(self, prompt: str) -> str:
        if not self._client:
            raise LLMError("GROQ_API_KEY não configurada.")
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_completion_tokens=1024,
            stream=False,
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMError("Groq retornou uma resposta vazia.")
        return content.strip()

    def gerar_json(self, prompt: str) -> dict[str, Any]:
        if not self._client:
            raise LLMError("GROQ_API_KEY não configurada.")
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_completion_tokens=512,
            response_format={"type": "json_object"},
            stream=False,
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMError("Groq retornou JSON vazio.")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMError("Groq retornou JSON inválido.") from exc
        if not isinstance(data, dict):
            raise LLMError("Groq retornou JSON que não é um objeto.")
        return data


class OllamaProvider:
    def __init__(self) -> None:
        self.model = OLLAMA_MODEL
        self._client = ollama.Client(host=OLLAMA_HOST, timeout=OLLAMA_TIMEOUT)

    def gerar(self, prompt: str) -> str:
        try:
            response = self._client.generate(
                model=self.model,
                prompt=prompt,
                think=False,
                stream=False,
            )
        except Exception as exc:
            raise LLMError(f"Ollama indisponível: {exc}") from exc

        content = response.get("response", "")
        if not content:
            raise LLMError("Ollama retornou uma resposta vazia.")
        return content.strip()

    def gerar_json(self, prompt: str) -> dict[str, Any]:
        try:
            response = self._client.generate(
                model=self.model,
                prompt=prompt,
                think=False,
                stream=False,
                format="json",
            )
        except Exception as exc:
            raise LLMError(f"Ollama indisponível: {exc}") from exc

        content = response.get("response", "")
        if not content:
            raise LLMError("Ollama retornou JSON vazio.")
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMError("Ollama retornou JSON inválido.") from exc
        if not isinstance(data, dict):
            raise LLMError("Ollama retornou JSON que não é um objeto.")
        return data


class HybridLLM(LLM):
    def __init__(self) -> None:
        self.groq = GroqProvider()
        self.ollama = OllamaProvider()
        self._groq_failed_until = 0.0
        self.last_provider = "none"

    def _groq_allowed(self) -> bool:
        return self.groq.enabled and time.monotonic() >= self._groq_failed_until

    def _mark_groq_failure(self) -> None:
        self._groq_failed_until = time.monotonic() + GROQ_COOLDOWN

    def gerar(self, prompt: str) -> str:
        if self._groq_allowed():
            try:
                answer = self.groq.gerar(prompt)
                self.last_provider = "groq"
                return answer
            except Exception as exc:
                self._mark_groq_failure()
                logger.warning("Groq falhou; usando fallback local. Motivo: %s", exc)

        try:
            answer = self.ollama.gerar(prompt)
            self.last_provider = "ollama"
            return answer
        except Exception as exc:
            raise LLMError(f"Groq e Ollama falharam. Último erro: {exc}") from exc

    def gerar_json(self, prompt: str) -> dict[str, Any]:
        if self._groq_allowed():
            try:
                data = self.groq.gerar_json(prompt)
                self.last_provider = "groq"
                return data
            except Exception as exc:
                self._mark_groq_failure()
                logger.warning("Groq JSON falhou; usando fallback local. Motivo: %s", exc)

        try:
            data = self.ollama.gerar_json(prompt)
            self.last_provider = "ollama"
            return data
        except Exception as exc:
            raise LLMError(f"Groq e Ollama falharam para JSON. Último erro: {exc}") from exc


llm = HybridLLM()
