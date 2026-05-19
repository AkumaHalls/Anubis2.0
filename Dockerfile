FROM python:3.11-slim-bookworm AS base-image

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-sandbox \
    chromium-common \
    openjdk-17-jre-headless \
    wget curl tar gzip \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_PATH=/usr/bin/chromium \
    CHROMIUM_PATH=/usr/bin/chromium

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

STOPSIGNAL SIGINT

CMD ["python", "main.py"]

FROM base-image AS dashboard

CMD ["python", "-m", "uvicorn", "dashboard.main:app", "--host", "0.0.0.0", "--port", "3000"]
