from __future__ import annotations

from typing import Protocol


class Provider(Protocol):
    def chat(self, messages: list[dict[str, str]], options: dict) -> str:
        ...
