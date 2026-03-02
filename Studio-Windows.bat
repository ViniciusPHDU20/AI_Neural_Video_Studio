@echo off
TITLE AI NEURAL VIDEO STUDIO - COMMAND CENTER
COLOR 0A

:: --- PATH CONFIGURATION ---
SET "BASE_DIR=%~dp0"
SET "VENV_DIR=%BASE_DIR%.venv"
SET "PYTHON=%VENV_DIR%\Scripts\python.exe"
SET "LAUNCHER=%BASE_DIR%core\launcher.py"

:: --- CHECKS ---
IF NOT EXIST "%PYTHON%" (
    ECHO [X] CRITICAL ERROR: Virtual Environment not found!
    ECHO [!] Please run Install-Windows.bat first.
    PAUSE
    EXIT /B
)

:: --- LAUNCH ---
ECHO [*] Launching Neural Studio Enterprise...
"%PYTHON%" "%LAUNCHER%"
PAUSE
