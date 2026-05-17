@echo off
title Anubis Web Dashboard
echo ============================================
echo     Anubis Web Dashboard v2.0
echo ============================================
echo.

:: Check venv
if not exist "venv" (
    echo [ERROR] Ambiente virtual nao encontrado!
    echo Execute setup.bat primeiro!
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
echo [..] Iniciando Dashboard em http://localhost:3000
echo.
echo Para usar com o bot, mantenha o bot rodando
echo em outro terminal com start.bat
echo.

:: Run dashboard
python -m uvicorn dashboard.main:app --host 0.0.0.0 --port 3000 --reload

echo.
echo Dashboard encerrado.
pause
