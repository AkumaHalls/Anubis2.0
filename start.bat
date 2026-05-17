@echo off
title Anubis Music Bot
echo ============================================
echo         Anubis Music Bot v2.0
echo ============================================
echo.

:: Check venv
if not exist "venv" (
    echo [ERROR] Ambiente virtual nao encontrado!
    echo Execute setup.bat primeiro!
    pause
    exit /b 1
)

:: Check .env
if not exist ".env" (
    echo [ERROR] Arquivo .env nao encontrado!
    echo Copie .example.env para .env e configure o TOKEN!
    pause
    exit /b 1
)

:: Activate venv
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Falha ao ativar ambiente virtual!
    pause
    exit /b 1
)

echo [OK] Ambiente virtual ativado.
echo [..] Iniciando Anubis Music Bot...
echo.

:: Run the bot
python main.py

:: If crashed
echo.
echo [WARN] O bot foi encerrado (codigo: %errorlevel%).
echo.
pause
