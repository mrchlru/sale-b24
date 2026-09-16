"""Конфигурация приложения из переменных окружения."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Параметры интеграции Битрикс24 и MAX."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bitrix_portal_domain: str
    bitrix_application_token: str
    bitrix_incoming_webhook_url: str
    bitrix_field_city: str = ""
    bitrix_field_visa_questions: str = ""

    max_api_base_url: str = "https://platform-api2.max.ru"
    max_bot_token: str
    max_webhook_secret: str
    max_subscribe_code: str

    data_dir: str = "./data"
    webhook_path_secret: str = ""

    def bitrix_lead_card_url(self, lead_id: int) -> str:
        """Ссылка на карточку лида в портале Битрикс24."""
        domain = self.bitrix_portal_domain.strip().rstrip("/")
        if domain.startswith("http://") or domain.startswith("https://"):
            base = domain
        else:
            base = f"https://{domain}"
        return f"{base}/crm/lead/details/{lead_id}/"

    def webhook_prefix(self) -> str:
        """Префикс URL для вебхуков с опциональным секретным сегментом."""
        secret = self.webhook_path_secret.strip().strip("/")
        if secret:
            return f"/{secret}"
        return ""


def get_settings() -> Settings:
    """Возвращает экземпляр настроек."""
    return Settings()
