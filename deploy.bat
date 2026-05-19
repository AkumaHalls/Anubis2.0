@echo off
REM ========================================
REM  Anubis Music Bot - Deploy Script (Win)
REM ========================================
REM Uso: deploy.bat <usuario@ip-da-vps> [caminho]
REM Ex:  deploy.bat ubuntu@147.15.124.229 /home/ubuntu/anubis
REM ========================================

set SSH_USER=%1
set REMOTE_PATH=%2

if "%SSH_USER%"=="" (
    echo Erro: Informe usuario@ip-da-vps
    echo Ex: deploy.bat ubuntu@147.15.124.229 /home/ubuntu/anubis
    exit /b 1
)

if "%REMOTE_PATH%"=="" (
    set REMOTE_PATH=/home/ubuntu/anubis
)

echo.
echo ========================================
echo  Copiando arquivos para %SSH_USER%:%REMOTE_PATH%
echo ========================================
echo.

REM Cria diretorio remoto
ssh %SSH_USER% "mkdir -p %REMOTE_PATH%"

REM Copia via SCP (exclui .env, __pycache__, .git)
scp -r ^
    --exclude=.env ^
    --exclude=__pycache__ ^
    --exclude=.git ^
    --exclude=.logs ^
    --exclude=local_database ^
    --exclude=.ytdl_cache ^
    --exclude=.app_commands_sync_data ^
    * %SSH_USER%:%REMOTE_PATH%/

if %ERRORLEVEL% neq 0 (
    echo.
    echo [AVISO] SCP com --exclude falhou. Tentando copia simples...
    echo Se estiver no Windows, use WinSCP ou PSCP para transferir.
    echo.
    echo Alternativa manual:
    echo   1. Abra WinSCP e conecte em %SSH_USER%
    echo   2. Copie a pasta Anubis2.0 para %REMOTE_PATH%
    echo   3. Execute no SSH:
    echo.
)

echo.
echo ========================================
echo  Executando build/deploy na VPS...
echo ========================================
echo.

ssh %SSH_USER% "cd %REMOTE_PATH% && ^
    docker compose down && ^
    DOCKER_BUILDKIT=0 docker compose build --no-cache && ^
    docker compose up -d && ^
    echo '========================================' && ^
    echo '  Deploy concluido!' && ^
    echo '  Dashboard: http://147.15.124.229:2500' && ^
    echo '========================================'"

echo.
echo Comando manual se o script acima falhar:
echo   ssh %SSH_USER% "cd %REMOTE_PATH% && docker compose down && DOCKER_BUILDKIT=0 docker compose build --no-cache && docker compose up -d"
echo.
pause
