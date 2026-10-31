from __future__ import annotations

import logging
import threading
import uuid
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import parse_qs

logger = logging.getLogger("jarvis.events")


@dataclass(frozen=True)
class NexusEvent:
    id: int
    type: str
    timestamp: str
    data: dict[str, Any]


class EventBus:
    """Thread-safe in-memory event stream with bounded history."""

    def __init__(self, history_size: int = 256) -> None:
        if history_size < 1:
            raise ValueError("history_size precisa ser maior que zero.")
        self._events: deque[NexusEvent] = deque(maxlen=history_size)
        self._lock = threading.RLock()
        self.stream_id = uuid.uuid4().hex
        self._next_id = 1
        self._subscribers: dict[int, Callable[[NexusEvent], None]] = {}
        self._next_subscriber_id = 1

    def publish(self, event_type: str, data: dict[str, Any] | None = None) -> NexusEvent:
        if not event_type or not isinstance(event_type, str):
            raise ValueError("event_type precisa ser uma string não vazia.")
        with self._lock:
            event = NexusEvent(
                id=self._next_id,
                type=event_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                data=dict(data or {}),
            )
            self._next_id += 1
            self._events.append(event)
            subscribers = tuple(self._subscribers.values())

        for callback in subscribers:
            try:
                callback(event)
            except Exception:
                logger.exception("Assinante falhou ao receber evento %s.", event_type)
        return event

    def get_events(self, *, after_id: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        if after_id < 0:
            raise ValueError("after_id não pode ser negativo.")
        if limit < 1:
            raise ValueError("limit precisa ser maior que zero.")
        with self._lock:
            events = [event for event in self._events if event.id > after_id]
        return [asdict(event) for event in events[:limit]]

    def latest_id(self) -> int:
        with self._lock:
            return self._next_id - 1

    def subscribe(self, callback: Callable[[NexusEvent], None]) -> Callable[[], None]:
        with self._lock:
            subscriber_id = self._next_subscriber_id
            self._next_subscriber_id += 1
            self._subscribers[subscriber_id] = callback

        def unsubscribe() -> None:
            with self._lock:
                self._subscribers.pop(subscriber_id, None)

        return unsubscribe


event_bus = EventBus()


def parse_event_query(query: str) -> tuple[int, int]:
    values = parse_qs(query, keep_blank_values=True, strict_parsing=True)
    if set(values) - {"after_id", "limit"} or any(len(items) != 1 for items in values.values()):
        raise ValueError("Parâmetros de consulta inválidos.")
    try:
        after_id = int(values.get("after_id", ["0"])[0])
        limit = int(values.get("limit", ["50"])[0])
    except ValueError as exc:
        raise ValueError("after_id e limit precisam ser números inteiros.") from exc
    if after_id < 0:
        raise ValueError("after_id não pode ser negativo.")
    if not 1 <= limit <= 100:
        raise ValueError("limit deve ficar entre 1 e 100.")
    return after_id, limit
