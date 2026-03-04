from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class SkillResult:
    text: str
    prefix: str = ""


class Skill(Protocol):
    name: str

    def can_handle(self, update, state: dict[str, str]) -> bool:
        ...

    async def run(self, update, state: dict[str, str], context) -> SkillResult:
        ...
