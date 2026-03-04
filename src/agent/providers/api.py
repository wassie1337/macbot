from __future__ import annotations


class ApiProvider:
    def __init__(self, api_key: str, model: str = "") -> None:
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[dict[str, str]], options: dict) -> str:
        raise NotImplementedError("ApiProvider is a stub. Configure later for /smart mode.")
