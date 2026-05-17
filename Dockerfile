FROM python:3.11-slim

WORKDIR /app

# Correção de servidores de download para contornar o bloqueio da Oracle Cloud
RUN sed -i 's/deb.debian.org/ftp.br.debian.org/g' /etc/apt/sources.list 2>/dev/null || true
RUN sed -i 's/deb.debian.org/ftp.br.debian.org/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true

# Instalação das dependências forçando IPv4 e usando o espelho brasileiro externo
RUN apt-get -o Acquire::ForceIPv4=true update && apt-get -o Acquire::ForceIPv4=true install -y \
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
