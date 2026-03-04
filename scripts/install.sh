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

if [[ ! -f .env ]]; then
  cp .env.example .env
fi
TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" ALLOWED_USER_ID="$ALLOWED_USER_ID" python3 - <<'PY'
import os
from pathlib import Path

env_path = Path('.env')
lines = env_path.read_text(encoding='utf-8').splitlines()
out = []
for line in lines:
    if line.startswith('TELEGRAM_BOT_TOKEN='):
        out.append(f"TELEGRAM_BOT_TOKEN={os.environ['TELEGRAM_BOT_TOKEN']}")
    elif line.startswith('ALLOWED_USER_IDS='):
        out.append(f"ALLOWED_USER_IDS={os.environ['ALLOWED_USER_ID']}")
    else:
        out.append(line)
env_path.write_text('\n'.join(out) + '\n', encoding='utf-8')
PY

log ".env geschreven met jouw token en user id"

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
echo "1) Start Ollama: ollama serve"
echo "2) Download model: ollama pull deepseek-r1:1.5b"
echo "3) Start bot: ./scripts/run.sh"
