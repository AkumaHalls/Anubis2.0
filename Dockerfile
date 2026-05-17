FROM python:3.11-slim

WORKDIR /app

# Instalação das dependências do sistema com a rede corrigida da VPS
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk-headless \
    git \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia o requirements e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Cria os diretórios necessários internos do bot
RUN mkdir -p .logs local_database .app_commands_sync_data

# Expõe a porta do servidor web do dashboard
EXPOSE 8080

# Comando para iniciar o bot
CMD ["python", "main.py"]
