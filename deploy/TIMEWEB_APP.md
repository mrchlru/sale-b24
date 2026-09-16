# Timeweb App Platform (Backend → FastAPI)

Подключение репозитория GitHub к App Platform.

## Настройки приложения

| Поле | Значение |
|------|----------|
| Тип | Backend → FastAPI |
| Python | 3.11+ |
| Команда сборки | `pip3 install --upgrade -r requirements.txt` |
| Команда запуска | `uvicorn main:app --host 0.0.0.0 --port 8000` |
| Health check | `/health` |

## Переменные окружения

Скопируйте из `.env.example` в панели App Platform (раздел «Переменные»):

- `BITRIX_PORTAL_DOMAIN`
- `BITRIX_APPLICATION_TOKEN`
- `BITRIX_INCOMING_WEBHOOK_URL`
- `BITRIX_FIELD_CITY`
- `BITRIX_FIELD_VISA_QUESTIONS`
- `MAX_API_BASE_URL` = `https://platform-api2.max.ru`
- `MAX_BOT_TOKEN`
- `MAX_WEBHOOK_SECRET`
- `MAX_SUBSCRIBE_CODE`
- `DATA_DIR` = `/tmp/sale_b24_data` (на PaaS диск эфемерный)

## URL после деплоя

Публичный URL платформы вида `https://xxx.timeweb.cloud` используйте в:

1. **Битрикс** исходящий webhook: `https://xxx.timeweb.cloud/bitrix/webhook`
2. **MAX** — после модерации, в консоли или через SSH/one-off:

```bash
python scripts/activate_max.py https://xxx.timeweb.cloud --bot-username НикБота
```

На App Platform нет постоянного SSH по умолчанию — webhook MAX можно зарегистрировать локально тем же скриптом (токен из env).

## Подписчики на PaaS

Файл `data/subscribers.json` может сбрасываться при redeploy. После каждого деплоя менеджерам нужно снова `/start КОД`, либо позже перенесём хранение в БД.

## Автодеплой

При push в `main` Timeweb пересоберёт приложение, если включён autodeploy в настройках репозитория.
