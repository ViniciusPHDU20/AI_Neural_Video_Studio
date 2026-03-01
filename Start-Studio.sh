#!/bin/bash

# --- AI NEURAL VIDEO STUDIO - STARTER (LINUX) ---
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo "[*] Abrindo Command Center V2.2.0..."

if [ ! -f ".venv/bin/python3" ]; then
    echo "[!] Ambiente virtual não encontrado!"
    echo "[?] Deseja rodar o instalador agora? (s/n)"
    read choice
    if [ "$choice" == "s" ]; then
        bash Install-Linux.sh
    else
        exit 1
    fi
fi

# Rodar via Python do VENV diretamente para evitar erros de import
./.venv/bin/python3 launcher.py
