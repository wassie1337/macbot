#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .env ]]; then
  echo "Maak eerst .env aan (bijv. via ./scripts/install.sh)."
  exit 1
fi

if command -v uv >/dev/null; then
  uv run python -m agent.app
elif [[ -d .venv ]]; then
  source .venv/bin/activate
  python -m agent.app
else
  python3 -m agent.app
fi
