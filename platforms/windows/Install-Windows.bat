@echo off
setlocal enabledelayedexpansion
title AI Neural Video Studio - Intelligence Installer V3.0.0
echo ===================================================
echo     INICIANDO INSTALACAO (ENTERPRISE ARCH)
echo ===================================================

cd /d "%~dp0..\.."

:: 1. Localizar Python Real (Ignorando Microsoft Store)
echo [*] Localizando interpretador Python real...
set PY_REAL=
for %%P in (python.exe) do (
    set "TEST_PY=%%~$PATH:P"
    if defined TEST_PY (
        echo !TEST_PY! | findstr /i "WindowsApps" > nul
        if errorlevel 1 (
            set "PY_REAL=!TEST_PY!"
        )
    )
)

if not defined PY_REAL (
    echo [!] Buscando em pastas padrao...
    if exist "C:\Python311\python.exe" set PY_REAL=C:\Python311\python.exe
    if exist "C:\Python310\python.exe" set PY_REAL=C:\Python310\python.exe
    if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set PY_REAL=%LocalAppData%\Programs\Python\Python311\python.exe
    if exist "%LocalAppData%\Programs\Python\Python310\python.exe" set PY_REAL=%LocalAppData%\Programs\Python\Python310\python.exe
)

if not defined PY_REAL (
    echo [X] ERRO: Nao encontrei um Python instalado corretamente.
    echo [!] Por favor, instale o Python 3.10 ou 3.11 do site python.org.
    pause
    exit /b
)

echo [V] Python encontrado em: %PY_REAL%
"%PY_REAL%" --version

:: 2. Detectar GPU
echo [*] Detectando Hardware...
set GPU=CPU
powershell -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name" | findstr /i "NVIDIA" > nul
if %errorlevel% equ 0 set GPU=NVIDIA
powershell -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name" | findstr /i "AMD" > nul
if %errorlevel% equ 0 set GPU=AMD
echo [+] GPU Identificada: %GPU%

:: 3. Criar Ambiente Virtual (Na Raiz)
if exist ".venv" (
    echo [!] Pasta .venv detectada na raiz. Reinstalando...
    rd /s /q .venv
)

echo [*] Criando ambiente virtual na raiz do projeto...
"%PY_REAL%" -m venv .venv
if %errorlevel% neq 0 (
    echo [X] ERRO CRITICO ao criar ambiente. Tente rodar como Administrador.
    pause
    exit /b
)
echo [V] Ambiente virtual criado.

:: 4. Instalar Dependencias
echo [*] Ativando e Instalando pacotes...
call .venv\Scripts\activate

echo [*] Instalando Pilha IA (PyTorch 2.5.1 + CUDA/DirectML)...
if "%GPU%"=="NVIDIA" (
    pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    pip install xformers==0.0.28.post3 --index-url https://download.pytorch.org/whl/cu121
) else if "%GPU%"=="AMD" (
    pip install torch-directml torchvision torchaudio
) else (
    pip install torch torchvision torchaudio
)

pip install huggingface-hub psutil customtkinter darkdetect requests tqdm pillow packaging
if exist "engine\requirements.txt" pip install -r engine\requirements.txt

:: 5. Finalizar
if not exist "models\checkpoints" mkdir models\checkpoints
if not exist "models\loras" mkdir models\loras
if not exist "models\vae" mkdir models\vae
if not exist "workspace\input" mkdir workspace\input
if not exist "workspace\output" mkdir workspace\output

echo ===================================================
echo [V] ESTUDIO V3.0.0 INSTALADO COM SUCESSO!
echo ===================================================
pause
