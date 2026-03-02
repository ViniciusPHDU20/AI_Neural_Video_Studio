@echo off
:: --- AI NEURAL VIDEO STUDIO - WINDOWS ENTRY POINT ---
cd /d "%~dp0"

echo [*] Iniciando Command Center V3.0.1 (Enterprise Architecture)...

if not exist .venv\Scripts\python.exe (
    echo [!] Ambiente virtual nao encontrado!
    echo [?] Rode o instalador em platforms\windows\Install-Windows.bat
    pause
    exit /b 1
)

:: Rodar o launcher dentro da pasta core
start "" ".venv\Scripts\python.exe" "core\launcher.py"
