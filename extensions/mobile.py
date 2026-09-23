from __future__ import annotations

from abc import ABC, abstractmethod


class MobileBridge(ABC):
    """Interface preparada para um aplicativo móvel futuro."""

    @abstractmethod
    def send_event(self, event: str, payload: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def receive_command(self, payload: dict) -> str:
        raise NotImplementedError


class DisabledMobileBridge(MobileBridge):
    def send_event(self, event: str, payload: dict) -> None:
        return None

    def receive_command(self, payload: dict) -> str:
        return "A ponte móvel ainda não está habilitada."
