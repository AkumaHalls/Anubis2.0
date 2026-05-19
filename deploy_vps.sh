#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "========================================"
echo "  Anubis Music Bot - Deploy (VPS)"
echo "========================================"
echo ""

# Verifica se esta no diretorio certo
if [ ! -f "main.py" ]; then
    echo "ERRO: Execute este script do diretorio raiz do Anubis"
    exit 1
fi

echo "[1/4] Parando containers antigos..."
docker compose down || true

echo ""
echo "[2/4] Reconstruindo imagem (DOCKER_BUILDKIT=0)..."
DOCKER_BUILDKIT=0 docker compose build --no-cache

echo ""
echo "[3/4] Subindo containers..."
docker compose up -d

echo ""
echo "[4/4] Verificando..."
sleep 5
docker compose ps

echo ""
echo "========================================"
echo "  Deploy concluido!"
echo "  Dashboard: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):2500"
echo "  Logs: docker compose logs -f"
echo "========================================"
