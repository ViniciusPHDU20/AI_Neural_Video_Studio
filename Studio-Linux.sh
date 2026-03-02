#!/bin/bash
# --- AI NEURAL VIDEO STUDIO - LINUX ENTRY POINT ---
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "[*] Iniciando Command Center V3.0.1 (Enterprise Architecture)..."

if [ ! -f ".venv/bin/activate" ]; then
    echo "[!] Ambiente virtual não encontrado!"
    echo "[?] Rode o instalador em platforms/linux/Install-Linux.sh"
    exit 1
fi

# Ativar o ambiente virtual
source .venv/bin/activate

# Rodar o launcher
python3 core/launcher.py
