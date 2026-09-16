"""HTTP-клиент Битрикс24 REST через OAuth из события."""

import httpx

from app.config import Settings
from app.models import BitrixSession


class BitrixClient:
    """REST-запросы к Битрикс24 с access_token из события."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._field_city = settings.bitrix_field_city.strip()
        self._field_visa = settings.bitrix_field_visa_questions.strip()

    async def get_lead(self, session: BitrixSession, lead_id: int) -> dict[str, object]:
        """
        Загружает лид по ID через OAuth-токен события.

        Returns:
            Словарь полей лида из crm.lead.get.
        """
        base = session.client_endpoint.rstrip("/") + "/"
        params = {"auth": session.access_token, "id": lead_id}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{base}crm.lead.get", params=params)
            if response.status_code == 401 and session.refresh_token:
                new_token = await self._refresh_access_token(session)
                params["auth"] = new_token
                response = await client.get(f"{base}crm.lead.get", params=params)
            response.raise_for_status()
            payload = response.json()

        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValueError(f"crm.lead.get: неожиданный ответ для лида {lead_id}")
        return result

    async def _refresh_access_token(self, session: BitrixSession) -> str:
        """Обновляет access_token через client_id/client_secret."""
        endpoint = session.server_endpoint.strip() or "https://oauth.bitrix.info/rest/"
        url = f"{endpoint.rstrip('/')}/oauth/token/"
        data = {
            "grant_type": "refresh_token",
            "client_id": self._settings.bitrix24_client_id,
            "client_secret": self._settings.bitrix24_client_secret,
            "refresh_token": session.refresh_token,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            payload = response.json()
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise ValueError("Не удалось обновить access_token Битрикс24")
        return token
