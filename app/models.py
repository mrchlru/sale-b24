"""Модели данных для вебхуков и CRM."""

from pydantic import BaseModel, Field


class BitrixWebhookAuth(BaseModel):
    """Блок auth в исходящем webhook Битрикс24."""

    application_token: str = Field(default="")


class BitrixLeadFields(BaseModel):
    """Минимальные поля события по лиду."""

    id: int = Field(alias="ID")


class BitrixWebhookPayload(BaseModel):
    """Тело исходящего webhook при событии CRM."""

    event: str
    data: dict[str, object] = Field(default_factory=dict)
    auth: BitrixWebhookAuth = Field(default_factory=BitrixWebhookAuth)


class MaxUser(BaseModel):
    """Пользователь MAX в событии update."""

    user_id: int | None = None
    name: str | None = None
    first_name: str | None = None


class MaxMessageBody(BaseModel):
    """Текст сообщения MAX."""

    text: str | None = None


class MaxRecipient(BaseModel):
    """Получатель сообщения MAX."""

    chat_id: int | None = None
    chat_type: str | None = None


class MaxMessage(BaseModel):
    """Сообщение в событии message_created."""

    sender: MaxUser | None = None
    recipient: MaxRecipient | None = None
    body: MaxMessageBody | None = None


class MaxUpdate(BaseModel):
    """Обновление от MAX Bot API."""

    update_type: str
    chat_id: int | None = None
    timestamp: int | None = None
    payload: str | None = None
    user: MaxUser | None = None
    message: MaxMessage | None = None
