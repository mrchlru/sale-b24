FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# CA Минцифры нужны для platform-api2.max.ru в slim-образе
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && curl -fsSL -o /usr/local/share/ca-certificates/russian_trusted_root_ca.crt \
        https://gu-st.ru/content/Other/doc/russian_trusted_root_ca_pem.crt \
    && curl -fsSL -o /usr/local/share/ca-certificates/russian_trusted_sub_ca.crt \
        https://gu-st.ru/content/Other/doc/russian_trusted_sub_ca_pem.crt \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
