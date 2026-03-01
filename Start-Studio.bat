@echo off
setlocal enabledelayedexpansion
title AI Neural Video Studio V1.3.8
cd /d "%~dp0"

:: Verificar se o VENV existe
if not exist ".venv\Scripts\python.exe" (
    echo [!] AMBIENTE VIRTUAL NAO ENCONTRADO!
    echo [?] Rode o Install-Windows.bat primeiro.
    pause
    exit /b
)

echo [*] Iniciando Command Center Blindado V1.3.8...
".venv\Scripts\python.exe" launcher.py
if %errorlevel% neq 0 (
    echo [X] Erro ao abrir o Launcher.
    pause
)
