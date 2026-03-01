#!/bin/bash

# --- Configuração de Caminhos Relativos ---
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$BASE_DIR/.venv"
CORE_PATH="$BASE_DIR/.core"
INPUT_DIR="$BASE_DIR/input"
OUTPUT_DIR="$BASE_DIR/output"
MODELS_CONFIG="$BASE_DIR/extra_model_paths.yaml"

echo "[*] Iniciando AI Neural Video Studio..."

if [ ! -d "$VENV_PATH" ]; then
    echo "[!] Ambiente virtual não encontrado! Execute './install_linux.sh' primeiro."
    exit 1
fi

# Criar pastas de entrada/saída se não existirem
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

# --- Ativação do Ambiente ---
source "$VENV_PATH/bin/activate"

# --- Inicialização do Motor ---
# --listen permite acesso na rede local
python3 "$CORE_PATH/main.py" \
    --input-directory "$INPUT_DIR" \
    --output-directory "$OUTPUT_DIR" \
    --extra-model-paths-config "$MODELS_CONFIG" \
    --listen 0.0.0.0 --port 8188
