# Bitrix24 → MAX: уведомления о новых лидах

Сервис принимает исходящий webhook Битрикс24 (`ONCRMLEADADD`), загружает поля лида и отправляет текст подписанным пользователям бота в MAX.

## Что нужно заранее

- VPS на TimeWeb с доменом и HTTPS (Let's Encrypt).
- Бот MAX (токен в кабинете партнёра; можно подключить после модерации).
- Битрикс24: входящий и исходящий webhook.

**TimeWeb App Platform (GitHub):** см. [`deploy/TIMEWEB_APP.md`](deploy/TIMEWEB_APP.md).

**TimeWeb VPS:** см. [`deploy/TIMEWEB.md`](deploy/TIMEWEB.md) — два этапа: инфраструктура сейчас и активация MAX после модерации.

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

| Переменная | Назначение |
|------------|------------|
| `BITRIX_PORTAL_DOMAIN` | Домен портала без пути, например `company.bitrix24.ru` |
| `BITRIX_APPLICATION_TOKEN` | Token из исходящего webhook |
| `BITRIX_INCOMING_WEBHOOK_URL` | Полный URL входящего webhook (`.../rest/1/xxx/`) |
| `BITRIX_FIELD_CITY` | Код UF-поля «город» (если пусто — строка не выводится) |
| `BITRIX_FIELD_VISA_QUESTIONS` | Код UF-поля «вопросы по визе» для квиза |
| `MAX_BOT_TOKEN` | Токен бота |
| `MAX_WEBHOOK_SECRET` | Секрет 5–256 символов (A–Z, a–z, 0–9, `-`, `_`) |
| `MAX_SUBSCRIBE_CODE` | Код для подписки: `/start <код>` или deeplink `?start=<код>` |

## Подписка в MAX

1. Запустите сервис и зарегистрируйте webhook MAX (см. ниже).
2. Откройте бота в MAX и отправьте: `/start ВАШ_КОД`  
   или ссылку вида `https://max.ru/YourBot?start=ВАШ_КОД`.
3. После успешной подписки бот ответит подтверждением.

Уведомления получают только chat_id, прошедшие проверку кода.

## Битрикс24

**Исходящий webhook**

- URL: `https://ВАШ_ДОМЕН/bitrix/webhook`
- Событие: **Лид создан** (`ONCRMLEADADD`)

**Входящий webhook**

- Права: CRM, чтение лидов (`crm`).

## Установка на VPS (Ubuntu)

```bash
sudo apt update && sudo apt install -y python3 python3-venv nginx certbot python3-certbot-nginx
sudo mkdir -p /opt/sale_b24
# Загрузите файлы проекта в /opt/sale_b24 (SFTP, scp, архив)
cd /opt/sale_b24
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
mkdir -p data
```

Systemd — пример unit-файла: `deploy/sale-b24.service` (путь и пользователь поправьте под себя).

```bash
sudo cp deploy/sale-b24.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sale-b24
```

Nginx — пример: `deploy/nginx.example.conf`, затем:

```bash
sudo certbot --nginx -d bot.example.com
```

## Регистрация webhook MAX

После модерации бота и когда `https://ВАШ_ДОМЕН/health` открывается:

```bash
cd /opt/sale_b24
source .venv/bin/activate
python scripts/activate_max.py https://ВАШ_ДОМЕН --bot-username НикБота
```

Проверка всей связки:

```bash
python scripts/check_infrastructure.py --public-url https://ВАШ_ДОМЕН
```

Пока бот на модерации:

```bash
python scripts/check_infrastructure.py --public-url https://ВАШ_ДОМЕН --skip-max
```

## Формат уведомления

```
Новый лид с сайта
Название: ...
Имя: ...
Телефон: ...
Город: ...          # если поле заполнено
Вопросы по визе: ... # если поле заполнено
Карточка: https://.../crm/lead/details/ID/
```

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Коды UF-полей в Битрикс

CRM → Настройки → Настройки CRM → Поля → Лиды → пользовательское поле → в URL или свойствах поля будет код вида `UF_CRM_1234567890`. Его укажите в `.env`.
