#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

command -v python3 >/dev/null || { echo "python3 ontbreekt"; exit 1; }
command -v brew >/dev/null || { echo "Homebrew ontbreekt"; exit 1; }

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

brew install ollama ffmpeg

if command -v uv >/dev/null; then
  uv sync
else
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -e .
fi

cp -n .env.example .env
TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" ALLOWED_USER_ID="$ALLOWED_USER_ID" python3 - <<'PY'
import os
from pathlib import Path

env_path = Path('.env')
text = env_path.read_text(encoding='utf-8')
text = text.replace('TELEGRAM_BOT_TOKEN=', f"TELEGRAM_BOT_TOKEN={os.environ['TELEGRAM_BOT_TOKEN']}")
text = text.replace('ALLOWED_USER_IDS=12345678', f"ALLOWED_USER_IDS={os.environ['ALLOWED_USER_ID']}")
env_path.write_text(text, encoding='utf-8')
PY

echo "Installatie klaar. Start Ollama met: ollama serve"
echo "En download model met: ollama pull deepseek-r1:1.5b"
echo "Start bot met: ./scripts/run.sh"
