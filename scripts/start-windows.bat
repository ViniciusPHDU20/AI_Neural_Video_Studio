@echo off
setlocal enabledelayedexpansion
title AI Neural Video Studio - Engine Launcher
cd /d %~dp0..

set ARGS=--input-directory "workspace\input" --output-directory "workspace\output" --extra-model-paths-config "config\extra_model_paths.yaml" --listen 127.0.0.1 --port 8188 --lowvram --fp8_e4m3fn-text-enc

:: Detectar se deve usar DirectML (AMD) via PowerShell
powershell -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name" | findstr /i "AMD" > nul
if %errorlevel% equ 0 (
    set ARGS=!ARGS! --directml
    echo [*] Modo AMD (DirectML) Ativado via CIM.
) else (
    echo [*] Modo NVIDIA (CUDA) Ativado via CIM.
)

if not exist "%~dp0..\.venv" (
    echo [!] ERRO: Ambiente virtual nao encontrado em: %~dp0..\.venv
    pause
    exit /b
)

echo [*] Ativando Motor em: %~dp0..\engine
cd /d "%~dp0.."
.venv\Scripts\python.exe engine\main.py %ARGS%
if %errorlevel% neq 0 (
    echo [X] A ENGINE PAROU OU FALHOU AO INICIAR.
    pause
)
