"""HTTP-клиент Битрикс24 REST."""

import httpx

from app.config import Settings


class BitrixClient:
    """Запросы к REST API через входящий webhook."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.bitrix_incoming_webhook_url.rstrip("/") + "/"
        self._field_city = settings.bitrix_field_city.strip()
        self._field_visa = settings.bitrix_field_visa_questions.strip()

    async def get_lead(self, lead_id: int) -> dict[str, object]:
        """
        Загружает лид по ID.

        Returns:
            Словарь полей лида из crm.lead.get.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._base_url}crm.lead.get",
                params={"id": lead_id},
            )
            response.raise_for_status()
            payload = response.json()
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValueError(f"crm.lead.get: неожиданный ответ для лида {lead_id}")
        return result
