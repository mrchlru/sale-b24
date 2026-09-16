"""Разбор тел запросов Битрикс24."""

import json
from urllib.parse import parse_qs

from app.models import BitrixWebhookAuth, BitrixWebhookPayload


def parse_bitrix_webhook_body(raw_body: bytes, content_type: str) -> BitrixWebhookPayload:
    """
    Парсит тело события (form или JSON).

    Raises:
        ValueError: если формат не распознан.
    """
    lowered = content_type.lower()
    if "application/json" in lowered:
        return _parse_json(raw_body)
    return _parse_form(raw_body)


def extract_lead_id(payload: BitrixWebhookPayload) -> int | None:
    """Достаёт ID лида из payload события."""
    data = payload.data
    fields = data.get("FIELDS")
    if not isinstance(fields, dict):
        return None
    lead_id = fields.get("ID")
    if lead_id is None:
        return None
    return int(lead_id)


def _parse_json(raw_body: bytes) -> BitrixWebhookPayload:
    data = json.loads(raw_body.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON webhook должен быть объектом")
    return BitrixWebhookPayload.model_validate(data)


def _parse_form(raw_body: bytes) -> BitrixWebhookPayload:
    decoded = raw_body.decode("utf-8")
    parsed = parse_qs(decoded, keep_blank_values=True)
    flat: dict[str, str] = {key: values[-1] if values else "" for key, values in parsed.items()}

    event = flat.get("event", "")
    lead_id_raw = flat.get("data[FIELDS][ID]", "")

    auth = BitrixWebhookAuth(
        access_token=flat.get("auth[access_token]", ""),
        client_endpoint=flat.get("auth[client_endpoint]", ""),
        domain=flat.get("auth[domain]", ""),
        application_token=flat.get("auth[application_token]", ""),
        member_id=flat.get("auth[member_id]", ""),
        server_endpoint=flat.get("auth[server_endpoint]", ""),
        refresh_token=flat.get("auth[refresh_token]", ""),
    )

    data: dict[str, object] = {}
    if lead_id_raw:
        data["FIELDS"] = {"ID": lead_id_raw}

    return BitrixWebhookPayload(event=event, data=data, auth=auth)
