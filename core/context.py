from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class ConversationTurn:
    user: str
    assistant: str


class ConversationContext:
    def __init__(self, max_turns: int = 8) -> None:
        self.max_turns = max_turns
        self._turns = deque(maxlen=max_turns)
        self._pending_user_message: str | None = None

    def add_user(self, content: str) -> None:
        content = content.strip()
        if content:
            self._pending_user_message = content

    def add_assistant(self, content: str) -> None:
        content = content.strip()
        if not content or self._pending_user_message is None:
            return
        self._turns.append(ConversationTurn(self._pending_user_message, content))
        self._pending_user_message = None

    def add_turn(self, user: str, assistant: str) -> None:
        user = user.strip()
        assistant = assistant.strip()
        if user and assistant:
            self._turns.append(ConversationTurn(user, assistant))
        self._pending_user_message = None

    def clear(self) -> None:
        self._turns.clear()
        self._pending_user_message = None

    def get_turns(self) -> list[ConversationTurn]:
        return list(self._turns)

    def get_messages(self) -> list[Message]:
        messages: list[Message] = []
        for turn in self._turns:
            messages.append(Message("user", turn.user))
            messages.append(Message("assistant", turn.assistant))
        return messages

    def format(self) -> str:
        if not self._turns:
            return "Nenhuma conversa anterior."
        lines = []
        for turn in self._turns:
            lines.append(f"Usuário: {turn.user}")
            lines.append(f"Nexus: {turn.assistant}")
        return "\n".join(lines)
