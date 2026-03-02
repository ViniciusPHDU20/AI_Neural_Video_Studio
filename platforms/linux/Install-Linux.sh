#!/bin/bash

# --- AI NEURAL VIDEO STUDIO - INSTALLER (LINUX V3.0.1) ---
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$BASE_DIR"

echo "==================================================="
echo "    AI NEURAL VIDEO STUDIO - ENTERPRISE INSTALLER"
echo "==================================================="

# 1. Recuperar Engine se estiver vazia
if [ -z "$(ls -A engine 2>/dev/null)" ]; then
    echo "[!] Pasta Engine vazia. Baixando núcleo ComfyUI..."
    git clone https://github.com/comfyanonymous/ComfyUI.git temp_engine
    mv temp_engine/* engine/
    mv temp_engine/.* engine/ 2>/dev/null
    rm -rf temp_engine
    echo "[V] Núcleo baixado com sucesso."
fi

# 2. Criar VENV
echo "[+] Configurando ambiente virtual..."
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependências base
echo "[+] Instalando dependências base (Torch/CUDA)..."
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 4. Instalar requisitos da Engine
echo "[+] Instalando dependências da Engine..."
if [ -f "engine/requirements.txt" ]; then
    pip install -r engine/requirements.txt
else
    pip install psutil
fi

# 5. Instalar requisitos da Interface
echo "[+] Instalando Interface e Downloader..."
pip install customtkinter darkdetect requests tqdm pillow packaging

# 6. Criar Pastas
mkdir -p models/checkpoints models/loras models/vae workspace/input workspace/output config

# 7. ComfyUI Manager
echo "[+] Verificando ComfyUI Manager..."
mkdir -p engine/custom_nodes
if [ ! -d "engine/custom_nodes/ComfyUI-Manager" ]; then
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git engine/custom_nodes/ComfyUI-Manager
fi

echo "==================================================="
echo "[V] Instalação V3.0.1 Concluída!"
echo "Use './Studio-Linux.sh' para iniciar."
echo "==================================================="
