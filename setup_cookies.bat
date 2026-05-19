@echo off
title Anubis - Configurar Cookies YouTube
echo ============================================
echo   Anubis Music Bot - Configurar Cookies
echo ============================================
echo.
echo Este script vai copiar seu arquivo de cookies
echo do YouTube para o bot usar.
echo.
echo Requisitos:
echo   1. Instale "Get cookies.txt LOCALLY" no Chrome/Firefox
echo   2. Va no youtube.com e exporte os cookies
echo   3. Coloque o arquivo exportado na pasta Anubis2.0
echo.
echo ============================================
echo.

set /p cookiefile="Nome do arquivo de cookies (ex: youtube.com_cookies.txt): "

if not exist "%cookiefile%" (
    echo ERRO: Arquivo "%cookiefile%" nao encontrado!
    echo Certifique-se de colocar o arquivo na pasta correta.
    pause
    exit /b 1
)

copy /Y "%cookiefile%" "youtube_cookies_user.txt" >nul
echo.
echo OK! Cookies copiados para youtube_cookies_user.txt
echo.
echo O bot vai usar este arquivo automaticamente.
echo Para aplicar no Docker, reconstrua a imagem ou
echo adicione o arquivo ao volume.
echo.
pause
