from __future__ import annotations

import json
import logging
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from core.config import MEMORY_FILE

logger = logging.getLogger("jarvis.memory")


class MemoryManager:
    def __init__(self, file_path: Path = MEMORY_FILE) -> None:
        self.file_path = file_path
        self._memory: dict[str, Any] = {}
        self._load()

    @staticmethod
    def _normalize_key(key: str) -> str:
        if not isinstance(key, str):
            return ""
        key = key.strip().lower()
        key = re.sub(r"[!?.,;:]+", " ", key)
        key = re.sub(r"\s+", " ", key)
        return key.strip()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        normalized = MemoryManager._normalize_key(text)
        return normalized.split() if normalized else []

    @staticmethod
    def _remove_stopwords(tokens: list[str]) -> list[str]:
        stopwords = {
            "a", "as", "o", "os", "um", "uma", "uns", "umas",
            "de", "da", "das", "do", "dos", "em", "na", "nas",
            "no", "nos", "meu", "minha", "meus", "minhas", "eu",
            "mim", "que", "qual", "quais", "é", "e", "eh", "são",
            "sao", "isso", "aquilo", "essa", "esse", "essas", "esses",
            "você", "voce", "lembra", "lembrar", "mesmo", "mesma",
            "sobre", "para", "por", "com", "como", "onde", "quando",
            "quem", "tenho", "tenha", "curto", "gosto",
        }
        return [token for token in tokens if token not in stopwords]

    def _load(self) -> None:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.file_path.exists():
                self._memory = {}
                self._save()
                return
            with self.file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            self._memory = data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            logger.exception("Não foi possível carregar a memória.")
            self._memory = {}

    def _save(self) -> bool:
        temp = self.file_path.with_suffix(".tmp")
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with temp.open("w", encoding="utf-8") as file:
                json.dump(self._memory, file, ensure_ascii=False, indent=4)
                file.flush()
            temp.replace(self.file_path)
            return True
        except OSError:
            logger.exception("Não foi possível salvar a memória.")
            try:
                if temp.exists():
                    temp.unlink()
            except OSError:
                pass
            return False

    def remember(self, key: str, value: Any) -> bool:
        normalized = self._normalize_key(key)
        if not normalized:
            return False
        self._memory[normalized] = value
        return self._save()

    def recall(self, key: str) -> Any | None:
        return self._memory.get(self._normalize_key(key))

    def find_relevant(self, query: str) -> tuple[str, Any] | None:
        query = self._normalize_key(query)
        if not query:
            return None
        if query in self._memory:
            return query, self._memory[query]

        query_tokens = self._remove_stopwords(self._tokenize(query))
        if not query_tokens:
            return None

        best_key: str | None = None
        best_value: Any = None
        best_score = 0.0
        query_set = set(query_tokens)

        for key, value in self._memory.items():
            key_normalized = self._normalize_key(key)
            key_tokens = self._remove_stopwords(self._tokenize(key_normalized))
            if not key_tokens:
                continue

            key_set = set(key_tokens)
            overlap = len(query_set.intersection(key_set))
            union = query_set.union(key_set)
            jaccard = len(query_set.intersection(key_set)) / len(union) if union else 0.0
            similarity = SequenceMatcher(None, query, key_normalized).ratio()
            score = overlap * 0.45 + jaccard * 0.35 + similarity * 0.20

            if overlap == 0 and similarity < 0.65:
                continue
            if score > best_score:
                best_score = score
                best_key = key
                best_value = value

        if best_key is None or best_score < 0.35:
            return None
        return best_key, best_value

    def has(self, key: str) -> bool:
        normalized = self._normalize_key(key)
        return bool(normalized and normalized in self._memory)

    def forget(self, key: str) -> bool:
        normalized = self._normalize_key(key)
        if normalized not in self._memory:
            return False
        del self._memory[normalized]
        return self._save()

    def get_all(self) -> dict[str, Any]:
        return dict(self._memory)

    def count(self) -> int:
        return len(self._memory)

    def clear(self) -> bool:
        self._memory.clear()
        return self._save()


memory = MemoryManager()
