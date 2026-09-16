"""Доставка уведомления о новом лиде подписчикам MAX."""

import logging

from app.config import Settings
from app.services.bitrix_client import BitrixClient
from app.services.lead_formatter import format_lead_notification
from app.services.max_client import MaxClient
from app.storage import JsonIdStore

logger = logging.getLogger(__name__)


async def notify_subscribers_about_lead(
    lead_id: int,
    settings: Settings,
    bitrix: BitrixClient,
    max_client: MaxClient,
    subscribers: JsonIdStore,
    processed: JsonIdStore,
) -> None:
    """
    Загружает лид, форматирует текст и рассылает подписчикам.

    Повторная обработка того же lead_id пропускается.
    """
    if processed.contains(lead_id):
        logger.info("Лид %s уже обработан, пропуск", lead_id)
        return

    chat_ids = subscribers.list_ids()
    if not chat_ids:
        logger.warning("Нет подписчиков MAX — лид %s не отправлен", lead_id)
        return

    lead = await bitrix.get_lead(lead_id)
    text = format_lead_notification(lead, settings)

    failed: list[int] = []
    for chat_id in chat_ids:
        try:
            await max_client.send_text_to_chat(chat_id, text)
        except Exception:
            logger.exception("Не удалось отправить лид %s в chat_id=%s", lead_id, chat_id)
            failed.append(chat_id)

    if not failed:
        processed.add(lead_id)
    else:
        logger.error(
            "Лид %s: ошибки отправки в %s чат(ов), повтор возможен",
            lead_id,
            len(failed),
        )
