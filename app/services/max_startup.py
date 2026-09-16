"""Регистрация MAX webhook при старте приложения."""

import logging

from app.config import Settings
from app.services.max_client import MaxClient

logger = logging.getLogger(__name__)

MAX_UPDATE_TYPES = ["bot_started", "message_created", "bot_stopped"]


def _public_base_url(settings: Settings) -> str:
    """Базовый публичный URL приложения."""
    if settings.public_app_url.strip():
        return settings.public_app_url.strip().rstrip("/")

    parsed = settings.bitrix24_handler_url.strip()
    if parsed.startswith("http://") or parsed.startswith("https://"):
        from urllib.parse import urlparse

        parts = urlparse(parsed)
        if parts.scheme and parts.netloc:
            return f"{parts.scheme}://{parts.netloc}"

    raise ValueError(
        "Не удалось определить публичный URL. "
        "Задайте PUBLIC_APP_URL или корректный BITRIX24_HANDLER_URL.",
    )


def _max_webhook_url(settings: Settings, base_url: str) -> str:
    """Полный URL webhook MAX."""
    prefix = settings.webhook_path_secret.strip().strip("/")
    path = f"/{prefix}/max/webhook" if prefix else "/max/webhook"
    return f"{base_url.rstrip('/')}{path}"


async def ensure_max_webhook(settings: Settings) -> None:
    """
    Регистрирует webhook MAX при старте, если включено MAX_AUTO_REGISTER_WEBHOOK.
    """
    if not settings.max_auto_register_webhook:
        logger.info("Авторегистрация MAX webhook отключена (MAX_AUTO_REGISTER_WEBHOOK=false)")
        return

    base_url = _public_base_url(settings)
    webhook_url = _max_webhook_url(settings, base_url)
    client = MaxClient(settings)

    try:
        me = await client.get_me()
        bot_label = me.get("username") or me.get("name") or "bot"
        result = await client.register_webhook(
            url=webhook_url,
            secret=settings.max_webhook_secret,
            update_types=MAX_UPDATE_TYPES,
        )
        logger.info(
            "MAX webhook зарегистрирован для %s: %s → %s",
            bot_label,
            webhook_url,
            result,
        )
    except Exception:
        logger.exception(
            "Не удалось зарегистрировать MAX webhook на %s. "
            "Проверьте MAX_BOT_TOKEN, MAX_WEBHOOK_SECRET и PUBLIC_APP_URL.",
            webhook_url,
        )
