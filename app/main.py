"""Точка входа FastAPI: вебхуки Битрикс24 и MAX."""

import logging
import os
from functools import lru_cache
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response

from app.config import Settings, get_settings
from app.models import MaxUpdate
from app.services.bitrix_client import BitrixClient
from app.services.bitrix_webhook_parser import extract_lead_id, parse_bitrix_webhook_body
from app.services.lead_notifier import notify_subscribers_about_lead
from app.services.max_client import MaxClient
from app.services.max_subscription import handle_max_update
from app.storage import processed_lead_store, subscriber_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bitrix24 → MAX lead notifier", version="1.0.0")


@lru_cache
def _settings() -> Settings:
    return get_settings()


def _data_dir() -> Path:
    return Path(_settings().data_dir)


@app.get("/health")
async def health() -> dict[str, str]:
    """Проверка доступности сервиса после деплоя."""
    return {"status": "ok"}


async def _handle_bitrix_webhook(request: Request, background_tasks: BackgroundTasks) -> Response:
    """Общая логика исходящего webhook Битрикс24."""
    settings = _settings()
    raw = await request.body()
    content_type = request.headers.get("content-type", "")
    try:
        payload = parse_bitrix_webhook_body(raw, content_type)
    except ValueError as exc:
        logger.warning("Некорректный webhook Битрикс: %s", exc)
        raise HTTPException(status_code=400, detail="Bad request") from exc

    token = payload.auth.application_token
    if token != settings.bitrix_application_token:
        logger.warning("Отклонён webhook Битрикс: неверный application_token")
        raise HTTPException(status_code=403, detail="Forbidden")

    event = payload.event.upper()
    if event != "ONCRMLEADADD":
        return Response(content="ignored", media_type="text/plain")

    lead_id = extract_lead_id(payload)
    if lead_id is None:
        logger.warning("ONCRMLEADADD без ID лида")
        return Response(content="no lead id", media_type="text/plain")

    background_tasks.add_task(_process_new_lead, lead_id)
    return Response(content="ok", media_type="text/plain")


async def _handle_max_webhook(request: Request, background_tasks: BackgroundTasks) -> Response:
    """Общая логика webhook MAX."""
    settings = _settings()
    secret_header = request.headers.get("X-Max-Bot-Api-Secret", "")
    if secret_header != settings.max_webhook_secret:
        logger.warning("Отклонён webhook MAX: неверный secret")
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        data = await request.json()
        update = MaxUpdate.model_validate(data)
    except Exception as exc:
        logger.warning("Некорректный JSON MAX: %s", exc)
        raise HTTPException(status_code=400, detail="Bad request") from exc

    background_tasks.add_task(_process_max_update, update)
    return Response(content="ok", media_type="text/plain")


@app.post("/bitrix/webhook")
async def bitrix_webhook(request: Request, background_tasks: BackgroundTasks) -> Response:
    """Принимает исходящий webhook Битрикс24 (ONCRMLEADADD)."""
    return await _handle_bitrix_webhook(request, background_tasks)


@app.post("/max/webhook")
async def max_webhook(request: Request, background_tasks: BackgroundTasks) -> Response:
    """Принимает обновления MAX Bot API."""
    return await _handle_max_webhook(request, background_tasks)


async def _process_new_lead(lead_id: int) -> None:
    settings = _settings()
    data_dir = _data_dir()
    await notify_subscribers_about_lead(
        lead_id=lead_id,
        settings=settings,
        bitrix=BitrixClient(settings),
        max_client=MaxClient(settings),
        subscribers=subscriber_store(data_dir),
        processed=processed_lead_store(data_dir),
    )


async def _process_max_update(update: MaxUpdate) -> None:
    settings = _settings()
    await handle_max_update(
        update=update,
        settings=settings,
        subscribers=subscriber_store(_data_dir()),
        max_client=MaxClient(settings),
    )


def _register_prefixed_webhooks() -> None:
    """Регистрирует те же обработчики с секретным префиксом URL."""
    secret = os.getenv("WEBHOOK_PATH_SECRET", "").strip().strip("/")
    if not secret:
        return

    @app.post(f"/{secret}/bitrix/webhook")
    async def bitrix_webhook_secret(
        request: Request,
        background_tasks: BackgroundTasks,
    ) -> Response:
        return await _handle_bitrix_webhook(request, background_tasks)

    @app.post(f"/{secret}/max/webhook")
    async def max_webhook_secret(
        request: Request,
        background_tasks: BackgroundTasks,
    ) -> Response:
        return await _handle_max_webhook(request, background_tasks)


_register_prefixed_webhooks()
