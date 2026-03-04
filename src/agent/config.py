from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """Raised when configuration is invalid."""


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_dotenv(dotenv_path: str = ".env") -> None:
    env_file = Path(dotenv_path)
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass
class Settings:
    telegram_bot_token: str
    allowed_user_ids: set[int]
    ollama_url: str
    ollama_model_default: str
    ollama_model_fast: str
    ollama_model_chat: str
    ollama_model_code: str
    default_mode: str
    num_ctx: int
    num_predict: int
    temperature: float
    enable_stt: bool
    whispercpp_bin: str
    whispercpp_model: str
    tmp_dir: str
    log_level: str
    rate_limit_per_min: int
    state_file: str
    ollama_timeout_sec: int
    stt_timeout_sec: int
    api_model: str
    api_key: str


def load_settings(dotenv_path: str = ".env") -> Settings:
    _load_dotenv(dotenv_path)

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ConfigError("TELEGRAM_BOT_TOKEN is required")

    user_ids_raw = os.getenv("ALLOWED_USER_IDS", "").strip()
    if not user_ids_raw:
        raise ConfigError("ALLOWED_USER_IDS is required")

    allowed_ids: set[int] = set()
    for part in user_ids_raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            allowed_ids.add(int(part))
        except ValueError as exc:
            raise ConfigError(f"Invalid ALLOWED_USER_IDS entry: {part}") from exc

    if not allowed_ids:
        raise ConfigError("At least one ALLOWED_USER_IDS entry is required")

    default_mode = os.getenv("DEFAULT_MODE", "fast").strip().lower()
    if default_mode not in {"fast", "chat", "code", "smart"}:
        raise ConfigError("DEFAULT_MODE must be one of fast|chat|code|smart")

    return Settings(
        telegram_bot_token=token,
        allowed_user_ids=allowed_ids,
        ollama_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").strip(),
        ollama_model_default=os.getenv("OLLAMA_MODEL_DEFAULT", "deepseek-r1:1.5b").strip(),
        ollama_model_fast=os.getenv("OLLAMA_MODEL_FAST", "deepseek-r1:1.5b").strip(),
        ollama_model_chat=os.getenv("OLLAMA_MODEL_CHAT", "llama3.2:3b").strip(),
        ollama_model_code=os.getenv("OLLAMA_MODEL_CODE", "qwen2.5:3b").strip(),
        default_mode=default_mode,
        num_ctx=int(os.getenv("NUM_CTX", "2048")),
        num_predict=int(os.getenv("NUM_PREDICT", "220")),
        temperature=float(os.getenv("TEMPERATURE", "0.6")),
        enable_stt=_parse_bool(os.getenv("ENABLE_STT"), False),
        whispercpp_bin=os.getenv("WHISPERCPP_BIN", "/usr/local/bin/whisper-cpp").strip(),
        whispercpp_model=os.getenv("WHISPERCPP_MODEL", "ggml-tiny.bin").strip(),
        tmp_dir=os.getenv("TMP_DIR", "/tmp/mac-telegram-agent").strip(),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip(),
        rate_limit_per_min=int(os.getenv("RATE_LIMIT_PER_MIN", "20")),
        state_file=os.getenv("STATE_FILE", "storage/state.json").strip(),
        ollama_timeout_sec=int(os.getenv("OLLAMA_TIMEOUT_SEC", "120")),
        stt_timeout_sec=int(os.getenv("STT_TIMEOUT_SEC", "180")),
        api_model=os.getenv("API_MODEL", "").strip(),
        api_key=os.getenv("API_KEY", "").strip(),
    )
