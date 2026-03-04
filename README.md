# mac-telegram-agent

Local-first Telegram agent voor macOS met Ollama als default provider. Ontworpen voor een lichtere MacBook (zoals MBP 2017, 8GB RAM) en uitbreidbaar met skills zoals gratis lokale STT via whisper.cpp.

## Features (fase 1 + basis fase 2)

- Telegram polling bot (`python-telegram-bot`)
- Strikte allowlist (`ALLOWED_USER_IDS`)
- Rate limiting per user/chat
- Modes: `/mode fast|chat|code|smart`
- Handmatige model override: `/model <name>`
- JSON state opslag per chat (`storage/state.json`)
- Ollama provider via `POST /api/chat`
- Skill framework + optionele `stt_whispercpp` skill (achter `ENABLE_STT`)

## Projectstructuur

```text
src/agent/
  app.py
  config.py
  router.py
  security.py
  logging_setup.py
  providers/
    ollama.py
    api.py
  skills/
    stt_whispercpp.py
  storage/
    state.py
scripts/
  install.sh
  install_whispercpp.sh
  install_models.sh
  run.sh
  launchd/com.evertjan.agent.plist
```

## 1) Snelle installatie (met prompts voor token + user id)

```bash
./scripts/install.sh
```

Dit script:
1. vraagt interactief om:
   - Telegram bot token
   - jouw Telegram user id
2. installeert basis dependencies (`ollama`, `ffmpeg`)
3. zet Python dependencies klaar (via `uv` of `venv` fallback)
4. maakt `.env` aan en vult token/user id in.

## 2) Ollama starten + modellen ophalen

```bash
ollama serve
./scripts/install_models.sh
```

Standaardmodellen:
- `deepseek-r1:1.5b` (fast/default)
- `llama3.2:3b` (chat)
- `qwen2.5:3b` (code)

## 3) Bot starten

```bash
./scripts/run.sh
```

## Telegram commands

- `/start`
- `/help`
- `/whoami`
- `/mode <fast|chat|code|smart>`
- `/model <naam>`
- `/reset`

## STT (optioneel, lokaal, gratis)

1. Installeer whisper.cpp:
   ```bash
   ./scripts/install_whispercpp.sh
   ```
2. Pas `.env` aan:
   ```dotenv
   ENABLE_STT=true
   WHISPERCPP_BIN=/pad/naar/repo/bin/whisper-cpp
   WHISPERCPP_MODEL=/pad/naar/repo/models/ggml-tiny.bin
   ```
3. Herstart bot.

## Veiligheid

- Alleen users in `ALLOWED_USER_IDS` krijgen response.
- Rate limiting via `RATE_LIMIT_PER_MIN`.
- Geen token logging.
- Polling i.p.v. webhook.
- Fail-closed startup: zonder token/user id start bot niet.

## launchd autostart (optioneel)

1. Pas paden in `scripts/launchd/com.evertjan.agent.plist` aan.
2. Laad service:
   ```bash
   cp scripts/launchd/com.evertjan.agent.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.evertjan.agent.plist
   ```

## Dev checks

```bash
python3 -m compileall src
python3 -m pytest
```
