from __future__ import annotations

import requests


class OllamaProvider:
    def __init__(self, base_url: str, timeout_sec: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def chat(self, messages: list[dict[str, str]], options: dict) -> str:
        payload = {
            "model": options["model"],
            "messages": messages,
            "stream": False,
            "options": {
                "num_ctx": options.get("num_ctx"),
                "num_predict": options.get("num_predict"),
                "temperature": options.get("temperature"),
            },
        }
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout_sec,
        )
        response.raise_for_status()
        body = response.json()
        message = body.get("message", {})
        content = message.get("content", "").strip()
        if not content:
            raise RuntimeError("Empty response from Ollama")
        return content
