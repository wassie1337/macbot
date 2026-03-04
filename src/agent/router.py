from __future__ import annotations

import logging
import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Update

logger = logging.getLogger(__name__)


class Router:
    def __init__(self, settings, ollama_provider, api_provider, skills: list) -> None:
        self.settings = settings
        self.ollama_provider = ollama_provider
        self.api_provider = api_provider
        self.skills = skills

    def resolve_model_for_mode(self, mode: str) -> str:
        mapping = {
            "fast": self.settings.ollama_model_fast,
            "chat": self.settings.ollama_model_chat,
            "code": self.settings.ollama_model_code,
            "smart": self.settings.ollama_model_default,
        }
        return mapping.get(mode, self.settings.ollama_model_default)

    async def prepare_input(self, update: "Update", state: dict[str, str], context) -> tuple[str, str]:
        if update.message and update.message.text:
            return update.message.text.strip(), ""

        for skill in self.skills:
            if skill.can_handle(update, state):
                result = await skill.run(update, state, context)
                return result.text, result.prefix

        if update.message and update.message.voice and not self.settings.enable_stt:
            return "", "STT staat uit. Zet ENABLE_STT=true om voice te gebruiken."

        return "", "Ik kan dit type bericht nog niet verwerken."

    def _provider_for_mode(self, mode: str):
        if mode == "smart" and self.settings.api_key:
            return self.api_provider
        return self.ollama_provider

    def generate_reply(self, user_text: str, state: dict[str, str]) -> str:
        mode = state["mode"]
        model = state.get("model") or self.resolve_model_for_mode(mode)
        provider = self._provider_for_mode(mode)

        options = {
            "model": model,
            "num_ctx": self.settings.num_ctx,
            "num_predict": self.settings.num_predict,
            "temperature": self.settings.temperature,
        }

        messages = [{"role": "user", "content": user_text}]

        started = time.perf_counter()
        try:
            text = provider.chat(messages, options)
        except Exception:
            if mode == "smart":
                logger.exception("Smart provider failed, falling back to Ollama")
                text = self.ollama_provider.chat(messages, options)
            else:
                raise

        latency = (time.perf_counter() - started) * 1000
        logger.info("reply_generated mode=%s model=%s latency_ms=%.0f", mode, model, latency)
        return text
