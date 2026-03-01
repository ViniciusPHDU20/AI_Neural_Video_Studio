@echo off
title AI Neural Video Studio - STOP
echo ===================================================
echo     DESLIGANDO STUDIO...
echo ===================================================

:: Tenta matar o processo Python que está ouvindo na porta 8188
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8188 ^| findstr LISTENING') do (
    echo [*] Finalizando processo PID: %%a
    taskkill /f /pid %%a
)

echo.
echo [V] Estúdio desligado.
pause
