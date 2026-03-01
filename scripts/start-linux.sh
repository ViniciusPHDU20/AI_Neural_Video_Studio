#!/bin/bash

# --- AI Neural Video Studio - Engine Launcher ---
# Este script é chamado pelo Launcher ou manualmente.

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$BASE_DIR/.venv"
ENGINE_DIR="$BASE_DIR/engine"
WORKSPACE_DIR="$BASE_DIR/workspace"
CONFIG_DIR="$BASE_DIR/config"

echo "[*] Ativando Motor em: $ENGINE_DIR"

if [ ! -d "$VENV_PATH" ]; then
    echo "[!] Ambiente virtual não encontrado na raiz!"
    exit 1
fi

source "$VENV_PATH/bin/activate"

# Rodar a Engine
python3 "$ENGINE_DIR/main.py" \
    --input-directory "$WORKSPACE_DIR/input" \
    --output-directory "$WORKSPACE_DIR/output" \
    --extra-model-paths-config "$CONFIG_DIR/extra_model_paths.yaml" \
    --listen 127.0.0.1 --port 8188 --lowvram --fp8_e4m3fn-text-enc
