from __future__ import annotations

import logging

from core.skill import Skill

logger = logging.getLogger("jarvis.skill_registry")


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        if skill.intent in self._skills:
            raise ValueError(f"A intent '{skill.intent}' já está registrada.")
        self._skills[skill.intent] = skill
        logger.info("Skill registrada: %s", skill.intent)

    def get(self, intent: str) -> Skill | None:
        return self._skills.get(intent)

    def has(self, intent: str) -> bool:
        return intent in self._skills

    def list_skills(self) -> list[Skill]:
        return list(self._skills.values())
