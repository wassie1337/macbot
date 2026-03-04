from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from agent.config import ConfigError, load_settings
from agent.logging_setup import configure_logging
from agent.providers.api import ApiProvider
from agent.providers.ollama import OllamaProvider
from agent.router import Router
from agent.security import Allowlist, RateLimiter
from agent.skills.stt_whispercpp import WhisperCppSTTSkill
from agent.storage.state import StateStore

logger = logging.getLogger(__name__)


def _get_user_id(update: Update) -> int | None:
    if update.effective_user:
        return update.effective_user.id
    return None


def _is_allowed(update: Update, allowlist: Allowlist) -> bool:
    return allowlist.is_allowed(_get_user_id(update))


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update, context.bot_data["allowlist"]):
        logger.warning("blocked_user user_id=%s", _get_user_id(update))
        return
    await update.message.reply_text("Welkom! Gebruik /help voor commando's.")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update, context.bot_data["allowlist"]):
        return
    text = (
        "Beschikbare commands:\n"
        "/start\n/help\n/whoami\n"
        "/mode <fast|chat|code|smart>\n"
        "/model <naam>\n/reset"
    )
    await update.message.reply_text(text)


async def whoami_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update, context.bot_data["allowlist"]):
        return
    await update.message.reply_text(f"user_id={_get_user_id(update)}")


async def mode_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update, context.bot_data["allowlist"]):
        return
    if not context.args:
        await update.message.reply_text("Gebruik: /mode <fast|chat|code|smart>")
        return

    mode = context.args[0].lower()
    if mode not in {"fast", "chat", "code", "smart"}:
        await update.message.reply_text("Ongeldige mode.")
        return

    state_store: StateStore = context.bot_data["state_store"]
    router: Router = context.bot_data["router"]
    chat_id = update.effective_chat.id
    model = router.resolve_model_for_mode(mode)
    state_store.update_chat_state(chat_id, mode=mode, model=model)
    await update.message.reply_text(f"Mode ingesteld op {mode} (model {model}).")


async def model_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update, context.bot_data["allowlist"]):
        return
    if not context.args:
        await update.message.reply_text("Gebruik: /model <naam>")
        return

    model_name = context.args[0]
    chat_id = update.effective_chat.id
    state_store: StateStore = context.bot_data["state_store"]
    state = state_store.update_chat_state(chat_id, model=model_name)
    await update.message.reply_text(f"Model ingesteld op {state['model']}.")


async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_allowed(update, context.bot_data["allowlist"]):
        return
    chat_id = update.effective_chat.id
    state_store: StateStore = context.bot_data["state_store"]
    state = state_store.reset_chat_state(chat_id)
    await update.message.reply_text(f"Reset voltooid: mode={state['mode']} model={state['model']}")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    allowlist: Allowlist = context.bot_data["allowlist"]
    if not _is_allowed(update, allowlist):
        logger.warning("blocked_user user_id=%s", _get_user_id(update))
        return

    limiter: RateLimiter = context.bot_data["rate_limiter"]
    user_id = _get_user_id(update)
    if user_id is None or not limiter.allow(user_id):
        await update.message.reply_text("Rate limit geraakt. Probeer over een minuut opnieuw.")
        return

    chat_id = update.effective_chat.id
    state_store: StateStore = context.bot_data["state_store"]
    state = state_store.get_chat_state(chat_id)

    router: Router = context.bot_data["router"]
    input_text, prefix_or_msg = await router.prepare_input(update, state, context)
    if not input_text:
        await update.message.reply_text(prefix_or_msg)
        return

    try:
        output = router.generate_reply(input_text, state)
    except Exception:
        logger.exception("provider_error")
        await update.message.reply_text("Kon geen antwoord genereren. Controleer of Ollama draait.")
        return

    if prefix_or_msg:
        output = f"{prefix_or_msg}{input_text}\n\n🤖 Antwoord:\n{output}"

    await update.message.reply_text(output)


def build_application() -> Application:
    settings = load_settings()
    configure_logging(settings.log_level)

    allowlist = Allowlist(settings.allowed_user_ids)
    limiter = RateLimiter(settings.rate_limit_per_min)
    state_store = StateStore(
        settings.state_file,
        default_mode=settings.default_mode,
        default_model=settings.ollama_model_default,
    )
    ollama_provider = OllamaProvider(settings.ollama_url, settings.ollama_timeout_sec)
    api_provider = ApiProvider(settings.api_key, settings.api_model)

    stt_skill = WhisperCppSTTSkill(
        enabled=settings.enable_stt,
        whisper_bin=settings.whispercpp_bin,
        model=settings.whispercpp_model,
        tmp_dir=settings.tmp_dir,
        timeout_sec=settings.stt_timeout_sec,
    )

    router = Router(settings, ollama_provider, api_provider, [stt_skill])

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data.update(
        {
            "allowlist": allowlist,
            "rate_limiter": limiter,
            "state_store": state_store,
            "router": router,
        }
    )

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("whoami", whoami_handler))
    app.add_handler(CommandHandler("mode", mode_handler))
    app.add_handler(CommandHandler("model", model_handler))
    app.add_handler(CommandHandler("reset", reset_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.VOICE, message_handler))

    return app


def main() -> None:
    try:
        app = build_application()
    except ConfigError as exc:
        raise SystemExit(f"Config error: {exc}") from exc

    logger.info("bot_starting")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
