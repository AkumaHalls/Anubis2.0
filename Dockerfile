FROM python:3.11-slim

WORKDIR /app

# Correção de servidores de download forçando a rede nativa da VPS
RUN --network=host sed -i 's/deb.debian.org/ftp.br.debian.org/g' /etc/apt/sources.list 2>/dev/null || true

# Instalação das dependências usando diretamente a rede host e IPv4
RUN --network=host apt-get -o Acquire::ForceIPv4=true update && apt-get -o Acquire::ForceIPv4=true install -y \
    openjdk-17-jdk-headless \
    git \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia o requirements e instala as dependências do Python usando a rede host
COPY requirements.txt .
RUN --network=host pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Cria os diretórios necessários internos do bot
RUN mkdir -p .logs local_database .app_commands_sync_data

# Expõe a porta do servidor web do dashboard
EXPOSE 8080

# Comando para iniciar o bot
CMD ["python", "main.py"]
