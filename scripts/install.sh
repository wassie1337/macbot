#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log() { echo "[install] $*"; }
warn() { echo "[install][warn] $*" >&2; }

command -v python3 >/dev/null || { echo "python3 ontbreekt"; exit 1; }

read -r -p "Telegram bot token: " TELEGRAM_BOT_TOKEN
read -r -p "Jouw Telegram user id: " ALLOWED_USER_ID

if [[ -z "$TELEGRAM_BOT_TOKEN" || -z "$ALLOWED_USER_ID" ]]; then
  echo "Token en user id zijn verplicht"
  exit 1
fi

if [[ ! "$ALLOWED_USER_ID" =~ ^[0-9]+$ ]]; then
  echo "User id moet numeriek zijn"
  exit 1
fi

TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" ALLOWED_USER_ID="$ALLOWED_USER_ID" python3 - <<'PY'
import os
from pathlib import Path

root = Path('.')
env_path = root / '.env'
template_path = root / '.env.example'

def parse_env(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        out[k.strip()] = v.strip()
    return out

if template_path.exists():
    values = parse_env(template_path.read_text(encoding='utf-8'))
else:
    values = {
        'OLLAMA_URL': 'http://127.0.0.1:11434',
        'OLLAMA_MODEL_DEFAULT': 'deepseek-r1:1.5b',
        'OLLAMA_MODEL_FAST': 'deepseek-r1:1.5b',
        'OLLAMA_MODEL_CHAT': 'llama3.2:3b',
        'OLLAMA_MODEL_CODE': 'qwen2.5:3b',
        'DEFAULT_MODE': 'fast',
        'NUM_CTX': '2048',
        'NUM_PREDICT': '220',
        'TEMPERATURE': '0.6',
        'ENABLE_STT': 'false',
        'WHISPERCPP_BIN': '/usr/local/bin/whisper-cpp',
        'WHISPERCPP_MODEL': 'ggml-tiny.bin',
        'TMP_DIR': '/tmp/mac-telegram-agent',
        'LOG_LEVEL': 'INFO',
        'RATE_LIMIT_PER_MIN': '20',
        'STATE_FILE': 'storage/state.json',
        'OLLAMA_TIMEOUT_SEC': '120',
        'STT_TIMEOUT_SEC': '180',
        'API_MODEL': '',
        'API_KEY': '',
    }

values['TELEGRAM_BOT_TOKEN'] = os.environ['TELEGRAM_BOT_TOKEN']
values['ALLOWED_USER_IDS'] = os.environ['ALLOWED_USER_ID']

order = [
    'TELEGRAM_BOT_TOKEN',
    'ALLOWED_USER_IDS',
    'OLLAMA_URL',
    'OLLAMA_MODEL_DEFAULT',
    'OLLAMA_MODEL_FAST',
    'OLLAMA_MODEL_CHAT',
    'OLLAMA_MODEL_CODE',
    'DEFAULT_MODE',
    'NUM_CTX',
    'NUM_PREDICT',
    'TEMPERATURE',
    'ENABLE_STT',
    'WHISPERCPP_BIN',
    'WHISPERCPP_MODEL',
    'TMP_DIR',
    'LOG_LEVEL',
    'RATE_LIMIT_PER_MIN',
    'STATE_FILE',
    'OLLAMA_TIMEOUT_SEC',
    'STT_TIMEOUT_SEC',
    'API_MODEL',
    'API_KEY',
]

lines: list[str] = []
for key in order:
    lines.append(f"{key}={values.get(key, '')}")

env_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f"[install] .env geschreven: {env_path.resolve()}")
PY

if [[ ! -s .env ]]; then
  echo "Kon .env niet aanmaken" >&2
  exit 1
fi

if [[ "${SKIP_BREW:-0}" == "1" ]]; then
  warn "SKIP_BREW=1: Homebrew installatie overgeslagen"
else
  if command -v brew >/dev/null; then
    if ! brew install ollama; then
      warn "Kon ollama niet installeren via brew (bijv. tag/version issue)."
      warn "Ga verder met de rest; installeer Ollama handmatig via https://ollama.com/download/mac"
    fi

    if ! brew install ffmpeg; then
      warn "Kon ffmpeg niet installeren via brew. Voice/STT werkt dan niet totdat ffmpeg is geïnstalleerd."
    fi
  else
    warn "Homebrew ontbreekt, sla brew installs over. Installeer handmatig: ollama + ffmpeg"
  fi
fi

if command -v uv >/dev/null; then
  if ! uv sync; then
    warn "uv sync faalde. Probeer later opnieuw of gebruik venv fallback handmatig."
  fi
else
  python3 -m venv .venv || warn "venv aanmaken faalde"
  if [[ -f .venv/bin/activate ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install --upgrade pip || warn "pip upgrade faalde"
    pip install -e . || warn "pip install -e . faalde (mogelijk netwerk/proxy)"
  fi
fi

log "Installatie afgerond"
echo "Volgende stappen:"
echo "1) Controleer .env: cat .env"
echo "2) Start Ollama: ollama serve"
echo "3) Download model: ollama pull deepseek-r1:1.5b"
echo "4) Start bot: ./scripts/run.sh"
