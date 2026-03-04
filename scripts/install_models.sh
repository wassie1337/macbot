#!/usr/bin/env bash
set -euo pipefail

ollama pull deepseek-r1:1.5b
ollama pull llama3.2:3b
ollama pull qwen2.5:3b
