from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Command:
    intent: str
    parameters: dict[str, Any] = field(default_factory=dict)
    original_text: str = ""


@dataclass(frozen=True)
class PlannedCommand:
    command: Command
    index: int
    total: int
