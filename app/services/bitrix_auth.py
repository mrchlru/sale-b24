"""Проверка подлинности событий Битрикс24."""

import logging

from app.config import Settings
from app.models import BitrixWebhookAuth

logger = logging.getLogger(__name__)


def verify_bitrix_auth(auth: BitrixWebhookAuth, settings: Settings) -> bool:
    """
    Проверяет блок auth из события Битрикс24.

    Если задан BITRIX24_APPLICATION_TOKEN — сверяет application_token.
    Иначе принимает событие с валидным OAuth access_token и domain.
    """
    if not auth.access_token.strip() or not auth.client_endpoint.strip():
        return False

    app_token = settings.bitrix24_application_token.strip()
    if app_token:
        return auth.application_token == app_token

    if not auth.domain.strip():
        return False

    logger.debug(
        "BITRIX24_APPLICATION_TOKEN не задан — проверка только access_token/domain",
    )
    return True
