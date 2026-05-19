FROM python:3.11-slim-bookworm

WORKDIR /app

# Instalação das dependências do sistema
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk-headless \
    git \
    ffmpeg \
    curl \
    chromium \
    chromium-sandbox \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Variaveis de ambiente para Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--no-sandbox --disable-gpu --disable-dev-shm-usage"
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Copia o requirements e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .
# Cria os diretórios necessários internos do bot
RUN mkdir -p .logs local_database .app_commands_sync_data plugins

# Expõe a porta do servidor web interno
EXPOSE 8080

# Comando para iniciar o bot
CMD ["python", "main.py"]
