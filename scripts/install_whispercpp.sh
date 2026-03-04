#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT_DIR/bin" "$ROOT_DIR/models"

brew install cmake ffmpeg

if [[ ! -d "$ROOT_DIR/.tmp/whisper.cpp" ]]; then
  mkdir -p "$ROOT_DIR/.tmp"
  git clone https://github.com/ggerganov/whisper.cpp "$ROOT_DIR/.tmp/whisper.cpp"
fi

cmake -S "$ROOT_DIR/.tmp/whisper.cpp" -B "$ROOT_DIR/.tmp/whisper.cpp/build"
cmake --build "$ROOT_DIR/.tmp/whisper.cpp/build" -j
cp "$ROOT_DIR/.tmp/whisper.cpp/build/bin/whisper-cli" "$ROOT_DIR/bin/whisper-cpp"

if [[ ! -f "$ROOT_DIR/models/ggml-tiny.bin" ]]; then
  curl -L https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin -o "$ROOT_DIR/models/ggml-tiny.bin"
fi

echo "whisper.cpp klaar: $ROOT_DIR/bin/whisper-cpp"
echo "Model klaar: $ROOT_DIR/models/ggml-tiny.bin"
