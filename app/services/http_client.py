"""HTTP-клиент с настройкой SSL для российских CA."""

import httpx

from app.config import Settings


def build_async_client(settings: Settings, timeout: float = 30.0) -> httpx.AsyncClient:
    """
    Создаёт httpx.AsyncClient с корректной проверкой SSL.

    На slim-Docker без CA Минцифры запросы к MAX API падают с CERTIFICATE_VERIFY_FAILED.
    """
    if settings.http_ca_bundle.strip():
        verify: bool | str = settings.http_ca_bundle.strip()
    elif settings.http_ssl_verify:
        verify = True
    else:
        verify = False
    return httpx.AsyncClient(timeout=timeout, verify=verify)
