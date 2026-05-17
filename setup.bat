@echo off
title Anubis - Setup
echo ============================================
echo         Anubis Music Bot - Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python nao encontrado!
    echo Instale Python 3.10+ em: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python encontrado:
python --version
echo.

:: Create virtual environment
if not exist "venv" (
    echo [..] Criando ambiente virtual...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Falha ao criar ambiente virtual!
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado!
) else (
    echo [OK] Ambiente virtual ja existe.
)
echo.

:: Activate and install dependencies
echo [..] Instalando dependencias...
call venv\Scripts\activate.bat

pip install --upgrade pip -q
if %errorlevel% neq 0 (
    echo [WARN] Falha ao atualizar pip, continuando...
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Falha ao instalar dependencias!
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas!
echo.

:: Check .env file
if not exist ".env" (
    echo [WARN] Arquivo .env nao encontrado!
    echo [..] Criando .env a partir do .example.env...
    copy .example.env .env >nul
    echo [INFO] Edite o arquivo .env e configure seu TOKEN do Discord!
) else (
    echo [OK] Arquivo .env encontrado.
)
echo.

:: Create data dirs
if not exist "local_database" mkdir local_database >nul 2>&1
if not exist ".logs" mkdir .logs >nul 2>&1
if not exist ".app_commands_sync_data" mkdir .app_commands_sync_data >nul 2>&1
echo [OK] Diretorios de dados criados.
echo.

:: Check Java for Lavalink
java -version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Java encontrado (necessario para Lavalink local)
    java -version 2>&1 | findstr "version" 
) else (
    echo [WARN] Java nao encontrado!
    echo [..] Instalando Eclipse Temurin JDK 17 via winget...
    echo.
    winget install EclipseAdoptium.Temurin.17.JDK --accept-package-agreements --silent
    if %errorlevel% equ 0 (
        echo [OK] Java 17 instalado com sucesso!
    ) else (
        echo [WARN] Falha ao instalar via winget.
        echo [WARN] Baixe e instale manualmente de: https://adoptium.net/
        echo [WARN] (versao JDK 17 para Windows x64)
    )
)
echo.

echo ============================================
echo  Setup concluido com sucesso!
echo.
echo  Para iniciar o bot:
echo    start.bat
echo.
echo  Para iniciar o Dashboard:
echo    start_dashboard.bat
echo.
echo  Configure o .env com seu TOKEN antes de iniciar!
echo ============================================
echo.
pause
