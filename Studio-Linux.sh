#!/bin/bash
# --- AI NEURAL VIDEO STUDIO - LINUX ENTRY POINT ---
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "[*] Iniciando Command Center V3.0.0 (Enterprise Architecture)..."

if [ ! -f ".venv/bin/python3" ]; then
    echo "[!] Ambiente virtual não encontrado!"
    echo "[?] Rode o instalador em platforms/linux/Install-Linux.sh"
    exit 1
fi

# Rodar o launcher dentro da pasta core
./.venv/bin/python3 core/launcher.py
