from __future__ import annotations

import json
from pathlib import Path


class StateStore:
    def __init__(self, path: str, default_mode: str, default_model: str) -> None:
        self.path = Path(path)
        self.default_mode = default_mode
        self.default_model = default_model
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self) -> dict[str, dict[str, str]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write(self, content: dict[str, dict[str, str]]) -> None:
        self.path.write_text(json.dumps(content, indent=2), encoding="utf-8")

    def get_chat_state(self, chat_id: int) -> dict[str, str]:
        data = self._read()
        state = data.get(str(chat_id), {})
        return {
            "mode": state.get("mode", self.default_mode),
            "model": state.get("model", self.default_model),
        }

    def update_chat_state(self, chat_id: int, *, mode: str | None = None, model: str | None = None) -> dict[str, str]:
        data = self._read()
        key = str(chat_id)
        existing = data.get(key, {"mode": self.default_mode, "model": self.default_model})
        if mode is not None:
            existing["mode"] = mode
        if model is not None:
            existing["model"] = model
        data[key] = existing
        self._write(data)
        return existing

    def reset_chat_state(self, chat_id: int) -> dict[str, str]:
        return self.update_chat_state(chat_id, mode=self.default_mode, model=self.default_model)
