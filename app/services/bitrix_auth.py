"""Проверка подлинности событий Битрикс24."""

import logging

from app.config import Settings
from app.models import BitrixWebhookAuth

logger = logging.getLogger(__name__)


def is_outgoing_webhook_event(auth: BitrixWebhookAuth) -> bool:
    """Событие исходящего webhook: есть application_token, нет access_token."""
    return bool(auth.application_token.strip()) and not auth.access_token.strip()


def verify_bitrix_auth(auth: BitrixWebhookAuth, settings: Settings) -> bool:
    """
    Проверяет блок auth из события Битрикс24.

    Поддерживает:
    - локальное приложение (access_token + client_endpoint + domain);
    - исходящий webhook (application_token + BITRIX_INCOMING_WEBHOOK_URL).
    """
    app_token_cfg = settings.bitrix24_application_token.strip()

    if app_token_cfg:
        if auth.application_token == app_token_cfg:
            return True
        if auth.access_token.strip() and auth.client_endpoint.strip() and auth.domain.strip():
            return True
        logger.warning("BITRIX24_APPLICATION_TOKEN задан, но токен события не совпал")
        return False

    if auth.access_token.strip() and auth.client_endpoint.strip() and auth.domain.strip():
        return True

    if is_outgoing_webhook_event(auth) and settings.bitrix_incoming_webhook_url.strip():
        logger.info("Исходящий webhook Битрикс24 (REST через входящий webhook)")
        return True

    logger.warning(
        "Auth отклонён: access_token=%s domain=%s application_token=%s incoming_webhook=%s",
        bool(auth.access_token.strip()),
        bool(auth.domain.strip()),
        bool(auth.application_token.strip()),
        bool(settings.bitrix_incoming_webhook_url.strip()),
    )
    return False
