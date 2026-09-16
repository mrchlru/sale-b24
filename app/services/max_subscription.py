"""Обработка подписки пользователей MAX по секретному коду."""

import re

from app.config import Settings
from app.models import MaxUpdate
from app.services.max_client import MaxClient
from app.storage import JsonIdStore


_START_WITH_CODE = re.compile(
    r"^/start(?:@\w+)?\s+(\S+)$",
    re.IGNORECASE,
)
_START_PLAIN = re.compile(r"^/start(?:@\w+)?$", re.IGNORECASE)


def resolve_chat_id(update: MaxUpdate) -> int | None:
    """Определяет chat_id для ответа и рассылки."""
    if update.chat_id is not None:
        return update.chat_id
    if update.message and update.message.recipient and update.message.recipient.chat_id:
        return update.message.recipient.chat_id
    return None


def extract_subscribe_code_from_update(update: MaxUpdate) -> str | None:
    """
    Извлекает код подписки из deeplink payload или текста сообщения.

    Поддерживает: ?start=CODE, «/start CODE», «start CODE», сообщение «CODE».
    """
    if update.update_type == "bot_started":
        if update.payload and update.payload.strip():
            return update.payload.strip()
        return None

    if update.update_type != "message_created" or not update.message:
        return None

    text = (update.message.body.text if update.message.body else None) or ""
    normalized = text.strip()
    if not normalized:
        return None

    match = _START_WITH_CODE.match(normalized)
    if match:
        return match.group(1)

    if _START_PLAIN.match(normalized):
        return None

    lower = normalized.lower()
    if lower.startswith("start "):
        parts = normalized.split(maxsplit=1)
        if len(parts) == 2:
            return parts[1].strip()

    if " " not in normalized and "\n" not in normalized:
        return normalized

    return None


async def handle_max_update(
    update: MaxUpdate,
    settings: Settings,
    subscribers: JsonIdStore,
    max_client: MaxClient,
) -> None:
    """Обрабатывает события MAX: подписка, отписка, ответы пользователю."""
    chat_id = resolve_chat_id(update)

    if update.update_type == "bot_stopped":
        if chat_id is not None:
            subscribers.remove(chat_id)
        return

    if update.update_type not in {"bot_started", "message_created"}:
        return

    code = extract_subscribe_code_from_update(update)
    if code is None:
        if update.update_type == "message_created" and chat_id is not None:
            text = (update.message.body.text if update.message and update.message.body else "") or ""
            if _START_PLAIN.match(text.strip()):
                await max_client.send_text_to_chat(
                    chat_id,
                    "Введите код подписки: /start <код>",
                )
        return

    if code != settings.max_subscribe_code:
        if chat_id is not None:
            await max_client.send_text_to_chat(chat_id, "Неверный код подписки.")
        return

    if chat_id is None:
        return

    is_new = subscribers.add(chat_id)
    if is_new:
        await max_client.send_text_to_chat(
            chat_id,
            "Вы подписаны на уведомления о новых лидах.",
        )
    else:
        await max_client.send_text_to_chat(
            chat_id,
            "Вы уже подписаны на уведомления.",
        )
