FROM python:3.11-slim-bookworm

WORKDIR /app

# Instalação das dependências (adicionamos python3-brotli e libx11)
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk-headless \
    git \
    ffmpeg \
    curl \
    chromium \
    chromium-sandbox \
    python3-brotli \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Variaveis de ambiente para o Chromium não quebrar
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--no-sandbox --disable-gpu --disable-dev-shm-usage --headless=new"
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir brotli  # Garante que o python também tenha o brotli

COPY . .
RUN mkdir -p .logs local_database .app_commands_sync_data plugins

EXPOSE 8080

CMD ["python", "main.py"]
