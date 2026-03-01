#!/bin/bash

# --- AI NEURAL VIDEO STUDIO - INSTALLER (LINUX) ---
# Forçando o diretório para a raiz do script
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "==================================================="
echo "    AI NEURAL VIDEO STUDIO - INSTALLER (LINUX)"
echo "==================================================="

# 1. Criar VENV
echo "[+] Criando ambiente virtual..."
python3 -m venv .venv

# 2. Ativar e Instalar
source .venv/bin/activate

echo "[+] Instalando dependências base (Torch/CUDA)..."
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo "[+] Instalando dependências da Engine..."
if [ -f "engine/requirements.txt" ]; then
    pip install -r engine/requirements.txt
else
    echo "[!] Alerta: engine/requirements.txt não encontrado. Instalando básicos..."
    pip install psutil
fi

echo "[+] Instalando Interface e Downloader..."
pip install customtkinter darkdetect requests tqdm pillow packaging

# 3. Criar Pastas
echo "[+] Organizando estrutura de pastas..."
mkdir -p models/checkpoints models/loras models/vae workspace/input workspace/output config

# 4. ComfyUI Manager
if [ -d "engine/custom_nodes" ]; then
    echo "[+] Instalando ComfyUI Manager..."
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git engine/custom_nodes/ComfyUI-Manager 2>/dev/null || echo "[*] Manager já existe."
fi

echo "==================================================="
echo "[V] Instalação Concluída!"
echo "Use './Start-Studio.sh' para iniciar."
echo "==================================================="
